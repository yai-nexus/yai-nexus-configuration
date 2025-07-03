#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration 使用示例

演示如何使用这个高质量的配置管理库。
"""

import json
import time
from typing import List

# 导入我们的库
from src.yai_nexus_configuration import (
    NexusConfigManager, 
    NexusConfig, 
    nacos_config,
    ConfigNotRegisteredError
)


# 示例 1: 数据库配置
@nacos_config(data_id="database.json", group="PROD")
class DatabaseConfig(NexusConfig):
    """数据库配置"""
    host: str
    port: int = 5432
    username: str
    password: str
    max_connections: int = 100
    ssl_enabled: bool = True


# 示例 2: Redis 配置
@nacos_config(data_id="redis.json", group="PROD") 
class RedisConfig(NexusConfig):
    """Redis 配置"""
    host: str
    port: int = 6379
    password: str = ""
    database: int = 0
    timeout: float = 5.0


# 示例 3: 应用配置
@nacos_config(data_id="app.json")  # 使用默认组 DEFAULT_GROUP
class AppConfig(NexusConfig):
    """应用配置"""
    app_name: str
    debug: bool = False
    log_level: str = "INFO"
    allowed_hosts: List[str] = []
    features: dict = {}


def demonstrate_basic_usage():
    """演示基本用法"""
    print("🚀 YAI Nexus Configuration 基本用法演示")
    print("=" * 50)
    
    # 创建管理器 - 使用工厂方法
    print("1. 创建配置管理器...")
    try:
        manager = NexusConfigManager.with_nacos(
            server_addresses="localhost:8848",
            namespace="",  # 公共命名空间
        )
        print("✅ 管理器创建成功")
    except Exception as e:
        print(f"❌ 连接 Nacos 失败: {e}")
        print("请确保 Nacos 服务器正在运行并且可访问")
        return
    
    # 注册配置
    print("\n2. 注册配置类...")
    configs_to_register = [DatabaseConfig, RedisConfig, AppConfig]
    
    for config_class in configs_to_register:
        try:
            manager.register(config_class)
            print(f"✅ 注册成功: {config_class.__name__}")
        except Exception as e:
            print(f"❌ 注册失败 {config_class.__name__}: {e}")
    
    # 获取和使用配置
    print("\n3. 获取配置实例...")
    try:
        # 获取数据库配置
        db_config = manager.get_config(DatabaseConfig)
        print(f"📊 数据库配置: {db_config.host}:{db_config.port}")
        print(f"   最大连接数: {db_config.max_connections}")
        
        # 获取 Redis 配置  
        redis_config = manager.get_config(RedisConfig)
        print(f"🔴 Redis 配置: {redis_config.host}:{redis_config.port}")
        
        # 获取应用配置
        app_config = manager.get_config(AppConfig)
        print(f"🏠 应用配置: {app_config.app_name}")
        print(f"   调试模式: {app_config.debug}")
        
    except ConfigNotRegisteredError as e:
        print(f"❌ 配置未注册: {e}")
    except Exception as e:
        print(f"❌ 获取配置失败: {e}")
    
    # 显示管理器状态
    print("\n4. 管理器状态信息...")
    manager_info = manager.get_manager_info()
    print(f"📈 状态信息:")
    print(f"   提供者: {manager_info['provider']['name']}")
    print(f"   连接状态: {'✅ 已连接' if manager_info['provider']['connected'] else '❌ 未连接'}")
    print(f"   已注册配置: {manager_info['registered_configs']} 个")
    print(f"   配置列表: {', '.join(manager_info['config_names'])}")
    
    # 清理资源
    print("\n5. 清理资源...")
    manager.close()
    print("✅ 管理器已关闭")


def demonstrate_configuration_update():
    """演示配置实时更新功能"""
    print("\n🔄 配置实时更新演示")
    print("=" * 50)
    
    try:
        # 创建管理器
        with NexusConfigManager.with_nacos("localhost:8848") as manager:
            # 注册一个配置
            manager.register(AppConfig)
            
            print("正在监听配置变更...")
            print("您可以在 Nacos 控制台修改 app.json 配置来测试实时更新功能")
            print("程序将在 30 秒后自动结束")
            
            # 监听 30 秒
            for i in range(6):
                time.sleep(5)
                try:
                    app_config = manager.get_config(AppConfig)
                    print(f"[{i*5+5}s] 当前配置: {app_config.get_config_summary()}")
                except Exception as e:
                    print(f"[{i*5+5}s] 获取配置失败: {e}")
                    
    except Exception as e:
        print(f"❌ 演示失败: {e}")


def create_sample_configs():
    """创建示例配置数据（需要手动在 Nacos 中创建）"""
    print("\n📝 示例配置数据")
    print("=" * 50)
    print("请在 Nacos 控制台中创建以下配置：")
    
    configs = {
        "PROD/database.json": {
            "host": "localhost",
            "port": 5432,
            "username": "myuser",
            "password": "mypassword",
            "max_connections": 50,
            "ssl_enabled": True
        },
        "PROD/redis.json": {
            "host": "localhost", 
            "port": 6379,
            "password": "",
            "database": 0,
            "timeout": 3.0
        },
        "DEFAULT_GROUP/app.json": {
            "app_name": "YAI Nexus Demo",
            "debug": False,
            "log_level": "INFO",
            "allowed_hosts": ["localhost", "127.0.0.1"],
            "features": {
                "feature_a": True,
                "feature_b": False
            }
        }
    }
    
    for config_path, config_data in configs.items():
        print(f"\n配置路径: {config_path}")
        print(f"配置内容:")
        print(json.dumps(config_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("🎉 欢迎使用 YAI Nexus Configuration!")
    print("这是一个基于 Provider 模式的高质量配置管理库\n")
    
    # 显示示例配置
    create_sample_configs()
    
    # 基本用法演示
    demonstrate_basic_usage()
    
    # 配置更新演示（可选）
    choice = input("\n是否演示配置实时更新功能？(y/n): ")
    if choice.lower() in ['y', 'yes']:
        demonstrate_configuration_update()
    
    print("\n🎊 演示结束！感谢使用 YAI Nexus Configuration!") 