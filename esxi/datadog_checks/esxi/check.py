# (C) Datadog, Inc. 2024-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

from pyVim import connect
from pyVmomi import vim, vmodl

from datadog_checks.base import AgentCheck  # noqa: F401

from .constants import HOST_RESOURCE, MAX_PROPERTIES, RESOURCE_TYPE_TO_NAME, SHORT_ROLLUP, VM_RESOURCE
from .metrics import RESOURCE_NAME_TO_METRICS


class EsxiCheck(AgentCheck):
    __NAMESPACE__ = 'esxi'

    def __init__(self, name, init_config, instances):
        super(EsxiCheck, self).__init__(name, init_config, instances)
        self.host = self.instance.get("host")
        self.username = self.instance.get("username")
        self.password = self.instance.get("password")
        self.tags = [f"esxi_url:{self.host}"]

    def get_resources(self):
        self.log.debug("Retrieving resources")
        property_specs = []

        resource_types = [VM_RESOURCE, HOST_RESOURCE]
        for resource_type in resource_types:
            # Create property spec for only Host objects; only request name attribute
            property_spec = vmodl.query.PropertyCollector.PropertySpec()
            property_spec.type = resource_type
            property_spec.pathSet = ["name"]
            property_specs.append(property_spec)

        # Specify the attribute of the root object to traverse to obtain all the attributes
        traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.path = "view"
        traversal_spec.skip = False
        traversal_spec.type = vim.view.ContainerView

        # Only collect 1 item for now
        retr_opts = vmodl.query.PropertyCollector.RetrieveOptions()
        retr_opts.maxObjects = MAX_PROPERTIES

        # Specify the root object from where we collect the rest of the objects
        obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.skip = True
        obj_spec.selectSet = [traversal_spec]

        # Create our filter spec from the above specs
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.propSet = property_specs

        # Only host objects
        view_ref = self.content.viewManager.CreateContainerView(self.content.rootFolder, resource_types, True)

        try:
            obj_spec.obj = view_ref
            filter_spec.objectSet = [obj_spec]

            # Collect the object and its properties
            res = self.content.propertyCollector.RetrievePropertiesEx([filter_spec], retr_opts)
            if res is None:
                obj_content_list = []
            else:
                obj_content_list = res.objects
        finally:
            view_ref.Destroy()

        return obj_content_list

    def get_available_metric_ids_for_entity(self, entity):
        resource_name = RESOURCE_TYPE_TO_NAME[type(entity)]
        avaliable_metrics = RESOURCE_NAME_TO_METRICS[resource_name]

        counter_keys_and_names = {}
        for counter in self.content.perfManager.perfCounter:
            full_name = f"{counter.groupInfo.key}.{counter.nameInfo.key}.{SHORT_ROLLUP[counter.rollupType]}"
            if full_name in avaliable_metrics:
                counter_keys_and_names[counter.key] = full_name
            else:
                self.log.trace("Skipping metric %s as it is not recognized", full_name)

        available_counter_ids = [m.counterId for m in self.content.perfManager.QueryAvailablePerfMetric(entity=entity)]
        counter_ids = [
            counter_id for counter_id in available_counter_ids if counter_id in counter_keys_and_names.keys()
        ]
        metric_ids = [vim.PerformanceManager.MetricId(counterId=counter, instance="") for counter in counter_ids]
        return counter_keys_and_names, metric_ids

    def collect_metrics_for_entity(self, metric_ids, counter_keys_and_names, entity, entity_name):

        resource_name = RESOURCE_TYPE_TO_NAME[type(entity)]
        spec = vim.PerformanceManager.QuerySpec(maxSample=1, entity=entity, metricId=metric_ids)
        result_stats = self.content.perfManager.QueryPerf([spec])

        for results_for_entity in result_stats:
            for metric_result in results_for_entity.value:
                metric_name = counter_keys_and_names.get(metric_result.id.counterId)
                if len(metric_result.value) == 0:
                    self.log.debug(
                        "Skipping metric %s for %s because no value was returned by the %s",
                        metric_name,
                        entity_name,
                        resource_name,
                    )
                    continue

                valid_values = [v for v in metric_result.value if v >= 0]
                if len(valid_values) <= 0:
                    self.log.debug(
                        "Skipping metric %s for %s, because the value returned by the %s"
                        " is negative (i.e. the metric is not yet available). values: %s",
                        metric_name,
                        entity_name,
                        resource_name,
                        list(metric_result.value),
                    )
                    continue
                else:
                    most_recent_val = valid_values[-1]

                    self.log.debug(
                        "Submit metric: name=`%s`, value=`%s`, hostname=`%s`, tags=`%s`",
                        metric_name,
                        most_recent_val,
                        entity_name,
                        self.tags,
                    )
                    self.gauge(metric_name, most_recent_val, hostname=entity_name, tags=self.tags)

    def check(self, _):
        try:
            connection = connect.SmartConnect(host=self.host, user=self.username, pwd=self.password)
            self.conn = connection
            self.log.info("Connected to ESXi host %s", self.host)
            self.count("host.can_connect", 1, tags=self.tags)

        except Exception as e:
            self.log.warning("Cannot connect to ESXi host %s: %s", self.host, str(e))
            self.count("host.can_connect", 0, tags=self.tags)
            return

        self.content = connection.content

        resources = self.get_resources()
        resource_map = {}
        for resource in resources:
            name = None
            for prop in resource.propSet:
                if prop.name == "name":
                    name = prop.val
            if name:
                resource_map[name] = resource.obj
            else:
                self.log.warning("No host name found for entity %s", resource.obj)

        if not resource_map:
            self.log.warning("No resources found; halting check execution")
            return

        for resource_name, resource_obj in resource_map.items():

            counter_keys_and_names, metric_ids = self.get_available_metric_ids_for_entity(resource_obj)
            self.collect_metrics_for_entity(metric_ids, counter_keys_and_names, resource_obj, resource_name)
