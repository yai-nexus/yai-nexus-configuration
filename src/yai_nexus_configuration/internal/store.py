#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 配置存储模块

提供线程安全的配置实例存储和管理功能。
"""

import threading
import logging
from typing import Type, TypeVar, Dict, Optional, Any
from pydantic import BaseModel

from ..config import NexusConfig
from ..exceptions import ConfigNotRegisteredError


T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class ConfigStore:
    """
    线程安全的配置存储中心
    
    管理所有已注册配置类的实例，提供线程安全的存储、检索和更新操作。
    """
    
    def __init__(self):
        self._store: Dict[Type[BaseModel], BaseModel] = {}
        self._lock = threading.RLock()  # 使用可重入锁
        
    def set_config(self, config_instance: T) -> None:
        """
        存储或更新配置实例
        
        Args:
            config_instance: 要存储的配置实例
        """
        if not isinstance(config_instance, NexusConfig):
            raise TypeError(f"只能存储 NexusConfig 的子类实例，但传入的是 {type(config_instance).__name__}")
            
        config_class = type(config_instance)
        
        with self._lock:
            old_instance = self._store.get(config_class)
            self._store[config_class] = config_instance
            
            if old_instance:
                logger.info(f"更新配置实例: {config_class.__name__}")
            else:
                logger.info(f"存储新配置实例: {config_class.__name__}")
    
    def get_config(self, config_class: Type[T]) -> T:
        """
        获取配置实例
        
        Args:
            config_class: 配置类型
            
        Returns:
            配置实例
            
        Raises:
            ConfigNotRegisteredError: 如果配置未注册
        """
        with self._lock:
            if config_class not in self._store:
                raise ConfigNotRegisteredError(config_class)
            return self._store[config_class]
    
    def has_config(self, config_class: Type[T]) -> bool:
        """
        检查是否存在指定配置
        
        Args:
            config_class: 配置类型
            
        Returns:
            True 如果配置存在，否则 False
        """
        with self._lock:
            return config_class in self._store
    
    def remove_config(self, config_class: Type[T]) -> bool:
        """
        移除配置实例
        
        Args:
            config_class: 配置类型
            
        Returns:
            True 如果成功移除，False 如果配置不存在
        """
        with self._lock:
            if config_class in self._store:
                del self._store[config_class]
                logger.info(f"移除配置实例: {config_class.__name__}")
                return True
            return False
    
    def get_all_configs(self) -> Dict[str, BaseModel]:
        """
        获取所有配置实例
        
        Returns:
            配置类名到配置实例的映射
        """
        with self._lock:
            return {cls.__name__: instance for cls, instance in self._store.items()}
    
    def clear(self) -> None:
        """清空所有配置"""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            logger.info(f"清空了 {count} 个配置实例")
    
    def get_config_count(self) -> int:
        """获取配置数量"""
        with self._lock:
            return len(self._store)
    
    def update_config_field(self, config_class: Type[T], field_name: str, field_value: Any) -> T:
        """
        原子化更新配置的单个字段
        
        Args:
            config_class: 配置类型
            field_name: 字段名
            field_value: 新的字段值
            
        Returns:
            更新后的配置实例
            
        Raises:
            ConfigNotRegisteredError: 如果配置未注册
        """
        with self._lock:
            if config_class not in self._store:
                raise ConfigNotRegisteredError(config_class)
                
            current_instance = self._store[config_class]
            current_data = current_instance.model_dump()
            current_data[field_name] = field_value
            
            # 创建新实例以确保数据一致性
            new_instance = config_class(**current_data)
            self._store[config_class] = new_instance
            
            logger.info(f"更新配置字段: {config_class.__name__}.{field_name}")
            return new_instance
