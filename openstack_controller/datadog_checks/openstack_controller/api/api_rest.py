# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)


from datadog_checks.openstack_controller.api.api import Api
from datadog_checks.openstack_controller.api.catalog import Catalog
from datadog_checks.openstack_controller.components.component import Component


class ApiRest(Api):
    def __init__(self, config, logger, http):
        super(ApiRest, self).__init__()
        self.log = logger
        self.config = config
        self.http = http
        self._add_microversion_headers()

        self._interface = self.config.endpoint_interface if self.config.endpoint_interface else 'public'
        self._region_id = self.config.endpoint_region_id
        self._catalog = None
        self._current_project_id = None
        self._role_names = None

    def auth_url(self):
        return self.config.keystone_server_url

    def has_admin_role(self):
        return 'admin' in self._role_names

    def component_in_catalog(self, component_types):
        return self._catalog.has_component(component_types)

    def get_response_time(self, endpoint_types):
        endpoint = (
            self._catalog.get_endpoint_by_type(endpoint_types).replace(self._current_project_id, "")
            if self._current_project_id
            else self._catalog.get_endpoint_by_type(endpoint_types)
        )
        response = self.http.get(endpoint)
        response.raise_for_status()
        return response.elapsed.total_seconds() * 1000

    def make_paginated_request(self, url, query_params, object_name):
        def make_request(url, params):
            resp = self.http.get(url, params=params)
            resp.raise_for_status()
            response_json = resp.json()
            return response_json

        if self.config.paginated_limit is None:
            response_json = make_request(url, query_params)
            objects = response_json.get(object_name, [])
            self.log.debug("objects %s url: %s", objects, url)
            return objects

        result = []
        query_params = query_params or {}
        query_params['limit'] = self.config.paginated_limit
        while True:
            self.log.debug(
                "Making paginated request; url: %s, params: %s, object_name: %s", url, query_params, object_name
            )
            response_json = make_request(url, query_params)

            objects = response_json.get(object_name, [])
            result.extend(objects)

            links = response_json.get("{}_links".format(object_name), [])

            # network pagination is handled differently https://docs.openstack.org/api-ref/network/v2/index.html#pagination
            if 'network' in url:
                has_next_link = False
                for link in links:
                    link_type = link.get('rel')
                    if link_type == 'next':
                        has_next_link = True
                if not has_next_link:
                    break

            # If there is no link to the next object, it means we're done.
            # For servers, see https://docs.openstack.org/api-ref/compute/?expanded=list-servers-detailed-detail#list-servers-detailed
            elif links is None or links == []:
                break

            query_params['marker'] = objects[-1]['id']

        return result

    def get_auth_projects(self):
        response = self.http.get('{}/v3/auth/projects'.format(self.config.keystone_server_url))
        response.raise_for_status()
        return response.json().get('projects', [])

    def authorize_user(self):
        data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": self.config.username,
                            "password": self.config.password,
                            "domain": {"id": self.config.domain_id},
                        }
                    },
                },
            }
        }
        # Testing purposes (we need this header to redirect requests correctly with caddy)
        self.http.options['headers']['X-Auth-Type'] = "unscoped"
        self._authorize_data(data)
        self._current_project_id = None

    def authorize_system(self):
        data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": self.config.username,
                            "password": self.config.password,
                            "domain": {"id": self.config.domain_id},
                        }
                    },
                },
                "scope": {"system": {"all": True}},
            }
        }
        # Testing purposes (we need this header to redirect requests correctly with caddy)
        self.http.options['headers']['X-Auth-Type'] = "system"
        self._authorize_data(data)
        self._current_project_id = None

    def authorize_project(self, project_id):
        data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": self.config.username,
                            "password": self.config.password,
                            "domain": {"id": self.config.domain_id},
                        }
                    },
                },
                "scope": {"project": {"id": project_id}},
            }
        }
        # Testing purposes (we need this header to redirect requests correctly with caddy)
        self.http.options['headers']['X-Auth-Type'] = project_id
        self._authorize_data(data)
        self._current_project_id = project_id

    def _authorize_data(self, data):
        self.log.debug("creating auth token")
        response = self.http.post('{}/v3/auth/tokens'.format(self.config.keystone_server_url), json=data)
        response.raise_for_status()
        response_json = response.json()
        self.log.debug("response: %s", response_json)
        self._catalog = Catalog(
            response_json.get('token', {}).get('catalog', []),
            self._interface,
            self._region_id,
        )
        self._role_names = [role.get('name') for role in response_json.get('token', {}).get('roles', [])]
        self.http.options['headers']['X-Auth-Token'] = response.headers['X-Subject-Token']

    def _add_microversion_headers(self):
        if self.config.nova_microversion:
            self.log.debug("adding X-OpenStack-Nova-API-Version header to `%s`", self.config.nova_microversion)
            self.http.options['headers']['X-OpenStack-Nova-API-Version'] = self.config.nova_microversion

        if self.config.ironic_microversion:
            self.log.debug("adding X-OpenStack-Ironic-API-Version header to `%s`", self.config.ironic_microversion)
            self.http.options['headers']['X-OpenStack-Ironic-API-Version'] = self.config.ironic_microversion

    def get_identity_regions(self):
        response = self.http.get(
            '{}/v3/regions'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value))
        )
        response.raise_for_status()
        return response.json().get('regions', [])

    def get_identity_domains(self):
        response = self.http.get(
            '{}/v3/domains'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value))
        )
        response.raise_for_status()
        return response.json().get('domains', [])

    def get_identity_projects(self):
        response = self.http.get(
            '{}/v3/projects'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value))
        )
        response.raise_for_status()
        return response.json().get('projects', [])

    def get_identity_users(self):
        response = self.http.get(
            '{}/v3/users'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value))
        )
        response.raise_for_status()
        return response.json().get('users', [])

    def get_identity_groups(self):
        response = self.http.get(
            '{}/v3/groups'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value))
        )
        response.raise_for_status()
        return response.json().get('groups', [])

    def get_identity_group_users(self, group_id):
        response = self.http.get(
            '{}/v3/groups/{}/users'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value), group_id)
        )
        response.raise_for_status()
        return response.json().get('users', [])

    def get_identity_services(self):
        response = self.http.get(
            '{}/v3/services'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value))
        )
        response.raise_for_status()
        return response.json().get('services', [])

    def get_identity_registered_limits(self):
        response = self.http.get(
            '{}/v3/registered_limits'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value))
        )
        response.raise_for_status()
        return response.json().get('registered_limits', [])

    def get_identity_limits(self):
        response = self.http.get(
            '{}/v3/limits'.format(self._catalog.get_endpoint_by_type(Component.Types.IDENTITY.value))
        )
        response.raise_for_status()
        return response.json().get('limits', [])

    def get_compute_limits(self, project_id):
        params = {'tenant_id': project_id}
        response = self.http.get(
            '{}/limits'.format(self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value)), params=params
        )
        response.raise_for_status()
        return response.json().get('limits', {})

    def get_compute_aggregates(self):
        response = self.http.get(
            '{}/os-aggregates'.format(self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value))
        )
        response.raise_for_status()
        return response.json().get('aggregates', [])

    def get_compute_quota_sets(self, project_id):
        response = self.http.get(
            '{}/os-quota-sets/{}'.format(self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value), project_id)
        )
        response.raise_for_status()
        return response.json().get('quota_set', {})

    def get_compute_servers(self, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/servers/detail'.format(self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value)),
            params,
            'servers',
        )

    def get_compute_server_diagnostics(self, server_id):
        response = self.http.get(
            '{}/servers/{}/diagnostics'.format(
                self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value), server_id
            )
        )
        response.raise_for_status()
        return response.json()

    def get_compute_flavor(self, flavor_id):
        response = self.http.get(
            '{}/flavors/{}'.format(self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value), flavor_id)
        )
        response.raise_for_status()
        return response.json().get('flavor', {})

    def get_compute_services(self):
        response = self.http.get(
            '{}/os-services'.format(self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value))
        )
        response.raise_for_status()
        return response.json().get('services', [])

    def get_compute_flavors(self):
        return self.make_paginated_request(
            '{}/flavors/detail'.format(self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value)), {}, 'flavors'
        )

    def get_compute_hypervisors(self):
        return self.make_paginated_request(
            '{}/os-hypervisors/detail'.format(self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value)),
            {},
            'hypervisors',
        )

    def get_compute_hypervisor_uptime(self, hypervisor_id):
        response = self.http.get(
            '{}/os-hypervisors/{}/uptime'.format(
                self._catalog.get_endpoint_by_type(Component.Types.COMPUTE.value), hypervisor_id
            )
        )
        response.raise_for_status()
        return response.json().get('hypervisor', {})

    def get_network_agents(self):
        return self.make_paginated_request(
            '{}/v2.0/agents'.format(self._catalog.get_endpoint_by_type(Component.Types.NETWORK.value)), {}, 'agents'
        )

    def get_network_networks(self, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/v2.0/networks'.format(self._catalog.get_endpoint_by_type(Component.Types.NETWORK.value)),
            params,
            'networks',
        )

    def get_network_quota(self, project_id):
        response = self.http.get(
            '{}/v2.0/quotas/{}'.format(self._catalog.get_endpoint_by_type(Component.Types.NETWORK.value), project_id)
        )
        response.raise_for_status()
        return response.json().get('quota', [])

    def get_baremetal_nodes(self):
        def use_legacy_nodes_resource(microversion):
            self.log.debug("Configured ironic microversion: %s", microversion)
            if not microversion:
                return True
            legacy_microversion = True
            try:
                legacy_microversion = float(microversion) < 1.43
            except Exception as e:
                if microversion.lower() == 'latest':
                    legacy_microversion = False
                else:
                    raise Exception(f"Invalid ironic microversion, cannot collect baremetal nodes: {str(e)}")
            self.log.debug("Collecting baremetal nodes with use_legacy_nodes_resource =%s", legacy_microversion)
            return legacy_microversion

        self.log.debug("getting baremetal nodes [microversion=%s]", self.config.ironic_microversion)
        ironic_endpoint = self._catalog.get_endpoint_by_type(Component.Types.BAREMETAL.value)

        if use_legacy_nodes_resource(self.config.ironic_microversion):
            response = self.make_paginated_request('{}/v1/nodes/detail'.format(ironic_endpoint), {}, 'nodes')
        else:
            params = {'detail': True}
            response = self.make_paginated_request('{}/v1/nodes'.format(ironic_endpoint), params, 'nodes')

        return response

    def get_baremetal_conductors(self):
        return self.make_paginated_request(
            '{}/v1/conductors'.format(self._catalog.get_endpoint_by_type(Component.Types.BAREMETAL.value)),
            {},
            'conductors',
        )

    def get_load_balancer_loadbalancers(self, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/v2/lbaas/loadbalancers'.format(self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value)),
            params,
            'loadbalancers',
        )

    def get_load_balancer_loadbalancer_stats(self, loadbalancer_id):
        response = self.http.get(
            '{}/v2/lbaas/loadbalancers/{}/stats'.format(
                self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value), loadbalancer_id
            )
        )
        response.raise_for_status()
        return response.json().get('stats', {})

    def get_load_balancer_listeners(self, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/v2/lbaas/listeners'.format(self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value)),
            params,
            'listeners',
        )

    def get_load_balancer_listener_stats(self, listener_id):
        response = self.http.get(
            '{}/v2/lbaas/listeners/{}/stats'.format(
                self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value), listener_id
            )
        )
        response.raise_for_status()
        return response.json().get('stats', {})

    def get_load_balancer_pools(self, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/v2/lbaas/pools'.format(self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value)),
            params,
            'pools',
        )

    def get_load_balancer_pool_members(self, pool_id, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/v2/lbaas/pools/{}/members'.format(
                self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value), pool_id
            ),
            params,
            'members',
        )

    def get_load_balancer_healthmonitors(self, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/v2/lbaas/healthmonitors'.format(
                self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value)
            ),
            params,
            'healthmonitors',
        )

    def get_load_balancer_quotas(self, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/v2/lbaas/quotas'.format(self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value)),
            params,
            'quotas',
        )

    def get_load_balancer_amphorae(self, project_id):
        params = {'project_id': project_id}
        return self.make_paginated_request(
            '{}/v2/octavia/amphorae'.format(self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value)),
            params,
            'amphorae',
        )

    def get_load_balancer_amphora_stats(self, amphora_id):
        response = self.http.get(
            '{}/v2/octavia/amphorae/{}/stats'.format(
                self._catalog.get_endpoint_by_type(Component.Types.LOAD_BALANCER.value), amphora_id
            )
        )
        response.raise_for_status()
        return response.json().get('amphora_stats', [])

    def get_glance_images(self):
        url = '{}/v2/images'.format(self._catalog.get_endpoint_by_type(Component.Types.IMAGE.value))
        return self.make_paginated_request(url, {}, 'images')
