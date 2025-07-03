# 快速开始

本指南将帮助您在 5 分钟内上手 YAI Nexus Configuration。我们将使用最基础的**本地文件**作为配置源，这不需要任何外部服务依赖。

## 1. 安装

首先，请确保您已经安装了 Python (3.8+)。然后通过 pip 安装我们的库：

```bash
pip install yai-nexus-configuration
```
!!! success "提示"
    文件和 YAML 支持是本库的核心功能，无需安装任何额外依赖。

## 2. 创建您的第一个配置

在您的项目根目录创建一个 `configs` 文件夹，并像这样组织您的配置：

```
configs/
└── DEFAULT_GROUP/
    └── app.json
```

然后，将以下内容写入 `configs/DEFAULT_GROUP/app.json` 文件:

```json
{
  "app_name": "My Awesome App",
  "debug": true,
  "log_level": "DEBUG"
}
```

## 3. 编写 Python 代码

现在，创建一个 Python 文件（例如 `main.py`），并写入以下代码：

```python
from yai_nexus_configuration import NexusConfigManager, NexusConfig, nexus_config

# 1. 定义一个配置模型，它的字段会自动映射到 app.json 的键
#    @nexus_config 装饰器将这个类与配置文件关联起来。
@nexus_config(data_id="app.json") # group 默认为 "DEFAULT_GROUP"
class AppConfig(NexusConfig):
    app_name: str
    debug: bool
    log_level: str

# 2. 使用 with 语句创建管理器，它会自动管理资源
#    我们告诉它在 "configs" 目录下寻找配置文件。
with NexusConfigManager.with_file(base_path="configs") as manager:
    
    # 3. 注册我们刚刚定义的配置类
    manager.register(AppConfig)
    
    # 4. 获取类型安全的配置实例
    #    IDE 会知道 app_config 是 AppConfig 类的实例，并提供代码补全！
    app_config = manager.get_config(AppConfig)
    
    print(f"应用名称: {app_config.app_name}")
    print(f"调试模式: {app_config.debug}")

    # 5. 试试看！在程序运行时，手动修改 app.json 文件并保存。
    #    再次获取配置，就会看到更新！
    import time
    time.sleep(5) # 等待几秒钟，给您时间修改文件
    
    updated_config = manager.get_config(AppConfig)
    print(f"更新后的应用名称: {updated_config.app_name}")
```

## 4. 运行！

打开终端，运行您的脚本：

```bash
python main.py
```

您应该能看到如下输出：

```
应用名称: My Awesome App
调试模式: True
更新后的应用名称: My Awesome App
```

现在，试着在程序运行时快速修改 `app.json` 中的 `app_name` 值，您将看到第二次打印出的应用名称发生了变化！

---

恭喜！您已经成功地使用 YAI Nexus Configuration 加载并实时更新了配置。接下来，您可以继续探索更高级的功能，例如：

-   [使用文件配置 (File Provider)](file_provider.md)
-   [连接到 Nacos (Nacos Provider)](nacos_provider.md)
-   [在大型项目中的最佳实践](best_practices.md) 