# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)


from datadog_checks.base import AgentCheck
from datadog_checks.openstack_controller.api.factory import make_api
from datadog_checks.openstack_controller.components.bare_metal import BareMetal
from datadog_checks.openstack_controller.components.block_storage import BlockStorage
from datadog_checks.openstack_controller.components.compute import Compute
from datadog_checks.openstack_controller.components.identity import Identity
from datadog_checks.openstack_controller.components.load_balancer import LoadBalancer
from datadog_checks.openstack_controller.components.network import Network
from datadog_checks.openstack_controller.config import OpenstackConfig


class OpenStackControllerCheck(AgentCheck):
    def __init__(self, name, init_config, instances):
        super(OpenStackControllerCheck, self).__init__(name, init_config, instances)
        self.config = OpenstackConfig(self.log, self.instance)
        self.api = make_api(self.config, self.log, self.http)
        self.identity = Identity(self)
        self.components = [
            self.identity,
            Compute(self),
            Network(self),
            BlockStorage(self),
            BareMetal(self),
            LoadBalancer(self),
        ]

    def check(self, _instance):
        self.log.info("running check")
        tags = ['keystone_server:{}'.format(self.api.auth_url())] + self.instance.get('tags', [])
        self.gauge("openstack.controller", 1, tags=tags)
        if self.identity.authorize():
            self.log.info("User successfully authorized")
            self._start_report()
            self._report_metrics(tags)
            self._finish_report(tags)
        else:
            self.log.error("Error while authorizing user")

    def _start_report(self):
        for component in self.components:
            component.start_report()

    def _report_metrics(self, tags):
        self.log.info("reporting metrics")
        self._report_global_metrics(tags)
        auth_projects = self.identity.get_auth_projects()
        self.log.info("auth_projects: %s", auth_projects)
        for project in auth_projects:
            self.api.set_current_project(project['id'])
            self.identity.authorize()
            if self.api.has_admin_role():
                self._report_global_metrics(tags)
            project_tags = tags + [
                f"domain_id:{project['domain_id']}",
                f"project_id:{project['id']}",
                f"project_name:{project['name']}",
            ]
            self._report_project_metrics(project['id'], project_tags)

    def _finish_report(self, tags):
        for component in self.components:
            component.finish_report(tags)

    def _report_global_metrics(self, tags):
        self.log.info("reporting global metrics")
        for component in self.components:
            component.report_global_metrics(tags)

    def _report_project_metrics(self, project_id, tags):
        self.log.info("reporting project `%s` metrics", project_id)
        for component in self.components:
            component.report_project_metrics(project_id, tags)