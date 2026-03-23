#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置中心服务
只返回敏感配置（如密钥），其余配置在yaml文件中
"""

import os
from pathlib import Path

from dotenv import load_dotenv

class ConfigService:
    """应用配置中心服务"""

    def __init__(self):
        env_file = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(env_file)
        self.configs = self._load_configs()

    def _load_configs(self):
        configs = {
            "jwt_secret": os.getenv("JWT_SECRET"),
            "mock_api_secret": os.getenv("MOCK_API_SECRET"),
            "ali_api_key": os.getenv("ALI_API_KEY"),
            "platform.metadata.api_key": os.getenv("PLATFORM_METADATA_API_KEY"),
            "platform.schedule.api_key": os.getenv("PLATFORM_SCHEDULE_API_KEY"),
            "platform.integration.api_key": os.getenv("PLATFORM_INTEGRATION_API_KEY"),
            "platform.lineage.api_key": os.getenv("PLATFORM_LINEAGE_API_KEY"),
        }

        required_keys = ("jwt_secret", "mock_api_secret", "ali_api_key")
        missing_keys = [key for key in required_keys if not configs.get(key)]
        if missing_keys:
            missing_labels = ", ".join(missing_keys)
            raise ValueError(f"Missing required config keys: {missing_labels}")

        return {k: v for k, v in configs.items() if v is not None}

    def get_config(self, key):
        """获取敏感配置"""
        if key in self.configs:
            return {"key": key, "value": self.configs[key]}
        return {"error": f"Config key '{key}' not found"}

    def get_all_configs(self):
        """获取所有敏感配置"""
        return {"configs": self.configs}

    def set_config(self, key, value):
        """设置敏感配置"""
        self.configs[key] = value
        return {"status": "success", "key": key}

    def delete_config(self, key):
        """删除敏感配置"""
        if key in self.configs:
            del self.configs[key]
            return {"status": "success", "key": key}
        return {"error": f"Config key '{key}' not found"}
