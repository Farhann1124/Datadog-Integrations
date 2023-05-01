import logging

import mock
import pytest

from datadog_checks.base import AgentCheck
from datadog_checks.dev.http import MockResponse
from datadog_checks.openstack_controller import OpenStackControllerCheck

from .common import MockHttp

pytestmark = [pytest.mark.unit]


def test_exception(dd_run_check, instance, caplog, monkeypatch):
    http = MockHttp("agent-integrations-openstack-ironic", exceptions={'baremetal': Exception()})
    monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
    monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))

    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    assert 'Exception while reporting baremetal metrics' in caplog.text


def test_endpoint_not_in_catalog(aggregator, dd_run_check, instance, monkeypatch):
    http = MockHttp("agent-integrations-openstack-default")
    monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
    monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))

    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_service_check(
        'openstack.ironic.api.up',
        status=AgentCheck.UNKNOWN,
        tags=[
            'domain_id:default',
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )
    aggregator.assert_service_check(
        'openstack.ironic.api.up',
        status=AgentCheck.UNKNOWN,
        tags=[
            'domain_id:default',
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )


def test_endpoint_down(aggregator, dd_run_check, instance, monkeypatch):
    http = MockHttp("agent-integrations-openstack-ironic", defaults={'baremetal': MockResponse(status_code=500)})
    monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
    monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))

    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_service_check(
        'openstack.ironic.api.up',
        status=AgentCheck.CRITICAL,
        tags=[
            'domain_id:default',
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )


def test_endpoint_up(aggregator, dd_run_check, instance, monkeypatch):
    http = MockHttp("agent-integrations-openstack-ironic")
    monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
    monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))

    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_service_check(
        'openstack.ironic.api.up',
        status=AgentCheck.OK,
        tags=[
            'domain_id:default',
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )


def test_node_metrics_default(aggregator, dd_run_check, instance, monkeypatch):
    http = MockHttp("agent-integrations-openstack-ironic")
    monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
    monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))

    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)

    base_tags = ['domain_id:default', 'keystone_server:{}'.format(instance["keystone_server_url"])]

    nodes_tags = [
        ['node_uuid:9d72cf53-19c8-4942-9314-005fa5d2a6a0', 'power_state:None'],
        ['node_uuid:20512deb-e493-4796-a046-5d6e4e072c95', 'power_state:power on'],
        ['node_uuid:54855e59-83ca-46f8-a78f-55d3370e0656', 'power_state:None'],
        ['node_uuid:bd7a61bb-5fe0-4c93-9628-55e312f9ef0e', 'power_state:None'],
    ]

    for node_tags in nodes_tags:
        tags = base_tags + node_tags
        aggregator.assert_metric('openstack.ironic.node.count', count=1, tags=tags)
        aggregator.assert_metric('openstack.ironic.node.up', count=1, tags=tags)

    aggregator.assert_metric('openstack.ironic.node.count', count=4)
    aggregator.assert_metric('openstack.ironic.node.up', count=4)


def test_node_metrics_latest(aggregator, dd_run_check, instance_ironic_nova_microversion_latest, monkeypatch):
    http = MockHttp("agent-integrations-openstack-ironic")
    monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
    monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))

    check = OpenStackControllerCheck('test', {}, [instance_ironic_nova_microversion_latest])
    dd_run_check(check)

    base_tags = ['domain_id:default', 'keystone_server:http://127.0.0.1:8080/identity']
    nodes_tags = [
        [
            'node_uuid:9d72cf53-19c8-4942-9314-005fa5d2a6a0',
            'node_name:node-0',
            'power_state:None',
        ],
        [
            'node_uuid:bd7a61bb-5fe0-4c93-9628-55e312f9ef0e',
            'node_name:node-1',
            'power_state:None',
        ],
        [
            'node_uuid:54855e59-83ca-46f8-a78f-55d3370e0656',
            'node_name:node-2',
            'power_state:None',
        ],
        [
            'node_uuid:20512deb-e493-4796-a046-5d6e4e072c95',
            'node_name:test',
            'power_state:power on',
        ],
    ]

    for node_tags in nodes_tags:
        tags = base_tags + node_tags
        aggregator.assert_metric('openstack.ironic.node.count', count=1, tags=tags)
        aggregator.assert_metric('openstack.ironic.node.up', count=1, tags=tags)

    aggregator.assert_metric('openstack.ironic.node.count', count=4)
    aggregator.assert_metric('openstack.ironic.node.up', count=4)


def test_conductor_metrics_default(aggregator, dd_run_check, instance, monkeypatch, caplog):
    http = MockHttp("agent-integrations-openstack-ironic")
    monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
    monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))

    caplog.set_level(logging.INFO)
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    assert "Ironic conductors metrics are not available." in caplog.text

    aggregator.assert_metric('openstack.ironic.conductor.up', count=0)


def test_conductor_metrics_latest(aggregator, dd_run_check, instance_ironic_nova_microversion_latest, monkeypatch):
    http = MockHttp("agent-integrations-openstack-ironic")
    monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
    monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))

    check = OpenStackControllerCheck('test', {}, [instance_ironic_nova_microversion_latest])
    dd_run_check(check)
    base_tags = [
        'domain_id:default',
        'keystone_server:{}'.format(instance_ironic_nova_microversion_latest["keystone_server_url"]),
    ]

    conductor_tags = ['conductor_hostname:agent-integrations-openstack-ironic']

    aggregator.assert_metric('openstack.ironic.conductor.up', value=1, count=1, tags=conductor_tags + base_tags)