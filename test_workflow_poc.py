#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流POC测试脚本
验证field-mapping工作流的执行效果
"""

import sys
import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_workflow_direct():
    """测试1: 直接调用工作流"""
    logger.info("=" * 60)
    logger.info("测试1: 直接调用工作流")
    logger.info("=" * 60)
    
    from app.workflows.loader import load_all_workflows
    from app.workflows.registry import get_workflow
    
    load_all_workflows()
    
    workflow = get_workflow("field-mapping")
    if not workflow:
        logger.error("❌ 工作流未注册")
        return False
    
    logger.info("✅ 工作流已注册")
    
    params = {
        "order_id": "TEST001",
        "source_db": "test_db",
        "source_table": "test_table",
        "target_db": "clickhouse",
        "target_table": "dw_test"
    }
    
    logger.info(f"📋 测试参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
    
    try:
        result = workflow.invoke(params)
        
        logger.info("=" * 60)
        logger.info("执行结果:")
        logger.info("=" * 60)
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
        
        errors = result.get("errors", [])
        if errors:
            logger.warning(f"⚠️ 有错误: {errors}")
            return False
        
        logger.info("✅ 测试1通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试1失败: {e}", exc_info=True)
        return False


def test_workflow_via_tool():
    """测试2: 通过工具调用工作流"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 通过工具调用工作流")
    logger.info("=" * 60)
    
    from app.workflows.loader import load_all_workflows
    from app.agents.tools.workflow_tool import execute_workflow
    
    load_all_workflows()
    
    params = {
        "order_id": "TEST002",
        "source_db": "test_db",
        "source_table": "test_table",
        "target_db": "clickhouse",
        "target_table": "dw_test"
    }
    
    logger.info(f"📋 测试参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
    
    try:
        result = execute_workflow.invoke({
            "workflow_name": "field-mapping",
            "params": params
        })
        
        logger.info("=" * 60)
        logger.info("执行结果:")
        logger.info("=" * 60)
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
        
        if not result.get("success"):
            logger.warning(f"⚠️ 执行失败: {result.get('error')}")
            return False
        
        logger.info("✅ 测试2通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试2失败: {e}", exc_info=True)
        return False


def test_list_workflows():
    """测试3: 列出所有工作流"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 列出所有工作流")
    logger.info("=" * 60)
    
    from app.workflows.loader import load_all_workflows
    from app.agents.tools.workflow_tool import list_workflows
    
    load_all_workflows()
    
    try:
        result = list_workflows.invoke({})
        
        logger.info("=" * 60)
        logger.info("可用工作流:")
        logger.info("=" * 60)
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
        
        workflows = result.get("workflows", [])
        if not workflows:
            logger.warning("⚠️ 没有可用工作流")
            return False
        
        logger.info(f"✅ 测试3通过 (共 {len(workflows)} 个工作流)")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试3失败: {e}", exc_info=True)
        return False


def main():
    """运行所有测试"""
    logger.info("🚀 开始工作流POC测试")
    logger.info("=" * 60)
    
    results = []
    
    results.append(("列出工作流", test_list_workflows()))
    
    logger.info("\n⚠️ 注意: 以下测试需要Mock服务运行")
    logger.info("如果Mock服务未运行,测试会失败,这是正常的")
    logger.info("=" * 60)
    
    results.append(("直接调用工作流", test_workflow_direct()))
    results.append(("通过工具调用工作流", test_workflow_via_tool()))
    
    logger.info("\n" + "=" * 60)
    logger.info("测试汇总")
    logger.info("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    logger.info("=" * 60)
    logger.info(f"总计: {passed}/{total} 通过")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 所有测试通过!")
        return 0
    else:
        logger.warning(f"⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
