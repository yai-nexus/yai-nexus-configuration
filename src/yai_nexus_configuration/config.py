#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 配置模型模块

定义了所有配置类的基类 `NexusConfig`。
该模块基于 Pydantic，为用户提供一个结构清晰、支持数据验证的配置声明方式。
"""

from pydantic import BaseModel, ConfigDict
from typing import Dict, Any


class NexusConfig(BaseModel):
    """
    所有配置类的统一基类。
    
    用户定义的配置类应从此类继承。它基于 Pydantic，提供了强大的
    数据验证、类型转换和序列化功能，是定义强类型配置结构的基础。

    主要特性:
      - **自动数据验证**: 基于类型提示确保数据值的正确性和完整性。
      - **丰富的字段类型**: 支持包括嵌套模型、列表、枚举在内的多种复杂类型。
      - **默认值**: 可以为字段提供默认值。
      - **易于集成**: 可轻松与 JSON 或字典等数据格式互相转换。

    用法示例:
        >>> from yai_nexus_configuration import NexusConfig, nexus_config
        >>> 
        >>> # 使用 @nexus_config 将类标记为配置模型，并提供元数据
        >>> @nexus_config(data_id="database.json", group="production")
        ... class DatabaseConfig(NexusConfig):
        ...     host: str
        ...     port: int = 5432
        ...     user: str
        ...     password: str
        ... 
        >>> # 此配置类现在可以被 NexusConfigManager 注册和管理。
        >>> # manager = NexusConfigManager.with_file()
        >>> # manager.register(DatabaseConfig)
        >>> # db_config = manager.get_config(DatabaseConfig)
    """
    
    # Pydantic V2+ Style Configuration
    model_config = ConfigDict(
        # 在对字段重新赋值时进行数据验证
        validate_assignment=True,
        # 序列化枚举时使用枚举的值而不是其名称
        use_enum_values=True
    )
    
    def model_dump_json_schema(self) -> Dict[str, Any]:
        """
        获取此配置模型的 JSON Schema。
        
        Returns:
            一个表示配置结构和类型的 JSON Schema 字典。
        """
        return self.model_json_schema()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置的摘要信息，同时隐藏敏感数据。
        
        此方法会屏蔽名称中包含 'password', 'token', 'secret' 等
        关键词的字段值，适用于日志记录和调试场景。
        
        Returns:
            一个包含配置摘要的字典，敏感字段的值被替换为 '***hidden***'。
        """
        data = self.model_dump()
        
        # 定义需要隐藏的敏感字段关键词
        sensitive_fields = {'password', 'token', 'secret', 'key', 'api_key'}
        
        for field_name in list(data.keys()):
            if any(sensitive in field_name.lower() for sensitive in sensitive_fields):
                data[field_name] = "***hidden***"
                
        return data
