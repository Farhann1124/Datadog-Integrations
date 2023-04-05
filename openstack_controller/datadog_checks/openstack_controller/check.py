# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

from requests.exceptions import HTTPError

from datadog_checks.base import AgentCheck
from datadog_checks.openstack_controller.api.factory import make_api
from datadog_checks.openstack_controller.config import OpenstackConfig
from datadog_checks.openstack_controller.metrics import (
    HYPERVISOR_SERVICE_CHECK,
    KEYSTONE_SERVICE_CHECK,
    LEGACY_NOVA_HYPERVISOR_LOAD_METRICS,
    LEGACY_NOVA_HYPERVISOR_METRICS,
    NOVA_FLAVOR_METRICS,
    NOVA_HYPERVISOR_LOAD_METRICS,
    NOVA_HYPERVISOR_METRICS,
    NOVA_LIMITS_METRICS,
    NOVA_LIMITS_METRICS_PREFIX,
    NOVA_QUOTA_SETS_METRICS,
    NOVA_QUOTA_SETS_METRICS_PREFIX,
    NOVA_SERVER_METRICS,
    NOVA_SERVICE_CHECK,
)


def _create_hypervisor_metric_tags(hypervisor_id, hypervisor_data, os_aggregates):
    tags = [
        f'hypervisor_id:{hypervisor_id}',
        f'hypervisor:{hypervisor_data.get("name")}',
        f'virt_type:{hypervisor_data.get("type")}',
        f'status:{hypervisor_data.get("status")}',
    ]
    for _os_aggregate_id, os_aggregate_value in os_aggregates.items():
        if hypervisor_data.get("name") in os_aggregate_value.get('hosts', []):
            tags.append('aggregate:{}'.format(os_aggregate_value.get("name")))
            tags.append('availability_zone:{}'.format(os_aggregate_value.get("availability_zone")))
    return tags


def _create_project_tags(project):
    return [f"project_id:{project.get('id')}", f"project_name:{project.get('name')}"]


class OpenStackControllerCheck(AgentCheck):
    def __init__(self, name, init_config, instances):
        super(OpenStackControllerCheck, self).__init__(name, init_config, instances)
        self.config = OpenstackConfig(self.log, self.instance)

    def check(self, _instance):
        tags = ['keystone_server:{}'.format(self.instance["keystone_server_url"])] + self.instance.get('tags', [])
        api = make_api(self.config, self.log, self.http)
        self.gauge("openstack.controller", 1)
        self._report_metrics(api, tags)

    def _report_metrics(self, api, tags):
        self._report_identity_metrics(api, tags)
        auth_projects = api.get_auth_projects()
        self.log.debug("auth_projects: %s", auth_projects)
        for project in auth_projects:
            self._report_project_metrics(api, project, tags)

    def _report_identity_metrics(self, api, tags):
        try:
            self._report_identity_response_time(api, tags)
        except HTTPError as e:
            self.warning(e)
            self.log.error("HTTPError while reporting identity metrics: %s", e)
            self.service_check(KEYSTONE_SERVICE_CHECK, AgentCheck.CRITICAL, tags=tags)
        except Exception as e:
            self.warning("Exception while reporting identity metrics: %s", e)

    def _report_identity_response_time(self, api, tags):
        response_time = api.get_identity_response_time()
        self.log.debug("identity response time: %s", response_time)
        if response_time is not None:
            self.gauge('openstack.keystone.response_time', response_time, tags=tags)
            self.service_check(KEYSTONE_SERVICE_CHECK, AgentCheck.OK, tags=tags)
        else:
            self.service_check(KEYSTONE_SERVICE_CHECK, AgentCheck.UNKNOWN, tags=tags)

    def _report_project_metrics(self, api, project, tags):
        project_id = project.get('id')
        project_name = project.get('name')
        self.log.debug("reporting metrics from project: [id:%s][name:%s]", project_id, project_name)
        project_tags = _create_project_tags(project)
        self._report_compute_metrics(api, project_id, tags + project_tags)
        self._report_network_metrics(api, project_id, tags + project_tags)
        self._report_block_storage_metrics(api, project_id, tags + project_tags)
        self._report_baremetal_metrics(api, project_id, tags + project_tags)
        self._report_load_balancer_metrics(api, project_id, tags + project_tags)

    def _report_compute_metrics(self, api, project_id, project_tags):
        try:
            self._report_compute_response_time(api, project_id, project_tags)
            self._report_compute_limits(api, project_id, project_tags)
            self._report_compute_quotas(api, project_id, project_tags)
            self._report_compute_servers(api, project_id, project_tags)
            self._report_compute_flavors(api, project_id, project_tags)
            self._report_compute_hypervisors(api, project_id, project_tags)
        except HTTPError as e:
            self.warning(e)
            self.log.error("HTTPError while reporting compute metrics: %s", e)
            self.service_check(NOVA_SERVICE_CHECK, AgentCheck.CRITICAL, tags=project_tags)
        except Exception as e:
            self.warning("Exception while reporting compute metrics: %s", e)

    def _report_compute_response_time(self, api, project_id, project_tags):
        response_time = api.get_compute_response_time(project_id)
        self.log.debug("compute response time: %s", response_time)
        if response_time is not None:
            self.gauge('openstack.nova.response_time', response_time, tags=project_tags)
            self.service_check(NOVA_SERVICE_CHECK, AgentCheck.OK, tags=project_tags)
        else:
            self.service_check(NOVA_SERVICE_CHECK, AgentCheck.UNKNOWN, tags=project_tags)

    def _report_compute_limits(self, api, project_id, project_tags):
        compute_limits = api.get_compute_limits(project_id)
        self.log.debug("compute_limits: %s", compute_limits)
        if compute_limits:
            for metric, value in compute_limits.items():
                long_metric_name = f'{NOVA_LIMITS_METRICS_PREFIX}.{metric}'
                if long_metric_name in NOVA_LIMITS_METRICS:
                    self.gauge(long_metric_name, value, tags=project_tags)
                else:
                    self.log.warning("%s metric not reported as nova limits metric", long_metric_name)

    def _report_compute_quotas(self, api, project_id, project_tags):
        compute_quotas = api.get_compute_quota_set(project_id)
        self.log.debug("compute_quotas: %s", compute_quotas)
        if compute_quotas:
            for metric, value in compute_quotas['metrics'].items():
                long_metric_name = f'{NOVA_QUOTA_SETS_METRICS_PREFIX}.{metric}'
                tags = project_tags + [f'quota_id:{compute_quotas["id"]}']
                if long_metric_name in NOVA_QUOTA_SETS_METRICS:
                    self.gauge(long_metric_name, value, tags=tags)
                else:
                    self.log.warning("%s metric not reported as nova quota metric", long_metric_name)

    def _report_compute_servers(self, api, project_id, project_tags):
        compute_servers = api.get_compute_servers(project_id)
        self.log.debug("compute_servers: %s", compute_servers)
        if compute_servers is not None:
            self.gauge(
                'openstack.nova.server.count',
                len(compute_servers),
                tags=project_tags,
            )
            for server_id, server_data in compute_servers.items():
                if server_data["status"] == "active" or server_data["status"] == "error":
                    self.gauge(
                        f'openstack.nova.server.{server_data["status"]}',
                        1,
                        tags=project_tags
                        + [
                            f'server_id:{server_id}',
                            f'server_name:{server_data["name"]}',
                            f'server_status:{server_data["status"]}',
                            f'hypervisor:{server_data["hypervisor_hostname"]}',
                            f'flavor_name:{server_data["flavor_name"]}',
                        ],
                    )
                for metric, value in server_data['metrics'].items():
                    long_metric_name = f'openstack.nova.server.{metric}'
                    if long_metric_name in NOVA_SERVER_METRICS:
                        self.gauge(
                            long_metric_name,
                            value,
                            tags=project_tags
                            + [
                                f'server_id:{server_id}',
                                f'server_name:{server_data["name"]}',
                                f'server_status:{server_data["status"]}',
                                f'hypervisor:{server_data["hypervisor_hostname"]}',
                                f'flavor_name:{server_data["flavor_name"]}',
                            ],
                        )

    def _report_compute_flavors(self, api, project_id, project_tags):
        compute_flavors = api.get_compute_flavors(project_id)
        self.log.debug("compute_flavors: %s", compute_flavors)
        if compute_flavors:
            for flavor_id, flavor_data in compute_flavors.items():
                for metric, value in flavor_data['metrics'].items():
                    long_metric_name = f'openstack.nova.flavor.{metric}'
                    if long_metric_name in NOVA_FLAVOR_METRICS:
                        self.gauge(
                            long_metric_name,
                            value,
                            tags=project_tags + [f'flavor_id:{flavor_id}', f'flavor_name:{flavor_data["name"]}'],
                        )

    def _report_compute_hypervisors(self, api, project_id, project_tags):
        compute_hypervisors = api.get_compute_hypervisors(project_id)
        self.log.debug("compute_hypervisors: %s", compute_hypervisors)
        compute_os_aggregates = api.get_compute_os_aggregates(project_id)
        self.log.debug("compute_os_aggregates: %s", compute_os_aggregates)
        if compute_hypervisors:
            for hypervisor_id, hypervisor_data in compute_hypervisors.items():
                hypervisor_tags = project_tags + _create_hypervisor_metric_tags(
                    hypervisor_id, hypervisor_data, compute_os_aggregates
                )
                self._report_hypervisor_service_check(
                    hypervisor_data.get('state'), hypervisor_data["name"], hypervisor_tags
                )
                if self.instance.get('collect_hypervisor_metrics', True):
                    self._report_hypervisor_metrics(hypervisor_data, hypervisor_tags)

    def _report_hypervisor_service_check(self, state, name, hypervisor_tags):
        self.service_check(
            'openstack.nova.hypervisor.up',
            HYPERVISOR_SERVICE_CHECK.get(state, AgentCheck.UNKNOWN),
            hostname=name,
            tags=hypervisor_tags,
        )

    def _report_hypervisor_metrics(self, hypervisor_data, hypervisor_tags):
        for metric, value in hypervisor_data.get('metrics', {}).items():
            self._report_hypervisor_metric(metric, value, hypervisor_tags)
            if self.instance.get('report_legacy_metrics', True):
                self._report_hypervisor_legacy_metric(metric, value, hypervisor_tags)

    def _report_hypervisor_metric(self, metric, value, tags):
        if metric in NOVA_HYPERVISOR_METRICS:
            self.gauge(f'openstack.nova.hypervisor.{metric}', value, tags=tags)
        elif self.instance.get('collect_hypervisor_load', True) and metric in NOVA_HYPERVISOR_LOAD_METRICS:
            self.gauge(f'openstack.nova.hypervisor.{metric}', value, tags=tags)

    def _report_hypervisor_legacy_metric(self, metric, value, tags):
        if metric in LEGACY_NOVA_HYPERVISOR_METRICS:
            self.gauge(f'openstack.nova.{metric}', value, tags=tags)
        elif self.instance.get('collect_hypervisor_load', True) and metric in LEGACY_NOVA_HYPERVISOR_LOAD_METRICS:
            self.gauge(f'openstack.nova.{LEGACY_NOVA_HYPERVISOR_LOAD_METRICS[metric]}', value, tags=tags)

    def _report_network_metrics(self, api, project_id, project_tags):
        try:
            self._report_network_response_time(api, project_id, project_tags)
            self._report_network_quotas(api, project_id, project_tags)
        except HTTPError as e:
            self.warning(e)
            self.log.error("HTTPError while reporting network metrics: %s", e)
            self.service_check('openstack.neutron.api.up', AgentCheck.CRITICAL, tags=project_tags)
        except Exception as e:
            self.warning("Exception while reporting network metrics: %s", e)

    def _report_network_response_time(self, api, project_id, project_tags):
        response_time = api.get_network_response_time(project_id)
        self.log.debug("network response time: %s", response_time)
        if response_time is not None:
            self.gauge('openstack.neutron.response_time', response_time, tags=project_tags)
            self.service_check('openstack.neutron.api.up', AgentCheck.OK, tags=project_tags)
        else:
            self.service_check('openstack.neutron.api.up', AgentCheck.UNKNOWN, tags=project_tags)

    def _report_network_quotas(self, api, project_id, project_tags):
        network_quotas = api.get_network_quotas(project_id)
        self.log.debug("network_quotas: %s", network_quotas)
        if network_quotas:
            for metric, value in network_quotas.items():
                self.gauge(f'openstack.neutron.quotas.{metric}', value, tags=project_tags)

    def _report_block_storage_metrics(self, api, project_id, project_tags):
        try:
            self._report_block_storage_response_time(api, project_id, project_tags)
        except HTTPError as e:
            self.warning(e)
            self.log.error("HTTPError while reporting block storage metrics: %s", e)
            self.service_check('openstack.cinder.api.up', AgentCheck.CRITICAL, tags=project_tags)
        except Exception as e:
            self.warning("Exception while reporting block storage metrics: %s", e)

    def _report_block_storage_response_time(self, api, project_id, project_tags):
        response_time = api.get_block_storage_response_time(project_id)
        self.log.debug("block storage response time: %s", response_time)
        if response_time is not None:
            self.gauge('openstack.cinder.response_time', response_time, tags=project_tags)
            self.service_check('openstack.cinder.api.up', AgentCheck.OK, tags=project_tags)
        else:
            self.service_check('openstack.cinder.api.up', AgentCheck.UNKNOWN, tags=project_tags)

    def _report_baremetal_metrics(self, api, project_id, project_tags):
        try:
            self._report_baremetal_response_time(api, project_id, project_tags)
        except HTTPError as e:
            self.warning(e)
            self.log.error("HTTPError while reporting baremetal metrics: %s", e)
            self.service_check('openstack.ironic.api.up', AgentCheck.CRITICAL, tags=project_tags)
        except Exception as e:
            self.warning("Exception while reporting baremetal metrics: %s", e)

    def _report_baremetal_response_time(self, api, project_id, project_tags):
        response_time = api.get_baremetal_response_time(project_id)
        self.log.debug("baremetal response time: %s", response_time)
        if response_time is not None:
            self.gauge('openstack.ironic.response_time', response_time, tags=project_tags)
            self.service_check('openstack.ironic.api.up', AgentCheck.OK, tags=project_tags)
        else:
            self.service_check('openstack.ironic.api.up', AgentCheck.UNKNOWN, tags=project_tags)

    def _report_load_balancer_metrics(self, api, project_id, project_tags):
        try:
            self._report_load_balancer_response_time(api, project_id, project_tags)
        except HTTPError as e:
            self.warning(e)
            self.log.error("HTTPError while reporting load balancer metrics: %s", e)
            self.service_check('openstack.octavia.api.up', AgentCheck.CRITICAL, tags=project_tags)
        except Exception as e:
            self.warning("Exception while reporting load balancer metrics: %s", e)

    def _report_load_balancer_response_time(self, api, project_id, project_tags):
        response_time = api.get_load_balancer_response_time(project_id)
        self.log.debug("load balancer response time: %s", response_time)
        if response_time is not None:
            self.gauge('openstack.octavia.response_time', response_time, tags=project_tags)
            self.service_check('openstack.octavia.api.up', AgentCheck.OK, tags=project_tags)
        else:
            self.service_check('openstack.octavia.api.up', AgentCheck.UNKNOWN, tags=project_tags)
