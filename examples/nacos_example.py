#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration Nacos Provider 使用示例

本示例演示如何连接到 Nacos 服务器并获取配置。
在运行此示例之前，请确保已根据下面的说明设置了必要的环境变量，
并在您的 Nacos 实例中发布了对应的配置。

--- Nacos 配置要求 ---
请在您的 Nacos 服务器上创建以下两个配置：

1. JSON 配置:
   - Data ID: yai-nexus-configuration-json-test-1.json
   - Group: yai-nexus-configuration
   - Namespace: (您正在使用的命名空间，默认为 public)
   - Content (JSON):
     {
       "app_name": "test_app",
       "version": "1.0.0",
       "enabled": true
     }

2. YAML 配置:
   - Data ID: yai-nexus-configuration-yaml-test-1.yaml
   - Group: yai-nexus-configuration
   - Namespace: (您正在使用的命名空间，默认为 public)
   - Content (YAML):
     server:
       host: "yaml-server.example.com"
       port: 8080
     retries:
       - 100
       - 200
       - 500
"""

import os
import sys
import time

# 将项目根目录添加到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.yai_nexus_configuration import (
    NexusConfigManager,
    NexusConfig,
    nexus_config,
)

# --- 1. 从环境变量读取 Nacos 连接信息 ---
# 这是运行此示例所必需的。
NACOS_SERVER_ADDR = os.environ.get("NACOS_SERVER_ADDR")

# 这些是可选的，但如果您的 Nacos 设置需要，请配置它们。
NACOS_GROUP = os.environ.get("NACOS_GROUP", "yai-nexus-configuration")
NACOS_NAMESPACE = os.environ.get("NACOS_NAMESPACE", "")
NACOS_USERNAME = os.environ.get("NACOS_USERNAME")
NACOS_PASSWORD = os.environ.get("NACOS_PASSWORD")

# --- 2. 定义与 Nacos 配置匹配的类 ---
JSON_DATA_ID = "yai-nexus-configuration-json-test-1.json"
YAML_DATA_ID = "yai-nexus-configuration-yaml-test-1.yaml"

@nexus_config(data_id=JSON_DATA_ID, group=NACOS_GROUP)
class NacosJsonConfig(NexusConfig):
    """映射到 JSON 配置的类"""
    app_name: str
    version: str
    enabled: bool

class ServerDetails(NexusConfig):
    """嵌套配置的子类"""
    host: str
    port: int

@nexus_config(data_id=YAML_DATA_ID, group=NACOS_GROUP)
class NacosYamlConfig(NexusConfig):
    """映射到 YAML 配置的类"""
    server: ServerDetails
    retries: list[int]


def main():
    """主执行函数"""
    print("🎉 欢迎使用 YAI Nexus Configuration Nacos 配置示例！ 🎉")

    # --- 检查先决条件 ---
    if not NACOS_SERVER_ADDR:
        print("\n❌ 错误: 缺少环境变量 `NACOS_SERVER_ADDR`。")
        print("   请在运行此脚本前设置该变量，例如:")
        print("   export NACOS_SERVER_ADDR=127.0.0.1:8848")
        sys.exit(1)

    print("\n--- Nacos 连接参数 ---")
    print(f"  服务器地址: {NACOS_SERVER_ADDR}")
    print(f"  命名空间: {NACOS_NAMESPACE or 'public'}")
    print(f"  分组: {NACOS_GROUP}")
    print(f"  用户名: {NACOS_USERNAME or '未设置'}")
    print("-------------------------\n")

    # --- 3. 初始化管理器并获取配置 ---
    try:
        connection_args = {
            "server_addresses": NACOS_SERVER_ADDR,
            "namespace": NACOS_NAMESPACE,
            "username": NACOS_USERNAME,
            "password": NACOS_PASSWORD
        }
        # 清理掉值为 None 的参数
        valid_args = {k: v for k, v in connection_args.items() if v is not None}

        with NexusConfigManager.with_nacos(**valid_args) as manager:
            print("✅ Nacos 管理器创建成功，已连接至服务器。")
            
            # 注册配置类
            manager.register(NacosJsonConfig)
            manager.register(NacosYamlConfig)
            print("✅ 配置类 `NacosJsonConfig` 和 `NacosYamlConfig` 注册成功。")
            
            # 获取并显示配置
            print("\n--- 获取配置 ---")
            json_config = manager.get_config(NacosJsonConfig)
            print(f"  - [JSON] app_name: {json_config.app_name}, version: {json_config.version}")
            
            yaml_config = manager.get_config(NacosYamlConfig)
            print(f"  - [YAML] server.host: {yaml_config.server.host}, retries: {yaml_config.retries}")

            # --- 4. 演示配置动态更新 ---
            print("\n--- 动态更新演示 (持续 15 秒) ---")
            print("现在您可以尝试在 Nacos 控制台修改上述任一配置的值。")
            print("脚本将每秒检查一次更新。")
            
            for i in range(15):
                json_ver = manager.get_config(NacosJsonConfig).version
                yaml_host = manager.get_config(NacosYamlConfig).server.host
                print(f"\r[{i+1:2d}/15s] 当前值: JSON version='{json_ver}', YAML host='{yaml_host}'          ", end="")
                time.sleep(1)
            print("\n--- 监听结束 ---\n")

    except Exception as e:
        print(f"\n❌ 发生严重错误: {e}")
        print("\n--- 故障排查建议 ---")
        print("1. 检查 Nacos 服务器是否正在运行并且网络可达。")
        print(f"2. 确认您的连接参数（服务器地址、命名空间、分组、用户名/密码）是否正确。")
        print(f"3. 确保在 Nacos 中已创建了本示例所需的两个配置（Data ID: {JSON_DATA_ID}, {YAML_DATA_ID}）。")

    print("🎊 Nacos 配置示例结束！")

if __name__ == "__main__":
    main() 