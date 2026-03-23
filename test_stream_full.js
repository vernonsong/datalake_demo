#!/usr/bin/env node
/**
 * 测试完整流式功能（Token 流 + Todos + 工具调用）
 */

const API_BASE_URL = 'http://localhost:8000';

async function testStreamChat() {
  console.log('🧪 开始测试完整流式功能...\n');

  try {
    const response = await fetch(`${API_BASE_URL}/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: '你好，请介绍一下自己',
        user_id: 'test_user',
        stream: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let tokenCount = 0;
    let messageCount = 0;
    let toolCallCount = 0;
    let todosCount = 0;

    console.log('📡 开始接收流式数据...\n');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);

          if (data === '[DONE]') {
            console.log('\n✅ 接收完成\n');
            break;
          }

          try {
            const event = JSON.parse(data);

            if (event.type === 'token') {
              tokenCount++;
              process.stdout.write(event.content);
            } else if (event.type === 'message') {
              messageCount++;
              console.log(`\n📝 收到完整消息 #${messageCount}`);
            } else if (event.type === 'tool') {
              console.log(`\n🔧 工具调用结果：${event.name}`);
            } else if (event.type === 'tool_call') {
              toolCallCount++;
              console.log(`\n🛠️ 工具调用请求 #${toolCallCount}: ${event.name}`);
              console.log('   参数:', JSON.stringify(event.args, null, 2));
            } else if (event.type === 'todos') {
              todosCount++;
              console.log(`\n📋 Todo 列表更新 #${todosCount}`);
              event.content.forEach((todo, idx) => {
                const status = todo.status === 'completed' ? '✅' : '⏳';
                const text = todo.text || todo;
                console.log(`   ${status} ${text}`);
              });
            } else if (event.type === 'error') {
              console.error(`\n❌ 错误：${event.error}`);
            }
          } catch (e) {
            console.error('解析失败:', e);
          }
        }
      }
    }

    console.log('\n\n📊 测试统计:');
    console.log(`  - Token 数：${tokenCount}`);
    console.log(`  - 完整消息数：${messageCount}`);
    console.log(`  - 工具调用数：${toolCallCount}`);
    console.log(`  - Todo 列表更新数：${todosCount}`);
    console.log('\n✅ 测试完成！\n');

  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    process.exit(1);
  }
}

testStreamChat();
