# YAI Nexus Configuration

🚀 **高质量的 Python 配置管理库** - 基于 Provider 模式，支持多种配置源

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)

## ✨ 主要特性

- 🎯 **简洁优雅的 API** - 采用工厂模式，一行代码创建管理器
- 🔒 **线程安全** - 所有操作都是线程安全的，适用于多线程环境
- 🔄 **自动配置更新** - 实时监听配置源变更，自动更新本地配置
- 🧩 **可扩展架构** - 基于 Provider 模式，轻松支持新的配置源
- ✅ **类型安全** - 完整的类型提示支持，基于 Pydantic 数据验证
- 📦 **零依赖冲突** - 精心设计的依赖管理，避免版本冲突

## 🎬 快速开始

### 安装

```bash
pip install yai-nexus-configuration
```

### 基本用法

```python
from yai_nexus_configuration import NexusManager, NexusConfig, nacos_config

# 1. 定义配置模型
@nacos_config(data_id="database.json", group="PROD")
class DatabaseConfig(NexusConfig):
    host: str
    port: int = 5432
    username: str
    password: str
    max_connections: int = 100

# 2. 创建管理器并注册配置
manager = NexusManager.with_nacos("localhost:8848")
manager.register(DatabaseConfig)

# 3. 获取配置实例
db_config = manager.get_config(DatabaseConfig)
print(f"Database: {db_config.host}:{db_config.port}")

# 4. 配置会自动更新，无需手动刷新！
```

## 🏗️ 架构设计

YAI Nexus Configuration 采用了经过深度思考的 **方案 E（工厂模式）** 架构：

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   用户代码      │────│  NexusManager    │────│  ConfigStore    │
│                 │    │  (工厂 + 管理)    │    │  (线程安全存储)  │
└─────────────────┘    └──────────┬───────┘    └─────────────────┘
                                  │
                                  ▼
                       ┌──────────────────┐
                       │ AbstractProvider │
                       │    (抽象层)       │
                       └─────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
            ┌──────────────┐        ┌──────────────┐
            │ NacosProvider│        │ 未来的Provider│
            │              │        │ (Apollo等)   │
            └──────────────┘        └──────────────┘
```

### 核心优势

- **高内聚，低耦合**: Provider 抽象层完全隔离了配置源实现
- **面向接口编程**: 核心逻辑只依赖抽象接口，便于测试和扩展
- **工厂模式**: 提供简洁的创建接口，隐藏复杂的初始化逻辑
- **单一职责**: 每个组件都有明确的职责边界

## 🔧 支持的配置源

| 配置源 | 状态 | 工厂方法 | 说明 |
|--------|------|----------|------|
| **Nacos** | ✅ 已支持 | `NexusManager.with_nacos()` | 阿里巴巴开源的配置中心 |
| **Apollo** | 🚧 规划中 | `NexusManager.with_apollo()` | 携程开源的配置中心 |
| **Etcd** | 🚧 规划中 | `NexusManager.with_etcd()` | 分布式键值存储 |
| **本地文件** | 🚧 规划中 | `NexusManager.with_file()` | 本地 JSON/YAML 文件 |

## 📖 详细文档

### 配置类定义

```python
from yai_nexus_configuration import NexusConfig, nacos_config
from typing import List

@nacos_config(data_id="app.json", group="DEFAULT_GROUP")
class AppConfig(NexusConfig):
    """应用配置"""
    app_name: str
    debug: bool = False
    log_level: str = "INFO"
    allowed_hosts: List[str] = []
    
    # 支持嵌套配置
    database: dict = {}
    redis: dict = {}
```

### 管理器使用

```python
# 创建管理器（支持多种参数）
manager = NexusManager.with_nacos(
    server_addresses="localhost:8848",
    namespace="production",
    username="admin",
    password="admin123"
)

# 批量注册配置
configs = [DatabaseConfig, RedisConfig, AppConfig]
for config_class in configs:
    manager.register(config_class)

# 获取配置（类型安全）
app_config: AppConfig = manager.get_config(AppConfig)

# 检查管理器状态
info = manager.get_manager_info()
print(f"已注册 {info['registered_configs']} 个配置")

# 优雅关闭
manager.close()
```

### 上下文管理器

```python
# 推荐使用 with 语句，自动管理资源
with NexusManager.with_nacos("localhost:8848") as manager:
    manager.register(AppConfig)
    
    app_config = manager.get_config(AppConfig)
    print(f"App: {app_config.app_name}")
    
# 管理器自动关闭，清理所有资源
```

### 配置实时更新

```python
# 配置更新是自动的！
manager.register(AppConfig)

# 在 Nacos 控制台修改配置后...
app_config = manager.get_config(AppConfig)  # 自动获取最新配置

# 也支持手动刷新
updated_config = manager.reload_config(AppConfig)
```

## 🧪 扩展新的配置源

YAI Nexus Configuration 的设计让添加新配置源变得非常简单：

```python
from yai_nexus_configuration.providers import AbstractProvider

class MyCustomProvider(AbstractProvider):
    def __init__(self, config_url: str):
        super().__init__("MyCustom")
        self.config_url = config_url
    
    def connect(self):
        # 实现连接逻辑
        pass
    
    def get_config(self, data_id: str, group: str) -> str:
        # 实现配置获取逻辑
        pass
    
    def watch_config(self, data_id: str, group: str, callback):
        # 实现配置监听逻辑
        pass
    
    # ... 其他必须实现的方法

# 在 NexusManager 中添加工厂方法
@classmethod
def with_my_custom(cls, config_url: str) -> "NexusManager":
    provider = MyCustomProvider(config_url)
    return cls(provider)
```

## 🔍 错误处理

```python
from yai_nexus_configuration import (
    ConfigNotRegisteredError,
    ConfigValidationError,
    ProviderConnectionError
)

try:
    manager = NexusManager.with_nacos("localhost:8848")
    manager.register(DatabaseConfig)
    db_config = manager.get_config(DatabaseConfig)
    
except ProviderConnectionError as e:
    print(f"无法连接到配置源: {e}")
    
except ConfigValidationError as e:
    print(f"配置数据验证失败: {e}")
    
except ConfigNotRegisteredError as e:
    print(f"配置未注册: {e}")
```

## 🧑‍💻 开发

### 环境准备

```bash
# 克隆项目
git clone https://github.com/yai-team/yai-nexus-configuration.git
cd yai-nexus-configuration

# 安装依赖
pip install -r requirements.txt

# 运行示例
python example.py
```

### 运行测试

```bash
# 单元测试
pytest tests/

# 覆盖率测试
pytest --cov=src/yai_nexus_configuration tests/
```

## 🎯 设计哲学

YAI Nexus Configuration 的设计遵循以下原则：

1. **简洁胜过复杂** - API 设计力求简洁直观
2. **显式胜过隐式** - 避免魔法方法，所有行为都是可预测的
3. **面向接口编程** - 通过抽象接口实现高度解耦
4. **失败快速暴露** - 配置错误在启动时就会被发现，而不是运行时
5. **类型安全第一** - 完整的类型提示，让 IDE 和工具更好地帮助开发

## 🤝 贡献

我们欢迎任何形式的贡献！

- 🐛 报告 Bug
- 💡 提出新功能建议  
- 📖 改进文档
- 🔧 提交代码改进

请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献指南。

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [Pydantic](https://pydantic-docs.helpmanual.io/) - 提供优秀的数据验证能力
- [nacos-sdk-python](https://github.com/nacos-group/nacos-sdk-python) - Nacos Python SDK
- 所有为这个项目贡献想法和代码的开发者们

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！