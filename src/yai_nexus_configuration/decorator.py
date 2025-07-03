#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration Decorator

提供 @nexus_config 装饰器，用于为配置类附加必要的元数据。
这些元数据将被 `NexusConfigManager` 用来从配置源（如 Nacos 或本地文件）获取正确的配置。
"""

import functools
from typing import Type, Optional

from .config import NexusConfig


def nexus_config(
    data_id: str, 
    group: str = "DEFAULT_GROUP",
    auto_refresh: bool = False
) -> callable:
    """
    一个装饰器，用于为 `NexusConfig` 子类附加配置元数据。

    Args:
        data_id (str): 配置的 data_id。在 Nacos 中，这是配置的唯一标识。
                       在使用文件提供者时，这通常是文件名（例如 `database.json`）。
        group (str, optional): 配置所属的组。默认为 "DEFAULT_GROUP"。
        auto_refresh (bool, optional): 是否在配置变更时自动更新实例。默认为 False。

    Returns:
        callable: 返回一个装饰器函数。

    Example:
        >>> @nexus_config(data_id="database.json", group="PROD", auto_refresh=True)
        ... class DatabaseConfig(NexusConfig):
        ...     host: str
        ...     port: int
    """
    def decorator(cls: Type[NexusConfig]) -> Type[NexusConfig]:
        if not issubclass(cls, NexusConfig):
            raise TypeError("The decorated class must be a subclass of NexusConfig.")

        # 将元数据附加到类本身
        setattr(cls, '__nexus_config__', {
            'data_id': data_id,
            'group': group,
            'auto_refresh': auto_refresh
        })
        
        return cls
    return decorator


def get_config_metadata(config_class: Type) -> Optional[dict]:
    """
    从配置类中提取元数据
    
    Args:
        config_class: 被装饰的配置类
        
    Returns:
        包含 data_id 和 group 的字典，如果类未被装饰则返回 None
    """
    return getattr(config_class, '__nexus_config__', None)
