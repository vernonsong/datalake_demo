#!/usr/bin/env node
/**
 * 前端功能测试脚本
 * 测试流式对话接口是否正常工作
 */

const API_BASE_URL = 'http://localhost:8000';

async function testStreamChat() {
  console.log('🧪 开始测试流式对话接口...\n');

  try {
    // 测试 1: 检查后端服务是否可用
    console.log('📌 测试 1: 检查后端服务...');
    const healthCheck = await fetch(`${API_BASE_URL}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: '你好',
        user_id: 'test',
        stream: false,
      }),
    });

    if (!healthCheck.ok) {
      throw new Error(`后端服务不可用，状态码：${healthCheck.status}`);
    }
    console.log('✅ 后端服务正常\n');

    // 测试 2: 测试流式接口
    console.log('📌 测试 2: 测试流式对话...');
    const response = await fetch(`${API_BASE_URL}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: '帮我生成 order_info 表到 dw_order 表的字段映射，单号是 ORDER012',
        user_id: 'test_user',
        stream: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`请求失败，状态码：${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let messageCount = 0;
    let hasToolMessage = false;
    let hasAiMessage = false;
    let hasDoneMessage = false;

    console.log('📡 接收流式消息:\n');

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);

          if (data === '[DONE]') {
            console.log(`[DONE] ✅ 处理完成\n`);
            hasDoneMessage = true;
            messageCount++;
            continue;
          }

          try {
            const parsed = JSON.parse(data);
            messageCount++;

            if (parsed.type === 'ai') {
              hasAiMessage = true;
              console.log(`[${messageCount}] 🤖 AI: ${parsed.content.substring(0, 50)}...`);
            } else if (parsed.type === 'tool') {
              hasToolMessage = true;
              console.log(`[${messageCount}] 🔧 工具 [${parsed.name}]: ${parsed.content.substring(0, 50)}...`);
            } else if (parsed.type === 'error') {
              console.log(`[${messageCount}] ❌ 错误：${parsed.error}`);
            }
          } catch (e) {
            console.error('解析失败:', e, '原始数据:', data);
          }
        }
      }
    }

    // 验证结果
    console.log('\n📊 测试结果:\n');
    console.log(`  - 总消息数：${messageCount}`);
    console.log(`  - AI 消息：${hasAiMessage ? '✅' : '❌'}`);
    console.log(`  - 工具消息：${hasToolMessage ? '✅' : '❌'}`);
    console.log(`  - 完成消息：${hasDoneMessage ? '✅' : '❌'}`);

    if (hasAiMessage && hasToolMessage && hasDoneMessage) {
      console.log('\n✅ 所有测试通过！流式对话功能正常。\n');
      return true;
    } else {
      console.log('\n❌ 测试失败！某些消息类型缺失。\n');
      return false;
    }

  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    return false;
  }
}

// 运行测试
testStreamChat().then(success => {
  process.exit(success ? 0 : 1);
});
