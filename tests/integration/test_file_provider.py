#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 集成测试 - 文件提供者

测试 FileProvider 与真实文件系统的交互。
"""

import pytest
import time
import json
import yaml
from pathlib import Path

from yai_nexus_configuration.internal.providers import FileProvider
from yai_nexus_configuration.exceptions import ConfigSourceError, ProviderConnectionError


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """提供一个临时的配置根目录。"""
    return tmp_path / "configs"


def test_file_provider_connect_creates_dir(tmp_path: Path):
    """测试当 auto_create_dirs=True 时，connect 方法能创建不存在的目录。"""
    non_existent_path = tmp_path / "new_configs"
    provider = FileProvider(base_path=non_existent_path, auto_create_dirs=True)
    
    assert not non_existent_path.exists()
    provider.connect()
    assert non_existent_path.exists()
    provider.disconnect()


def test_file_provider_connect_fails_if_no_dir(tmp_path: Path):
    """测试当 auto_create_dirs=False 且目录不存在时，connect 方法会失败。"""
    non_existent_path = tmp_path / "no_configs_here"
    provider = FileProvider(base_path=non_existent_path, auto_create_dirs=False)
    
    with pytest.raises(ProviderConnectionError, match="配置目录不存在"):
        provider.connect()


def test_get_json_config_success(temp_config_dir: Path):
    """测试从一个合法的 JSON 文件中成功读取配置。"""
    group_path = temp_config_dir / "app"
    group_path.mkdir(parents=True)
    
    config_file = group_path / "config.json"
    config_data = {"host": "localhost", "port": 8080}
    config_file.write_text(json.dumps(config_data))
    
    provider = FileProvider(base_path=temp_config_dir)
    provider.connect()
    
    content = provider.get_config(data_id="config.json", group="app")
    assert json.loads(content) == config_data
    provider.disconnect()


def test_get_yaml_config_success(temp_config_dir: Path):
    """测试从一个合法的 YAML 文件中成功读取配置。"""
    group_path = temp_config_dir / "db"
    group_path.mkdir(parents=True)
    
    config_file = group_path / "database.yml"
    config_data = {"user": "admin", "pass": "secret"}
    config_file.write_text(yaml.dump(config_data))

    provider = FileProvider(base_path=temp_config_dir, default_format="yaml")
    provider.connect()
    
    content = provider.get_config(data_id="database.yml", group="db")
    assert yaml.safe_load(content) == config_data
    provider.disconnect()


def test_get_config_non_existent_file_fails(temp_config_dir: Path):
    """测试读取一个不存在的配置文件会引发 ConfigSourceError。"""
    provider = FileProvider(base_path=temp_config_dir)
    provider.connect()
    
    with pytest.raises(ConfigSourceError, match="配置文件不存在"):
        provider.get_config("no_such_file.json", "default")
    provider.disconnect()


def test_get_config_empty_file_fails(temp_config_dir: Path):
    """测试读取一个空文件会引发 ConfigSourceError。"""
    group_path = temp_config_dir / "empty"
    group_path.mkdir(parents=True)
    (group_path / "empty.json").touch()

    provider = FileProvider(base_path=temp_config_dir)
    provider.connect()

    with pytest.raises(ConfigSourceError, match="配置文件为空"):
        provider.get_config("empty.json", "empty")
    provider.disconnect()


@pytest.mark.slow
def test_file_watching_callback(temp_config_dir: Path):
    """测试当文件内容发生变化时，注册的回调函数会被正确调用。"""
    group_path = temp_config_dir / "watch"
    group_path.mkdir(parents=True)
    config_file = group_path / "app.json"
    
    # 初始配置
    initial_data = {"version": 1}
    config_file.write_text(json.dumps(initial_data))

    # 使用较短的监听间隔以加速测试
    provider = FileProvider(base_path=temp_config_dir, watch_interval=0.1)
    provider.connect()

    # 使用真实的回调函数，而不是 mock
    received_updates = []
    
    def real_callback(new_content: str):
        """真实的回调函数，记录接收到的配置更新"""
        received_updates.append(new_content)

    provider.watch_config(data_id="app.json", group="watch", callback=real_callback)

    # 等待一小段时间，确保第一次文件状态已被记录
    time.sleep(0.2)
    assert len(received_updates) == 0

    # 修改文件内容
    updated_data = {"version": 2}
    config_file.write_text(json.dumps(updated_data))

    # 等待足够长的时间以确保 watcher 线程能检测到变更
    time.sleep(0.5)

    # 验证回调函数被调用，且内容正确
    assert len(received_updates) == 1
    assert json.loads(received_updates[0]) == updated_data
    
    provider.disconnect() 