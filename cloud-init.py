import os
import sys
import secrets
import time

from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider, NodeState

import libcloud.security
libcloud.security.CA_CERTS_PATH = ['./root-ca.crt']

# openstacksdk drives Octavia (managed load balancer); libcloud has no LB driver.
from openstack import connection

group_number = 22  # define group number

AUTH_URL = 'https://10.32.4.29:5000'
AUTH_USERNAME = 'CloudComp' + str(group_number)
AUTH_PASSWORD = 'demo'
print(f'Using username: {AUTH_USERNAME}\n')
PROJECT_NAME = 'CloudComp' + str(group_number)
PROJECT_NETWORK = 'CloudComp' + str(group_number) + '-net'
DOMAIN_NAME = 'Default'
UBUNTU_IMAGE_NAME = "ubuntu-22.04-jammy-server-cloud-image-amd64"

KEYPAIR_NAME = 'groupproject-pub'
PUB_KEY_FILE = os.path.expanduser('~/.ssh/cloudcomp.pub')

FLAVOR_NAME = 'm1.small'

# How many instances of each tier to spawn behind their Octavia load balancer.
NUM_BACKEND_INSTANCES = 1
NUM_FRONTEND_INSTANCES = 1

REGION_NAME = 'RegionOne'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    jwt_secret = secrets.token_hex(32)

    # libcloud connection — compute (instances, keypairs, security groups)
    provider = get_driver(Provider.OPENSTACK)
    conn = provider(AUTH_USERNAME,
                    AUTH_PASSWORD,
                    ex_force_auth_url=AUTH_URL,
                    ex_force_auth_version='3.x_password',
                    ex_tenant_name=PROJECT_NAME,
                    ex_force_service_region=REGION_NAME)

    # openstacksdk connection — Octavia load balancers + floating IPs
    os_conn = connection.Connection(
        auth_url=AUTH_URL,
        username=AUTH_USERNAME,
        password=AUTH_PASSWORD,
        project_name=PROJECT_NAME,
        user_domain_name=DOMAIN_NAME,
        project_domain_name=DOMAIN_NAME,
        region_name=REGION_NAME,
        verify='./root-ca.crt',
    )

    # get image, flavor, network for instance creation
    images = conn.list_images()
    image = ''
    for img in images:
        if img.name == UBUNTU_IMAGE_NAME:
            image = img

    flavors = conn.list_sizes()
    flavor = ''
    for flav in flavors:
        if flav.name == FLAVOR_NAME:
            flavor = conn.ex_get_size(flav.id)

    # external network for floating IPs (openstacksdk)
    ext_net = next(os_conn.network.networks(is_router_external=True))
    ext_net_id = ext_net.id

    # ensure the project network / subnet / router exist — a fresh project has
    # none, in which case find_network() returns None and the LB/instances have
    # nowhere to attach. Each step below is idempotent.
    network_sdk = os_conn.network.find_network(PROJECT_NETWORK)
    if network_sdk is None:
        print(f'Creating network {PROJECT_NETWORK}...')
        network_sdk = os_conn.network.create_network(name=PROJECT_NETWORK)

    subnets = list(os_conn.network.subnets(network_id=network_sdk.id))
    if subnets:
        subnet = subnets[0]
    else:
        print(f'Creating subnet for {PROJECT_NETWORK}...')
        subnet = os_conn.network.create_subnet(
            name=PROJECT_NETWORK + '-subnet',
            network_id=network_sdk.id,
            ip_version=4,
            cidr='10.0.0.0/24',
            gateway_ip='10.0.0.1',
            is_dhcp_enabled=True,
            dns_nameservers=['8.8.8.8'],
        )
    subnet_id = subnet.id

    # router gives the subnet a default gateway to ext_net (SNAT for outbound
    # internet so cloud-init can git clone, plus floating-IP connectivity)
    router_name = PROJECT_NETWORK + '-router'
    router = os_conn.network.find_router(router_name)
    if router is None:
        print(f'Creating router {router_name}...')
        router = os_conn.network.create_router(
            name=router_name,
            external_gateway_info={'network_id': ext_net_id})
    try:
        os_conn.network.add_interface_to_router(router, subnet_id=subnet_id)
    except Exception:
        pass  # subnet already attached to the router

    # libcloud network object for instance creation (re-list so we pick up a
    # network we may have just created above)
    network = ''
    for net in conn.ex_list_networks():
        if net.name == PROJECT_NETWORK:
            network = net
    if network == '':
        raise SystemExit(
            f'libcloud cannot see network {PROJECT_NETWORK} after creation')

    # delete old keypair and re-import so the local key is always in sync
    print('Syncing SSH key pair...')
    for keypair in conn.list_key_pairs():
        if keypair.name == KEYPAIR_NAME:
            conn.delete_key_pair(keypair)
            print(f'Deleted old keypair {KEYPAIR_NAME}')
    conn.import_key_pair_from_file(KEYPAIR_NAME, PUB_KEY_FILE)
    print(f'Imported keypair from {PUB_KEY_FILE}')

    # delete existing load balancers first (cascade removes listeners/pools/members
    # and frees their floating IPs for reuse)
    print('Deleting existing load balancers...')
    for lb in os_conn.load_balancer.load_balancers():
        print(f'Deleting load balancer {lb.name}')
        os_conn.load_balancer.delete_load_balancer(lb, cascade=True)
        os_conn.load_balancer.wait_for_delete(lb)

    # destroy every instance
    for instance in conn.list_nodes():
        conn.destroy_node(instance)

    # wait until all nodes are destroyed to be able to remove depended security groups
    nodes_still_running = True
    while nodes_still_running:
        nodes_still_running = False
        time.sleep(3)
        instances = conn.list_nodes()
        for instance in instances:
            if instance.state not in (NodeState.TERMINATED, NodeState.UNKNOWN):
                nodes_still_running = True
                print('There are still instances running, waiting for them to be destroyed...')

    # delete any leftover security groups from previous runs — otherwise the
    # names below collide and libcloud can't resolve e.g. 'ssh' to one group
    managed_sg_names = {'ssh', 'icmp', 'postgres', 'login', 'backend', 'frontend'}
    for sg in conn.ex_list_security_groups():
        if sg.name in managed_sg_names:
            conn.ex_delete_security_group(sg)
            print(f'Deleted old security group {sg.name}')

    # create security groups
    sg_ssh = conn.ex_create_security_group('ssh', 'SSH access')
    conn.ex_create_security_group_rule(sg_ssh, 'tcp', 22, 22, cidr='0.0.0.0/0')

    sg_icmp = conn.ex_create_security_group('icmp', 'ICMP ping')
    conn.ex_create_security_group_rule(sg_icmp, 'icmp', -1, -1, cidr='0.0.0.0/0')

    sg_postgres = conn.ex_create_security_group('postgres', 'PostgreSQL port 5432')
    conn.ex_create_security_group_rule(sg_postgres, 'tcp', 5432, 5432, cidr='0.0.0.0/0')

    sg_login = conn.ex_create_security_group('login', 'Login service port 8001')
    conn.ex_create_security_group_rule(sg_login, 'tcp', 8001, 8001, cidr='0.0.0.0/0')

    sg_backend = conn.ex_create_security_group('backend', 'FastAPI backend port 8000')
    conn.ex_create_security_group_rule(sg_backend, 'tcp', 8000, 8000, cidr='0.0.0.0/0')

    sg_frontend = conn.ex_create_security_group('frontend', 'Next.js frontend port 80')
    conn.ex_create_security_group_rule(sg_frontend, 'tcp', 80, 80, cidr='0.0.0.0/0')

    ###########################################################################
    #
    # floating IP helpers (openstacksdk)
    #
    ###########################################################################

    _reserved_ips = set()

    def get_floating_ip():
        """Re-use an unassociated Floating IP, else allocate a new one."""
        for fip in os_conn.network.ips():
            if not fip.port_id and fip.floating_ip_address not in _reserved_ips:
                _reserved_ips.add(fip.floating_ip_address)
                return fip
        fip = os_conn.network.create_ip(floating_network_id=ext_net_id)
        _reserved_ips.add(fip.floating_ip_address)
        return fip

    def attach_floating_ip_to_node(node, fip):
        """Associate a floating IP with a libcloud node via its Neutron port."""
        port = next(iter(os_conn.network.ports(device_id=node.id)))
        os_conn.network.update_ip(fip, port_id=port.id)

    def attach_floating_ip_to_lb(lb, fip):
        """Associate a floating IP with an Octavia LB's VIP port."""
        os_conn.network.update_ip(fip, port_id=lb.vip_port_id)

    ###########################################################################
    #
    # instance / load-balancer helper functions
    #
    ###########################################################################

    def create_instances(count, base_name, security_groups, userdata):
        """Boot `count` identical instances and return their private IPs."""
        nodes = []
        for i in range(count):
            name = base_name if count == 1 else f'{base_name}-{i + 1}'
            print(f'Starting {name} instance...')
            nodes.append(conn.create_node(
                name=name,
                image=image,
                size=flavor,
                networks=[network],
                ex_keyname=KEYPAIR_NAME,
                ex_security_groups=security_groups,
                ex_userdata=userdata,
            ))
        running = conn.wait_until_running(nodes=nodes, timeout=300,
                                          ssh_interface='private_ips')
        private_ips = [node.private_ips[0] for node, _ in running]
        for node, _ in running:
            print(f'{node.name} private IP: {node.private_ips[0]}')
        return private_ips

    def create_load_balancer(name, listen_port, member_ips, member_port):
        """Create an Octavia load balancer balancing TCP traffic across member_ips."""
        print(f'Creating Octavia load balancer {name}...')
        lb = os_conn.load_balancer.create_load_balancer(
            name=name, vip_subnet_id=subnet_id)
        os_conn.load_balancer.wait_for_load_balancer(
            lb.id, status='ACTIVE', failures=['ERROR'], interval=5, wait=600)

        listener = os_conn.load_balancer.create_listener(
            name=f'{name}-listener', load_balancer_id=lb.id,
            protocol='TCP', protocol_port=listen_port)
        os_conn.load_balancer.wait_for_load_balancer(lb.id, interval=5, wait=600)

        pool = os_conn.load_balancer.create_pool(
            name=f'{name}-pool', listener_id=listener.id,
            protocol='TCP', lb_algorithm='ROUND_ROBIN')
        os_conn.load_balancer.wait_for_load_balancer(lb.id, interval=5, wait=600)

        os_conn.load_balancer.create_health_monitor(
            name=f'{name}-hm', pool_id=pool.id, type='TCP',
            delay=5, timeout=3, max_retries=3)
        os_conn.load_balancer.wait_for_load_balancer(lb.id, interval=5, wait=600)

        # Octavia goes PENDING_UPDATE between operations, so wait after each member.
        for ip in member_ips:
            os_conn.load_balancer.create_member(
                pool.id, address=ip, protocol_port=member_port, subnet_id=subnet_id)
            os_conn.load_balancer.wait_for_load_balancer(lb.id, interval=5, wait=600)
            print(f'  added member {ip}:{member_port}')

        return lb

    # ── Databases ─────────────────────────────────────────────────────────────

    db_script = open(os.path.join(BASE_DIR, 'cloud-init-database.sh')).read()
    login_db_script = db_script.replace('INSTALL_login=0', 'INSTALL_login=1')
    user_db_script  = db_script.replace('INSTALL_userdata=0', 'INSTALL_userdata=1')

    print('Starting login-database instance...')
    node_login_db = conn.create_node(
        name='login-database',
        image=image,
        size=flavor,
        networks=[network],
        ex_keyname=KEYPAIR_NAME,
        ex_security_groups=[sg_ssh, sg_icmp, sg_postgres],
        ex_userdata=login_db_script,
    )
    node_login_db = conn.wait_until_running(nodes=[node_login_db], timeout=120,
                                            ssh_interface='private_ips')[0][0]
    login_database_ip = node_login_db.private_ips[0]
    print(f'login-database private IP: {login_database_ip}')

    print('Starting userdata-database instance...')
    node_user_db = conn.create_node(
        name='userdata-database',
        image=image,
        size=flavor,
        networks=[network],
        ex_keyname=KEYPAIR_NAME,
        ex_security_groups=[sg_ssh, sg_icmp, sg_postgres],
        ex_userdata=user_db_script,
    )
    node_user_db = conn.wait_until_running(nodes=[node_user_db], timeout=120,
                                           ssh_interface='private_ips')[0][0]
    userdata_database_ip = node_user_db.private_ips[0]
    print(f'userdata-database private IP: {userdata_database_ip}')

    # Pre-allocate frontend floating IP so backend/login can set it as CORS origin
    floating_ip_frontend = get_floating_ip()
    frontend_origin = f'http://{floating_ip_frontend.floating_ip_address}'
    print(f'Pre-allocated frontend IP: {floating_ip_frontend.floating_ip_address}')

    # ── Login service ──────────────────────────────────────────────────────────

    login_db_url = f'postgresql://postgres:postgres@{login_database_ip}:5432/appdb'
    login_script = open(os.path.join(BASE_DIR, 'cloud-init-login.sh')).read()
    login_userdata = login_script.replace('#!/bin/bash\n',
        f'#!/bin/bash\n'
        f'export DATABASE_URL="{login_db_url}"\n'
        f'export JWT_SECRET_KEY="{jwt_secret}"\n'
        f'export CORS_ORIGINS="{frontend_origin}"\n')

    print('Starting login-service instance...')
    node_login = conn.create_node(
        name='login-service',
        image=image,
        size=flavor,
        networks=[network],
        ex_keyname=KEYPAIR_NAME,
        ex_security_groups=[sg_ssh, sg_icmp, sg_login],
        ex_userdata=login_userdata,
    )
    node_login = conn.wait_until_running(nodes=[node_login], timeout=120,
                                         ssh_interface='private_ips')[0][0]

    floating_ip_login = get_floating_ip()
    attach_floating_ip_to_node(node_login, floating_ip_login)
    print('Login service IP: ' + floating_ip_login.floating_ip_address)

    # ── Backend ────────────────────────────────────────────────────────────────

    database_url = f'postgresql://postgres:postgres@{userdata_database_ip}:5432/appdb'
    backend_script = open(os.path.join(BASE_DIR, 'cloud-init-backend.sh')).read()
    backend_userdata = backend_script.replace('#!/bin/bash\n',
        f'#!/bin/bash\n'
        f'export DATABASE_URL="{database_url}"\n'
        f'export JWT_SECRET_KEY="{jwt_secret}"\n'
        f'export CORS_ORIGINS="{frontend_origin}"\n')

    backend_private_ips = create_instances(
        NUM_BACKEND_INSTANCES, 'backend',
        [sg_ssh, sg_icmp, sg_backend], backend_userdata)

    # Octavia LB is the public entry point; instances stay on the private net.
    lb_backend = create_load_balancer('backend-lb', 8000, backend_private_ips, 8000)
    floating_ip_backend = get_floating_ip()
    attach_floating_ip_to_lb(lb_backend, floating_ip_backend)
    print('Backend load balancer IP: ' + floating_ip_backend.floating_ip_address)

    # ── Frontend ───────────────────────────────────────────────────────────────
    # Both API URLs must be known at build time (NEXT_PUBLIC_* are baked in by Next.js)

    backend_api_url = f'http://{floating_ip_backend.floating_ip_address}:8000'
    login_api_url = f'http://{floating_ip_login.floating_ip_address}:8001'
    frontend_script = open(os.path.join(BASE_DIR, 'cloud-init-frontend.sh')).read()
    frontend_userdata = frontend_script.replace('#!/bin/bash\n',
        f'#!/bin/bash\n'
        f'export NEXT_PUBLIC_API_URL="{backend_api_url}"\n'
        f'export NEXT_PUBLIC_LOGIN_URL="{login_api_url}"\n')

    frontend_private_ips = create_instances(
        NUM_FRONTEND_INSTANCES, 'frontend',
        [sg_ssh, sg_icmp, sg_frontend], frontend_userdata)

    # Frontend load balancer takes the pre-allocated floating IP (the public URL).
    lb_frontend = create_load_balancer('frontend-lb', 80, frontend_private_ips, 80)
    attach_floating_ip_to_lb(lb_frontend, floating_ip_frontend)
    print('Frontend load balancer IP: ' + floating_ip_frontend.floating_ip_address)

    print('\n=== Deployment complete ===')
    print(f'Frontend:      http://{floating_ip_frontend.floating_ip_address}'
          f'  ({NUM_FRONTEND_INSTANCES} instance(s) behind LB)')
    print(f'Backend:       http://{floating_ip_backend.floating_ip_address}:8000'
          f'  ({NUM_BACKEND_INSTANCES} instance(s) behind LB)')
    print(f'Login service: http://{floating_ip_login.floating_ip_address}:8001')


if __name__ == '__main__':
    main()
