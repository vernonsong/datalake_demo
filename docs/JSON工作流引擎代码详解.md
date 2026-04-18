# JSON工作流引擎代码详解

## 目录

1. [架构概览](#架构概览)
2. [核心模块](#核心模块)
3. [工作流定义](#工作流定义)
4. [节点类型](#节点类型)
5. [执行流程](#执行流程)
6. [进度回调机制](#进度回调机制)
7. [错误处理](#错误处理)
8. [智能体集成](#智能体集成)

---

## 架构概览

### 整体架构

```
用户对话
    ↓
智能体 (DeepAgent)
    ↓
execute_workflow 工具 (LangChain Tool)
    ↓
工作流引擎 (LangGraph)
    ↓
节点执行器 (Python/LLM/HTTP/Map)
    ↓
进度回调 → 前端显示
```

### 目录结构

```
app/workflows/
├── __init__.py           # 模块初始化
├── state.py              # 工作流状态定义
├── loader.py             # JSON加载和验证
├── engine.py             # 工作流编译引擎
├── tool.py               # LangChain工具封装
├── error_handler.py      # 错误处理
└── nodes/                # 节点实现
    ├── base.py           # 基础节点类
    ├── python_executor.py # Python执行节点
    ├── llm_node.py       # LLM节点
    ├── http_request.py   # HTTP请求节点
    └── map_node.py       # Map批量处理节点
```

---

## 核心模块

### 1. 状态定义 (state.py)

工作流状态是整个引擎的数据载体,定义了工作流执行过程中的所有数据。

```python
from typing import TypedDict, Dict, Any, List, Optional

class WorkflowState(TypedDict):
    """工作流状态定义"""
    
    # 用户输入参数
    input: Dict[str, Any]
    
    # 节点输出数据 {node_id: output_data}
    data: Dict[str, Any]
    
    # 最终结果(给智能体看的文本)
    result: Optional[str]
    
    # 迭代信息(用于追踪和调试)
    it: Dict[str, Any]
    
    # 执行轨迹(记录每个节点的执行情况)
    _execution_trace: List[Dict[str, Any]]
    
    # 当前执行的节点ID
    _current_node: Optional[str]
```

**关键字段说明**:

- `input`: 工作流的输入参数,由用户或智能体提供
- `data`: 存储每个节点的输出,格式为 `{node_id: output_data}`
- `result`: 工作流的最终结果文本,会返回给智能体
- `it`: 迭代信息,包含 workflow_name, trace_id, user_id 等
- `_execution_trace`: 执行轨迹,记录每个节点的执行时间、状态等
- `_current_node`: 当前正在执行的节点ID

**为什么这样设计?**

1. **数据隔离**: 每个节点的输出存储在独立的命名空间中,避免冲突
2. **可追溯**: `_execution_trace` 记录完整的执行历史
3. **调试友好**: `it` 字段包含追踪ID,方便日志关联
4. **LangGraph兼容**: TypedDict 是 LangGraph 要求的状态格式

---

### 2. 加载器 (loader.py)

负责加载和验证工作流JSON定义。

```python
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# 工作流缓存 - 启动时加载所有工作流
_workflow_cache: Dict[str, Dict[str, Any]] = {}


def load_all_workflows() -> None:
    """加载所有工作流定义到缓存
    
    在应用启动时调用,扫描 workflows/definitions 目录
    加载所有 .json 文件到内存缓存
    """
    workflow_dir = Path("workflows/definitions")
    
    if not workflow_dir.exists():
        logger.warning(f"工作流定义目录不存在: {workflow_dir}")
        return
    
    # 遍历所有 JSON 文件
    for workflow_file in workflow_dir.glob("*.json"):
        try:
            workflow_name = workflow_file.stem  # 文件名(不含扩展名)
            
            # 读取 JSON
            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow_json = json.load(f)
            
            # 验证格式
            validate_workflow_definition(workflow_json)
            
            # 存入缓存
            _workflow_cache[workflow_name] = workflow_json
            logger.info(f"已加载工作流: {workflow_name}")
            
        except Exception as e:
            logger.error(f"加载工作流 {workflow_file} 失败: {e}")


def get_all_workflow_names() -> List[str]:
    """获取所有已加载的工作流名称"""
    return list(_workflow_cache.keys())


def get_workflow_from_cache(workflow_name: str) -> Dict[str, Any]:
    """从缓存获取工作流定义
    
    Args:
        workflow_name: 工作流名称
        
    Returns:
        工作流JSON定义
        
    Raises:
        FileNotFoundError: 工作流不存在
    """
    if workflow_name not in _workflow_cache:
        raise FileNotFoundError(f"工作流未找到: {workflow_name}")
    return _workflow_cache[workflow_name]


def load_workflow_definition(workflow_name: str) -> Dict[str, Any]:
    """加载工作流定义(兼容旧代码)
    
    优先从缓存读取,如果缓存中没有则从文件加载
    """
    # 先尝试从缓存读取
    if workflow_name in _workflow_cache:
        return _workflow_cache[workflow_name]
    
    # 缓存中没有,从文件加载
    workflow_path = Path("workflows/definitions") / f"{workflow_name}.json"
    
    if not workflow_path.exists():
        raise FileNotFoundError(f"工作流定义文件不存在: {workflow_path}")
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_json = json.load(f)
    
    validate_workflow_definition(workflow_json)
    
    return workflow_json


def validate_workflow_definition(workflow_json: Dict[str, Any]) -> None:
    """验证工作流定义格式
    
    检查必需字段和数据类型
    
    Args:
        workflow_json: 工作流JSON定义
        
    Raises:
        ValueError: 格式不正确
    """
    # 检查必需字段
    required_fields = ["nodes", "edges"]
    for field in required_fields:
        if field not in workflow_json:
            raise ValueError(f"工作流定义缺少必需字段: {field}")
    
    # 检查字段类型
    if not isinstance(workflow_json["nodes"], list):
        raise ValueError("nodes字段必须是数组")
    
    if not isinstance(workflow_json["edges"], list):
        raise ValueError("edges字段必须是数组")
    
    # 验证每个节点
    for node in workflow_json["nodes"]:
        if "id" not in node:
            raise ValueError("节点缺少id字段")
        if "type" not in node:
            raise ValueError(f"节点{node['id']}缺少type字段")
        if "config" not in node:
            raise ValueError(f"节点{node['id']}缺少config字段")
    
    # 验证每条边
    for edge in workflow_json["edges"]:
        if "from" not in edge or "to" not in edge:
            raise ValueError("边缺少from或to字段")
```

**关键设计**:

1. **缓存机制**: 启动时加载所有工作流到内存,避免重复读取文件
2. **验证严格**: 加载时验证格式,确保运行时不会出错
3. **错误友好**: 详细的错误信息,方便调试

---

### 3. 工作流引擎 (engine.py)

核心编译引擎,将JSON定义编译为LangGraph可执行图。

```python
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import WorkflowState
from .nodes.python_executor import PythonExecutorNode
from .nodes.llm_node import LLMNode
from .nodes.http_request import HttpRequestNode
from .nodes.map_node import MapNode


def compile_workflow_to_langgraph(workflow_json: Dict[str, Any]):
    """将JSON工作流定义编译为LangGraph图
    
    这是整个引擎的核心函数,负责:
    1. 创建状态图
    2. 为每个节点创建执行器
    3. 添加节点到图中
    4. 连接节点(根据edges定义)
    5. 编译图
    
    Args:
        workflow_json: 工作流JSON定义
        
    Returns:
        编译后的LangGraph图,可以直接执行
    """
    # 1. 创建状态图
    graph = StateGraph(WorkflowState)
    
    # 2. 创建节点映射 {node_id: node_config}
    nodes_map = {node["id"]: node for node in workflow_json["nodes"]}
    
    # 3. 为每个节点添加执行函数
    for node_id, node_config in nodes_map.items():
        node_type = node_config["type"]
        
        # 根据类型创建节点执行器
        if node_type == "python_executor":
            executor = PythonExecutorNode(node_id, node_config)
        elif node_type == "llm":
            executor = LLMNode(node_id, node_config)
        elif node_type == "http_request":
            executor = HttpRequestNode(node_id, node_config)
        elif node_type == "map":
            executor = MapNode(node_id, node_config)
        else:
            raise ValueError(f"不支持的节点类型: {node_type}")
        
        # 创建节点包装函数
        async def node_wrapper(state: WorkflowState, executor=executor, node_id=node_id):
            """节点包装函数
            
            这个函数是LangGraph节点的标准格式:
            - 接收 state 参数
            - 返回 state 更新字典
            
            为什么需要包装?
            - LangGraph要求节点函数返回状态更新,而不是直接修改状态
            - 我们需要统一处理节点执行、错误捕获、进度上报
            """
            try:
                # 执行节点
                result = await executor.execute(state)
                
                # 返回状态更新
                return {
                    "_current_node": node_id,
                    "data": {node_id: result},
                    "_execution_trace": state["_execution_trace"] + [{
                        "node_id": node_id,
                        "status": "completed",
                        "result": result
                    }]
                }
                
            except Exception as e:
                # 错误处理
                error_info = {
                    "message": str(e),
                    "type": type(e).__name__,
                    "node_id": node_id
                }
                
                return {
                    "_current_node": node_id,
                    "data": {node_id: {"status": "error", "error": error_info}},
                    "_execution_trace": state["_execution_trace"] + [{
                        "node_id": node_id,
                        "status": "error",
                        "error": error_info
                    }]
                }
        
        # 添加节点到图
        graph.add_node(node_id, node_wrapper)
    
    # 4. 添加边(连接节点)
    for edge in workflow_json["edges"]:
        from_node = edge["from"]
        to_node = edge["to"]
        
        if from_node == "__start__":
            # 设置入口节点
            graph.set_entry_point(to_node)
        elif to_node == "__end__":
            # 连接到结束
            graph.add_edge(from_node, END)
        else:
            # 普通边
            graph.add_edge(from_node, to_node)
    
    # 5. 编译图
    return graph.compile()
```

**关键设计**:

1. **节点工厂模式**: 根据type字段动态创建不同类型的节点执行器
2. **节点包装**: 统一处理执行、错误、追踪
3. **状态更新**: 返回更新字典而不是直接修改状态(LangGraph要求)
4. **边的处理**: 支持 `__start__` 和 `__end__` 特殊节点

---

## 节点类型

### 基础节点类 (nodes/base.py)

所有节点的基类,定义了统一的接口和进度回调机制。

```python
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod

# 全局进度回调函数
_progress_callback: Optional[Callable[[dict], None]] = None


def set_workflow_progress_callback(callback: Callable[[dict], None]):
    """设置工作流进度回调函数
    
    在智能体执行工作流前调用,设置回调函数
    工作流执行过程中会调用这个函数报告进度
    
    Args:
        callback: 回调函数,接收进度事件字典
    """
    global _progress_callback
    _progress_callback = callback


def clear_workflow_progress_callback():
    """清除工作流进度回调函数
    
    工作流执行完成后调用,清理回调
    """
    global _progress_callback
    _progress_callback = None


def _emit_progress(progress_data: dict):
    """发送工作流进度事件
    
    节点执行过程中调用此函数报告进度
    如果设置了回调函数,会调用回调函数
    
    Args:
        progress_data: 进度事件数据
    """
    global _progress_callback
    if _progress_callback:
        _progress_callback(progress_data)


class BaseNode(ABC):
    """节点基类
    
    所有节点类型都继承此类
    定义了统一的接口和通用逻辑
    """
    
    def __init__(self, node_id: str, node_config: Dict[str, Any]):
        """初始化节点
        
        Args:
            node_id: 节点ID
            node_config: 节点配置(来自JSON定义)
        """
        self.node_id = node_id
        self.node_config = node_config
    
    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点逻辑
        
        子类必须实现此方法
        
        Args:
            state: 工作流状态
            
        Returns:
            节点输出数据
        """
        pass
```

**关键设计**:

1. **全局回调**: 使用全局变量存储回调函数,所有节点共享
2. **抽象基类**: 强制子类实现 `execute` 方法
3. **统一接口**: 所有节点都接收 state,返回输出数据

---

### Python执行节点 (nodes/python_executor.py)

执行Python脚本的节点,支持调试断点。

```python
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any
from .base import BaseNode


class PythonExecutorNode(BaseNode):
    """Python脚本执行节点
    
    功能:
    - 动态加载Python脚本
    - 执行脚本的main函数
    - 支持调试断点(通过importlib加载)
    - 表达式解析(从state中获取参数)
    """
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行Python脚本
        
        执行流程:
        1. 获取脚本路径
        2. 解析输入参数(支持表达式)
        3. 动态加载脚本模块
        4. 调用main函数
        5. 返回结果
        """
        # 1. 获取配置
        config = self.node_config.get("config", {})
        script_path = config.get("script")
        input_config = config.get("input", {})
        
        if not script_path:
            raise ValueError(f"节点 {self.node_id} 缺少script配置")
        
        # 2. 解析输入参数
        # 支持表达式: ${data.node_id.field}
        script_input = {}
        for key, value in input_config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # 表达式解析
                expr = value[2:-1]  # 去掉 ${ 和 }
                script_input[key] = self._resolve_expression(expr, state)
            else:
                # 直接值
                script_input[key] = value
        
        # 3. 动态加载脚本
        script_full_path = Path(script_path)
        if not script_full_path.exists():
            raise FileNotFoundError(f"脚本文件不存在: {script_path}")
        
        # 使用 importlib 动态加载(支持调试)
        spec = importlib.util.spec_from_file_location(
            f"workflow_script_{self.node_id}",
            script_full_path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        
        # 4. 调用main函数
        if not hasattr(module, "main"):
            raise AttributeError(f"脚本 {script_path} 缺少main函数")
        
        # 构造脚本state参数
        script_state = {
            "input": state["input"],
            "data": state["data"],
            **script_input  # 合并解析后的输入
        }
        
        # 执行main函数
        result = module.main(script_state)
        
        # 5. 返回结果
        return result
    
    def _resolve_expression(self, expr: str, state: Dict[str, Any]) -> Any:
        """解析表达式
        
        支持的表达式格式:
        - data.node_id.field
        - input.param_name
        
        Args:
            expr: 表达式字符串
            state: 工作流状态
            
        Returns:
            解析后的值
        """
        parts = expr.split(".")
        
        # 从state开始解析
        value = state
        for part in parts:
            if value is None:
                return None
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value
```

**关键设计**:

1. **动态加载**: 使用 `importlib` 而不是 `exec`,支持调试器断点
2. **表达式解析**: 支持从其他节点获取数据 `${data.node_id.field}`
3. **错误友好**: 详细的错误信息,包含文件路径

---

### Map节点 (nodes/map_node.py)

批量处理节点,串行执行子工作流。

```python
from typing import Dict, Any, List
from .base import BaseNode, _emit_progress
from ..engine import compile_workflow_to_langgraph
from ..loader import load_workflow_definition


class MapNode(BaseNode):
    """Map批量处理节点
    
    功能:
    - 对数组中的每一项执行子工作流
    - 串行执行(避免进度混乱)
    - 发送详细的进度事件
    """
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行Map节点
        
        执行流程:
        1. 获取输入数组
        2. 加载子工作流定义
        3. 串行处理每一项:
           a. 发送 map_item_start 事件
           b. 执行子工作流
           c. 收集子工作流进度
           d. 发送 map_item_completed 事件
        4. 返回所有结果
        """
        config = self.node_config.get("config", {})
        
        # 1. 获取输入数组
        input_expr = config.get("input")
        if not input_expr:
            raise ValueError(f"Map节点 {self.node_id} 缺少input配置")
        
        # 解析表达式获取数组
        input_array = self._resolve_expression(input_expr, state)
        
        if not isinstance(input_array, list):
            raise ValueError(f"Map节点输入必须是数组,实际: {type(input_array)}")
        
        # 2. 加载子工作流
        sub_workflow_name = config.get("workflow")
        if not sub_workflow_name:
            raise ValueError(f"Map节点 {self.node_id} 缺少workflow配置")
        
        sub_workflow_json = load_workflow_definition(sub_workflow_name)
        
        # 3. 串行处理每一项
        results = []
        total_items = len(input_array)
        
        for index, item in enumerate(input_array):
            # 发送开始事件
            _emit_progress({
                "type": "map_item_start",
                "parent_node": self.node_id,
                "item_index": index,
                "total_items": total_items,
                "item_data": item
            })
            
            # 编译子工作流
            sub_graph = compile_workflow_to_langgraph(sub_workflow_json)
            
            # 构造子工作流状态
            sub_state = {
                "input": {"item": item, "index": index},
                "data": {},
                "result": None,
                "it": {
                    **state["it"],
                    "parent_node": self.node_id,
                    "item_index": index
                },
                "_execution_trace": [],
                "_current_node": None
            }
            
            # 执行子工作流(串行)
            async for event in sub_graph.astream(sub_state, stream_mode="updates"):
                # 处理子工作流事件
                for node_id, node_output in event.items():
                    if node_id.startswith("__"):
                        continue
                    
                    # 检查错误
                    node_data = node_output.get("data", {}).get(node_id)
                    if isinstance(node_data, dict) and node_data.get("status") == "error":
                        # 子工作流出错,立即中断
                        error_info = node_data.get("error")
                        raise MapNodeExecutionError(
                            f"Map节点第{index+1}项执行失败: {error_info.get('message')}"
                        )
                    
                    # 发送子节点进度
                    _emit_progress({
                        "type": "map_item_progress",
                        "parent_node": self.node_id,
                        "item_index": index,
                        "node_id": node_id,
                        "node_name": self._get_node_name(sub_workflow_json, node_id)
                    })
            
            # 收集结果
            result_data = sub_state.get("result") or sub_state.get("data")
            results.append(result_data)
            
            # 发送完成事件
            _emit_progress({
                "type": "map_item_completed",
                "parent_node": self.node_id,
                "item_index": index,
                "total_items": total_items
            })
        
        # 4. 返回所有结果
        return {
            "results": results,
            "count": len(results)
        }
    
    def _resolve_expression(self, expr: str, state: Dict[str, Any]) -> Any:
        """解析表达式(同PythonExecutorNode)"""
        if isinstance(expr, str) and expr.startswith("${") and expr.endswith("}"):
            expr_content = expr[2:-1]
            parts = expr_content.split(".")
            value = state
            for part in parts:
                if value is None:
                    return None
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        return expr
    
    def _get_node_name(self, workflow_json: Dict[str, Any], node_id: str) -> str:
        """获取节点名称"""
        for node in workflow_json.get("nodes", []):
            if node["id"] == node_id:
                return node.get("name", node_id)
        return node_id


class MapNodeExecutionError(Exception):
    """Map节点执行错误"""
    pass
```

**关键设计**:

1. **串行执行**: 使用 `async for` 循环,确保一个接一个处理
2. **详细进度**: 发送 start/progress/completed 三种事件
3. **错误中断**: 任何一项失败立即中断,不继续执行
4. **子工作流隔离**: 每一项都有独立的state

---

## 工作流工具 (tool.py)

将工作流引擎封装为LangChain工具,供智能体调用。

```python
import json
import uuid
from typing import Dict, Any
from langchain.tools import tool
from .loader import load_workflow_definition
from .engine import compile_workflow_to_langgraph
from .error_handler import format_error_for_agent
from .nodes.base import _emit_progress


def get_node_name(workflow_json: Dict[str, Any], node_id: str) -> str:
    """获取节点名称(用于进度显示)"""
    for node in workflow_json.get("nodes", []):
        if node["id"] == node_id:
            return node.get("name", node_id)
    return node_id


@tool
async def execute_workflow(workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行工作流 - LangChain工具
    
    这是智能体调用的入口函数
    
    Args:
        workflow_name: 工作流名称(对应JSON文件名)
        params: 工作流输入参数
        
    Returns:
        Dict包含:
        - success: bool - 是否成功
        - result: str - 结果文本(给智能体看)
        - error: str - 错误信息(如果失败)
        - execution_trace: List - 执行轨迹
    """
    try:
        # 1. 加载工作流定义
        workflow_json = load_workflow_definition(workflow_name)
        
        # 2. 编译为LangGraph图
        graph = compile_workflow_to_langgraph(workflow_json)
        
        # 3. 初始化状态
        state = {
            "input": params,
            "data": {},
            "result": None,
            "it": {
                "workflow_name": workflow_name,
                "trace_id": str(uuid.uuid4()),
                "user_id": params.get("_user_id"),
                "conversation_id": params.get("_conversation_id")
            },
            "_execution_trace": [],
            "_current_node": None
        }
        
        # 4. 流式执行工作流
        async for event in graph.astream(state, stream_mode="updates"):
            # 处理每个节点的更新事件
            for node_id, node_update in event.items():
                if node_id.startswith("__"):
                    continue  # 跳过特殊节点
                
                # 获取节点输出数据
                node_data = node_update.get("data", {}).get(node_id)
                
                # 检查错误
                if isinstance(node_data, dict) and node_data.get("status") == "error":
                    error_info = node_data.get("error")
                    
                    # 发送错误进度事件
                    _emit_progress({
                        "type": "node_error",
                        "workflow_name": workflow_name,
                        "node_id": node_id,
                        "node_name": get_node_name(workflow_json, node_id),
                        "error": error_info
                    })
                    
                    # 返回错误结果
                    return {
                        "success": False,
                        "result": None,
                        "error": format_error_for_agent(
                            workflow_name=workflow_name,
                            node_id=node_id,
                            node_name=get_node_name(workflow_json, node_id),
                            error_info=error_info,
                            execution_trace=state["_execution_trace"]
                        ),
                        "execution_trace": state["_execution_trace"]
                    }
                
                # 发送成功进度事件
                _emit_progress({
                    "type": "node_completed",
                    "workflow_name": workflow_name,
                    "node_id": node_id,
                    "node_name": get_node_name(workflow_json, node_id),
                    "status": "completed",
                    "data": node_data
                })
        
        # 5. 构造结果文本
        result_text = state.get("result") or f"工作流 {workflow_name} 执行成功"
        
        # 6. 返回成功结果
        return {
            "success": True,
            "result": result_text,
            "error": None,
            "execution_trace": state["_execution_trace"]
        }
        
    except Exception as e:
        # 捕获所有异常
        return {
            "success": False,
            "result": None,
            "error": f"工作流执行失败: {str(e)}",
            "execution_trace": []
        }
```

**关键设计**:

1. **@tool装饰器**: 将函数注册为LangChain工具
2. **流式执行**: 使用 `astream` 获取每个节点的更新
3. **进度上报**: 每个节点完成都发送进度事件
4. **错误处理**: 捕获所有错误并格式化返回
5. **智能体友好**: 返回格式化的文本结果

---

## 智能体集成 (dependencies.py)

将工作流工具注册到智能体。

```python
def get_deep_agent():
    """获取 DeepAgent 智能体(依赖注入)"""
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver
    from deepagents.backends import LocalShellBackend
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    llm = get_llm()
    checkpointer = MemorySaver()

    # 加载所有工作流到缓存
    from app.workflows.loader import load_all_workflows
    load_all_workflows()
    
    # 导入工具
    from app.agents.tools.platform_tool import get_platform_tools
    from app.agents.tools.workflow_tool import get_workflow_tools
    from app.workflows.tool import execute_workflow as json_workflow_execute
    
    # 组合所有工具
    platform_tools = get_platform_tools()
    workflow_tools = get_workflow_tools()  # 旧的工作流工具
    json_workflow_tools = [json_workflow_execute]  # 新的JSON工作流工具
    
    all_tools = platform_tools + workflow_tools + json_workflow_tools
    
    # 创建智能体
    return create_deep_agent(
        model=llm,
        system_prompt=SYSTEM_PROMPT,
        backend=LocalShellBackend(root_dir=str(PROJECT_ROOT)),
        skills=[...],
        tools=all_tools,  # 注册所有工具
        interrupt_on=None,
        middleware=[...],
        checkpointer=checkpointer,
    )
```

**关键步骤**:

1. 启动时加载所有工作流
2. 导入 `execute_workflow` 工具
3. 将工具添加到 `all_tools` 列表
4. 传递给 `create_deep_agent`

---

## 进度回调机制 (chat_agent.py)

在智能体执行前设置回调,接收工作流进度。

```python
async def chat_stream(self, user_id: str, message: str, conv_id: Optional[str] = None):
    """流式对话接口"""
    
    # 设置工作流进度回调
    from app.agents.tools.workflow_tool import set_workflow_progress_callback as set_old_workflow_callback
    from app.workflows.nodes.base import set_workflow_progress_callback as set_json_workflow_callback
    
    workflow_progress_buffer = []
    
    def on_workflow_progress(progress_data: dict):
        """工作流进度回调函数"""
        workflow_progress_buffer.append(progress_data)
        logger.info(f"🔔 收到工作流进度: {progress_data.get('node_name')} - {progress_data.get('status')}")
    
    # 设置回调(同时支持新旧工作流)
    set_old_workflow_callback(on_workflow_progress)
    set_json_workflow_callback(on_workflow_progress)
    logger.info("✅ 工作流进度回调已设置")
    
    try:
        # 执行智能体
        async for namespace, mode, data in self.agent.astream(...):
            # 处理进度事件
            if mode == "updates":
                if workflow_progress_buffer:
                    # 发送缓存的进度事件到前端
                    for progress_event in workflow_progress_buffer:
                        yield {
                            'type': 'workflow_progress',
                            'workflow_name': progress_event.get('workflow_name'),
                            'node_name': progress_event.get('node_name'),
                            'status': progress_event.get('status'),
                            'data': progress_event.get('data')
                        }
                    workflow_progress_buffer.clear()
            
            # ... 处理其他事件
    
    finally:
        # 清理回调
        from app.agents.tools.workflow_tool import clear_workflow_progress_callback as clear_old
        from app.workflows.nodes.base import clear_workflow_progress_callback as clear_json
        clear_old()
        clear_json()
```

**关键设计**:

1. **回调缓存**: 使用 `workflow_progress_buffer` 缓存进度事件
2. **事件转发**: 在 `updates` 模式下将进度事件发送到前端
3. **清理机制**: finally块中清理回调,避免内存泄漏

---

## 完整执行流程

### 1. 用户发送消息

```
用户: "帮我执行test_basic工作流"
```

### 2. 智能体理解意图

```python
# 智能体分析消息,决定调用 execute_workflow 工具
tool_call = {
    "name": "execute_workflow",
    "args": {
        "workflow_name": "test_basic",
        "params": {}
    }
}
```

### 3. 执行工作流工具

```python
# tool.py: execute_workflow()
result = await execute_workflow.ainvoke({
    "workflow_name": "test_basic",
    "params": {}
})
```

### 4. 加载工作流定义

```python
# loader.py: load_workflow_definition()
workflow_json = {
    "nodes": [
        {"id": "read_config", "type": "python_executor", ...},
        {"id": "analyze_data", "type": "llm", ...}
    ],
    "edges": [
        {"from": "__start__", "to": "read_config"},
        {"from": "read_config", "to": "analyze_data"},
        {"from": "analyze_data", "to": "__end__"}
    ]
}
```

### 5. 编译为LangGraph图

```python
# engine.py: compile_workflow_to_langgraph()
graph = StateGraph(WorkflowState)
graph.add_node("read_config", python_executor_wrapper)
graph.add_node("analyze_data", llm_node_wrapper)
graph.add_edge("read_config", "analyze_data")
compiled_graph = graph.compile()
```

### 6. 流式执行

```python
# 初始化状态
state = {
    "input": {},
    "data": {},
    "result": None,
    "it": {"workflow_name": "test_basic", "trace_id": "..."},
    "_execution_trace": [],
    "_current_node": None
}

# 流式执行
async for event in compiled_graph.astream(state, stream_mode="updates"):
    # event = {"read_config": {"data": {"read_config": {...}}}}
    # 发送进度事件
    _emit_progress({
        "type": "node_completed",
        "workflow_name": "test_basic",
        "node_id": "read_config",
        "node_name": "读取配置",
        "status": "completed"
    })
```

### 7. 进度回调

```python
# chat_agent.py: on_workflow_progress()
def on_workflow_progress(progress_data):
    workflow_progress_buffer.append(progress_data)

# 在 updates 事件中发送到前端
yield {
    'type': 'workflow_progress',
    'workflow_name': 'test_basic',
    'node_name': '读取配置',
    'status': 'completed'
}
```

### 8. 前端显示

```javascript
// Chat.jsx
if (event.type === 'workflow_progress') {
    // 更新工作流进度卡片
    updateWorkflowProgress({
        workflow_name: event.workflow_name,
        node_name: event.node_name,
        status: event.status
    });
}
```

### 9. 返回结果

```python
# tool.py: execute_workflow()
return {
    "success": True,
    "result": "工作流 test_basic 执行成功",
    "error": None,
    "execution_trace": [...]
}
```

### 10. 智能体回复

```
智能体: "工作流 test_basic 执行成功!
- ✅ 读取配置 节点完成
- ✅ 分析数据 节点完成"
```

---

## 总结

### 核心设计原则

1. **模块化**: 每个模块职责单一,易于维护
2. **可扩展**: 新增节点类型只需继承BaseNode
3. **类型安全**: 使用TypedDict定义状态结构
4. **错误友好**: 详细的错误信息和追踪
5. **调试支持**: Python节点支持断点调试
6. **进度透明**: 实时上报执行进度

### 关键技术

- **LangGraph**: 状态图编排引擎
- **LangChain**: 工具框架
- **asyncio**: 异步执行
- **importlib**: 动态模块加载
- **TypedDict**: 类型定义

### 扩展方向

1. **新节点类型**: 继承BaseNode实现新的节点
2. **条件分支**: 支持if/else逻辑
3. **并行执行**: 支持并行节点(需要修改Map节点)
4. **工作流嵌套**: 支持更深层次的嵌套
5. **持久化**: 支持工作流状态持久化和恢复

---

## 参考资料

- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
- [LangChain工具文档](https://python.langchain.com/docs/modules/agents/tools/)
- [任务文档](../tasks/2026-04-18-10-00-实现JSON工作流引擎.md)
