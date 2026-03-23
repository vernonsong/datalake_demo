import React, { useState, useRef, useEffect } from 'react';
import { streamChat } from '../api/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Box,
  Group,
  Text,
  ScrollArea,
  TextInput,
  ActionIcon,
  Collapse,
  Card,
  Badge,
  Code,
  ThemeIcon,
  Divider,
  Stack,
  UnstyledButton,
  Center,
  Title,
} from '@mantine/core';
import {
  IconSend,
  IconRobot,
  IconUser,
  IconTool,
  IconFile,
  IconCheck,
  IconClock,
  IconChevronDown,
  IconChevronRight,
  IconBrain,
  IconTrash,
  IconCircleCheckFilled,
  IconCircleDashed,
  IconCircle,
  IconTerminal2,
  IconX
} from '@tabler/icons-react';
import { useDisclosure } from '@mantine/hooks';

// 注入一个简单的旋转动画样式
const spinAnimation = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

/**
 * 思考过程组件（包含所有待办项和全局工具调用）
 */
function ThinkingProcess({ data }) {
  const [isCollapsed, { toggle }] = useDisclosure(false);
  const [isSummaryClosed, { close: closeSummary }] = useDisclosure(false);
  
  if (!data || (!data.todos?.length && !data.globalTools?.length)) {
    return null;
  }

  const completedCount = data.todos?.filter(t => t.status === 'completed').length || 0;
  const totalCount = data.todos?.length || 0;

  return (
    <Box mb="xl" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <style>{spinAnimation}</style>
      {/* 思考过程 Header Button */}
      <UnstyledButton 
        onClick={toggle} 
        bg="#f1f3f5" 
        px="sm" 
        py={4} 
        style={{ borderRadius: 6 }}
        mb="md"
      >
        <Group gap="xs">
          <ThemeIcon variant="transparent" size="xs" c="gray.7">
            {isCollapsed ? <IconChevronRight size={14} /> : <IconChevronDown size={14} />}
          </ThemeIcon>
          <Text size="sm" c="gray.7" fw={500}>思考过程</Text>
        </Group>
      </UnstyledButton>

      <Collapse in={!isCollapsed}>
        <Stack gap="sm" pl="sm" style={{ borderLeft: '1px solid #dee2e6', marginLeft: '6px' }}>
          
          {/* 全局工具调用 (在待办清单之前) */}
          {data.globalTools?.filter(t => t.name !== 'write_todos').map((tool, idx) => {
            let commandText = '';
            if (tool.name === 'execute') {
              commandText = tool.args?.command || '';
            } else if (tool.name === 'read_file') {
              commandText = `cat ${tool.args?.file_path || ''}`;
            } else if (tool.name === 'platform_service') {
              commandText = `curl ${tool.args?.method || 'GET'} ${tool.args?.endpoint || ''}`;
            } else if (tool.name === 'file_read') {
              commandText = `cat ${tool.path || ''}`;
            } else {
              commandText = `${tool.name} ${JSON.stringify(tool.args)}`;
            }

            return (
              <Box 
                key={`global-${idx}`} 
                bg="#f8f9fa" 
                p="md" 
                style={{ borderRadius: 8, fontFamily: 'Menlo, Monaco, Consolas, monospace', border: '1px solid #dee2e6' }}
              >
                <Text size="sm" c="gray.7" style={{ wordBreak: 'break-all' }}>
                  <Text span c="blue.7">$ </Text>
                  {commandText}
                </Text>
              </Box>
            );
          })}

          {data.todos?.map((todo, index) => {
            const isCompleted = todo.status === 'completed';
            const isInProgress = todo.status === 'in_progress';
            const isPending = todo.status === 'pending';
            
            const tools = (data.todoTools?.[index] || []).filter(t => t.todoIndex === index && t.name !== 'write_todos');
            const files = (data.todoFiles?.[index] || []).filter(f => f.todoIndex === index);
            const hasChildren = tools.length > 0 || files.length > 0;
            
            return (
              <Box key={index}>
                <Group wrap="nowrap" gap="sm" align="flex-start">
                  <Box mt={2}>
                    {isCompleted && <IconCircleCheckFilled size={18} color="#22c55e" />}
                    {isInProgress && <IconCircleDashed size={18} color="#adb5bd" style={{ animation: 'spin 2s linear infinite' }} />}
                    {isPending && <IconCircle size={18} color="#ced4da" />}
                  </Box>
                  <Box flex={1}>
                    <Group gap="xs" style={{ cursor: hasChildren ? 'pointer' : 'default' }}>
                      <Text size="sm" c={isPending ? 'gray.5' : 'gray.9'}>
                        {todo.content}
                      </Text>
                      {hasChildren && (
                        <IconChevronDown size={14} color="#adb5bd" />
                      )}
                    </Group>
                    
                    {/* Render tool/file executions */}
                    {hasChildren && (
                      <Stack gap="xs" mt="xs">
                        {tools.map((tool, idx) => {
                          let commandText = '';
                          if (tool.name === 'execute') {
                            commandText = tool.args?.command || '';
                          } else if (tool.name === 'read_file') {
                            commandText = `cat ${tool.args?.file_path || ''}`;
                          } else if (tool.name === 'write_file') {
                            commandText = `echo "..." > ${tool.args?.file_path || ''}`;
                          } else if (tool.name === 'platform_service') {
                            commandText = `curl ${tool.args?.method || 'GET'} ${tool.args?.endpoint || ''}`;
                          } else {
                            commandText = `${tool.name} ${JSON.stringify(tool.args)}`;
                          }
                          
                          return (
                            <Box 
                              key={idx} 
                              bg="#f8f9fa" 
                              p="md" 
                              style={{ borderRadius: 8, fontFamily: 'Menlo, Monaco, Consolas, monospace', border: '1px solid #dee2e6' }}
                            >
                              <Text size="sm" c="gray.7" style={{ wordBreak: 'break-all' }}>
                                <Text span c="blue.7">$ </Text>
                                {commandText}
                              </Text>
                            </Box>
                          );
                        })}
                        {files.map((file, idx) => (
                           <Box 
                             key={`f-${idx}`} 
                             bg="#f8f9fa" 
                             p="md" 
                             style={{ borderRadius: 8, fontFamily: 'Menlo, Monaco, Consolas, monospace', border: '1px solid #dee2e6' }}
                           >
                             <Text size="sm" c="gray.7" style={{ wordBreak: 'break-all' }}>
                               <Text span c="blue.7">$ </Text>
                               cat {file.path}
                             </Text>
                           </Box>
                        ))}
                      </Stack>
                    )}
                  </Box>
                </Group>
              </Box>
            );
          })}
          
          {/* 汇总卡片 - 仅用于嵌套待办 (当前数据结构下暂时隐藏 redundant 卡片) */}
          {totalCount > 0 && !isSummaryClosed && data.todos.some(t => t.sub_todos?.length > 0) && (
            <Card 
              bg="#ffffff" 
              withBorder 
              style={{ borderColor: '#dee2e6', borderRadius: 8, maxWidth: '500px' }}
              mt="sm"
              p={0}
            >
              <Group justify="space-between" p="sm" style={{ borderBottom: '1px solid #dee2e6' }}>
                <Group gap="xs">
                  <IconTerminal2 size={16} color="#adb5bd" />
                  <Text size="sm" c="gray.7" fw={500}>{completedCount}/{totalCount} 已完成</Text>
                </Group>
                <ActionIcon variant="transparent" c="gray.5" size="sm" onClick={closeSummary}>
                  <IconX size={14} />
                </ActionIcon>
              </Group>
              <Stack gap={8} p="sm">
                {data.todos.map((todo, idx) => {
                   const isComp = todo.status === 'completed';
                   const isProg = todo.status === 'in_progress';
                   return (
                     <Group key={idx} gap="xs" wrap="nowrap">
                       {isComp ? (
                         <IconCircleCheckFilled size={14} color="#22c55e" />
                       ) : isProg ? (
                         <IconCircleDashed size={14} color="#adb5bd" style={{ animation: 'spin 2s linear infinite' }} />
                       ) : (
                         <IconCircle size={14} color="#ced4da" />
                       )}
                       <Text 
                         size="sm" 
                         c={isComp ? 'gray.5' : 'gray.8'} 
                         style={{ textDecoration: isComp ? 'line-through' : 'none' }}
                       >
                         {todo.content}
                       </Text>
                     </Group>
                   );
                })}
              </Stack>
            </Card>
          )}

        </Stack>
      </Collapse>
    </Box>
  );
}

/**
 * 聊天消息组件
 */
function Message({ message }) {
  const isUser = message.role === 'user';
  const isTool = message.type === 'tool';
  const isError = message.type === 'error';
  const isThinking = message.type === 'thinking';

  if (isThinking) {
    return (
      <Box mb="lg">
        <ThinkingProcess 
          data={message.thinkingData} 
          isRunning={message.isRunning} 
        />
      </Box>
    );
  }

  return (
    <Group 
      align="flex-start" 
      gap="md" 
      mb="lg"
      style={{ 
        flexDirection: isUser ? 'row-reverse' : 'row',
      }}
    >
      <ThemeIcon 
        variant="light" 
        size="lg" 
        radius="xl"
        color={isUser ? 'blue' : isError ? 'red' : 'green'}
      >
        {isUser ? <IconUser size={20} /> : isTool ? <IconTool size={20} /> : isError ? <IconTrash size={20} /> : <IconRobot size={20} />}
      </ThemeIcon>
      
      <Card 
        padding="md" 
        radius="md" 
        withBorder={!isUser}
        bg={isUser ? 'blue.6' : 'white'}
        style={{
          maxWidth: '80%',
          borderTopRightRadius: isUser ? '0' : 'md',
          borderTopLeftRadius: isUser ? 'md' : '0',
          borderColor: isUser ? 'transparent' : '#dee2e6',
        }}
      >
        {isTool && (
          <Badge size="sm" color="blue" variant="light" mb="xs">
            工具：{message.name || 'unknown'}
          </Badge>
        )}
        <Box 
          c={isError ? 'red.7' : 'gray.9'} 
          style={{ 
            fontSize: '15px', 
            lineHeight: 1.6,
            wordBreak: 'break-word',
          }}
          className="markdown-body"
        >
          {isUser ? (
            <Text style={{ whiteSpace: 'pre-wrap' }}>{message.content}</Text>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </Box>
      </Card>
    </Group>
  );
}

/**
 * 聊天主组件
 */
function Chat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);
  
  // 思考状态管理
  const currentTodosRef = useRef([]);
  const todoToolsRef = useRef({});
  const todoFilesRef = useRef({});
  const todoProcessTextRef = useRef({});
  const globalToolsRef = useRef([]);
  const aiTextRef = useRef('');

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 发送消息
  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const content = inputValue.trim();
    setInputValue('');
    
    const userMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    const currentConversationId = conversationId || `conv_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    if (!conversationId) {
      setConversationId(currentConversationId);
    }

    abortControllerRef.current = new AbortController();

    try {
      const generator = streamChat({
        message: content,
        userId: 'default_user',
        conversationId: currentConversationId,
      });

      let aiMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };
      
      // 重置状态
      currentTodosRef.current = [];
      todoToolsRef.current = {};
      todoFilesRef.current = {};
      todoProcessTextRef.current = {};
      globalToolsRef.current = [];
      aiTextRef.current = '';

      const updateThinkingMessage = (isRunning = true) => {
        const thinkingData = {
          todos: [...currentTodosRef.current],
          todoTools: {...todoToolsRef.current},
          todoFiles: {...todoFilesRef.current},
          todoProcessText: {...todoProcessTextRef.current},
          globalTools: [...globalToolsRef.current],
        };

        const thinkingMessage = {
          type: 'thinking',
          thinkingData,
          isRunning,
          timestamp: new Date().toISOString(),
        };

        setMessages(prev => {
          // 查找最后一个用户消息的索引
          let lastUserIndex = -1;
          for (let i = prev.length - 1; i >= 0; i--) {
            if (prev[i].role === 'user') {
              lastUserIndex = i;
              break;
            }
          }

          // 查找最后一个思考过程消息的索引
          let lastThinkingIndex = -1;
          for (let i = prev.length - 1; i >= 0; i--) {
            if (prev[i].type === 'thinking') {
              lastThinkingIndex = i;
              break;
            }
          }

          // 只有当思考过程在当前轮次（即在最后一个用户消息之后）时才更新
          if (lastThinkingIndex >= 0 && lastThinkingIndex > lastUserIndex) {
            const newMessages = [...prev];
            newMessages[lastThinkingIndex] = thinkingMessage;
            return newMessages;
          } else {
            // 否则，在最后一个助手消息或用户消息之后插入新的思考过程
            let lastAiIndex = -1;
            for (let i = prev.length - 1; i >= 0; i--) {
              if (prev[i].role === 'assistant' && !prev[i].type) {
                lastAiIndex = i;
                break;
              }
            }

            if (lastAiIndex >= 0 && lastAiIndex > lastUserIndex) {
              // 插入在当前轮次的助手消息之后
              return [...prev.slice(0, lastAiIndex + 1), thinkingMessage, ...prev.slice(lastAiIndex + 1)];
            } else {
              // 插入在当前轮次的用户消息之后
              return [...prev.slice(0, lastUserIndex + 1), thinkingMessage, ...prev.slice(lastUserIndex + 1)];
            }
          }
        });
      };

      for await (const event of generator) {
        if (event.type === 'token') {
          aiTextRef.current += event.content;
          aiMessage.content = aiTextRef.current;
          
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.type) {
              return [...prev.slice(0, -1), {...aiMessage}];
            } else {
              return [...prev, {...aiMessage}];
            }
          });
        } else if (event.type === 'message') {
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
          const toolMessage = {
            type: 'tool',
            name: event.name,
            content: event.content,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, toolMessage]);
        } else if (event.type === 'tool_call') {
          const currentTodoCount = currentTodosRef.current.length;
          const toolInfo = {
            name: event.name,
            args: event.args,
            timestamp: new Date().toISOString(),
          };
          
          if (currentTodoCount > 0) {
            const todoIndex = currentTodoCount - 1;
            if (!todoToolsRef.current[todoIndex]) {
              todoToolsRef.current[todoIndex] = [];
            }
            toolInfo.todoIndex = todoIndex;
            todoToolsRef.current[todoIndex].push(toolInfo);
          } else {
            globalToolsRef.current.push(toolInfo);
          }
          
          updateThinkingMessage();
        } else if (event.type === 'file_read') {
          const fileRead = {
            path: event.path,
            timestamp: new Date().toISOString(),
          };
          
          const currentTodoCount = currentTodosRef.current.length;
          if (currentTodoCount > 0) {
            const todoIndex = currentTodoCount - 1;
            if (!todoFilesRef.current[todoIndex]) {
              todoFilesRef.current[todoIndex] = [];
            }
            fileRead.todoIndex = todoIndex;
            todoFilesRef.current[todoIndex].push(fileRead);
          } else {
            globalToolsRef.current.push({
              name: 'file_read',
              path: event.path,
              timestamp: new Date().toISOString(),
            });
          }
          
          updateThinkingMessage();
        } else if (event.type === 'todos') {
          currentTodosRef.current = event.content;
          updateThinkingMessage();
        } else if (event.type === 'done') {
          updateThinkingMessage(false);
        } else if (event.type === 'error') {
          const errorMessage = {
            type: 'error',
            content: event.error,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, errorMessage]);
        }
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

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <Box h="100vh" display="flex" style={{ flexDirection: 'column', backgroundColor: '#f8f9fa' }}>
      {/* Header */}
      <Card 
        padding="md" 
        bg="#ffffff" 
        withBorder={false}
        style={{ borderBottom: '1px solid #dee2e6', borderRadius: 0 }}
      >
        <Group justify="space-between">
          <Group gap="sm">
            <ThemeIcon variant="filled" size="md" radius="sm" color="blue">
              <IconRobot size={18} color="white" />
            </ThemeIcon>
            <Title order={5} c="gray.9" style={{ fontWeight: 600 }}>SOLO Coder</Title>
          </Group>
          <ActionIcon 
            variant="subtle" 
            color="gray" 
            onClick={handleClear}
            title="清空对话"
          >
            <IconTrash size={18} />
          </ActionIcon>
        </Group>
      </Card>

      {/* Messages */}
      <ScrollArea flex={1} px="xl" py="lg">
        <Box style={{ maxWidth: '800px', margin: '0 auto' }}>
          {messages.length === 0 && (
            <Center h="60vh">
              <Card padding="xl" bg="#ffffff" withBorder style={{ maxWidth: '500px', borderColor: '#dee2e6' }}>
                <Stack align="center" gap="md">
                  <ThemeIcon variant="light" size="xl" radius="xl" color="blue">
                    <IconRobot size={32} />
                  </ThemeIcon>
                  <Title order={3} c="gray.9">👋 欢迎使用 SOLO Coder</Title>
                  <Text c="dimmed" ta="center">
                    我可以帮助您完成：
                  </Text>
                  <Stack gap="xs" mt="md">
                    <Text size="sm" c="gray.7">• 字段映射 - 将 MySQL 源表字段映射到 DWS 目标表</Text>
                    <Text size="sm" c="gray.7">• 元数据查询 - 查询数据库、表结构等信息</Text>
                    <Text size="sm" c="gray.7">• 集成任务 - 创建和管理数据集成任务</Text>
                    <Text size="sm" c="gray.7">• 调度任务 - 创建和管理定时数据调度任务</Text>
                  </Stack>
                </Stack>
              </Card>
            </Center>
          )}

          {messages.map((message, index) => (
            <Message key={index} message={message} />
          ))}

          {isLoading && !messages.some(m => m.type === 'thinking' && m.isRunning) && (
            <Group align="flex-start" gap="md" mb="lg">
              <ThemeIcon variant="light" size="lg" radius="xl" color="blue">
                <IconRobot size={20} />
              </ThemeIcon>
              <Text size="sm" c="dimmed" mt={8}>思考中...</Text>
            </Group>
          )}

          <div ref={messagesEndRef} />
        </Box>
      </ScrollArea>

      {/* Input */}
      <Box p="md" bg="#ffffff" style={{ borderTop: '1px solid #dee2e6' }}>
        <Box style={{ maxWidth: '800px', margin: '0 auto' }}>
          <TextInput
            value={inputValue}
            onChange={(e) => setInputValue(e.currentTarget.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="输入消息... (按 Enter 发送，Shift+Enter 换行)"
            disabled={isLoading}
            size="md"
            radius="md"
            styles={{
              input: {
                backgroundColor: '#ffffff',
                border: '1px solid #dee2e6',
                color: '#1a1b1e',
                '&:focus': {
                  borderColor: '#228be6',
                }
              }
            }}
            rightSection={
              <Group gap="xs" mr="xs">
                {isLoading && (
                  <ActionIcon
                    onClick={handleCancel}
                    variant="subtle"
                    color="red"
                    size="sm"
                  >
                    <IconX size={16} />
                  </ActionIcon>
                )}
                <ActionIcon 
                  onClick={handleSend} 
                  disabled={isLoading || !inputValue.trim()}
                  variant="filled" 
                  color="blue" 
                  size="sm"
                >
                  <IconSend size={16} />
                </ActionIcon>
              </Group>
            }
          />
        </Box>
      </Box>
    </Box>
  );
}

export default Chat;
