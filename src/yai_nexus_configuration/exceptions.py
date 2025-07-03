#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 自定义异常模块

定义了配置系统中可能出现的各种异常情况。
"""

from typing import Type


class NexusConfigError(Exception):
    """配置系统的基础异常类"""
    pass


class ProviderError(NexusConfigError):
    """提供者相关的异常"""
    pass


class ConfigNotRegisteredError(NexusConfigError):
    """当尝试获取未注册的配置时抛出"""
    
    def __init__(self, config_class: Type):
        self.config_class = config_class
        super().__init__(f"配置类 {config_class.__name__} 尚未注册")


class ConfigValidationError(NexusConfigError):
    """配置验证失败时抛出"""
    
    def __init__(self, config_name: str, original_error: Exception):
        self.config_name = config_name
        self.original_error = original_error
        super().__init__(f"配置 {config_name} 验证失败: {original_error}")


class ProviderConnectionError(ProviderError):
    """提供者连接失败时抛出"""
    
    def __init__(self, provider_name: str, reason: str):
        self.provider_name = provider_name
        self.reason = reason
        super().__init__(f"无法连接到 {provider_name}: {reason}")


class ConfigSourceError(ProviderError):
    """配置源操作失败时抛出"""
    
    def __init__(self, data_id: str, group: str, operation: str, reason: str):
        self.data_id = data_id
        self.group = group
        self.operation = operation
        self.reason = reason
        super().__init__(f"配置源操作失败 [{operation}] {group}/{data_id}: {reason}")


class MissingConfigMetadataError(NexusConfigError):
    """配置类缺少必要的元数据时抛出"""
    
    def __init__(self, config_class: Type, missing_attr: str):
        self.config_class = config_class
        self.missing_attr = missing_attr
        super().__init__(
            f"配置类 {config_class.__name__} 缺少必要的元数据. "
            f"请确保使用了 @nexus_config 装饰器。"
        )
