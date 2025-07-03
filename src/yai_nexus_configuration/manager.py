#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 核心管理器

NexusConfigManager 是整个配置系统的入口，采用工厂模式设计，提供优雅的 API。
"""

import json
import logging
import threading
from typing import Type, TypeVar, Dict, Any, Optional, Union, List

from .providers import AbstractProvider, NacosProvider
from .store import ConfigStore
from .decorator import get_config_metadata
from .exceptions import (
    ConfigNotRegisteredError,
    ConfigValidationError,
    MissingConfigMetadataError,
    ProviderConnectionError
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


class NexusConfigManager:
    """
    配置管理器
    
    提供配置的注册、获取和自动更新功能。采用工厂模式设计，
    支持多种配置源（Nacos、Apollo 等）。
    
    主要特性：
    - 工厂方法创建：通过 with_nacos() 等方法创建实例
    - 自动配置更新：监听配置源变更，自动更新本地配置
    - 线程安全：所有操作都是线程安全的
    - 类型安全：完整的类型提示支持
    """
    
    def __init__(self, provider: AbstractProvider):
        """
        初始化管理器
        
        Note: 通常不直接调用此方法，而是使用工厂方法如 with_nacos()
        
        Args:
            provider: 配置提供者实例
        """
        self._provider = provider
        self._store = ConfigStore()
        self._registered_configs: Dict[Type, Dict[str, str]] = {}
        self._lock = threading.RLock()
        
        # 连接到配置源
        self._provider.connect()
        
    @classmethod
    def with_nacos(
        cls,
        server_addresses: Union[str, List[str]],
        namespace: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ) -> "NexusConfigManager":
        """
        使用 Nacos 作为配置源创建管理器
        
        Args:
            server_addresses: Nacos 服务器地址
            namespace: 命名空间，默认为空（公共命名空间）
            username: 用户名（可选）
            password: 密码（可选）
            **kwargs: 其他传递给 Nacos 客户端的参数
            
        Returns:
            配置好的 NexusConfigManager 实例
            
        Example:
            >>> manager = NexusConfigManager.with_nacos("localhost:8848")
            >>> manager.register(DatabaseConfig)
            >>> db_config = manager.get_config(DatabaseConfig)
        """
        provider = NacosProvider(
            server_addresses=server_addresses,
            namespace=namespace,
            username=username,
            password=password,
            **kwargs
        )
        return cls(provider)
    
    def register(self, config_class: Type[T]) -> None:
        """
        注册配置类
        
        注册后，管理器会：
        1. 从配置源获取初始配置数据
        2. 创建配置实例并存储
        3. 开始监听配置变更
        
        Args:
            config_class: 被 @nacos_config 装饰的配置类
            
        Raises:
            MissingConfigMetadataError: 如果配置类缺少必要的元数据
            ConfigValidationError: 如果配置数据验证失败
        """
        with self._lock:
            # 检查是否已注册
            if config_class in self._registered_configs:
                logger.warning(f"配置类 {config_class.__name__} 已经注册，跳过")
                return
            
            # 获取配置元数据
            metadata = get_config_metadata(config_class)
            if not metadata:
                raise MissingConfigMetadataError(config_class, "nacos_config")
            
            data_id = metadata['data_id']
            group = metadata['group']
            
            # 从配置源获取初始配置
            try:
                raw_config = self._provider.get_config(data_id, group)
                config_data = json.loads(raw_config)
                
                # 创建配置实例
                config_instance = config_class(**config_data)
                self._store.set_config(config_instance)
                
                # 记录注册信息
                self._registered_configs[config_class] = metadata
                
                # 开始监听配置变更
                self._start_watching(config_class, data_id, group)
                
                logger.info(f"成功注册配置: {config_class.__name__} ({group}/{data_id})")
                
            except json.JSONDecodeError as e:
                raise ConfigValidationError(f"{group}/{data_id}", f"JSON 解析失败: {e}")
            except Exception as e:
                if "ValidationError" in str(type(e)):
                    raise ConfigValidationError(f"{group}/{data_id}", str(e))
                raise
    
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
        return self._store.get_config(config_class)
    
    def unregister(self, config_class: Type[T]) -> bool:
        """
        取消注册配置类
        
        Args:
            config_class: 配置类型
            
        Returns:
            True 如果成功取消注册，False 如果配置未注册
        """
        with self._lock:
            if config_class not in self._registered_configs:
                return False
            
            metadata = self._registered_configs[config_class]
            data_id = metadata['data_id']
            group = metadata['group']
            
            # 停止监听
            self._provider.unwatch_config(data_id, group)
            
            # 移除存储
            self._store.remove_config(config_class)
            del self._registered_configs[config_class]
            
            logger.info(f"取消注册配置: {config_class.__name__}")
            return True
    
    def reload_config(self, config_class: Type[T]) -> T:
        """
        重新加载指定配置
        
        Args:
            config_class: 配置类型
            
        Returns:
            更新后的配置实例
        """
        with self._lock:
            if config_class not in self._registered_configs:
                raise ConfigNotRegisteredError(config_class)
            
            metadata = self._registered_configs[config_class]
            data_id = metadata['data_id']
            group = metadata['group']
            
            try:
                raw_config = self._provider.get_config(data_id, group)
                config_data = json.loads(raw_config)
                config_instance = config_class(**config_data)
                
                self._store.set_config(config_instance)
                logger.info(f"重新加载配置: {config_class.__name__}")
                return config_instance
                
            except Exception as e:
                logger.error(f"重新加载配置失败: {config_class.__name__}, 错误: {e}")
                raise
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有已注册的配置实例"""
        return self._store.get_all_configs()
    
    def get_manager_info(self) -> Dict[str, Any]:
        """
        获取管理器状态信息
        
        Returns:
            包含提供者信息、注册配置数量等的状态字典
        """
        return {
            'provider': self._provider.get_provider_info(),
            'registered_configs': len(self._registered_configs),
            'config_names': [cls.__name__ for cls in self._registered_configs.keys()],
            'store_config_count': self._store.get_config_count()
        }
    
    def close(self) -> None:
        """
        关闭管理器，断开连接并清理资源
        """
        with self._lock:
            # 停止所有监听器
            for config_class, metadata in self._registered_configs.items():
                self._provider.unwatch_config(metadata['data_id'], metadata['group'])
            
            # 断开提供者连接
            self._provider.disconnect()
            
            # 清空存储
            self._store.clear()
            self._registered_configs.clear()
            
            logger.info("管理器已关闭")
    
    def _start_watching(self, config_class: Type, data_id: str, group: str) -> None:
        """开始监听配置变更"""
        def on_config_change(new_content: str):
            """配置变更回调"""
            try:
                config_data = json.loads(new_content)
                new_instance = config_class(**config_data)
                self._store.set_config(new_instance)
                logger.info(f"配置已更新: {config_class.__name__}")
            except Exception as e:
                logger.error(f"处理配置变更时出错: {config_class.__name__}, 错误: {e}")
        
        self._provider.watch_config(data_id, group, on_config_change)
    
    def __enter__(self):
        """上下文管理器支持"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器支持"""
        self.close()
