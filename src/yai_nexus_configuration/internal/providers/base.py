#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - Provider 抽象基类

定义了配置提供者的标准接口，所有具体的 Provider 实现都必须继承此类。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class AbstractProvider(ABC):
    """
    配置提供者的抽象基类
    
    定义了所有配置提供者必须实现的标准接口，包括：
    - 获取配置数据
    - 监听配置变更
    - 连接和断开连接
    """
    
    def __init__(self, name: str):
        """
        初始化 Provider
        
        Args:
            name: Provider 的名称，用于日志和错误信息
        """
        self.name = name
        self._connected = False
        self._watchers: Dict[str, Callable[[str], None]] = {}
    
    @abstractmethod
    def connect(self) -> None:
        """
        建立与配置源的连接
        
        Raises:
            ProviderConnectionError: 连接失败时抛出
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开与配置源的连接"""
        pass
    
    @abstractmethod
    def get_config(self, data_id: str, group: str) -> str:
        """
        获取配置数据
        
        Args:
            data_id: 配置 ID
            group: 配置组
            
        Returns:
            配置数据的原始字符串（通常是 JSON）
            
        Raises:
            ConfigSourceError: 获取配置失败时抛出
        """
        pass
    
    @abstractmethod
    def watch_config(self, data_id: str, group: str, callback: Callable[[str], None]) -> None:
        """
        监听配置变更
        
        Args:
            data_id: 配置 ID
            group: 配置组
            callback: 配置变更时的回调函数，参数为新的配置内容
        """
        pass
    
    @abstractmethod
    def unwatch_config(self, data_id: str, group: str) -> None:
        """
        取消监听配置变更
        
        Args:
            data_id: 配置 ID
            group: 配置组
        """
        pass
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def _set_connected(self, connected: bool) -> None:
        """设置连接状态（供子类使用）"""
        self._connected = connected
        logger.info(f"Provider {self.name} 连接状态: {'已连接' if connected else '已断开'}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        获取 Provider 的基本信息
        
        Returns:
            包含 Provider 名称、连接状态等信息的字典
        """
        return {
            'name': self.name,
            'connected': self._connected,
            'watchers_count': len(self._watchers)
        }
    
    def _register_watcher(self, key: str, callback: Callable[[str], None]) -> None:
        """注册监听器（供子类使用）"""
        self._watchers[key] = callback
        logger.debug(f"注册配置监听器: {key}")
    
    def _unregister_watcher(self, key: str) -> None:
        """取消注册监听器（供子类使用）"""
        if key in self._watchers:
            del self._watchers[key]
            logger.debug(f"取消配置监听器: {key}")
    
    def _get_watcher_key(self, data_id: str, group: str) -> str:
        """生成监听器的唯一键"""
        return f"{group}::{data_id}"
