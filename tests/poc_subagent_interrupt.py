#!/usr/bin/env python3
"""
POC: SubAgent中断传递验证

验证目标：
1. 每个订单在独立的SubAgent上下文中处理
2. SubAgent调用需要确认的接口时，中断能正确传播到主Agent
3. 用户确认后，SubAgent能继续执行
4. 主Agent能正确管理多个订单的处理流程

测试场景：
- 上传包含2个订单的Excel文件
- 主Agent解析Excel，创建待办列表
- 主Agent使用task工具委托给field-mapping SubAgent
- SubAgent处理订单，调用platform_service执行SQL（需要确认）
- 验证中断传播和用户确认流程
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.dependencies import get_deep_agent
from langgraph.checkpoint.memory import MemorySaver


def test_subagent_interrupt():
    """测试SubAgent中断传递"""
    
    print("=" * 80)
    print("POC: SubAgent中断传递验证")
    print("=" * 80)
    
    agent = get_deep_agent()
    thread_id = "poc_test_001"
    
    print("\n[步骤1] 模拟用户上传Excel并请求批量处理")
    print("-" * 80)
    
    user_message = """
我上传了一个Excel文件，包含以下订单信息：

| 单号 | 源库 | 源表 | 目标库 | 目标表 |
|------|------|------|--------|--------|
| ORDER001 | source_db | order_info | target_db | dw_order |
| ORDER002 | source_db | user_info | target_db | dw_user |

请帮我批量处理这些订单的字段映射。
"""
    
    print(f"用户消息: {user_message}")
    
    print("\n[步骤2] 主Agent开始处理")
    print("-" * 80)
    
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"configurable": {"thread_id": thread_id}}
        )
        
        print("\n[步骤3] 检查结果")
        print("-" * 80)
        
        messages = result.get("messages", [])
        print(f"消息数量: {len(messages)}")
        
        if messages:
            last_message = messages[-1]
            print(f"\n最后一条消息类型: {type(last_message).__name__}")
            print(f"最后一条消息内容: {last_message.content if hasattr(last_message, 'content') else last_message}")
        
        if "__interrupt__" in result:
            print("\n✅ 检测到中断！")
            interrupt_data = result["__interrupt__"]
            print(f"中断信息: {json.dumps(interrupt_data, indent=2, ensure_ascii=False)}")
            
            print("\n[步骤4] 模拟用户确认")
            print("-" * 80)
            
            from langgraph.types import Command
            
            resume_value = {
                "decisions": [
                    {
                        "action_name": "platform_service",
                        "type": "approve"
                    }
                ]
            }
            
            print(f"发送确认: {json.dumps(resume_value, indent=2, ensure_ascii=False)}")
            
            result2 = agent.invoke(
                Command(resume=resume_value),
                config={"configurable": {"thread_id": thread_id}}
            )
            
            print("\n[步骤5] 确认后的结果")
            print("-" * 80)
            
            messages2 = result2.get("messages", [])
            print(f"消息数量: {len(messages2)}")
            
            if messages2:
                last_message2 = messages2[-1]
                print(f"\n最后一条消息类型: {type(last_message2).__name__}")
                print(f"最后一条消息内容: {last_message2.content if hasattr(last_message2, 'content') else last_message2}")
            
            if "__interrupt__" in result2:
                print("\n⚠️ 仍有中断（可能是第二个订单）")
                interrupt_data2 = result2["__interrupt__"]
                print(f"中断信息: {json.dumps(interrupt_data2, indent=2, ensure_ascii=False)}")
            else:
                print("\n✅ 没有更多中断，处理完成")
        else:
            print("\n❌ 未检测到中断！")
            print("可能的原因：")
            print("1. SubAgent未被正确调用")
            print("2. 中断配置未生效")
            print("3. 接口文档中REQUIRES_CONFIRMATION标记未设置")
        
        print("\n" + "=" * 80)
        print("POC验证完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_subagent_interrupt()
