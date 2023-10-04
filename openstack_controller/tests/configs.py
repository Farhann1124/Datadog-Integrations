# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import os

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
TEST_OPENSTACK_CONFIG_UNIT_TESTS_PATH = os.path.join(CONFIG_DIR, 'openstack_config_unit_tests.yaml')
TEST_OPENSTACK_CONFIG_E2E_PATH = os.path.join(CONFIG_DIR, 'openstack_config.yaml')
TEST_OPENSTACK_UPDATED_CONFIG_E2E_PATH = os.path.join(CONFIG_DIR, 'openstack_config_updated.yaml')
TEST_OPENSTACK_BAD_CONFIG_PATH = os.path.join(CONFIG_DIR, 'openstack_bad_config.yaml')

REST = {
    'keystone_server_url': 'http://127.0.0.1:8080/identity',
    'username': 'admin',
    'password': 'password',
}

REST_NOVA_MICROVERSION_2_93 = {
    'keystone_server_url': 'http://127.0.0.1:8080/identity',
    'username': 'admin',
    'password': 'password',
    'nova_microversion': '2.93',
}

REST_IRONIC_MICROVERSION_1_80 = {
    'keystone_server_url': 'http://127.0.0.1:8080/identity',
    'username': 'admin',
    'password': 'password',
    'ironic_microversion': '1.80',
}

SDK = {
    'openstack_cloud_name': 'test_cloud',
    'openstack_config_file_path': TEST_OPENSTACK_CONFIG_UNIT_TESTS_PATH,
}

SDK_NOVA_MICROVERSION_2_93 = {
    'openstack_cloud_name': 'test_cloud',
    'openstack_config_file_path': TEST_OPENSTACK_CONFIG_UNIT_TESTS_PATH,
    'nova_microversion': '2.93',
}

SDK_IRONIC_MICROVERSION_1_80 = {
    'openstack_cloud_name': 'test_cloud',
    'openstack_config_file_path': TEST_OPENSTACK_CONFIG_UNIT_TESTS_PATH,
    'ironic_microversion': '1.80',
}