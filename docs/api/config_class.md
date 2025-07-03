# 配置类 (NexusConfig & @nexus_config)

`NexusConfig` 是所有配置模型的基类，而 `@nexus_config` 装饰器则负责将您的模型与具体的配置源信息（如 `data_id` 和 `group`）关联起来。

## `NexusConfig` 基类

所有自定义配置类都应继承自 `NexusConfig`。它基于 Pydantic 的 `BaseModel`，因此您可以使用所有 Pydantic 提供的功能，例如类型验证、默认值和字段自定义。

::: yai_nexus_configuration.config.NexusConfig
    handler: python
    options:
      show_root_heading: false
      heading_level: 3
      show_signature_annotations: true

## `@nexus_config` 装饰器

这个装饰器是必须的，它为您的配置类注入了元数据。

::: yai_nexus_configuration.decorator.nexus_config
    handler: python
    options:
      show_root_heading: false
      heading_level: 3 