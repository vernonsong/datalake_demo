#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版批量处理工具
支持用户介入、详细输出、生成文件等高级功能
"""

import json
import uuid
import os
from typing import Dict, Any, List
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


@tool
def batch_process_with_intervention(
    items: str,
    instruction_template: str,
    batch_size: int = 5,
    collect_outputs: bool = True,
    output_dir: str = "batch_outputs"
) -> Dict[str, Any]:
    """增强版批量处理工具，支持用户介入和详细输出收集。
    
    对列表中的每个项目执行相同的处理逻辑，每个项目在独立的子会话中执行。
    支持识别需要用户介入的项目，并收集详细的输出结果。
    
    Args:
        items: JSON字符串，包含待处理的项目列表
        instruction_template: 处理指令模板，使用{列名}作为占位符引用Excel列
        batch_size: 每批处理的数量，默认5
        collect_outputs: 是否收集详细输出（包括生成的文件），默认True
        output_dir: 输出文件收集目录，默认"batch_outputs"
    
    Returns:
        批量处理结果，包含：
        - 成功/失败统计
        - 需要介入的项目列表
        - 详细结果（包括生成的文件路径）
        - 汇总报告
    
    示例:
        items = '[{"单号": "ORDER001", "源表": "order_info"}, ...]'
        instruction_template = "处理单号{单号}的字段映射，源表为{源表}"
        
        返回结果会包含每个项目的详细信息和需要介入的项目
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
            "results": [],
            "needs_intervention": []
        }
    
    from app.core.dependencies import get_deep_agent
    agent = get_deep_agent()
    
    results = []
    needs_intervention = []
    processed = 0
    
    if collect_outputs and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        current_batch = items_list[batch_start:batch_end]
        
        logger.info(f"📦 开始处理第 {batch_start//batch_size + 1} 批 ({batch_start+1}-{batch_end}/{total})")
        
        for idx, item in enumerate(current_batch):
            global_idx = batch_start + idx + 1
            
            try:
                instruction = instruction_template.format(**item)
            except KeyError as e:
                results.append({
                    "index": global_idx,
                    "item": item,
                    "status": "failed",
                    "error": f"指令模板缺少键: {str(e)}",
                    "needs_intervention": False
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
                full_response = ""
                if isinstance(result, dict):
                    messages = result.get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, 'content'):
                            full_response = last_message.content
                            response_message = full_response
                        elif isinstance(last_message, dict):
                            full_response = last_message.get("content", "")
                            response_message = full_response
                
                needs_user_input = _check_needs_intervention(full_response)
                
                generated_files = []
                if collect_outputs:
                    generated_files = _collect_generated_files(item, output_dir)
                
                is_success = "完成" in response_message or "成功" in response_message
                
                result_item = {
                    "index": global_idx,
                    "item": item,
                    "status": "success" if is_success else "completed",
                    "response_summary": response_message[:200],
                    "full_response": full_response if collect_outputs else response_message[:500],
                    "generated_files": generated_files,
                    "needs_intervention": needs_user_input
                }
                
                results.append(result_item)
                
                if needs_user_input:
                    needs_intervention.append(result_item)
                    logger.warning(f"  ⚠️  [{global_idx}/{total}] 需要用户介入")
                
                processed += 1
                logger.info(f"  ✅ [{global_idx}/{total}] 处理完成")
                
            except Exception as e:
                logger.error(f"  ❌ [{global_idx}/{total}] 处理失败: {e}")
                result_item = {
                    "index": global_idx,
                    "item": item,
                    "status": "failed",
                    "error": str(e),
                    "needs_intervention": True
                }
                results.append(result_item)
                needs_intervention.append(result_item)
        
        logger.info(f"📊 第 {batch_start//batch_size + 1} 批处理完成 ({batch_end}/{total})")
        
        if batch_end < total:
            return {
                "success": True,
                "status": "partial",
                "total": total,
                "processed": processed,
                "remaining": total - processed,
                "results": results,
                "needs_intervention": needs_intervention,
                "message": f"已完成 {processed}/{total}，剩余 {total - processed} 个项目"
            }
    
    success_count = sum(1 for r in results if r["status"] in ["success", "completed"])
    fail_count = sum(1 for r in results if r["status"] == "failed")
    intervention_count = len(needs_intervention)
    
    summary_report = _generate_summary_report(results, output_dir)
    
    return {
        "success": True,
        "status": "completed",
        "total": total,
        "processed": processed,
        "success_count": success_count,
        "fail_count": fail_count,
        "intervention_count": intervention_count,
        "results": results,
        "needs_intervention": needs_intervention,
        "summary_report": summary_report,
        "message": f"批量处理完成！总计 {total} 个，成功 {success_count} 个，失败 {fail_count} 个，需要介入 {intervention_count} 个"
    }


def _check_needs_intervention(response: str) -> bool:
    """检查响应是否需要用户介入"""
    intervention_keywords = [
        "需要确认",
        "请确认",
        "不存在",
        "找不到",
        "权限不足",
        "无法访问",
        "请选择",
        "请提供",
        "缺少",
        "不明确",
        "冲突"
    ]
    
    return any(keyword in response for keyword in intervention_keywords)


def _collect_generated_files(item: Dict, output_dir: str) -> List[str]:
    """收集生成的文件"""
    order_id = item.get('单号', '')
    if not order_id:
        return []
    
    possible_files = [
        f"{order_id}.csv",
        f"{order_id}-mapped.csv",
        f"{order_id}-ddl.sql"
    ]
    
    collected_files = []
    for filename in possible_files:
        if os.path.exists(filename):
            target_path = os.path.join(output_dir, filename)
            try:
                import shutil
                shutil.copy2(filename, target_path)
                collected_files.append(target_path)
            except Exception as e:
                logger.warning(f"无法复制文件 {filename}: {e}")
    
    return collected_files


def _generate_summary_report(results: List[Dict], output_dir: str) -> str:
    """生成汇总报告"""
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("批量处理汇总报告")
    report_lines.append("=" * 60)
    report_lines.append("")
    
    for result in results:
        item = result['item']
        order_id = item.get('单号', f"项目{result['index']}")
        status = result['status']
        
        status_icon = "✅" if status in ["success", "completed"] else "❌"
        report_lines.append(f"{status_icon} {order_id} - {status}")
        
        if result.get('needs_intervention'):
            report_lines.append(f"   ⚠️  需要用户介入")
        
        if result.get('generated_files'):
            report_lines.append(f"   📄 生成文件:")
            for file_path in result['generated_files']:
                report_lines.append(f"      - {file_path}")
        
        if result.get('error'):
            report_lines.append(f"   ❌ 错误: {result['error']}")
        
        report_lines.append("")
    
    report_lines.append("=" * 60)
    
    report_content = "\n".join(report_lines)
    
    report_path = os.path.join(output_dir, "summary_report.txt")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"汇总报告已保存: {report_path}")
    except Exception as e:
        logger.warning(f"无法保存汇总报告: {e}")
    
    return report_content


def get_batch_tools_enhanced():
    """获取增强版批量处理工具列表"""
    return [batch_process_with_intervention]
