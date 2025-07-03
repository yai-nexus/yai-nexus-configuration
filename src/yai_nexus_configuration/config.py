#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAI Nexus Configuration - 配置基类模块

提供配置类的基础实现，基于 Pydantic 进行数据验证和序列化。
"""

from pydantic import BaseModel
from typing import Dict, Any


class NexusConfig(BaseModel):
    """
    配置类的基类
    
    继承自 pydantic.BaseModel，提供以下特性：
    - 自动数据验证
    - 类型提示支持
    - JSON 序列化/反序列化
    - 配置值的不可变性（可选）
    
    Example:
        >>> from yai_nexus_configuration import NexusConfig, nacos_config
        >>> 
        >>> @nacos_config(data_id="db.json")
        >>> class DatabaseConfig(NexusConfig):
        ...     host: str
        ...     port: int = 5432
        ...     username: str
        ...     password: str
        ...     
        >>> # 配置类现在可以被 NexusManager 注册和管理
    """
    
    class Config:
        # 允许字段值不可变，防止意外修改
        allow_mutation = True
        # 在赋值时验证数据
        validate_assignment = True
        # 使用枚举的值而不是名称进行序列化
        use_enum_values = True
        
    def model_dump_json_schema(self) -> Dict[str, Any]:
        """
        获取配置模型的 JSON Schema
        
        Returns:
            配置结构的 JSON Schema 定义
        """
        return self.model_json_schema()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要信息（不包含敏感数据）
        
        Returns:
            配置的摘要信息，密码等敏感字段会被隐藏
        """
        data = self.model_dump()
        
        # 隐藏可能的敏感字段
        sensitive_fields = {'password', 'token', 'secret', 'key', 'api_key'}
        
        for field_name in list(data.keys()):
            if any(sensitive in field_name.lower() for sensitive in sensitive_fields):
                data[field_name] = "***hidden***"
                
        return data
