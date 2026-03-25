#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台服务工具 - LangChain Tool
使用@tool装饰器定义，支持hook处理接口输出
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from langchain_core.tools import tool


_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_doc_path(doc_path: str) -> Path:
    resolved = (_PROJECT_ROOT / doc_path).resolve()
    if _PROJECT_ROOT not in resolved.parents and resolved != _PROJECT_ROOT:
        raise ValueError("doc_path 必须位于项目目录内")
    if not resolved.is_file():
        raise ValueError(f"doc_path 文件不存在: {doc_path}")
    return resolved


def _validate_doc(platform: str, doc_path: str, doc_excerpt: str) -> None:
    allowed_prefixes = {
        "metadata": "skills/platform-skill/metadata-service/",
        "schedule": "skills/platform-skill/schedule-service/",
        "integration": "skills/platform-skill/integration-service/",
        "sql": "skills/platform-skill/sql-service/",
    }

    prefix = allowed_prefixes.get(platform)
    if not prefix:
        raise ValueError(f"不支持的平台: {platform}")
    if not doc_path.startswith(prefix):
        raise ValueError(f"doc_path 必须以 {prefix} 开头")
    if "DOC_GUARD:" not in doc_excerpt:
        raise ValueError("doc_excerpt 必须包含从文档复制的 DOC_GUARD 行")

    resolved = _resolve_doc_path(doc_path)
    content = resolved.read_text(encoding="utf-8")
    if "DOC_GUARD:" not in content:
        raise ValueError("文档缺少 DOC_GUARD 标记，无法用于调用约束")
    if doc_excerpt not in content:
        raise ValueError("doc_excerpt 未在 doc_path 中匹配到，请从文档原文复制")


def _parse_params(params: Optional[Union[str, Dict]]) -> Optional[Dict]:
    """解析参数，支持字符串或字典"""
    if params is None:
        return None
    if isinstance(params, dict):
        return params
    if isinstance(params, str):
        try:
            return json.loads(params)
        except json.JSONDecodeError:
            return None
    return None


@tool
def platform_service(
    platform: str,
    method: str,
    endpoint: str,
    doc_path: str,
    doc_excerpt: str,
    params: Optional[Union[str, Dict]] = None,
    json_body: Optional[Union[str, Dict]] = None,
    hook: Optional[str] = None
) -> Dict[str, Any]:
    """调用平台服务API的工具。

    ⚠️ 重要约束：在调用此工具之前，必须先阅读对应平台的接口文档。

    本工具不提供任何具体端点示例。调用方必须显式传入：
    - doc_path: 你阅读的接口文档路径（相对项目根目录）
    - doc_excerpt: 从该文档中原样复制的一行（必须包含 DOC_GUARD:）

    Args:
        platform: 平台类型: metadata/schedule/integration/sql
        method: HTTP方法: GET/POST/PUT/DELETE
        endpoint: API端点路径，如 /api/metadata/databases
        doc_path: 接口文档相对路径（如 skills/platform-skill/metadata-service/get-table-schema.md）
        doc_excerpt: 从文档复制的 DOC_GUARD 行
        params: URL查询参数(可选，支持字符串或字典)
        json_body: 请求体JSON(可选，支持字符串或字典)
        hook: 可选的Python脚本，用于处理接口返回结果。脚本接收变量 'result'，需返回处理后的结果。

    Returns:
        API响应结果，或hook处理后的结果

    ## Hook

    hook 是一段可选的 Python 脚本，用于在接口返回后对 `result` 做二次处理。
    hook 的具体写法与约束应来自对应 Skill 或平台文档，本工具不提供可直接照抄的示例。

    ### 完整调用示例（占位符）

    ```python
    platform_service(
        platform="metadata",
        method="GET",
        endpoint="<从接口文档复制>",
        doc_path="<你已阅读的接口文档路径>",
        doc_excerpt="DOC_GUARD: <从文档原样复制>",
        params=None,
        json_body=None,
        hook=None,
    )
    ```
    """
    from app.core.dependencies import (
        get_metadata_client,
    get_schedule_client,
    get_integration_client,
    get_sql_execution_client
)

    clients = {
        "metadata": get_metadata_client,
        "schedule": get_schedule_client,
        "integration": get_integration_client,
        "sql": get_sql_execution_client,
    }

    if platform not in clients:
        return {
            "success": False,
            "error": f"不支持的平台: {platform}，支持的平台: {list(clients.keys())}"
        }

    try:
        _validate_doc(platform=platform, doc_path=doc_path, doc_excerpt=doc_excerpt)
    except Exception as e:
        return {
            "success": False,
            "error": f"接口文档校验失败: {str(e)}",
        }

    client = clients[platform]()

    parsed_params = _parse_params(params)
    parsed_json_body = _parse_params(json_body) if json_body else None

    try:
        result = client.request(
            method=method,
            endpoint=endpoint,
            params=parsed_params,
            json=parsed_json_body
        )
    except Exception as e:
        return {
            "success": False,
            "error": f"请求失败: {str(e)}"
        }

    if hook:
        try:
            exec_globals = {'result': result}
            exec(hook, exec_globals)
            return exec_globals.get('result', result)
        except Exception as e:
            return {
                "success": False,
                "error": f"Hook执行失败: {str(e)}",
                "original_result": result
            }

    return result


def get_platform_tools():
    """获取平台服务工具列表"""
    return [platform_service]
