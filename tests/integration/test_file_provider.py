#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 端到端集成测试

测试 NexusConfigManager + FileProvider 的完整工作流程，
包括配置注册、获取、文件变更和自动更新，不使用任何 mock。
"""

import pytest
import time
import json
import yaml
import shutil
from pathlib import Path

from yai_nexus_configuration import (
    NexusConfigManager,
    NexusConfig,
    nexus_config,
    ConfigNotRegisteredError
)


# 测试用的配置类
@nexus_config(data_id="database.json", group="prod")
class DatabaseConfig(NexusConfig):
    host: str
    port: int
    username: str
    password: str


@nexus_config(data_id="redis.yaml", group="cache")
class RedisConfig(NexusConfig):
    host: str
    port: int = 6379
    db: int = 0


@pytest.fixture
def config_workspace(tmp_path: Path) -> Path:
    """
    创建一个临时的配置工作区。
    现在它将在项目根目录下创建 .test_workspace/，并在测试后清理。
    """
    print("\n--- [Fixture Setup] 开始创建项目内临时配置工作区 ---")
    
    # 获取项目根目录，并创建 .test_workspace 目录
    project_root = Path(__file__).parent.parent
    workspace = project_root / ".test_workspace"
    
    # 如果目录已存在，先清理
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    
    print(f"  工作区路径: {workspace}")
    
    # 创建配置文件
    prod_dir = workspace / "prod"
    cache_dir = workspace / "cache"
    prod_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)
    print(f"  创建目录: {prod_dir}")
    print(f"  创建目录: {cache_dir}")
    
    # 数据库配置 (JSON)
    db_config = {
        "host": "db.example.com",
        "port": 5432,
        "username": "admin",
        "password": "secret123"
    }
    db_file = prod_dir / "database.json"
    db_file.write_text(json.dumps(db_config, indent=2))
    print(f"  创建文件: {db_file}")
    
    # Redis 配置 (YAML)
    redis_config = {
        "host": "redis.example.com",
        "port": 6379,
        "db": 0
    }
    redis_file = cache_dir / "redis.yaml"
    redis_file.write_text(yaml.dump(redis_config))
    print(f"  创建文件: {redis_file}")
    
    print("--- [Fixture Setup] 工作区创建完成 ---")
    
    yield workspace
    
    # --- Fixture Teardown ---
    print("\n--- [Fixture Teardown] 开始处理临时配置工作区 ---")
    # 根据用户要求，不再删除工作区，以便于调试和检查
    # if workspace.exists():
    #     shutil.rmtree(workspace)
    #     print(f"  已删除工作区: {workspace}")
    print(f"  工作区已保留: {workspace}")
    print("--- [Fixture Teardown] 处理完成 ---")


def test_complete_configuration_workflow(config_workspace: Path):
    """测试完整的配置管理工作流程"""
    print("\n--- 开始完整的配置工作流测试 ---")
    
    # 1. 创建管理器
    print("步骤 1: 使用文件提供者创建管理器...")
    manager = NexusConfigManager.with_file(
        base_path=config_workspace,
        watch_interval=0.1  # 快速监听，加速测试
    )
    print("管理器创建成功。")
    
    # 2. 注册配置
    print("\n步骤 2: 注册 DatabaseConfig 和 RedisConfig...")
    manager.register(DatabaseConfig)
    manager.register(RedisConfig)
    print("配置注册完成。")
    
    # 3. 获取配置并验证初始值
    print("\n步骤 3: 获取并验证初始配置...")
    db_config = manager.get_config(DatabaseConfig)
    print(f"  获取到 DatabaseConfig: host={db_config.host}, port={db_config.port}")
    assert db_config.host == "db.example.com"
    assert db_config.port == 5432
    assert db_config.username == "admin"
    assert db_config.password == "secret123"
    
    redis_config = manager.get_config(RedisConfig)
    print(f"  获取到 RedisConfig: host={redis_config.host}, db={redis_config.db}")
    assert redis_config.host == "redis.example.com"
    assert redis_config.port == 6379
    assert redis_config.db == 0
    print("初始配置验证成功。")
    
    # 4. 修改文件内容，测试自动更新
    print("\n步骤 4: 修改 database.json 文件内容...")
    new_db_config = {
        "host": "new-db.example.com",
        "port": 3306,
        "username": "root",
        "password": "newpassword"
    }
    
    db_file = config_workspace / "prod" / "database.json"
    db_file.write_text(json.dumps(new_db_config, indent=2))
    print("文件已修改，等待监听器响应...")
    
    # 等待文件监听器检测到变更
    time.sleep(0.3)
    
    # 5. 验证配置已自动更新
    print("\n步骤 5: 验证配置已自动更新...")
    updated_db_config = manager.get_config(DatabaseConfig)
    print(f"  获取到更新后的 DatabaseConfig: host={updated_db_config.host}, port={updated_db_config.port}")
    assert updated_db_config.host == "new-db.example.com"
    assert updated_db_config.port == 3306
    assert updated_db_config.username == "root"
    assert updated_db_config.password == "newpassword"
    print("数据库配置更新验证成功。")
    
    # Redis 配置应该保持不变
    redis_config_after = manager.get_config(RedisConfig)
    assert redis_config_after.host == "redis.example.com"
    print("Redis 配置保持不变验证成功。")
    
    # 6. 测试注销配置
    print("\n步骤 6: 注销 DatabaseConfig...")
    assert manager.unregister(DatabaseConfig) is True
    with pytest.raises(ConfigNotRegisteredError):
        manager.get_config(DatabaseConfig)
    print("DatabaseConfig 注销并访问失败，验证成功。")
    
    # Redis 配置应该仍然可用
    redis_config_final = manager.get_config(RedisConfig)
    assert redis_config_final.host == "redis.example.com"
    print("Redis 配置在注销其他配置后依然可用。")
    
    # 7. 清理
    print("\n步骤 7: 关闭管理器...")
    manager.close()
    print("管理器已关闭。")
    print("--- 测试结束 ---")


def test_manager_info_and_statistics(config_workspace: Path):
    """测试管理器的信息和统计功能"""
    
    manager = NexusConfigManager.with_file(base_path=config_workspace)
    
    # 初始状态
    info = manager.get_manager_info()
    assert info['registered_configs'] == 0
    assert info['config_names'] == []
    assert info['store_config_count'] == 0
    
    # 注册配置后
    manager.register(DatabaseConfig)
    manager.register(RedisConfig)
    
    info = manager.get_manager_info()
    assert info['registered_configs'] == 2
    assert set(info['config_names']) == {'DatabaseConfig', 'RedisConfig'}
    assert info['store_config_count'] == 2
    
    # 获取所有配置
    all_configs = manager.get_all_configs()
    assert len(all_configs) == 2
    assert 'DatabaseConfig' in all_configs
    assert 'RedisConfig' in all_configs
    
    manager.close()


def test_reload_config_manually(config_workspace: Path):
    """测试手动重新加载配置"""
    
    manager = NexusConfigManager.with_file(base_path=config_workspace)
    manager.register(DatabaseConfig)
    
    # 获取初始配置
    original_config = manager.get_config(DatabaseConfig)
    assert original_config.host == "db.example.com"
    
    # 修改文件（但不依赖自动监听）
    new_config_data = {
        "host": "manually-updated.example.com",
        "port": 5432,
        "username": "admin",
        "password": "secret123"
    }
    
    db_file = config_workspace / "prod" / "database.json"
    db_file.write_text(json.dumps(new_config_data, indent=2))
    
    # 手动重新加载
    reloaded_config = manager.reload_config(DatabaseConfig)
    assert reloaded_config.host == "manually-updated.example.com"
    
    # 验证存储中的配置也已更新
    stored_config = manager.get_config(DatabaseConfig)
    assert stored_config.host == "manually-updated.example.com"
    
    manager.close()


@pytest.mark.slow
def test_multiple_file_changes(config_workspace: Path):
    """测试多次文件变更的场景"""
    
    manager = NexusConfigManager.with_file(
        base_path=config_workspace,
        watch_interval=0.05  # 非常快的监听间隔
    )
    manager.register(DatabaseConfig)
    
    db_file = config_workspace / "prod" / "database.json"
    
    # 进行多次快速的文件更新
    for i in range(3):
        updated_config = {
            "host": f"host-{i}.example.com",
            "port": 5432 + i,
            "username": "admin",
            "password": "secret123"
        }
        
        db_file.write_text(json.dumps(updated_config, indent=2))
        time.sleep(0.2)  # 给监听器时间处理更新
        
        # 验证配置已更新
        current_config = manager.get_config(DatabaseConfig)
        assert current_config.host == f"host-{i}.example.com"
        assert current_config.port == 5432 + i
    
    manager.close() 