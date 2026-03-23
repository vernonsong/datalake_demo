#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock元数据服务
"""

import json

class MockMetadataService:
    """Mock元数据服务"""
    
    def __init__(self):
        self.databases = {
            "source_db": {
                "tables": ["user_info", "product_info", "order_info"],
                "type": "mysql"
            },
            "target_db": {
                "tables": ["dw_user", "dw_product", "dw_order"],
                "type": "hive"
            }
        }
    
    def get_databases(self, db_type=None):
        """获取数据库列表"""
        if db_type:
            return {
                "databases": [
                    db for db, info in self.databases.items() 
                    if info["type"] == db_type
                ]
            }
        return {"databases": list(self.databases.keys())}
    
    def get_tables(self, database):
        """获取表列表"""
        if database in self.databases:
            return {"tables": self.databases[database]["tables"]}
        return {"tables": []}
    
    def get_table_schema(self, database, table):
        """获取表结构"""
        if database in self.databases and table in self.databases[database]["tables"]:
            return {
                "columns": [
                    {"name": "id", "type": "int"},
                    {"name": "name", "type": "string"},
                    {"name": "created_at", "type": "timestamp"}
                ]
            }
        return {"columns": []}
