import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 流式对话 API - 支持 token 流、todos、工具调用
 * @param {Object} params - 请求参数
 * @param {string} params.message - 用户消息
 * @param {string} params.userId - 用户 ID
 * @param {string} params.conversationId - 会话 ID（可选）
 * @returns {AsyncGenerator} 返回异步生成器，用于流式读取响应
 * 
 * 支持的事件类型：
 * - {type: "token", content: "文本"}  # token 级流式
 * - {type: "message", role: "assistant", content: "完整消息"}
 * - {type: "tool", name: "工具名", content: "详情"}
 * - {type: "tool_call", name: "工具名", args: {...}}
 * - {type: "todos", content: [...]}  # todo 列表
 * - {type: "done", content: "完成"}
 * - {type: "error", error: "错误信息"}
 */
export async function* streamChat({ message, userId = 'default_user', conversationId = null }) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        user_id: userId,
        conversation_id: conversationId,
        stream: true,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || errorData.message || '请求失败');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      buffer = buffer.replace(/\r\n/g, '\n');

      let sepIndex;
      while ((sepIndex = buffer.indexOf('\n\n')) !== -1) {
        const rawEvent = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);

        const lines = rawEvent.split('\n');
        const dataLines = lines
          .filter((l) => l.startsWith('data:'))
          .map((l) => l.replace(/^data:\s?/, ''));

        if (dataLines.length === 0) continue;

        const data = dataLines.join('\n');
        if (data === '[DONE]') {
          yield { type: 'done', content: '处理完成' };
          return;
        }

        try {
          const parsed = JSON.parse(data);
          if (parsed.type === 'token') {
            yield { type: 'token', content: parsed.content };
          } else if (parsed.type === 'message') {
            yield { type: 'message', role: parsed.role, content: parsed.content };
          } else if (parsed.type === 'tool') {
            yield { type: 'tool', name: parsed.name, content: parsed.content };
          } else if (parsed.type === 'tool_call') {
            yield { type: 'tool_call', name: parsed.name, args: parsed.args };
          } else if (parsed.type === 'todos') {
            yield { type: 'todos', content: parsed.content };
          } else if (parsed.type === 'phase') {
            yield { type: 'phase', phase: parsed.phase };
          } else if (parsed.type === 'done') {
            yield { type: 'done', content: parsed.content };
          } else if (parsed.type === 'error') {
            yield { type: 'error', error: parsed.error };
          } else {
            yield parsed;
          }
        } catch (e) {
          console.error('解析响应数据失败:', e, '原始数据:', data);
        }
      }
    }
  } catch (error) {
    console.error('流式对话错误:', error);
    yield { 
      type: 'error', 
      error: error.message || '网络错误，请稍后重试' 
    };
  }
}

/**
 * 普通对话 API（非流式）
 * @param {Object} params - 请求参数
 * @param {string} params.message - 用户消息
 * @param {string} params.userId - 用户 ID
 * @param {string} params.conversationId - 会话 ID（可选）
 * @returns {Promise<Object>} 返回对话响应
 */
export async function chat({ message, userId = 'default_user', conversationId = null }) {
  try {
    const response = await apiClient.post('/chat/', {
      message,
      user_id: userId,
      conversation_id: conversationId,
      stream: false,
    });

    return response.data;
  } catch (error) {
    console.error('对话 API 错误:', error);
    throw error;
  }
}

export default apiClient;
