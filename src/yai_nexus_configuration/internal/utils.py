import os
from string import Template
from typing import Any


def recursive_replace_env_vars(config_part: Any) -> Any:
    """
    递归地遍历配置结构（字典、列表），并使用 string.Template
    安全地替换所有字符串中格式为 `${VAR_NAME}` 或 `$VAR_NAME` 的环境变量。

    这种方法比手动解析正则表达式更健壮、更安全。

    Args:
        config_part: 配置数据的一部分，可以是字典、列表、字符串或任何其他类型。

    Returns:
        处理过的配置部分，其中环境变量已被其值替换。
        如果环境变量未找到，占位符将保持原样。
    """
    if isinstance(config_part, dict):
        return {k: recursive_replace_env_vars(v) for k, v in config_part.items()}

    if isinstance(config_part, list):
        return [recursive_replace_env_vars(i) for i in config_part]

    if isinstance(config_part, str):
        # 使用 string.Template 的 safe_substitute 方法。
        # 它专门用于处理环境变量替换，如果变量在 os.environ 中不存在，
        # 它会安全地将占位符（如 ${MY_VAR}）保留在原地，而不会引发错误。
        # 同时，它也正确支持使用 $$ 来转义成一个普通的 $ 符号。
        return Template(config_part).safe_substitute(os.environ)

    # 对于非字符串、字典、列表的任何其他数据类型（如 int, bool, None），原样返回。
    return config_part 