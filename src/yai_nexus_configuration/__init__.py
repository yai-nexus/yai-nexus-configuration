#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 高质量的配置管理库

一个基于 Provider 模式的通用配置管理库，支持多种配置源（Nacos、Apollo 等）。

主要特性：
- 🚀 简洁优雅的 API 设计
- 🔒 线程安全的配置存储
- 🔄 自动配置变更监听
- 🎯 完整的类型提示支持
- 🧩 可扩展的 Provider 架构
- ✅ 基于 Pydantic 的数据验证

基本用法：
    >>> from yai_nexus_configuration import NexusConfigManager, NexusConfig, nacos_config
    >>> 
    >>> @nacos_config(data_id="database.json")
    >>> class DatabaseConfig(NexusConfig):
    ...     host: str
    ...     port: int = 5432
    ...     username: str
    ...     password: str
    >>> 
    >>> # 创建管理器并注册配置
    >>> manager = NexusConfigManager.with_nacos("localhost:8848")
    >>> manager.register(DatabaseConfig)
    >>> 
    >>> # 获取配置实例
    >>> db_config = manager.get_config(DatabaseConfig)
    >>> print(f"Database: {db_config.host}:{db_config.port}")
"""

__version__ = "0.1.0"
__author__ = "YAI Team"
__email__ = "team@yai.com"

# 导出核心组件
from .manager import NexusConfigManager
from .config import NexusConfig
from .decorator import nexus_config

# 导出异常类
from .exceptions import (
    NexusConfigError,
    ProviderError,
    ConfigNotRegisteredError,
    ConfigValidationError,
    ProviderConnectionError,
    ConfigSourceError,
    MissingConfigMetadataError,
)

# 公共 API
__all__ = [
    # 版本信息
    "__version__",
    
    # 核心组件
    "NexusConfigManager",
    "NexusConfig",
    
    # Decorators
    "nexus_config",
    
    # 异常类
    "NexusConfigError",
    "ProviderError", 
    "ConfigNotRegisteredError",
    "ConfigValidationError",
    "ProviderConnectionError",
    "ConfigSourceError",
    "MissingConfigMetadataError",
]
