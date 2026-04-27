import os
import sys
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
PUB_KEY_FILE = '~/.ssh/id_ed25519.pub'

FLAVOR_NAME = 'm1.small'

REGION_NAME = 'RegionOne'


def main():
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

    # create keypair dependency
    print('Checking for existing SSH key pair...')
    keypair_exists = False
    for keypair in conn.list_key_pairs():
        if keypair.name == KEYPAIR_NAME:
            keypair_exists = True

    if keypair_exists:
        print(('Keypair ' + KEYPAIR_NAME + ' already exists. Skipping import.'))
    else:
        print('adding keypair...')
        conn.import_key_pair_from_file(KEYPAIR_NAME, PUB_KEY_FILE)

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

    # create security group dependency
    # TODO

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


    # create database
    database_cloud_init_script = 'https://raw.githubusercontent.com/Melonmain/CloudComputing/refs/heads/Database/cloud-init-database.sh'

    userdata_service = '#!/usr/bin/env bash\n' \
               f'curl -L -s {database_cloud_init_script} | bash -s -- -i login'

    print('Starting login database instance and wait until it is running...')
    instance_services = conn.create_node(name='login-database',
                                         image=image,
                                         size=flavor,
                                         networks=[network],
                                         ex_keyname=KEYPAIR_NAME,
                                         ex_userdata=userdata_service)
    instance_services = conn.wait_until_running(nodes=[instance_services], timeout=120,
                                                ssh_interface='private_ips')[0][0]
    login_database_ip = instance_services.private_ips[0]

    userdata_service = '#!/usr/bin/env bash\n' \
               f'curl -L -s {database_cloud_init_script} | bash -s -- -i user'

    print('Starting userdata database instance and wait until it is running...')
    instance_services = conn.create_node(name='userdata-database',
                                         image=image,
                                         size=flavor,
                                         networks=[network],
                                         ex_keyname=KEYPAIR_NAME,
                                         ex_userdata=userdata_service)
    instance_services = conn.wait_until_running(nodes=[instance_services], timeout=120,
                                                ssh_interface='private_ips')[0][0]
    userdata_database_ip = instance_services.private_ips[0]


    # create login-service

    # create backend


if __name__ == '__main__':
    main()
