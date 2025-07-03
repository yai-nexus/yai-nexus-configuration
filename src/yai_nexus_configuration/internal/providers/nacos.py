#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - Nacos Provider

Nacos 配置中心的具体实现，提供与 Nacos 服务器的交互功能。
"""

import json
import logging
from typing import Callable, Optional, Union, List

from .base import AbstractProvider
from ...exceptions import ProviderConnectionError, ConfigSourceError

logger = logging.getLogger(__name__)

try:
    import nacos
except ImportError:
    nacos = None


class NacosProvider(AbstractProvider):
    """
    Nacos 配置提供者
    
    提供与 Nacos 服务器的连接和配置管理功能，包括：
    - 连接到 Nacos 服务器
    - 获取配置数据
    - 监听配置变更
    """
    
    def __init__(
        self,
        server_addresses: Union[str, List[str]],
        namespace: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """
        初始化 Nacos Provider
        
        Args:
            server_addresses: Nacos 服务器地址，可以是单个地址或地址列表
            namespace: 命名空间 ID，默认为空字符串（公共命名空间）
            username: 用户名，可选
            password: 密码，可选
            **kwargs: 其他传递给 nacos 客户端的参数
        """
        super().__init__("Nacos")
        
        if nacos is None:
            raise ImportError(
                "nacos-sdk-python 未安装。请运行: pip install nacos-sdk-python"
            )
        
        self.server_addresses = server_addresses
        self.namespace = namespace
        self.username = username
        self.password = password
        self.client_kwargs = kwargs
        self._client: Optional[nacos.NacosClient] = None
    
    def connect(self) -> None:
        """
        建立与 Nacos 服务器的连接
        
        Raises:
            ProviderConnectionError: 连接失败时抛出
        """
        try:
            # 构建客户端参数
            client_config = {
                'server_addresses': self.server_addresses,
                'namespace': self.namespace,
                **self.client_kwargs
            }
            
            # 添加认证信息（如果提供）
            if self.username and self.password:
                client_config.update({
                    'username': self.username,
                    'password': self.password
                })
            
            self._client = nacos.NacosClient(**client_config)
            
            # 测试连接
            try:
                # 尝试获取一个不存在的配置来测试连接
                self._client.get_config("__connection_test__", "DEFAULT_GROUP", no_snapshot=True)
            except Exception:
                # 预期会失败，但这说明连接是正常的
                pass
            
            self._set_connected(True)
            logger.info(f"成功连接到 Nacos 服务器: {self.server_addresses}")
            
        except Exception as e:
            self._set_connected(False)
            raise ProviderConnectionError("Nacos", f"连接失败: {str(e)}")
    
    def disconnect(self) -> None:
        """断开与 Nacos 服务器的连接"""
        if self._client:
            # Nacos 客户端没有显式的断开连接方法，直接置空
            self._client = None
        
        self._set_connected(False)
        self._watchers.clear()
        logger.info("已断开 Nacos 连接")
    
    def get_config(self, data_id: str, group: str) -> str:
        """
        从 Nacos 获取配置数据
        
        Args:
            data_id: 配置 ID
            group: 配置组
            
        Returns:
            配置数据的原始字符串
            
        Raises:
            ConfigSourceError: 获取配置失败时抛出
        """
        if not self._client:
            raise ConfigSourceError(data_id, group, "get_config", "未连接到 Nacos 服务器")
        
        try:
            config_content = self._client.get_config(data_id, group)
            
            if config_content is None:
                raise ConfigSourceError(
                    data_id, group, "get_config",
                    "配置不存在或返回空内容"
                )
            
            logger.debug(f"成功获取配置: {group}/{data_id}")
            return config_content
            
        except Exception as e:
            logger.error(f"获取配置失败: {group}/{data_id}, 错误: {str(e)}")
            raise ConfigSourceError(data_id, group, "get_config", str(e))
    
    def watch_config(self, data_id: str, group: str, callback: Callable[[str], None]) -> None:
        """
        监听 Nacos 配置变更
        
        Args:
            data_id: 配置 ID
            group: 配置组
            callback: 配置变更时的回调函数
        """
        if not self._client:
            raise ConfigSourceError(data_id, group, "watch_config", "未连接到 Nacos 服务器")
        
        watcher_key = self._get_watcher_key(data_id, group)
        
        def nacos_callback(new_content: str):
            """Nacos 配置变更回调的包装器"""
            try:
                logger.info(f"检测到配置变更: {group}/{data_id}")
                callback(new_content)
            except Exception as e:
                logger.error(f"处理配置变更回调时出错: {group}/{data_id}, 错误: {str(e)}")
        
        try:
            self._client.add_config_watcher(data_id, group, nacos_callback)
            self._register_watcher(watcher_key, nacos_callback)
            logger.info(f"开始监听配置变更: {group}/{data_id}")
            
        except Exception as e:
            logger.error(f"注册配置监听器失败: {group}/{data_id}, 错误: {str(e)}")
            raise ConfigSourceError(data_id, group, "watch_config", str(e))
    
    def unwatch_config(self, data_id: str, group: str) -> None:
        """
        取消监听 Nacos 配置变更
        
        Args:
            data_id: 配置 ID
            group: 配置组
        """
        if not self._client:
            return
        
        watcher_key = self._get_watcher_key(data_id, group)
        
        # 从内部存储中获取回调函数
        callback = self._watchers.get(watcher_key)
        
        if not callback:
            logger.warning(f"尝试取消未注册的监听器: {group}/{data_id}")
            return
            
        try:
            self._client.remove_config_watcher(data_id, group, cb=callback)
            self._unregister_watcher(watcher_key)
            logger.info(f"停止监听配置变更: {group}/{data_id}")
            
        except Exception as e:
            logger.warning(f"取消配置监听器时出错: {group}/{data_id}, 错误: {str(e)}")
    
    def get_provider_info(self) -> dict:
        """获取 Nacos Provider 的详细信息"""
        base_info = super().get_provider_info()
        nacos_info = {
            'server_addresses': self.server_addresses,
            'namespace': self.namespace,
            'username': self.username if self.username else None,
            'client_initialized': self._client is not None
        }
        return {**base_info, **nacos_info}
