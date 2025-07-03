# 最佳实践：大型项目集成

在大型项目中使用 `YAI Nexus Configuration` 时，我们推荐采用**中心化配置模块**的模式来管理 `NexusConfigManager` 的生命周期和实例。

这种方式能有效避免资源浪费和实例状态不一致的问题，同时让业务代码保持整洁。

## 推荐方案：中央配置模块

创建一个专门的模块（例如 `my_project/config.py`）来管理 `NexusConfigManager`。

```python
# my_project/config.py

from yai_nexus_configuration import NexusConfigManager
from .models import DatabaseConfig, RedisConfig, AppConfig # 导入所有配置模型

# 1. 在模块级别创建并初始化管理器
#    在应用启动时执行一次即可
manager = NexusConfigManager.with_nacos(
    server_addresses="your_nacos_server",
    # ... 其他参数
)

# 2. 集中注册所有配置类
manager.register(DatabaseConfig, RedisConfig, AppConfig)

# 3. 提供预先加载好的配置实例
#    其他模块可以直接导入这些实例，而无需关心 manager
DB_CONFIG: DatabaseConfig = manager.get_config(DatabaseConfig)
REDIS_CONFIG: RedisConfig = manager.get_config(RedisConfig)
APP_CONFIG: AppConfig = manager.get_config(AppConfig)

# 4. 提供一个关闭函数，在应用退出时调用
def close_config_manager():
    manager.close()
```

### 使用方式

在项目的任何其他模块中，直接导入配置实例即可：

```python
# my_project/services/user_service.py

from my_project.config import DB_CONFIG

def get_user(user_id: int):
    # 直接使用，非常清晰
    db_host = DB_CONFIG.host
    # ...
```

## 与 Web 框架集成

如果您的项目基于 FastAPI 等现代框架，也可以利用其依赖注入系统来管理配置实例的生命周期。 