# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)


from datadog_checks.openstack_controller.components.component import Component
from datadog_checks.openstack_controller.metrics import (
    CINDER_RESPONSE_TIME,
    CINDER_SERVICE_CHECK,
)


class BlockStorage(Component):
    component_type = Component.Type.BLOCK_STORAGE
    service_check_id = CINDER_SERVICE_CHECK

    def __init__(self, check):
        super(BlockStorage, self).__init__(self, check)

    @Component.register_global_metrics(Component.Type.BLOCK_STORAGE)
    @Component.http_error(service_check=True)
    def _report_response_time(self, tags):
        self.check.log.debug("reporting `%s` response time", Component.Type.BLOCK_STORAGE.value)
        response_time = self.check.api.get_response_time(Component.Type.BLOCK_STORAGE)
        self.check.log.debug("`%s` response time: %s", Component.Type.BLOCK_STORAGE.value, response_time)
        self.check.gauge(CINDER_RESPONSE_TIME, response_time, tags=tags)
