#!/usr/bin/env python3
"""
POC: 直接测试task工具调用SubAgent

验证目标：
1. 直接使用task工具调用field-mapping SubAgent
2. SubAgent调用platform_service时触发中断
3. 验证中断能正确传播到主Agent
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.dependencies import get_deep_agent
from langgraph.types import Command


def test_task_tool_direct():
    """直接测试task工具"""
    
    print("=" * 80)
    print("POC: 直接测试task工具调用SubAgent")
    print("=" * 80)
    
    agent = get_deep_agent()
    thread_id = "poc_task_direct_001"
    
    print("\n[步骤1] 直接使用task工具调用field-mapping SubAgent")
    print("-" * 80)
    
    user_message = """
请使用task工具调用field-mapping子Agent，处理以下订单：

单号: ORDER001
源库: source_db
源表: order_info
目标库: target_db
目标表: dw_order

注意：
1. 必须使用task工具，subagent_type="field-mapping"
2. SubAgent会调用platform_service执行SQL，这会触发用户确认
3. 我们要验证中断能否正确传播
"""
    
    print(f"用户消息: {user_message}")
    
    print("\n[步骤2] Agent开始处理")
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
            if hasattr(last_message, 'content'):
                content = last_message.content
                if len(content) > 500:
                    print(f"最后一条消息内容（前500字符）: {content[:500]}...")
                else:
                    print(f"最后一条消息内容: {content}")
        
        if "__interrupt__" in result:
            print("\n✅ 检测到中断！")
            interrupt_data = result["__interrupt__"]
            
            try:
                if isinstance(interrupt_data, list):
                    print(f"中断数量: {len(interrupt_data)}")
                    for i, item in enumerate(interrupt_data):
                        print(f"\n中断 {i+1}:")
                        if hasattr(item, '__dict__'):
                            print(f"  - value: {getattr(item, 'value', 'N/A')}")
                            print(f"  - resumable: {getattr(item, 'resumable', 'N/A')}")
                            print(f"  - ns: {getattr(item, 'ns', 'N/A')}")
                        else:
                            print(f"  - {item}")
                else:
                    print(f"中断信息: {interrupt_data}")
            except Exception as e:
                print(f"解析中断信息失败: {e}")
                print(f"原始中断数据: {interrupt_data}")
            
            print("\n[步骤4] 模拟用户确认")
            print("-" * 80)
            
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
                if hasattr(last_message2, 'content'):
                    content2 = last_message2.content
                    if len(content2) > 500:
                        print(f"最后一条消息内容（前500字符）: {content2[:500]}...")
                    else:
                        print(f"最后一条消息内容: {content2}")
            
            if "__interrupt__" in result2:
                print("\n⚠️ 仍有中断")
            else:
                print("\n✅ 没有更多中断，处理完成")
        else:
            print("\n❌ 未检测到中断！")
            print("\n可能的原因：")
            print("1. Agent未使用task工具")
            print("2. SubAgent未被正确调用")
            print("3. SubAgent未调用需要确认的接口")
            print("4. 中断配置未生效")
        
        print("\n" + "=" * 80)
        print("POC验证完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_task_tool_direct()
