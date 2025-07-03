#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 单元测试 - 核心管理器

测试 NexusConfigManager 的核心功能，包括配置生命周期、工厂方法和错误处理。
"""

import pytest
from unittest.mock import MagicMock, patch, ANY

from yai_nexus_configuration import (
    NexusConfigManager,
    NexusConfig,
    nexus_config,
    ConfigNotRegisteredError,
    MissingConfigMetadataError,
    ConfigValidationError,
)
from yai_nexus_configuration.internal.providers import AbstractProvider


# 用于测试的、被装饰器标记的配置类
@nexus_config(data_id="test_config.json", group="test_group")
class DecoratedConfig(NexusConfig):
    host: str
    port: int

# 用于测试的、未被装饰器标记的配置类
class UndecoratedConfig(NexusConfig):
    value: str


@pytest.fixture
def mock_provider() -> MagicMock:
    """提供一个 AbstractProvider 的模拟替代品。"""
    provider = MagicMock(spec=AbstractProvider)
    # 模拟从 Provider 获取一个合法的 JSON 配置字符串
    provider.get_config.return_value = '{"host": "test.db", "port": 5432}'
    return provider


@pytest.fixture
def manager(mock_provider: MagicMock) -> NexusConfigManager:
    """提供一个使用模拟 Provider 初始化的 NexusConfigManager 实例。"""
    # 在单元测试中，我们不希望调用真实的 connect() 方法。
    # 通过 patch Provider 的 connect，我们可以在无副作用的情况下实例化 manager。
    with patch.object(AbstractProvider, 'connect'):
        mgr = NexusConfigManager(provider=mock_provider)
    
    # 确保 manager 在初始化时调用了其 provider 的 connect 方法。
    # 我们直接对传入的 mock_provider 进行断言，因为 manager 内部持有了它的引用。
    mock_provider.connect.assert_called_once()
    return mgr


def test_register_and_get_config_success(manager: NexusConfigManager, mock_provider: MagicMock):
    """测试一个被装饰的配置类可以被成功注册和获取。"""
    manager.register(DecoratedConfig)

    # 断言 manager 调用了 provider 来获取初始配置
    mock_provider.get_config.assert_called_once_with("test_config.json", "test_group")

    # 断言 manager 开始监听配置变更
    mock_provider.watch_config.assert_called_once_with("test_config.json", "test_group", ANY)

    # 获取配置实例并验证其内容
    config_instance = manager.get_config(DecoratedConfig)
    assert isinstance(config_instance, DecoratedConfig)
    assert config_instance.host == "test.db"
    assert config_instance.port == 5432


def test_get_unregistered_config_fails(manager: NexusConfigManager):
    """测试获取一个未注册的配置类会引发异常。"""
    with pytest.raises(ConfigNotRegisteredError):
        manager.get_config(DecoratedConfig)


def test_register_undecorated_config_fails(manager: NexusConfigManager):
    """测试注册一个没有被 @nexus_config 装饰的配置类会引发异常。"""
    with pytest.raises(MissingConfigMetadataError):
        manager.register(UndecoratedConfig)


def test_register_already_registered_skips(manager: NexusConfigManager, mock_provider: MagicMock, caplog):
    """测试重复注册一个配置类会被安全地忽略。"""
    manager.register(DecoratedConfig)
    
    # 在初次注册后重置 mock 的调用计数
    mock_provider.get_config.reset_mock()
    
    # 尝试再次注册
    with caplog.at_level("WARNING"):
        manager.register(DecoratedConfig)

    # 验证 provider 的 get_config 没有被再次调用
    mock_provider.get_config.assert_not_called()
    # 验证日志中记录了相应的警告信息
    assert "已经注册，跳过" in caplog.text


def test_unregister_config_success(manager: NexusConfigManager, mock_provider: MagicMock):
    """测试一个已注册的配置可以被成功注销。"""
    manager.register(DecoratedConfig)

    # 注销配置
    unregistered = manager.unregister(DecoratedConfig)
    assert unregistered is True

    # 验证 provider 停止了对该配置的监听
    mock_provider.unwatch_config.assert_called_once_with("test_config.json", "test_group")

    # 验证该配置无法再被获取
    with pytest.raises(ConfigNotRegisteredError):
        manager.get_config(DecoratedConfig)


def test_unregister_not_registered_config(manager: NexusConfigManager):
    """测试注销一个从未注册过的配置会返回 False。"""
    unregistered = manager.unregister(DecoratedConfig)
    assert unregistered is False


@patch('yai_nexus_configuration.manager.NacosProvider')
def test_with_nacos_factory(MockNacosProvider):
    """测试 with_nacos 工厂方法能创建一个带有 NacosProvider 的管理器。"""
    # 创建一个模拟的 provider 实例，工厂方法将会返回它
    mock_instance = MockNacosProvider.return_value
    
    server_addr = "localhost:8848"
    namespace = "test-ns"
    
    # 调用工厂方法
    manager = NexusConfigManager.with_nacos(server_addresses=server_addr, namespace=namespace)

    # 断言 NacosProvider 是用正确的参数初始化的
    MockNacosProvider.assert_called_once_with(
        server_addresses=server_addr,
        namespace=namespace,
        username=None,
        password=None
    )

    # 断言 manager 的 provider 就是我们模拟的实例
    assert manager._provider == mock_instance
    # 断言 provider 的 connect 方法被调用了
    mock_instance.connect.assert_called_once()


@patch('yai_nexus_configuration.manager.FileProvider')
def test_with_file_factory(MockFileProvider):
    """测试 with_file 工厂方法能创建一个带有 FileProvider 的管理器。"""
    mock_instance = MockFileProvider.return_value
    
    base_path = "/tmp/configs"
    
    manager = NexusConfigManager.with_file(base_path=base_path)

    # 断言 FileProvider 是用正确的参数初始化的
    MockFileProvider.assert_called_once_with(
        base_path=base_path,
        default_format="json",
        watch_interval=1.0,
        auto_create_dirs=True
    )
    
    # 断言 manager 的 provider 就是我们模拟的实例
    assert manager._provider == mock_instance
    # 断言 provider 的 connect 方法被调用了
    mock_instance.connect.assert_called_once()


def test_reload_config_success(manager: NexusConfigManager, mock_provider: MagicMock):
    """测试 reload_config 方法能强制从 provider 重新加载配置。"""
    manager.register(DecoratedConfig)
    
    # 模拟 provider 返回了新的配置数据
    mock_provider.get_config.return_value = '{"host": "new.db", "port": 1234}'
    
    # 重新加载配置
    reloaded_config = manager.reload_config(DecoratedConfig)

    # 验证 get_config 被再次调用以获取新数据
    assert mock_provider.get_config.call_count == 2
    
    # 验证返回的实例和存储中的实例都已更新
    assert reloaded_config.host == "new.db"
    assert reloaded_config.port == 1234
    
    stored_config = manager.get_config(DecoratedConfig)
    assert stored_config.host == "new.db"


def test_reload_unregistered_config_fails(manager: NexusConfigManager):
    """测试对一个未注册的配置调用 reload_config 会引发异常。"""
    with pytest.raises(ConfigNotRegisteredError):
        manager.reload_config(DecoratedConfig)


def test_config_change_callback_updates_store(manager: NexusConfigManager, mock_provider: MagicMock):
    """测试当 provider 的配置变更时，manager 会自动更新存储中的配置实例。"""
    manager.register(DecoratedConfig)

    # 从 watch_config 的调用中捕获回调函数
    # call_args[0] 是位置参数，(data_id, group, callback)
    captured_callback = mock_provider.watch_config.call_args[0][2]
    
    # 模拟一次配置变更，并调用回调函数
    new_config_content = '{"host": "updated.db", "port": 5678}'
    captured_callback(new_config_content)

    # 验证存储中的配置实例是否已自动更新
    updated_config = manager.get_config(DecoratedConfig)
    assert updated_config.host == "updated.db"
    assert updated_config.port == 5678


def test_register_with_invalid_json_content(mock_provider):
    """测试当配置文件内容为非法 JSON 时，register 方法会失败。"""
    
    @nexus_config(data_id="invalid.json", group="test")
    class InvalidJsonConfig(NexusConfig):
        key: str

    # 模拟 provider 返回非法的 JSON 字符串
    mock_provider.get_config.return_value = "{'key': 'invalid json'}" # 使用单引号
    
    manager = NexusConfigManager(mock_provider)
    
    with pytest.raises(ConfigValidationError, match="JSON 解析失败"):
        manager.register(InvalidJsonConfig)


def test_register_with_invalid_yaml_content(mock_provider):
    """
    测试当 YAML 内容解析后不是字典时，register 方法会失败。
    PyYAML 对于某些格式错误（如缩进）不会抛出 YAMLError，而是会解析成非字典类型。
    """

    @nexus_config(data_id="invalid.yml", group="test")
    class InvalidYamlConfig(NexusConfig):
        key: str

    # 这个字符串会被 PyYAML 解析为一个列表，而不是字典
    mock_provider.get_config.return_value = "- item1\n- item2"
    
    manager = NexusConfigManager(mock_provider)
    
    with pytest.raises(ConfigValidationError, match="配置内容必须是字典/映射格式"):
        manager.register(InvalidYamlConfig)


def test_register_with_non_dict_content(mock_provider):
    """测试当配置文件内容解析后不是字典时，register 方法会失败。"""
    
    @nexus_config(data_id="list.json", group="test")
    class ListConfig(NexusConfig):
        key: str
        
    # 模拟 provider 返回一个 JSON 数组，而不是对象
    mock_provider.get_config.return_value = "[1, 2, 3]"
    
    manager = NexusConfigManager(mock_provider)
    
    with pytest.raises(ConfigValidationError, match="配置内容必须是字典/映射格式"):
        manager.register(ListConfig)


def test_close_manager(mock_provider):
    """测试 close 方法能正确关闭 manager，并清理所有资源。"""
    
    @nexus_config(data_id="config.json", group="test")
    class SomeConfig(NexusConfig):
        key: str
        
    # 为 get_config 设置一个符合 SomeConfig 结构的返回值
    mock_provider.get_config.return_value = '{"key": "some_value"}'
        
    manager = NexusConfigManager(mock_provider)
    manager.register(SomeConfig)
    
    # 在 close 之前，确认状态
    assert len(manager._registered_configs) == 1
    assert manager._store.get_config_count() == 1
    mock_provider.connect.assert_called_once()
    mock_provider.watch_config.assert_called_once()
    
    # 调用 close
    manager.close()
    
    # 验证清理行为
    mock_provider.disconnect.assert_called_once()
    mock_provider.unwatch_config.assert_called_once_with("config.json", "test")
    assert len(manager._registered_configs) == 0
    assert manager._store.get_config_count() == 0
    
    # 验证 close 之后，再次调用无副作用
    manager.close()
    mock_provider.disconnect.assert_called_once() # disconnect 不应被再次调用 