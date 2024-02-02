# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

# This file is autogenerated.
# To change this file you should edit assets/configuration/spec.yaml and then run the following commands:
#     ddev -x validate config -s <INTEGRATION_NAME>
#     ddev -x validate models -s <INTEGRATION_NAME>

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from datadog_checks.base.utils.functions import identity
from datadog_checks.base.utils.models import validation

from . import defaults, validators


class AuthToken(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    reader: Optional[MappingProxyType[str, Any]] = None
    writer: Optional[MappingProxyType[str, Any]] = None


class Include(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    name: Optional[str] = None
    uptime: Optional[bool] = None


class Nodes(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of nodes to be processed.\n')


class Baremetal(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    conductors: Optional[bool] = None
    nodes: Optional[Union[bool, Nodes]] = None


class Hypervisors(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of hypervisors to be processed.\n')


class Include2(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    diagnostics: Optional[bool] = None
    flavors: Optional[bool] = None
    name: Optional[str] = None


class Servers(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include2], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of servers to be processed.\n')


class Compute(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    flavors: Optional[bool] = None
    hypervisors: Optional[Union[bool, Hypervisors]] = None
    limits: Optional[bool] = None
    quota_sets: Optional[bool] = None
    servers: Optional[Union[bool, Servers]] = None
    services: Optional[bool] = None


class Identity(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    domains: Optional[bool] = None
    groups: Optional[bool] = None
    limits: Optional[bool] = None
    projects: Optional[bool] = None
    regions: Optional[bool] = None
    services: Optional[bool] = None
    users: Optional[bool] = None


class Image(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    images: Optional[bool] = None


class Include3(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    id: Optional[str] = None
    stats: Optional[bool] = None


class Amphorae(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include3], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of amphorae to be processed.\n')


class Include4(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    name: Optional[str] = None


class Healthmonitors(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include4], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of healthmonitors to be processed.\n')


class Include5(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    name: Optional[str] = None
    stats: Optional[bool] = None


class Listeners(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include5], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of listeners to be processed.\n')


class Loadbalancers(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include5], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of loadbalancers to be processed.\n')


class Include8(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    name: Optional[str] = None


class Members(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include8], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of members to be processed.\n')


class Include7(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    members: Optional[Union[bool, Members]] = None
    name: Optional[str] = None


class Pools(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    include: Optional[tuple[Union[str, Include7], ...]] = None
    limit: Optional[int] = Field(None, description='Maximum number of pools to be processed.\n')


class Include9(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    name: Optional[str] = None


class Quotas(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include9], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of quotas to be processed.\n')


class LoadBalancer(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    amphorae: Optional[Union[bool, Amphorae]] = None
    healthmonitors: Optional[Union[bool, Healthmonitors]] = None
    listeners: Optional[Union[bool, Listeners]] = None
    loadbalancers: Optional[Union[bool, Loadbalancers]] = None
    pools: Optional[Union[bool, Pools]] = None
    quotas: Optional[Union[bool, Quotas]] = None


class Networks(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, Include9], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of networks to be processed.\n')


class Network(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    agents: Optional[bool] = None
    networks: Optional[Union[bool, Networks]] = None
    quotas: Optional[bool] = None


class Components(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    baremetal: Optional[Union[bool, Baremetal]] = None
    block_storage: Optional[Union[bool, MappingProxyType[str, Any]]] = Field(None, alias='block-storage')
    compute: Optional[Union[bool, Compute]] = None
    identity: Optional[Union[bool, Identity]] = None
    image: Optional[Union[bool, Image]] = None
    load_balancer: Optional[Union[bool, LoadBalancer]] = Field(None, alias='load-balancer')
    network: Optional[Union[bool, Network]] = None


class MetricPatterns(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[str, ...]] = None


class Projects(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    exclude: Optional[tuple[str, ...]] = None
    include: Optional[tuple[Union[str, MappingProxyType[str, Any]], ...]] = None
    interval: Optional[int] = None
    limit: Optional[int] = Field(None, description='Maximum number of clusters to be processed.\n')


class Proxy(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        frozen=True,
    )
    http: Optional[str] = None
    https: Optional[str] = None
    no_proxy: Optional[tuple[str, ...]] = None


class InstanceConfig(BaseModel):
    model_config = ConfigDict(
        validate_default=True,
        arbitrary_types_allowed=True,
        frozen=True,
    )
    allow_redirects: Optional[bool] = None
    auth_token: Optional[AuthToken] = None
    auth_type: Optional[str] = None
    aws_host: Optional[str] = None
    aws_region: Optional[str] = None
    aws_service: Optional[str] = None
    blacklist_project_names: Optional[tuple[str, ...]] = None
    collect_hypervisor_load: Optional[bool] = None
    collect_hypervisor_metrics: Optional[bool] = None
    collect_network_metrics: Optional[bool] = None
    collect_project_metrics: Optional[bool] = None
    collect_server_diagnostic_metrics: Optional[bool] = None
    collect_server_flavor_metrics: Optional[bool] = None
    components: Optional[Components] = None
    connect_timeout: Optional[float] = None
    disable_generic_tags: Optional[bool] = None
    domain_id: Optional[str] = None
    empty_default_hostname: Optional[bool] = None
    endpoint_interface: Optional[str] = None
    endpoint_region_id: Optional[str] = None
    exclude_network_ids: Optional[tuple[str, ...]] = None
    exclude_server_ids: Optional[tuple[str, ...]] = None
    extra_headers: Optional[MappingProxyType[str, Any]] = None
    headers: Optional[MappingProxyType[str, Any]] = None
    ironic_microversion: Optional[str] = None
    kerberos_auth: Optional[str] = None
    kerberos_cache: Optional[str] = None
    kerberos_delegate: Optional[bool] = None
    kerberos_force_initiate: Optional[bool] = None
    kerberos_hostname: Optional[str] = None
    kerberos_keytab: Optional[str] = None
    kerberos_principal: Optional[str] = None
    keystone_server_url: Optional[str] = None
    log_requests: Optional[bool] = None
    metric_patterns: Optional[MetricPatterns] = None
    min_collection_interval: Optional[float] = None
    name: Optional[str] = None
    nova_microversion: Optional[str] = None
    ntlm_domain: Optional[str] = None
    openstack_cloud_name: Optional[str] = None
    openstack_config_file_path: Optional[str] = None
    paginated_limit: Optional[int] = None
    password: Optional[str] = None
    persist_connections: Optional[bool] = None
    projects: Optional[Projects] = None
    proxy: Optional[Proxy] = None
    read_timeout: Optional[float] = None
    request_size: Optional[float] = None
    service: Optional[str] = None
    skip_proxy: Optional[bool] = None
    tags: Optional[tuple[str, ...]] = None
    timeout: Optional[float] = None
    tls_ca_cert: Optional[str] = None
    tls_cert: Optional[str] = None
    tls_ignore_warning: Optional[bool] = None
    tls_private_key: Optional[str] = None
    tls_protocols_allowed: Optional[tuple[str, ...]] = None
    tls_use_host_header: Optional[bool] = None
    tls_verify: Optional[bool] = None
    use_agent_proxy: Optional[bool] = None
    use_legacy_auth_encoding: Optional[bool] = None
    use_legacy_check_version: Optional[bool] = None
    use_shortname: Optional[bool] = None
    user: Optional[MappingProxyType[str, Any]] = None
    username: Optional[str] = None
    whitelist_project_names: Optional[tuple[str, ...]] = None

    @model_validator(mode='before')
    def _initial_validation(cls, values):
        return validation.core.initialize_config(getattr(validators, 'initialize_instance', identity)(values))

    @field_validator('*', mode='before')
    def _validate(cls, value, info):
        field = cls.model_fields[info.field_name]
        field_name = field.alias or info.field_name
        if field_name in info.context['configured_fields']:
            value = getattr(validators, f'instance_{info.field_name}', identity)(value, field=field)
        else:
            value = getattr(defaults, f'instance_{info.field_name}', lambda: value)()

        return validation.utils.make_immutable(value)

    @model_validator(mode='after')
    def _final_validation(cls, model):
        return validation.core.check_model(getattr(validators, 'check_instance', identity)(model))
