#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 单元测试 - 配置模型

测试 NexusConfig 基础模型的功能。
"""

import pytest
from pydantic import ValidationError

from yai_nexus_configuration import NexusConfig, nexus_config


def test_nexus_config_basic_validation():
    """测试 NexusConfig 的基本 Pydantic 验证功能"""

    class ServerConfig(NexusConfig):
        host: str
        port: int = 8080

    # 测试成功创建
    config = ServerConfig(host="localhost")
    assert config.host == "localhost"
    assert config.port == 8080

    # 测试缺少必需字段
    with pytest.raises(ValidationError):
        ServerConfig()  # host is required

    # 测试字段类型错误
    with pytest.raises(ValidationError):
        ServerConfig(host="localhost", port="not-a-number")  # port must be an int


def test_nexus_config_assignment_validation():
    """测试在字段赋值时进行验证"""

    class DatabaseConfig(NexusConfig):
        host: str
        port: int

    config = DatabaseConfig(host="db", port=5432)

    # 测试修改合法值
    config.port = 5433
    assert config.port == 5433

    # 测试赋给错误类型的值
    with pytest.raises(ValidationError):
        config.port = "not-a-number"


def test_nexus_config_decorator_metadata():
    """测试 @nexus_config 装饰器是否正确附加元数据"""

    @nexus_config(data_id="app.json", group="DEFAULT_GROUP")
    class AppConfig(NexusConfig):
        debug: bool
        log_level: str

    assert hasattr(AppConfig, "__nexus_config__")
    metadata = getattr(AppConfig, "__nexus_config__")
    assert metadata["data_id"] == "app.json"
    assert metadata["group"] == "DEFAULT_GROUP"
    assert not metadata["auto_refresh"]  # Check default value


def test_nexus_config_get_summary_hides_sensitive_data():
    """测试 get_config_summary 方法是否能隐藏敏感信息"""

    class CredentialsConfig(NexusConfig):
        username: str
        password: str
        api_key: str
        secret_token: str
        normal_field: str

    config = CredentialsConfig(
        username="testuser",
        password="plain-text-password",
        api_key="my-api-key",
        secret_token="a-secret-token",
        normal_field="visible"
    )

    summary = config.get_config_summary()

    assert summary["username"] == "testuser"
    assert summary["normal_field"] == "visible"
    assert summary["password"] == "***hidden***"
    assert summary["api_key"] == "***hidden***"
    assert summary["secret_token"] == "***hidden***" 