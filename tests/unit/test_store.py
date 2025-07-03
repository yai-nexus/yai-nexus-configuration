#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 单元测试 - 配置存储

测试 ConfigStore 的核心功能，确保其线程安全地存储和检索配置实例。
"""

import pytest
import threading

from yai_nexus_configuration.internal.store import ConfigStore
from yai_nexus_configuration.exceptions import ConfigNotRegisteredError
from yai_nexus_configuration import NexusConfig


class ConfigA(NexusConfig):
    name: str

class ConfigB(NexusConfig):
    value: int


@pytest.fixture
def store() -> ConfigStore:
    """提供一个空的 ConfigStore 实例。"""
    return ConfigStore()


def test_set_and_get_config(store: ConfigStore):
    """测试设置和获取单个配置实例。"""
    instance_a = ConfigA(name="test_a")
    store.set_config(instance_a)

    retrieved_a = store.get_config(ConfigA)
    assert retrieved_a is instance_a
    assert store.get_config_count() == 1


def test_get_non_existent_config_fails(store: ConfigStore):
    """测试获取一个不存在的配置会引发异常。"""
    with pytest.raises(ConfigNotRegisteredError):
        store.get_config(ConfigA)


def test_set_multiple_configs(store: ConfigStore):
    """测试设置和获取多个不同的配置实例。"""
    instance_a = ConfigA(name="test_a")
    instance_b = ConfigB(value=123)

    store.set_config(instance_a)
    store.set_config(instance_b)

    assert store.get_config_count() == 2
    assert store.get_config(ConfigA) is instance_a
    assert store.get_config(ConfigB) is instance_b


def test_overwrite_config(store: ConfigStore):
    """测试用一个新的实例覆盖一个已存在的配置。"""
    original_instance = ConfigA(name="original")
    store.set_config(original_instance)

    new_instance = ConfigA(name="new")
    store.set_config(new_instance)

    assert store.get_config_count() == 1
    assert store.get_config(ConfigA) is new_instance
    assert store.get_config(ConfigA).name == "new"


def test_remove_config(store: ConfigStore):
    """测试移除一个已存在的配置。"""
    instance_a = ConfigA(name="test_a")
    store.set_config(instance_a)
    assert store.get_config_count() == 1

    removed = store.remove_config(ConfigA)
    assert removed is True
    assert store.get_config_count() == 0

    with pytest.raises(ConfigNotRegisteredError):
        store.get_config(ConfigA)


def test_remove_non_existent_config(store: ConfigStore):
    """测试移除一个不存在的配置会返回 False。"""
    removed = store.remove_config(ConfigA)
    assert removed is False


def test_get_all_configs(store: ConfigStore):
    """测试 get_all_configs 方法能返回所有配置的字典。"""
    instance_a = ConfigA(name="test_a")
    instance_b = ConfigB(value=123)

    store.set_config(instance_a)
    store.set_config(instance_b)

    all_configs = store.get_all_configs()
    assert len(all_configs) == 2
    assert all_configs[ConfigA.__name__] is instance_a
    assert all_configs[ConfigB.__name__] is instance_b


def test_clear_store(store: ConfigStore):
    """测试 clear 方法能移除所有配置。"""
    store.set_config(ConfigA(name="test_a"))
    store.set_config(ConfigB(value=123))
    assert store.get_config_count() == 2

    store.clear()
    assert store.get_config_count() == 0
    assert store.get_all_configs() == {}


def test_concurrent_access_to_store():
    """测试 ConfigStore 在多线程环境下的线程安全。"""
    store = ConfigStore()
    
    class ConfigA(NexusConfig):
        val: int
    
    class ConfigB(NexusConfig):
        val: int

    num_threads = 10
    iterations = 100
    
    def worker(config_class, start_val):
        for i in range(iterations):
            instance = config_class(val=start_val + i)
            store.set_config(instance)
            retrieved = store.get_config(config_class)
            assert retrieved.val >= start_val

    threads = []
    for i in range(num_threads):
        # 交替读写不同的配置类
        config_class = ConfigA if i % 2 == 0 else ConfigB
        thread = threading.Thread(target=worker, args=(config_class, i * iterations))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # 验证最终状态
    assert store.get_config_count() == 2
    final_a = store.get_config(ConfigA)
    final_b = store.get_config(ConfigB)
    assert isinstance(final_a, ConfigA)
    assert isinstance(final_b, ConfigB)


def test_set_config_with_invalid_type():
    """测试当 set_config 接收到非 NexusConfig 对象时会失败。"""
    store = ConfigStore()
    
    class NotAConfig:
        pass
    
    with pytest.raises(TypeError, match="只能存储 NexusConfig 的子类实例"):
        store.set_config(NotAConfig()) 