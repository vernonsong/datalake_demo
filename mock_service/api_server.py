#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock API服务器
整合所有Mock服务，支持Token鉴权
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_service.metadata_service import MockMetadataService
from mock_service.integration_service import MockIntegrationService
from mock_service.schedule_service import MockScheduleService
from mock_service.sql_execution_service import MockSqlExecutionService
from mock_service.config_service import ConfigService
from mock_service.token_service import TokenService
from http.server import HTTPServer, BaseHTTPRequestHandler


PUBLIC_PATHS = {"/health", "/api/token", "/api/config", "/api/config/"}


class AuthRequiredError(Exception):
    """需要鉴权的异常"""
    pass


class MockApiRequestHandler(BaseHTTPRequestHandler):
    """Mock API请求处理器"""

    def __init__(self, *args, **kwargs):
        self.metadata_service = MockMetadataService()
        self.integration_service = MockIntegrationService()
        self.schedule_service = MockScheduleService()
        self.sql_service = MockSqlExecutionService()
        self.config_service = ConfigService()
        self.token_service = TokenService()
        super().__init__(*args, **kwargs)

    def check_auth(self) -> bool:
        """检查请求是否需要鉴权并验证"""
        if self.path in PUBLIC_PATHS:
            return True

        if self.path.startswith("/api/config/"):
            config_key = self.path.replace("/api/config/", "")
            public_keys = ("jwt_secret", "mock_api_secret", "ali_api_key")
            if not config_key or config_key in public_keys:
                return True

        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return False

        token = auth_header[7:]
        return self.token_service.verify_token(token)

    def send_response_json(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error_response(self, status_code, message):
        """发送错误响应"""
        self.send_response_json({"error": message}, status_code)

    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response_json({})

    def do_GET(self):
        """处理GET请求"""
        if not self.check_auth():
            self.send_error_response(401, "Unauthorized: Invalid or missing token")
            return

        if self.path == '/health':
            self.send_response_json({"status": "healthy", "service": "mock_api_server"})
        elif self.path == '/api/token':
            self.send_response_json({"message": "Use POST to generate token"})
        elif self.path.startswith('/api/metadata/databases'):
            db_type = None
            if '?' in self.path:
                query_string = self.path.split('?')[1]
                for param in query_string.split('&'):
                    if param.startswith('db_type='):
                        db_type = param.split('=')[1]
            result = self.metadata_service.get_databases(db_type)
            self.send_response_json(result)
        elif self.path.startswith('/api/metadata/tables/'):
            parts = self.path.split('/')
            if len(parts) >= 5:
                database = parts[4]
                result = self.metadata_service.get_tables(database)
                self.send_response_json(result)
            else:
                self.send_response_json({"error": "Invalid path"}, 400)
        elif self.path.startswith('/api/metadata/schema/'):
            parts = self.path.split('/')
            if len(parts) >= 6:
                database = parts[4]
                table = parts[5]
                result = self.metadata_service.get_table_schema(database, table)
                self.send_response_json(result)
            else:
                self.send_response_json({"error": "Invalid path"}, 400)
        elif self.path.startswith('/api/integration/tasks'):
            result = self.integration_service.list_tasks()
            self.send_response_json(result)
        elif self.path.startswith('/api/schedules'):
            result = self.schedule_service.list_schedules()
            self.send_response_json(result)
        elif self.path.startswith('/api/sql/executions'):
            result = self.sql_service.list_executions()
            self.send_response_json(result)
        elif self.path == '/api/config':
            result = self.config_service.get_all_configs()
            self.send_response_json(result)
        elif self.path.startswith('/api/config/'):
            key = self.path.split('/api/config/')[1]
            result = self.config_service.get_config(key)
            self.send_response_json(result)
        else:
            self.send_response_json({"message": "Mock API server"})

    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/token':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            secret = data.get("secret", "")
            from dotenv import load_dotenv
            load_dotenv()
            expected_secret = os.getenv("MOCK_API_SECRET", "")

            if secret != expected_secret:
                self.send_error_response(403, "Invalid secret")
                return

            token = self.token_service.generate_token()
            self.send_response_json({"token": token, "expires_in": 3600})
            return

        if not self.check_auth():
            self.send_error_response(401, "Unauthorized: Invalid or missing token")
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        if self.path == '/api/metadata/request':
            self.send_response_json({"status": "success", "data": data})
        elif self.path == '/api/integration/request':
            self.send_response_json({"status": "success", "data": data})
        elif self.path == '/api/schedule/request':
            self.send_response_json({"status": "success", "data": data})
        elif self.path == '/api/sql/request':
            self.send_response_json({"status": "success", "data": data})
        elif self.path == '/api/integration/tasks':
            result = self.integration_service.create_task(data)
            self.send_response_json(result)
        elif self.path == '/api/schedules':
            result = self.schedule_service.create_schedule(data)
            self.send_response_json(result)
        elif self.path == '/api/sql/execute':
            result = self.sql_service.execute_sql(data)
            self.send_response_json(result)
        elif self.path == '/api/config':
            key = data.get("key")
            value = data.get("value")
            if key and value is not None:
                result = self.config_service.set_config(key, value)
            else:
                result = {"error": "Missing key or value"}
            self.send_response_json(result)
        else:
            self.send_response_json({"status": "success", "received": data})

    def do_PUT(self):
        """处理PUT请求"""
        if not self.check_auth():
            self.send_error_response(401, "Unauthorized: Invalid or missing token")
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        if self.path.startswith('/api/schedules/'):
            schedule_id = self.path.split('/api/schedules/')[1]
            result = self.schedule_service.update_schedule(schedule_id, data)
            self.send_response_json(result)
        elif self.path.startswith('/api/config/'):
            key = self.path.split('/api/config/')[1]
            value = data.get("value")
            if value is not None:
                result = self.config_service.set_config(key, value)
            else:
                result = {"error": "Missing value"}
            self.send_response_json(result)
        else:
            self.send_response_json({"error": "Invalid path"}, 404)

    def do_DELETE(self):
        """处理DELETE请求"""
        if not self.check_auth():
            self.send_error_response(401, "Unauthorized: Invalid or missing token")
            return

        if self.path.startswith('/api/config/'):
            key = self.path.split('/api/config/')[1]
            result = self.config_service.delete_config(key)
            self.send_response_json(result)
        else:
            self.send_response_json({"error": "Invalid path"}, 404)


def run_api_server(port=5001):
    """运行API服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MockApiRequestHandler)
    print(f"Mock API服务运行在 http://localhost:{port}")
    print(f"可用接口:")
    print(f"  - 元数据服务: /api/metadata/* (需鉴权)")
    print(f"  - 集成服务: /api/integration/* (需鉴权)")
    print(f"  - 调度服务: /api/schedules/* (需鉴权)")
    print(f"  - SQL执行服务: /api/sql/* (需鉴权)")
    print(f"  - 配置中心: /api/config/* (部分需鉴权)")
    print(f"  - Token生成: POST /api/token")
    print(f"  - 健康检查: /health (公开)")
    httpd.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    run_api_server(port)
