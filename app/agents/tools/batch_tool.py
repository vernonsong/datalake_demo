#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用批量处理工具
支持对列表中的每个项目执行相同的处理逻辑，每个项目在独立的子会话中执行
"""

import json
import uuid
from typing import Dict, Any
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


class BatchProgressCallback:
    """批量处理进度回调 - 用于向主会话推送进度"""
    
    def __init__(self):
        self.progress_events = []
    
    def on_item_start(self, index: int, total: int, item: Dict[str, Any]):
        """订单开始处理"""
        event = {
            "type": "item_start",
            "index": index,
            "total": total,
            "item": item,
            "timestamp": logger.name
        }
        self.progress_events.append(event)
        print(f"\n[BATCH_PROGRESS] {json.dumps(event, ensure_ascii=False)}")
    
    def on_item_complete(self, index: int, total: int, item: Dict[str, Any], status: str, message: str = ""):
        """订单处理完成"""
        event = {
            "type": "item_complete",
            "index": index,
            "total": total,
            "item": item,
            "status": status,
            "message": message[:200] if message else ""
        }
        self.progress_events.append(event)
        print(f"\n[BATCH_PROGRESS] {json.dumps(event, ensure_ascii=False)}")
    
    def on_item_error(self, index: int, total: int, item: Dict[str, Any], error: str):
        """订单处理失败"""
        event = {
            "type": "item_error",
            "index": index,
            "total": total,
            "item": item,
            "error": error
        }
        self.progress_events.append(event)
        print(f"\n[BATCH_PROGRESS] {json.dumps(event, ensure_ascii=False)}")


@tool
def batch_process(
    items: str,
    instruction_template: str,
    batch_size: int = 5,
) -> Dict[str, Any]:
    """通用批量处理工具。
    
    对列表中的每个项目执行相同的处理逻辑，每个项目在独立的子会话中执行，避免上下文累积。
    
    Args:
        items: JSON字符串，包含待处理的项目列表
        instruction_template: 处理指令模板，使用{列名}作为占位符引用Excel列
        batch_size: 每批处理的数量，默认5（超过此数量会分批并询问用户）
    
    Returns:
        批量处理结果，包含成功/失败统计和详细结果
    
    示例:
        items = '[{"单号": "ORDER001", "源表": "order_info"}, ...]'
        instruction_template = "处理单号{单号}的字段映射，源表为{源表}"
        
        工具会为每个项目创建独立的子会话，执行对应的指令
    """
    
    try:
        items_list = json.loads(items)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"items参数必须是有效的JSON数组: {str(e)}"
        }
    
    if not isinstance(items_list, list):
        return {
            "success": False,
            "error": "items必须是JSON数组"
        }
    
    total = len(items_list)
    
    if total == 0:
        return {
            "success": True,
            "total": 0,
            "processed": 0,
            "results": []
        }
    
    from app.core.dependencies import get_deep_agent
    agent = get_deep_agent()
    
    callback = BatchProgressCallback()
    results = []
    processed = 0
    
    print(f"\n[BATCH_PROGRESS] {json.dumps({'type': 'batch_start', 'total': total}, ensure_ascii=False)}")
    
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        current_batch = items_list[batch_start:batch_end]
        
        logger.info(f"📦 开始处理第 {batch_start//batch_size + 1} 批 ({batch_start+1}-{batch_end}/{total})")
        
        for idx, item in enumerate(current_batch):
            global_idx = batch_start + idx + 1
            
            callback.on_item_start(global_idx, total, item)
            
            try:
                instruction = instruction_template.format(**item)
            except KeyError as e:
                error_msg = f"指令模板缺少键: {str(e)}"
                callback.on_item_error(global_idx, total, item, error_msg)
                results.append({
                    "index": global_idx,
                    "item": item,
                    "status": "failed",
                    "error": error_msg
                })
                continue
            
            sub_thread_id = f"batch_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"  [{global_idx}/{total}] 处理项目: {item.get('单号', item)}")
            
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": instruction}]},
                    config={"configurable": {"thread_id": sub_thread_id}}
                )
                
                response_message = ""
                if isinstance(result, dict):
                    messages = result.get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, 'content'):
                            response_message = last_message.content
                        elif isinstance(last_message, dict):
                            response_message = last_message.get("content", "")
                
                is_success = "完成" in response_message or "成功" in response_message
                status = "success" if is_success else "completed"
                
                callback.on_item_complete(global_idx, total, item, status, response_message)
                
                results.append({
                    "index": global_idx,
                    "item": item,
                    "status": status,
                    "response": response_message[:200]
                })
                
                processed += 1
                logger.info(f"  ✅ [{global_idx}/{total}] 处理完成")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"  ❌ [{global_idx}/{total}] 处理失败: {e}")
                callback.on_item_error(global_idx, total, item, error_msg)
                results.append({
                    "index": global_idx,
                    "item": item,
                    "status": "failed",
                    "error": error_msg
                })
        
        logger.info(f"📊 第 {batch_start//batch_size + 1} 批处理完成 ({batch_end}/{total})")
        
        if batch_end < total:
            partial_result = {
                "success": True,
                "status": "partial",
                "total": total,
                "processed": processed,
                "remaining": total - processed,
                "results": results,
                "message": f"已完成 {processed}/{total}，剩余 {total - processed} 个项目"
            }
            print(f"\n[BATCH_PROGRESS] {json.dumps({'type': 'batch_partial', **partial_result}, ensure_ascii=False)}")
            return partial_result
    
    success_count = sum(1 for r in results if r["status"] in ["success", "completed"])
    fail_count = total - success_count
    
    final_result = {
        "success": True,
        "status": "completed",
        "total": total,
        "processed": processed,
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results,
        "message": f"批量处理完成！总计 {total} 个，成功 {success_count} 个，失败 {fail_count} 个"
    }
    
    print(f"\n[BATCH_PROGRESS] {json.dumps({'type': 'batch_complete', **final_result}, ensure_ascii=False)}")
    
    return final_result


def get_batch_tools():
    """获取批量处理工具列表"""
    return [batch_process]
