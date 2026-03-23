# 任务: Chat Agent配置优化

## 任务描述
优化chat_agent，遵循服务配置规范，APIKey从配置中心获取，编写聊天接口验证可用

## 完成内容

### 1. 重构ChatAgent
- 文件: `app/agents/chat_agent.py`
- 通过依赖注入获取LLM和Agent

### 2. 添加依赖注入函数
- 文件: `app/core/dependencies.py`
- get_ali_api_key(): 从配置中心获取API Key
- get_llm(): 获取语言模型
- get_deep_agent(): 获取DeepAgent智能体
- get_chat_agent(): 获取聊天智能体

### 3. APIKey配置流程
```
配置中心 (ali_api_key)
    ↓
get_ali_api_key() 
    ↓
get_llm() → ChatOpenAI(api_key=...)
```

### 4. 添加聊天路由
- 文件: `app/routers/chat.py`
- POST /chat/ 接口

### 5. 验证结果
```json
{
    "success": true,
    "message": "你好！我是智能入湖平台的助手，有什么可以帮你的吗？",
    "conversation_id": null,
    "workflow_json": null
}
```

## 验证状态
✅ 已通过 task-completion-validator 验证
