import os
import sys
import secrets
import time

from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider

import libcloud.security
libcloud.security.CA_CERTS_PATH = ['./root-ca.crt']

group_number = 22  # define group number

AUTH_URL = 'https://10.32.4.29:5000'
AUTH_USERNAME = 'CloudComp' + str(group_number)
AUTH_PASSWORD = 'demo'
print(f'Using username: {AUTH_USERNAME}\n')
PROJECT_NAME = 'CloudComp' + str(group_number)
PROJECT_NETWORK = 'CloudComp' + str(group_number) + '-net'
UBUNTU_IMAGE_NAME = "ubuntu-22.04-jammy-server-cloud-image-amd64"

KEYPAIR_NAME = 'groupproject-pub'
PUB_KEY_FILE = os.path.expanduser('~/.ssh/cloudcomp.pub')

FLAVOR_NAME = 'm1.small'

REGION_NAME = 'RegionOne'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    jwt_secret = secrets.token_hex(32)

    # create connection
    provider = get_driver(Provider.OPENSTACK)
    conn = provider(AUTH_USERNAME,
                    AUTH_PASSWORD,
                    ex_force_auth_url=AUTH_URL,
                    ex_force_auth_version='3.x_password',
                    ex_tenant_name=PROJECT_NAME,
                    ex_force_service_region=REGION_NAME)

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

    networks = conn.ex_list_networks()
    network = ''
    for net in networks:
        if net.name == PROJECT_NETWORK:
            network = net

    # delete old keypair and re-import so the local key is always in sync
    print('Syncing SSH key pair...')
    for keypair in conn.list_key_pairs():
        if keypair.name == KEYPAIR_NAME:
            conn.delete_key_pair(keypair)
            print(f'Deleted old keypair {KEYPAIR_NAME}')
    conn.import_key_pair_from_file(KEYPAIR_NAME, PUB_KEY_FILE)
    print(f'Imported keypair from {PUB_KEY_FILE}')

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
            nodes_still_running = True
            print('There are still instances running, waiting for them to be destroyed...')

    # delete security groups
    for group in conn.ex_list_security_groups():
        if group.name.startswith('default'):
            continue
        conn.ex_delete_security_group(group)

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
    # get floating ip helper function
    #
    ###########################################################################

    def get_floating_ip(connection):
        """A helper function to re-use available Floating IPs"""
        unused_floating_ip = None
        for float_ip in connection.ex_list_floating_ips():
            if not float_ip.node_id:
                unused_floating_ip = float_ip
                break
        if not unused_floating_ip:
            pool = connection.ex_list_floating_ip_pools()[0]
            unused_floating_ip = pool.create_floating_ip()
        return unused_floating_ip

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

    # ── Login service ──────────────────────────────────────────────────────────

    login_db_url = f'postgresql://postgres:postgres@{login_database_ip}:5432/appdb'
    login_script = open(os.path.join(BASE_DIR, 'cloud-init-login.sh')).read()
    login_userdata = login_script.replace('#!/bin/bash\n',
        f'#!/bin/bash\n'
        f'export DATABASE_URL="{login_db_url}"\n'
        f'export JWT_SECRET_KEY="{jwt_secret}"\n'
        f'export CORS_ORIGINS="*"\n')

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

    floating_ip_login = get_floating_ip(conn)
    conn.ex_attach_floating_ip_to_node(node_login, floating_ip_login)
    print('Login service IP: ' + floating_ip_login.ip_address)

    # ── Backend ────────────────────────────────────────────────────────────────

    database_url = f'postgresql://postgres:postgres@{userdata_database_ip}:5432/appdb'
    backend_script = open(os.path.join(BASE_DIR, 'cloud-init-backend.sh')).read()
    backend_userdata = backend_script.replace('#!/bin/bash\n',
        f'#!/bin/bash\n'
        f'export DATABASE_URL="{database_url}"\n'
        f'export JWT_SECRET_KEY="{jwt_secret}"\n'
        f'export CORS_ORIGINS="*"\n')

    print('Starting backend instance...')
    node_backend = conn.create_node(
        name='backend',
        image=image,
        size=flavor,
        networks=[network],
        ex_keyname=KEYPAIR_NAME,
        ex_security_groups=[sg_ssh, sg_icmp, sg_backend],
        ex_userdata=backend_userdata,
    )
    node_backend = conn.wait_until_running(nodes=[node_backend], timeout=120,
                                           ssh_interface='private_ips')[0][0]

    floating_ip_backend = get_floating_ip(conn)
    conn.ex_attach_floating_ip_to_node(node_backend, floating_ip_backend)
    print('Backend IP: ' + floating_ip_backend.ip_address)

    # ── Frontend ───────────────────────────────────────────────────────────────
    # Both API URLs must be known at build time (NEXT_PUBLIC_* are baked in by Next.js)

    backend_api_url = f'http://{floating_ip_backend.ip_address}:8000'
    login_api_url = f'http://{floating_ip_login.ip_address}:8001'
    frontend_script = open(os.path.join(BASE_DIR, 'cloud-init-frontend.sh')).read()
    frontend_userdata = frontend_script.replace('#!/bin/bash\n',
        f'#!/bin/bash\n'
        f'export NEXT_PUBLIC_API_URL="{backend_api_url}"\n'
        f'export NEXT_PUBLIC_LOGIN_URL="{login_api_url}"\n')

    print('Starting frontend instance...')
    node_frontend = conn.create_node(
        name='frontend',
        image=image,
        size=flavor,
        networks=[network],
        ex_keyname=KEYPAIR_NAME,
        ex_security_groups=[sg_ssh, sg_icmp, sg_frontend],
        ex_userdata=frontend_userdata,
    )
    node_frontend = conn.wait_until_running(nodes=[node_frontend], timeout=120,
                                            ssh_interface='private_ips')[0][0]

    floating_ip_frontend = get_floating_ip(conn)
    conn.ex_attach_floating_ip_to_node(node_frontend, floating_ip_frontend)
    print('Frontend IP: ' + floating_ip_frontend.ip_address)

    print('\n=== Deployment complete ===')
    print(f'Frontend:      http://{floating_ip_frontend.ip_address}')
    print(f'Backend:       http://{floating_ip_backend.ip_address}:8000')
    print(f'Login service: http://{floating_ip_login.ip_address}:8001')


if __name__ == '__main__':
    main()
