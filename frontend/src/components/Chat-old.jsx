import React, { useState, useRef, useEffect } from 'react';
import { streamChat } from '../api/chat';
import './Chat.css';

/**
 * 聊天消息组件
 */
function Message({ message }) {
  const isUser = message.role === 'user';
  const isTool = message.type === 'tool';
  const isError = message.type === 'error';
  const isThinking = message.type === 'thinking';

  return (
    <div className={`message ${isUser ? 'user' : 'ai'} ${isTool ? 'tool' : ''} ${isError ? 'error' : ''} ${isThinking ? 'thinking' : ''}`}>
      <div className="message-avatar">
        {isUser ? '👤' : isTool ? '🔧' : isError ? '❌' : isThinking ? '💭' : '🤖'}
      </div>
      <div className="message-content">
        {isTool && (
          <div className="tool-header">
            <span className="tool-name">工具：{message.name || 'unknown'}</span>
          </div>
        )}
        {isThinking && message.title && (
          <div className="thinking-title">
            <strong>{message.title}</strong>
          </div>
        )}
        <div className="message-text">
          {message.content}
        </div>
        {isThinking && message.items && message.items.length > 0 && (
          <div className="thinking-items">
            {message.items.map((item, idx) => (
              <div key={idx} className={`thinking-item ${item.status || ''}`}>
                <span className="thinking-icon">{item.status === 'completed' ? '✅' : item.status === 'pending' ? '⏳' : '⭕'}</span>
                <span className="thinking-text">{item.text || item}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 输入框组件
 */
function ChatInput({ onSend, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="输入消息... (按 Enter 发送，Shift+Enter 换行)"
        disabled={disabled}
        rows={2}
      />
      <button type="submit" disabled={disabled || !input.trim()}>
        发送
      </button>
    </form>
  );
}

/**
 * 聊天主组件
 */
function Chat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);
  const thinkingStateRef = useRef({ todos: [], toolCalls: [], fileReads: [] });
  const thinkingMessageInsertedRef = useRef(false);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 发送消息
  const handleSend = async (content) => {
    // 添加用户消息
    const userMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // 创建 AbortController 用于取消请求
    abortControllerRef.current = new AbortController();

    try {
      // 流式调用
      const generator = streamChat({
        message: content,
        userId: 'default_user',
        conversationId,
      });

      let aiMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };
      
      // 重置思考状态
      thinkingStateRef.current = { todos: [], toolCalls: [], fileReads: [] };
      thinkingMessageInsertedRef.current = false;

      // 创建或更新思考消息的函数
      const updateThinkingMessage = () => {
        const state = thinkingStateRef.current;
        if (state.todos.length === 0 && state.toolCalls.length === 0 && state.fileReads.length === 0) {
          return;
        }

        const thinkingMessage = {
          type: 'thinking',
          title: '思考过程',
          content: '',
          items: [
            ...state.fileReads.map(f => ({ text: `📄 读取文件：${f.path}`, status: 'completed' })),
            ...state.toolCalls.map(t => ({ text: `🔧 调用工具：${t.name}`, status: 'completed' })),
            ...state.todos.map(t => ({ text: t.content || t.text || t, status: t.status }))
          ],
          timestamp: new Date().toISOString(),
        };

        setMessages(prev => {
          // 检查是否已经插入过思考消息
          const existingIndex = prev.findIndex(m => m.type === 'thinking');
          if (existingIndex >= 0) {
            // 更新现有的思考消息
            const newMessages = [...prev];
            newMessages[existingIndex] = thinkingMessage;
            return newMessages;
          } else {
            // 插入新的思考消息到 AI 消息之前
            const aiIndex = prev.findIndex(m => m.role === 'assistant' && !m.type);
            if (aiIndex >= 0) {
              return [...prev.slice(0, aiIndex), thinkingMessage, ...prev.slice(aiIndex)];
            } else {
              return [...prev, thinkingMessage];
            }
          }
        });
      };

      // 读取流式响应
      for await (const event of generator) {
        if (event.type === 'token') {
          // Token 级流式 - 逐字追加
          aiMessage.content += event.content;
          // 实时更新 AI 消息
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.type) {
              return [...prev.slice(0, -1), {...aiMessage}];
            } else {
              return [...prev, {...aiMessage}];
            }
          });
        } else if (event.type === 'message') {
          // 完整 AI 消息
          aiMessage.content = event.content;
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.type) {
              return [...prev.slice(0, -1), {...aiMessage}];
            } else {
              return [...prev, {...aiMessage}];
            }
          });
        } else if (event.type === 'tool') {
          // 工具调用结果 - 作为独立消息显示
          const toolMessage = {
            type: 'tool',
            name: event.name,
            content: event.content,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, toolMessage]);
        } else if (event.type === 'tool_call') {
          // 工具调用请求 - 更新思考状态并立即显示
          thinkingStateRef.current.toolCalls.push({
            name: event.name,
            args: event.args,
            timestamp: new Date().toISOString(),
          });
          updateThinkingMessage();
        } else if (event.type === 'file_read') {
          // 文件读取事件 - 更新思考状态并立即显示
          thinkingStateRef.current.fileReads.push({
            path: event.path,
            timestamp: new Date().toISOString(),
          });
          updateThinkingMessage();
        } else if (event.type === 'todos') {
          // Todo 列表更新 - 更新思考状态并立即显示
          thinkingStateRef.current.todos = event.content;
          updateThinkingMessage();
        } else if (event.type === 'done') {
          // 完成
          console.log('对话完成');
        } else if (event.type === 'error') {
          // 错误
          const errorMessage = {
            type: 'error',
            content: event.error,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      }

      // 保存会话 ID（如果有）
      if (!conversationId) {
        setConversationId(`conv_${Date.now()}`);
      }

    } catch (error) {
      console.error('发送消息失败:', error);
      const errorMessage = {
        type: 'error',
        content: error.message || '发送失败，请稍后重试',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // 取消请求
  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  };

  // 清空对话
  const handleClear = () => {
    setMessages([]);
    thinkingStateRef.current = { todos: [], toolCalls: [], fileReads: [] };
    setConversationId(null);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>智能入湖平台 - 对话助手</h1>
        <button onClick={handleClear} className="clear-btn">
          清空对话
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>👋 欢迎使用智能入湖平台</h2>
            <p>我可以帮助您完成：</p>
            <ul>
              <li>字段映射 - 将 MySQL 源表字段映射到 DWS 目标表</li>
              <li>元数据查询 - 查询数据库、表结构等信息</li>
              <li>集成任务 - 创建和管理数据集成任务</li>
              <li>调度任务 - 创建和管理定时数据调度任务</li>
            </ul>
            <p>请输入您的问题开始对话！</p>
          </div>
        )}

        {messages.map((message, index) => (
          <Message key={index} message={message} />
        ))}

        {isLoading && (
          <div className="message ai loading">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-footer">
        <ChatInput onSend={handleSend} disabled={isLoading} />
        {isLoading && (
          <button onClick={handleCancel} className="cancel-btn">
            取消
          </button>
        )}
      </div>
    </div>
  );
}

export default Chat;
