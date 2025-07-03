#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration File Provider 使用示例

演示如何使用本地文件作为配置源。
"""

import json
import time
from typing import List

# 导入我们的库
from src.yai_nexus_configuration import (
    NexusConfigManager, 
    NexusConfig, 
    nexus_config,
    ConfigNotRegisteredError
)


# 示例 1: 数据库配置
@nexus_config(data_id="database.json", group="PROD")
class DatabaseConfig(NexusConfig):
    """数据库配置"""
    host: str
    port: int = 5432
    username: str
    password: str
    max_connections: int = 100
    ssl_enabled: bool = True


# 示例 2: Redis 配置
@nexus_config(data_id="redis.json", group="PROD") 
class RedisConfig(NexusConfig):
    """Redis 配置"""
    host: str
    port: int = 6379
    password: str = ""
    database: int = 0
    timeout: float = 5.0


# 示例 3: 应用配置
@nexus_config(data_id="app.json")  # 使用默认组 DEFAULT_GROUP
class AppConfig(NexusConfig):
    """应用配置"""
    app_name: str
    debug: bool = False
    log_level: str = "INFO"
    allowed_hosts: List[str] = []
    features: dict = {}


def create_sample_files():
    """创建示例配置文件"""
    print("📁 创建示例配置文件...")
    
    # 使用 file provider 创建示例文件
    from src.yai_nexus_configuration.providers.file import FileProvider
    
    provider = FileProvider(base_path="configs", auto_create_dirs=True)
    provider.connect()
    
    # 创建配置数据
    configs = {
        ("database.json", "PROD"): {
            "host": "localhost",
            "port": 5432,
            "username": "myuser",
            "password": "mypassword",
            "max_connections": 50,
            "ssl_enabled": True
        },
        ("redis.json", "PROD"): {
            "host": "localhost", 
            "port": 6379,
            "password": "",
            "database": 0,
            "timeout": 3.0
        },
        ("app.json", "DEFAULT_GROUP"): {
            "app_name": "YAI Nexus File Demo",
            "debug": False,
            "log_level": "INFO",
            "allowed_hosts": ["localhost", "127.0.0.1"],
            "features": {
                "feature_a": True,
                "feature_b": False
            }
        }
    }
    
    for (data_id, group), config_data in configs.items():
        file_path = provider.create_sample_config(data_id, group, config_data)
        print(f"✅ 已创建: {file_path}")
    
    provider.disconnect()
    print("📁 示例文件创建完成！")


def demonstrate_file_usage():
    """演示文件配置的基本用法"""
    print("\n🚀 YAI Nexus Configuration 文件配置演示")
    print("=" * 50)
    
    # 创建管理器 - 使用文件配置源
    print("1. 创建文件配置管理器...")
    try:
        manager = NexusConfigManager.with_file(
            base_path="configs",
            default_format="json",
            watch_interval=1.0,
            auto_create_dirs=True
        )
        print("✅ 文件管理器创建成功")
    except Exception as e:
        print(f"❌ 创建管理器失败: {e}")
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


def demonstrate_file_watching():
    """演示文件配置实时更新功能"""
    print("\n🔄 文件配置实时更新演示")
    print("=" * 50)
    
    try:
        # 创建管理器
        with NexusConfigManager.with_file("configs") as manager:
            # 注册一个配置
            manager.register(AppConfig)
            
            print("正在监听配置文件变更...")
            print("您可以编辑 configs/DEFAULT_GROUP/app.json 文件来测试实时更新功能")
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


def demonstrate_yaml_support():
    """演示 YAML 格式支持"""
    print("\n📄 YAML 格式支持演示")
    print("=" * 50)
    
    try:
        import yaml
        print("✅ PyYAML 已安装，支持 YAML 格式")
        
        # 创建 YAML 格式的管理器
        manager = NexusConfigManager.with_file(
            base_path="configs_yaml",
            default_format="yaml",
            auto_create_dirs=True
        )
        
        # 创建 YAML 示例配置
        from src.yai_nexus_configuration.providers.file import FileProvider
        provider = FileProvider(base_path="configs_yaml", default_format="yaml", auto_create_dirs=True)
        provider.connect()
        
        sample_config = {
            "app_name": "YAI Nexus YAML Demo",
            "debug": True,
            "log_level": "DEBUG",
            "allowed_hosts": ["localhost"],
            "features": {
                "yaml_support": True,
                "json_support": True
            }
        }
        
        yaml_file = provider.create_sample_config("app.yaml", "DEFAULT_GROUP", sample_config)
        print(f"✅ 已创建 YAML 配置文件: {yaml_file}")
        
        provider.disconnect()
        manager.close()
        
    except ImportError:
        print("❌ PyYAML 未安装，跳过 YAML 演示")
        print("   安装命令: pip install PyYAML")


if __name__ == "__main__":
    print("🎉 欢迎使用 YAI Nexus Configuration 文件配置！")
    print("这是一个支持本地文件的配置管理库\n")
    
    # 创建示例文件
    create_sample_files()
    
    # 基本用法演示
    demonstrate_file_usage()
    
    # YAML 支持演示
    demonstrate_yaml_support()
    
    # 配置更新演示（可选）
    choice = input("\n是否演示配置文件实时更新功能？(y/n): ")
    if choice.lower() in ['y', 'yes']:
        demonstrate_file_watching()
    
    print("\n🎊 文件配置演示结束！感谢使用 YAI Nexus Configuration!") 