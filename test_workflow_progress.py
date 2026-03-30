#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流进度推送功能
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_workflow_progress():
    """测试工作流进度推送"""
    logger.info("=" * 60)
    logger.info("测试工作流进度推送")
    logger.info("=" * 60)
    
    from app.workflows.loader import load_all_workflows
    from app.agents.tools.workflow_tool import execute_workflow
    
    load_all_workflows()
    
    params = {
        "order_id": "PROGRESS_TEST",
        "source_db": "test_db",
        "source_table": "test_table",
        "target_db": "clickhouse",
        "target_table": "dw_test"
    }
    
    logger.info(f"📋 测试参数: {params}")
    logger.info("\n" + "=" * 60)
    logger.info("开始执行工作流,观察进度输出:")
    logger.info("=" * 60 + "\n")
    
    try:
        result = execute_workflow.invoke({
            "workflow_name": "field-mapping",
            "params": params
        })
        
        logger.info("\n" + "=" * 60)
        logger.info("执行结果:")
        logger.info("=" * 60)
        logger.info(f"Success: {result.get('success')}")
        if result.get('error'):
            logger.info(f"Error: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


def main():
    """运行测试"""
    logger.info("🚀 开始测试工作流进度推送")
    logger.info("=" * 60)
    logger.info("注意: 此测试需要Mock服务运行")
    logger.info("如果Mock服务未运行,会看到错误,但进度推送机制仍然可以验证")
    logger.info("=" * 60 + "\n")
    
    success = test_workflow_progress()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ 测试通过")
        return 0
    else:
        logger.warning("⚠️ 测试失败(可能是Mock服务未运行)")
        logger.info("💡 提示: 检查上面的输出中是否有 [WORKFLOW_PROGRESS] 标记")
        logger.info("如果有,说明进度推送机制工作正常")
        return 1


if __name__ == "__main__":
    sys.exit(main())
