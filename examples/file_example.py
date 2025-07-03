#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration File Provider 使用示例

本示例演示如何从预置的本地文件加载配置。
配置文件位于 `examples/resources` 和 `examples/resources_yaml` 目录下。
"""

import time
from typing import List
import sys
import os

# 将项目根目录添加到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入我们的库
from src.yai_nexus_configuration import (
    NexusConfigManager,
    NexusConfig,
    nexus_config,
    ConfigNotRegisteredError
)


# === 1. 定义配置类 ===
# 这些类映射到 `resources/` 目录下的配置文件。

@nexus_config(data_id="database.json", group="PROD")
class DatabaseConfig(NexusConfig):
    """数据库配置 (对应 an `examples/resources/PROD/database.json`)"""
    host: str
    port: int
    username: str
    password: str

@nexus_config(data_id="redis.json", group="PROD")
class RedisConfig(NexusConfig):
    """Redis 配置 (对应 `examples/resources/PROD/redis.json`)"""
    host: str
    port: int
    password: str

@nexus_config(data_id="app.json")  # 使用默认组 DEFAULT_GROUP
class AppConfig(NexusConfig):
    """应用配置 (对应 `examples/resources/DEFAULT_GROUP/app.json`)"""
    app_name: str
    debug: bool
    log_level: str

# 用于 YAML 演示的配置类
@nexus_config(data_id="app.yaml", group="DEFAULT_GROUP")
class YamlAppConfig(NexusConfig):
    """YAML 应用配置 (对应 `examples/resources/DEFAULT_GROUP/app.yaml`)"""
    app_name: str
    debug: bool


def demonstrate_basic_usage():
    """演示文件配置的基本用法"""
    print("\n🚀 1. JSON 配置基本用法演示")
    print("=" * 50)

    # 使用 `with` 语句确保资源被正确管理
    try:
        with NexusConfigManager.with_file(
            base_path="examples/resources",
            default_format="json"
        ) as manager:
            
            print("✅ 文件管理器创建成功 (base_path: 'examples/resources')")

            # 注册所有配置
            manager.register(DatabaseConfig)
            manager.register(RedisConfig)
            manager.register(AppConfig)
            print("✅ 配置类 `DatabaseConfig`, `RedisConfig`, `AppConfig` 注册成功")

            # 获取并使用配置
            db_config = manager.get_config(DatabaseConfig)
            print(f"   - 数据库配置: {db_config.host}:{db_config.port} (用户: {db_config.username})")

            redis_config = manager.get_config(RedisConfig)
            print(f"   - Redis 配置: {redis_config.host}:{redis_config.port}")

            app_config = manager.get_config(AppConfig)
            print(f"   - 应用配置: {app_config.app_name} (Debug: {app_config.debug})")

    except ConfigNotRegisteredError as e:
        print(f"❌ 配置未注册: {e}")
    except FileNotFoundError:
        print("❌ 错误: 找不到配置目录 `examples/resources`。请确保示例资源文件已存在。")
    except Exception as e:
        print(f"❌ 演示失败: {e}")


def demonstrate_yaml_support():
    """演示 YAML 格式支持"""
    print("\n📄 2. YAML 格式支持演示")
    print("=" * 50)

    try:
        # 动态检查 PyYAML 是否安装
        import yaml
    except ImportError:
        print("⚠️  PyYAML 未安装，跳过 YAML 演示。请运行 `pip install PyYAML`。")
        return

    try:
        # 创建一个专用于 YAML 的管理器
        with NexusConfigManager.with_file(
            base_path="examples/resources",
            default_format="yaml"  # 指定默认格式为 YAML
        ) as manager:
            
            print("✅ YAML 文件管理器创建成功 (base_path: 'examples/resources')")
            manager.register(YamlAppConfig)
            print("✅ 配置类 `YamlAppConfig` 注册成功")

            # 获取配置
            yaml_config = manager.get_config(YamlAppConfig)
            print(f"   - YAML 应用名: {yaml_config.app_name} (Debug: {yaml_config.debug})")

    except FileNotFoundError:
        print("❌ 错误: 找不到配置目录 `examples/resources`。请确保示例资源文件已存在。")
    except Exception as e:
        print(f"❌ YAML 演示失败: {e}")


def demonstrate_file_watching():
    """演示文件配置实时更新功能"""
    print("\n🔄 3. 文件配置实时更新演示")
    print("=" * 50)
    
    print("本功能会监控 `examples/resources/DEFAULT_GROUP/app.json` 文件的变更。")
    print("请在 15 秒内手动修改该文件中的 `app_name` 字段并保存，观察下面的输出。")

    try:
        # watch_interval 设置为 1.0 秒，以便快速响应变更
        with NexusConfigManager.with_file(base_path="examples/resources", watch_interval=1.0) as manager:
            manager.register(AppConfig)
            
            print("\n--- 开始监听 (持续 15 秒) ---")
            for i in range(15):
                app_config = manager.get_config(AppConfig)
                # 使用 \r 实现单行刷新
                print(f"\r[{i+1:2d}/15s] 当前应用名称: {app_config.app_name}          ", end="")
                time.sleep(1)
            print("\n--- 监听结束 ---\n")
            
    except Exception as e:
        print(f"❌ 实时更新演示失败: {e}")


if __name__ == "__main__":
    print("🎉 欢迎使用 YAI Nexus Configuration 文件配置示例！ 🎉")
    
    # 依次执行所有演示
    demonstrate_basic_usage()
    demonstrate_yaml_support()
    demonstrate_file_watching()
    
    print("\n�� 文件配置示例全部结束！感谢使用！") 