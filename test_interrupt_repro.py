
import sys
import os
from pathlib import Path
from langchain_core.messages import AIMessage, ToolCall
from langchain.agents.middleware.human_in_the_loop import InterruptOnConfig

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

from app.core.dependencies import DynamicHumanInTheLoopMiddleware, _should_interrupt_platform_service

def test_dynamic_middleware():
    print("\n=== 测试 DynamicHumanInTheLoopMiddleware ===")
    
    # 1. 初始化 Middleware
    static_config = {"write_file": True}
    dynamic_conditions = {"platform_service": _should_interrupt_platform_service}
    
    middleware = DynamicHumanInTheLoopMiddleware(
        interrupt_on=static_config,
        dynamic_conditions=dynamic_conditions
    )
    
    print(f"Initial interrupt_on: {middleware.interrupt_on.keys()}")
    
    # 2. 构造 State (模拟 LLM 输出 ToolCall)
    # Case A: 需要确认的 ToolCall
    tool_call_confirm = ToolCall(
        name="platform_service",
        args={"doc_path": "skills/platform-skill/integration-service/create-task.md"},
        id="call_1"
    )
    
    state_confirm = {
        "messages": [
            AIMessage(content="Creating task...", tool_calls=[tool_call_confirm])
        ]
    }
    
    # 3. 调用 after_model
    # 注意：after_model 会返回 None (如果没有中断) 或者修改后的消息 (如果有中断)
    # 但是 HumanInTheLoopMiddleware.after_model 会触发 interrupt() 函数，这会抛出 GraphInterrupt
    # 我们无法在脚本中捕获 GraphInterrupt 并继续，除非我们在 LangGraph 运行时中
    # 但我们可以检查 middleware.interrupt_on 是否被临时修改了
    
    # 为了测试，我们可以 mock super().after_model 或者检查 self.interrupt_on
    # 这里我们通过继承并覆盖 after_model 来观察
    
    print("\n--- Testing Case A (Should Interrupt) ---")
    
    # 临时覆盖 super().after_model 以避免实际中断
    original_super_after_model = super(DynamicHumanInTheLoopMiddleware, middleware).after_model
    
    def mock_super_after_model(state, runtime):
        print(f"Inside super().after_model, interrupt_on keys: {middleware.interrupt_on.keys()}")
        if "platform_service" in middleware.interrupt_on:
            print("SUCCESS: platform_service is in interrupt_on")
            return "INTERRUPTED"
        else:
            print("FAILURE: platform_service is NOT in interrupt_on")
            return None

    # 动态替换方法（Python 允许这样做吗？对于 super() 调用可能不行）
    # 实际上，我们可以直接调用 middleware.after_model，它会调用 super().after_model
    # 如果 super().after_model 抛出异常或中断，我们可以捕获
    
    # 让我们尝试直接运行，看看是否会因为 interrupt() 而报错（因为不在 Graph 中）
    try:
        middleware.after_model(state_confirm, None)
    except Exception as e:
        print(f"Caught exception: {e}")
        # 如果是因为 interrupt() 调用失败（没有 Graph 上下文），那说明逻辑走到了那里
        if "No graph context" in str(e) or "interrupt" in str(e):
            print("This likely means interrupt() was called, which is GOOD.")
            
    # Case B: 不需要确认的 ToolCall
    print("\n--- Testing Case B (Should NOT Interrupt) ---")
    tool_call_pass = ToolCall(
        name="platform_service",
        args={"doc_path": "skills/platform-skill/metadata-service/get-table-schema.md"},
        id="call_2"
    )
    
    state_pass = {
        "messages": [
            AIMessage(content="Getting schema...", tool_calls=[tool_call_pass])
        ]
    }
    
    try:
        result = middleware.after_model(state_pass, None)
        if result is None:
            print("SUCCESS: Result is None (No interrupt)")
        else:
            print(f"FAILURE: Result is {result}")
    except Exception as e:
        print(f"Caught exception: {e}")

if __name__ == "__main__":
    test_dynamic_middleware()
