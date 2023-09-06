# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

# This file is autogenerated.
# To change this file you should edit assets/configuration/spec.yaml and then run the following commands:
#     ddev -x validate config -s <INTEGRATION_NAME>
#     ddev -x validate models -s <INTEGRATION_NAME>


def shared_skip_proxy():
    return False


def shared_timeout():
    return 10


def instance_allow_redirects():
    return True


def instance_auth_type():
    return 'basic'


def instance_disable_generic_tags():
    return False


def instance_empty_default_hostname():
    return False


def instance_kerberos_auth():
    return 'disabled'


def instance_kerberos_delegate():
    return False


def instance_kerberos_force_initiate():
    return False


def instance_log_requests():
    return False


def instance_max_lookback():
    return 60


def instance_min_collection_interval():
    return 15


def instance_persist_connections():
    return False


def instance_request_size():
    return 16


def instance_results_per_page():
    return 100


def instance_skip_proxy():
    return False


def instance_timeout():
    return 10


def instance_tls_ignore_warning():
    return False


def instance_tls_use_host_header():
    return False


def instance_tls_verify():
    return True


def instance_use_legacy_auth_encoding():
    return True
