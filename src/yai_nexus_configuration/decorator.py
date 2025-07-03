#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 装饰器模块

提供 @nacos_config 装饰器，用于为配置类附加必要的元数据。
"""

from typing import TypeVar, Type, Optional
from functools import wraps


T = TypeVar("T")


def nacos_config(data_id: str, group: str = "DEFAULT_GROUP") -> callable:
    """
    Nacos 配置装饰器
    
    为配置类附加 data_id 和 group 元数据，这些信息将被 NacosProvider 用于
    从 Nacos 服务器获取配置数据。
    
    Args:
        data_id: Nacos 中的配置 ID
        group: Nacos 中的配置组，默认为 "DEFAULT_GROUP"
        
    Returns:
        装饰后的配置类
        
    Example:
        >>> @nacos_config(data_id="database.json", group="PROD")
        >>> class DatabaseConfig(NexusConfig):
        ...     host: str
        ...     port: int
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # 将元数据直接附加到类上
        setattr(cls, '_nacos_data_id', data_id)
        setattr(cls, '_nacos_group', group)
        
        # 添加便捷的类方法来获取元数据
        @classmethod
        def get_nacos_metadata(cls):
            """获取 Nacos 元数据"""
            return {
                'data_id': getattr(cls, '_nacos_data_id', None),
                'group': getattr(cls, '_nacos_group', None)
            }
        
        cls.get_nacos_metadata = get_nacos_metadata
        return cls
    
    return decorator


def get_config_metadata(config_class: Type) -> Optional[dict]:
    """
    从配置类中提取元数据
    
    Args:
        config_class: 被装饰的配置类
        
    Returns:
        包含 data_id 和 group 的字典，如果类未被装饰则返回 None
        
    Raises:
        AttributeError: 如果配置类缺少必要的元数据
    """
    if not hasattr(config_class, '_nacos_data_id'):
        return None
        
    return {
        'data_id': getattr(config_class, '_nacos_data_id'),
        'group': getattr(config_class, '_nacos_group', 'DEFAULT_GROUP')
    }
