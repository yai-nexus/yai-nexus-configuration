#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 核心管理器

NexusConfigManager 是整个配置系统的入口，采用工厂模式设计，提供优雅的 API。
"""

import json
import yaml
import logging
import warnings  # 导入 warnings 模块
import threading
from pathlib import Path
from typing import Type, TypeVar, Dict, Any, Optional, Union, List

from .internal.providers import AbstractProvider, NacosProvider, FileProvider
from .internal.store import ConfigStore
from .internal.utils import recursive_replace_env_vars  # 导入新函数
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
    
    def __init__(self, provider: Optional[AbstractProvider] = None):
        """
        初始化管理器
        
        Note: 通常不直接调用此方法，而是使用工厂方法如 with_nacos()
        
        Args:
            provider: 配置提供者实例
        """
        if provider is None:
            warnings.warn(
                "直接实例化 NexusConfigManager 已不被推荐，并将在未来版本中移除。"
                "请使用 .with_file() 或 .with_nacos() 等工厂方法创建管理器。",
                DeprecationWarning,
                stacklevel=2
            )
            # 为了保持向后兼容性，我们允许这样做，但功能将受限
            self._provider = None
        else:
            self._provider = provider
            # 仅在提供了有效的 provider 时才连接
            self._provider.connect()

        self._store = ConfigStore()
        self._registered_configs: Dict[Type, Dict[str, str]] = {}
        self._lock = threading.RLock()
        self._closed = False
        
    @classmethod
    def with_nacos(
        cls,
        server_addresses: Union[str, List[str]],
        namespace: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any
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
    
    @classmethod
    def with_file(
        cls,
        base_path: Union[str, Path] = "configs",
        default_format: str = "json",
        watch_interval: float = 1.0,
        auto_create_dirs: bool = True
    ) -> "NexusConfigManager":
        """
        使用本地文件作为配置源创建管理器
        
        Args:
            base_path: 配置文件的基础目录路径，默认为 "configs"
            default_format: 默认文件格式，支持 "json" 或 "yaml"，默认为 "json"
            watch_interval: 文件变更监听间隔（秒），默认为 1.0
            auto_create_dirs: 是否自动创建不存在的目录，默认为 True
            
        Returns:
            配置好的 NexusConfigManager 实例
            
        Example:
            >>> # 使用默认设置（JSON 格式，configs 目录）
            >>> manager = NexusConfigManager.with_file()
            >>> 
            >>> # 自定义配置
            >>> manager = NexusConfigManager.with_file(
            ...     base_path="my_configs",
            ...     default_format="yaml",
            ...     watch_interval=0.5
            ... )
            >>> manager.register(DatabaseConfig)
            >>> db_config = manager.get_config(DatabaseConfig)
            
        Note:
            文件路径格式为: {base_path}/{group}/{data_id}.{format}
            例如: configs/PROD/database.json
        """
        provider = FileProvider(
            base_path=base_path,
            default_format=default_format,
            watch_interval=watch_interval,
            auto_create_dirs=auto_create_dirs
        )
        return cls(provider)
    
    def _parse_config_content(self, content: str, data_id: str) -> Dict[str, Any]:
        """
        智能解析配置内容，支持 JSON 和 YAML，并自动替换环境变量。
        
        Args:
            content: 配置内容的原始字符串
            data_id: 配置文件名，用于推断格式
            
        Returns:
            解析后的配置字典
            
        Raises:
            ConfigValidationError: 如果解析失败或格式不正确
        """
        lowered_data_id = data_id.lower()
        data: Any

        # 严格根据文件扩展名选择解析器
        if lowered_data_id.endswith(('.yaml', '.yml')):
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ConfigValidationError(data_id, f"YAML 解析失败: {e}")
        else:
            # 默认为 JSON 解析
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ConfigValidationError(data_id, f"JSON 解析失败: {e}")

        # 验证解析后的根对象必须是字典
        if not isinstance(data, dict):
            raise ConfigValidationError(
                data_id, 
                f"配置内容必须是字典/映射格式，但解析后得到的是 {type(data).__name__}"
            )
        
        # 新增步骤：在验证前进行环境变量替换
        processed_data = recursive_replace_env_vars(data)
            
        return processed_data

    def register(self, config_class: Type[T]) -> None:
        """
        注册配置类
        
        注册后，管理器会：
        1. 从配置源获取初始配置数据
        2. 创建配置实例并存储
        3. 开始监听配置变更
        
        Args:
            config_class: 被 @nexus_config 装饰的配置类
            
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
                raise MissingConfigMetadataError(config_class, "nexus_config")
            
            data_id = metadata['data_id']
            group = metadata['group']
            
            # 从配置源获取初始配置
            try:
                raw_config = self._provider.get_config(data_id, group)
                config_data = self._parse_config_content(raw_config, data_id)
                
                # 创建配置实例
                config_instance = config_class(**config_data)
                self._store.set_config(config_instance)
                
                # 记录注册信息
                self._registered_configs[config_class] = metadata
                
                # 开始监听配置变更
                self._start_watching(config_class, data_id, group)
                
                logger.info(f"成功注册配置: {config_class.__name__} ({group}/{data_id})")
                
            except ConfigValidationError:
                raise
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
                config_data = self._parse_config_content(raw_config, data_id)
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
        关闭管理器，断开连接并清理资源。此操作是幂等的。
        """
        with self._lock:
            # 如果已经关闭，则不执行任何操作
            if self._closed:
                logger.info("管理器已关闭，无需重复操作")
                return

            # 停止所有监听器
            for config_class, metadata in list(self._registered_configs.items()):
                self._provider.unwatch_config(metadata['data_id'], metadata['group'])
            
            # 断开提供者连接
            if self._provider and self._provider.is_connected():
                self._provider.disconnect()
            
            # 清空存储并标记为已关闭
            self._store.clear()
            self._registered_configs.clear()
            self._closed = True
            
            logger.info("管理器已成功关闭")
    
    def _start_watching(self, config_class: Type, data_id: str, group: str) -> None:
        """开始监听配置变更"""
        def on_config_change(new_content: str):
            """配置变更回调"""
            try:
                config_data = self._parse_config_content(new_content, data_id)
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
