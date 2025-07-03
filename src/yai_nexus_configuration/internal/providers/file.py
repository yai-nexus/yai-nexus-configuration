#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - File Provider

本地文件配置提供者，支持从 JSON/YAML 文件读取配置并监听文件变更。
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Union
from threading import Thread, Event

from .base import AbstractProvider
from ...exceptions import ProviderConnectionError, ConfigSourceError

logger = logging.getLogger(__name__)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None


class FileProvider(AbstractProvider):
    """
    本地文件配置提供者
    
    支持从本地 JSON 和 YAML 文件读取配置，并可以监听文件变更。
    文件路径模式: {base_path}/{group}/{data_id}
    """
    
    def __init__(
        self,
        base_path: Union[str, Path] = "configs",
        default_format: str = "json",
        watch_interval: float = 1.0,
        auto_create_dirs: bool = True
    ):
        """
        初始化文件 Provider
        
        Args:
            base_path: 配置文件的基础目录路径
            default_format: 默认文件格式 ('json' 或 'yaml')
            watch_interval: 文件变更监听间隔（秒）
            auto_create_dirs: 是否自动创建目录
        """
        super().__init__("File")
        
        self.base_path = Path(base_path)
        self.default_format = default_format.lower()
        self.watch_interval = watch_interval
        self.auto_create_dirs = auto_create_dirs
        
        # 文件监听相关
        self._watching = False
        self._watch_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._file_mtimes: Dict[str, float] = {}
        
        # 验证参数
        if self.default_format not in ['json', 'yaml']:
            raise ValueError("default_format 必须是 'json' 或 'yaml'")
        
        if self.default_format == 'yaml' and not HAS_YAML:
            raise ImportError("使用 YAML 格式需要安装 PyYAML: pip install PyYAML")
    
    def connect(self) -> None:
        """
        建立与文件系统的连接（主要是验证基础路径）
        
        Raises:
            ProviderConnectionError: 连接失败时抛出
        """
        try:
            # 创建基础目录（如果允许）
            if self.auto_create_dirs and not self.base_path.exists():
                self.base_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"已创建配置目录: {self.base_path}")
            
            # 验证基础路径
            if not self.base_path.exists():
                raise ProviderConnectionError(
                    "File", 
                    f"配置目录不存在: {self.base_path}"
                )
            
            if not self.base_path.is_dir():
                raise ProviderConnectionError(
                    "File", 
                    f"配置路径不是目录: {self.base_path}"
                )
            
            # 启动文件监听
            self._start_file_watching()
            
            self._set_connected(True)
            logger.info(f"成功连接到文件系统: {self.base_path}")
            
        except Exception as e:
            self._set_connected(False)
            if isinstance(e, ProviderConnectionError):
                raise
            raise ProviderConnectionError("File", f"连接失败: {str(e)}")
    
    def disconnect(self) -> None:
        """断开与文件系统的连接"""
        self._stop_file_watching()
        self._set_connected(False)
        self._watchers.clear()
        self._file_mtimes.clear()
        logger.info("已断开文件系统连接")
    
    def get_config(self, data_id: str, group: str) -> str:
        """
        从文件获取配置数据
        
        Args:
            data_id: 配置文件名（可包含扩展名）
            group: 配置组（目录名）
            
        Returns:
            配置数据的原始字符串
            
        Raises:
            ConfigSourceError: 获取配置失败时抛出
        """
        if not self.is_connected():
            raise ConfigSourceError(data_id, group, "get_config", "未连接到文件系统")
        
        try:
            file_path = self._get_config_file_path(data_id, group)
            
            if not file_path.exists():
                raise ConfigSourceError(
                    data_id, group, "get_config",
                    f"配置文件不存在: {file_path}"
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                raise ConfigSourceError(
                    data_id, group, "get_config",
                    "配置文件为空"
                )
            
            # 验证文件格式
            # self._validate_config_content(content, file_path)
            
            logger.debug(f"成功读取配置文件: {file_path}")
            return content
            
        except Exception as e:
            if isinstance(e, ConfigSourceError):
                raise
            logger.error(f"读取配置文件失败: {group}/{data_id}, 错误: {str(e)}")
            raise ConfigSourceError(data_id, group, "get_config", str(e))
    
    def watch_config(self, data_id: str, group: str, callback: Callable[[str], None]) -> None:
        """
        监听文件配置变更
        
        Args:
            data_id: 配置文件名
            group: 配置组
            callback: 配置变更时的回调函数
        """
        if not self.is_connected():
            raise ConfigSourceError(data_id, group, "watch_config", "未连接到文件系统")
        
        watcher_key = self._get_watcher_key(data_id, group)
        file_path = self._get_config_file_path(data_id, group)
        
        # 记录初始修改时间
        if file_path.exists():
            self._file_mtimes[str(file_path)] = file_path.stat().st_mtime
        
        self._register_watcher(watcher_key, callback)
        logger.info(f"开始监听配置文件变更: {file_path}")
    
    def unwatch_config(self, data_id: str, group: str) -> None:
        """
        取消监听文件配置变更
        
        Args:
            data_id: 配置文件名
            group: 配置组
        """
        watcher_key = self._get_watcher_key(data_id, group)
        file_path = self._get_config_file_path(data_id, group)
        
        # 移除修改时间记录
        if str(file_path) in self._file_mtimes:
            del self._file_mtimes[str(file_path)]
        
        self._unregister_watcher(watcher_key)
        logger.info(f"停止监听配置文件变更: {file_path}")
    
    def _get_config_file_path(self, data_id: str, group: str) -> Path:
        """
        获取配置文件的完整路径
        
        Args:
            data_id: 配置文件名
            group: 配置组
            
        Returns:
            配置文件的 Path 对象
        """
        # 如果 data_id 没有扩展名，添加默认扩展名
        if not Path(data_id).suffix:
            data_id = f"{data_id}.{self.default_format}"
        
        return self.base_path / group / data_id
    
    def _start_file_watching(self) -> None:
        """启动文件变更监听线程"""
        if self._watching:
            return
        
        self._watching = True
        self._stop_event.clear()
        self._watch_thread = Thread(target=self._file_watch_loop, daemon=True)
        self._watch_thread.start()
        logger.debug("文件监听线程已启动")
    
    def _stop_file_watching(self) -> None:
        """停止文件变更监听线程"""
        if not self._watching:
            return
        
        self._watching = False
        self._stop_event.set()
        
        if self._watch_thread and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=2.0)
        
        logger.debug("文件监听线程已停止")
    
    def _file_watch_loop(self) -> None:
        """文件变更监听循环"""
        while self._watching and not self._stop_event.is_set():
            try:
                self._check_file_changes()
            except Exception as e:
                logger.error(f"文件监听出错: {str(e)}")
            
            # 等待下次检查
            self._stop_event.wait(self.watch_interval)
    
    def _check_file_changes(self) -> None:
        """检查文件变更并触发回调"""
        # 创建 watcher 字典的副本进行迭代，以避免在迭代期间修改字典
        for watcher_key, callback in list(self._watchers.items()):
            group, data_id = watcher_key.split("::", 1)
            file_path = self._get_config_file_path(data_id, group)
            
            # 检查文件是否存在
            if not file_path.exists():
                continue
            
            try:
                current_mtime = file_path.stat().st_mtime
                last_mtime = self._file_mtimes.get(str(file_path))

                # 如果是新文件或文件已修改
                if last_mtime is None or current_mtime > last_mtime:
                    logger.info(f"检测到文件变更: {file_path}")
                    self._file_mtimes[str(file_path)] = current_mtime
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        if content:
                            callback(content)
                        else:
                            logger.warning(f"配置文件变为空，跳过回调: {file_path}")
                            
                    except Exception as e:
                        logger.error(f"读取变更后的文件失败: {file_path}, 错误: {e}")

            except FileNotFoundError:
                # 文件可能在检查期间被删除
                if str(file_path) in self._file_mtimes:
                    del self._file_mtimes[str(file_path)]
                logger.warning(f"文件在检查期间被删除: {file_path}")
            
            except Exception as e:
                logger.error(f"检查文件变更时出错: {file_path}, 错误: {e}")
    
    def create_sample_config(self, data_id: str, group: str, config_data: dict) -> Path:
        """
        创建示例配置文件（辅助方法）
        
        Args:
            data_id: 配置文件名
            group: 配置组
            config_data: 配置数据
            
        Returns:
            创建的文件路径
        """
        file_path = self._get_config_file_path(data_id, group)
        
        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 根据文件扩展名选择格式
        file_ext = file_path.suffix.lower()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_ext in ['.yaml', '.yml'] and HAS_YAML:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            else:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"已创建示例配置文件: {file_path}")
        return file_path 