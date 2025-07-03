#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - Nacos Provider 集成测试

测试 NexusConfigManager + NacosProvider 的工作流程。
这个测试需要一个正在运行的 Nacos 实例，并通过环境变量进行配置。
"""

import pytest
import os
import json
from typing import Optional

from yai_nexus_configuration import (
    NexusConfigManager,
    NexusConfig,
    nexus_config,
)

# --- 从环境变量获取 Nacos 配置 ---
# 您提供的服务器地址将通过环境变量传入
NACOS_SERVER_ADDR = os.environ.get("NACOS_SERVER_ADDR")
# 您提供的分组
NACOS_GROUP = os.environ.get("NACOS_GROUP", "yai-nexus-configuration")
# 其他可选配置
NACOS_NAMESPACE = os.environ.get("NACOS_NAMESPACE", "")
NACOS_USERNAME = os.environ.get("NACOS_USERNAME")
NACOS_PASSWORD = os.environ.get("NACOS_PASSWORD")

# --- 测试用的 Data ID 和预期的配置内容 ---
JSON_TEST_DATA_ID = "yai-nexus-configuration-json-test-1.json"
YAML_TEST_DATA_ID = "yai-nexus-configuration-yaml-test-1.yaml"

EXPECTED_JSON_CONFIG = {
    "app_name": "test_app",
    "version": "1.0.0",
    "enabled": True,
}

EXPECTED_YAML_CONFIG = {
    "server": {"host": "yaml-server.example.com", "port": 8080},
    "retries": [100, 200, 500],
}

# --- Pytest 标记 ---
# 如果没有设置 NACOS_SERVER_ADDR，则跳过此测试模块中的所有测试
requires_nacos = pytest.mark.skipif(
    not NACOS_SERVER_ADDR,
    reason="需要设置 NACOS_SERVER_ADDR 环境变量来运行 Nacos 集成测试"
)


# --- 测试用的配置类 ---
@nexus_config(data_id=JSON_TEST_DATA_ID, group=NACOS_GROUP)
class NacosJsonTestConfig(NexusConfig):
    app_name: str
    version: str
    enabled: bool


class ServerDetails(NexusConfig):
    host: str
    port: int


@nexus_config(data_id=YAML_TEST_DATA_ID, group=NACOS_GROUP)
class NacosYamlTestConfig(NexusConfig):
    server: ServerDetails
    retries: list[int]


@pytest.fixture(scope="module")
def nacos_connection_args():
    """提供 Nacos 连接参数字典的 Fixture"""
    if not NACOS_SERVER_ADDR:
        pytest.skip("Nacos server address not configured.")

    print(f"\n--- [Nacos Test Setup] ---")
    print(f"  服务器: {NACOS_SERVER_ADDR}")
    print(f"  命名空间: {NACOS_NAMESPACE or 'public'}")
    print(f"  用户: {NACOS_USERNAME or '未设置'}")
    print(f"  分组: {NACOS_GROUP}")
    print(f"  测试 JSON Data ID: {JSON_TEST_DATA_ID}")
    print(f"  测试 YAML Data ID: {YAML_TEST_DATA_ID}")
    print(f"--- [Nacos Test Setup] ---")

    connection_args = {
        "server_addresses": NACOS_SERVER_ADDR,
        "namespace": NACOS_NAMESPACE,
        "username": NACOS_USERNAME,
        "password": NACOS_PASSWORD
    }
    
    # 清理掉值为 None 的参数
    return {k: v for k, v in connection_args.items() if v is not None}


@requires_nacos
def test_nacos_config_retrieval(nacos_connection_args):
    """
    测试从 Nacos 成功获取 JSON 和 YAML 配置。
    
    这个测试会：
    1. 使用 `with_nacos` 初始化管理器。
    2. 注册 JSON 和 YAML 两个配置类。
    3. 获取配置并分别验证其内容是否正确。
    """
    print("\n--- 开始 Nacos 配置获取测试 (JSON & YAML) ---")

    # 1. 使用 Nacos 提供者创建管理器
    print("步骤 1: 使用 Nacos 提供者创建管理器...")
    manager = NexusConfigManager.with_nacos(**nacos_connection_args)
    print("  管理器创建成功。")

    # 2. 注册配置
    print(f"\n步骤 2: 注册 NacosJsonTestConfig 和 NacosYamlTestConfig...")
    manager.register(NacosJsonTestConfig)
    manager.register(NacosYamlTestConfig)
    print("  配置注册完成。")

    # 3. 获取并验证
    print("\n步骤 3: 获取并验证配置...")
    try:
        # 验证 JSON 配置
        json_config = manager.get_config(NacosJsonTestConfig)
        print(f"  成功获取 JSON 配置: app_name='{json_config.app_name}', version='{json_config.version}'")
        assert json_config.app_name == EXPECTED_JSON_CONFIG["app_name"]
        assert json_config.version == EXPECTED_JSON_CONFIG["version"]
        assert json_config.enabled == EXPECTED_JSON_CONFIG["enabled"]
        print("  JSON 配置内容验证成功。")
        
        # 验证 YAML 配置
        yaml_config = manager.get_config(NacosYamlTestConfig)
        print(f"  成功获取 YAML 配置: server.host='{yaml_config.server.host}', retries={yaml_config.retries}")
        assert yaml_config.server.host == EXPECTED_YAML_CONFIG["server"]["host"]
        assert yaml_config.server.port == EXPECTED_YAML_CONFIG["server"]["port"]
        assert yaml_config.retries == EXPECTED_YAML_CONFIG["retries"]
        print("  YAML 配置内容验证成功。")

    except Exception as e:
        pytest.fail(
            f"获取 Nacos 配置失败: {e}\n\n"
            f"请确保在 Nacos 服务器上【同时存在】以下两个配置:\n"
            f"1. JSON 配置:\n"
            f"  - Data ID: {JSON_TEST_DATA_ID}\n"
            f"  - Group: {NACOS_GROUP}\n"
            f"  - Namespace: {NACOS_NAMESPACE or 'public'}\n"
            f"  - Content (JSON): {json.dumps(EXPECTED_JSON_CONFIG)}\n\n"
            f"2. YAML 配置:\n"
            f"  - Data ID: {YAML_TEST_DATA_ID}\n"
            f"  - Group: {NACOS_GROUP}\n"
            f"  - Namespace: {NACOS_NAMESPACE or 'public'}\n"
            f"  - Content (YAML):\n{json.dumps(EXPECTED_YAML_CONFIG, indent=2)}\n"
        )
    finally:
        # 4. 清理
        print("\n步骤 4: 关闭管理器...")
        manager.close()
        print("  管理器已关闭。")
        print("--- Nacos 配置获取测试结束 ---") 