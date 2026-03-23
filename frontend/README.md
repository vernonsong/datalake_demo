# 智能入湖平台 - React 前端

这是一个基于 React + Vite 的前端项目，用于对接智能入湖平台的流式对话接口。

## 技术栈

- **React 18** - UI 框架
- **Vite** - 构建工具
- **Axios** - HTTP 客户端
- **原生 Fetch API** - 流式请求

## 项目结构

```
frontend/
├── src/
│   ├── api/
│   │   └── chat.js          # API 服务层（流式对话接口）
│   ├── components/
│   │   ├── Chat.jsx         # 聊天主组件
│   │   └── Chat.css         # 聊天组件样式
│   ├── App.jsx              # 应用主组件
│   ├── App.css              # 应用样式
│   ├── index.css            # 全局样式
│   └── main.jsx             # 应用入口
├── index.html               # HTML 模板
├── package.json             # 依赖配置
└── vite.config.js           # Vite 配置
```

## 功能特性

### 1. 流式对话
- 使用 Server-Sent Events (SSE) 格式接收流式响应
- 实时显示 AI 的思考和行动过程
- 支持显示工具调用信息

### 2. 消息类型
- **用户消息** - 蓝色气泡显示
- **AI 消息** - 白色气泡显示
- **工具调用** - 带工具名称的卡片显示
- **错误消息** - 红色背景显示

### 3. 交互功能
- 支持多行输入（Shift+Enter 换行）
- 自动滚动到最新消息
- 清空对话功能
- 取消正在进行的请求

## 安装和运行

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 预览生产版本
```bash
npm run preview
```

## API 接口

### 流式对话
```javascript
import { streamChat } from './api/chat';

// 使用异步生成器接收流式响应
const generator = streamChat({
  message: '帮我生成字段映射',
  userId: 'user123',
  conversationId: 'conv_001',
});

for await (const event of generator) {
  if (event.type === 'ai') {
    console.log('AI 回复:', event.content);
  } else if (event.type === 'tool') {
    console.log('工具调用:', event.name, event.content);
  } else if (event.type === 'done') {
    console.log('对话完成');
  }
}
```

## 响应格式

流式接口返回 SSE 格式数据：

```
data: {"type": "ai", "content": "AI 思考内容"}

data: {"type": "tool", "name": "read_file", "content": "阅读 SKILL.md"}

data: {"type": "done", "content": "处理完成"}

data: [DONE]
```

## 样式特点

- 响应式设计
- 平滑动画效果
- 打字指示器动画
- 自定义滚动条样式
- 消息渐入动画

## 开发说明

### 添加新的消息类型
在 `Chat.jsx` 的 `Message` 组件中添加新的类型判断和样式。

### 自定义 API 基础 URL
修改 `src/api/chat.js` 中的 `API_BASE_URL` 常量。

### 主题定制
修改 `Chat.css` 中的 CSS 变量和样式定义。

## 注意事项

1. **CORS 配置** - 确保后端服务已配置 CORS 允许跨域请求
2. **端口配置** - 默认后端服务运行在 `http://localhost:8000`
3. **超时设置** - 默认超时时间为 60 秒

## 许可证

MIT
