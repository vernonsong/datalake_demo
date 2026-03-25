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
  IconX,
  IconPaperclip
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
 * 批量处理进度组件
 */
function BatchProgress({ data }) {
  const [isCollapsed, { toggle }] = useDisclosure(false);
  
  if (!data || !data.items || data.items.length === 0) {
    return null;
  }

  const { total = 0, items = [] } = data;
  const processedCount = items.filter(item => 
    item.status === 'success' || item.status === 'completed' || item.status === 'failed'
  ).length;
  const successCount = items.filter(item => 
    item.status === 'success' || item.status === 'completed'
  ).length;
  const failedCount = items.filter(item => item.status === 'failed').length;
  const processingItem = items.find(item => item.status === 'processing');
  
  const percentage = total > 0 ? Math.round((processedCount / total) * 100) : 0;

  return (
    <Box mb="xl" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* 批量处理进度 Header */}
      <Card 
        padding="md" 
        bg="#ffffff" 
        withBorder
        style={{ borderColor: '#228be6', borderRadius: 8 }}
      >
        <UnstyledButton onClick={toggle} style={{ width: '100%' }}>
          <Group justify="space-between" mb={isCollapsed ? 0 : 'sm'}>
            <Group gap="xs">
              <ThemeIcon variant="light" size="sm" color="blue">
                {isCollapsed ? <IconChevronRight size={14} /> : <IconChevronDown size={14} />}
              </ThemeIcon>
              <Text size="sm" fw={600} c="blue.7">
                📦 批量处理进度
              </Text>
              <Badge size="sm" color={processedCount === total ? 'green' : 'blue'}>
                {processedCount}/{total}
              </Badge>
              <Text size="xs" c="dimmed">
                {percentage}%
              </Text>
            </Group>
            <Group gap="xs">
              {successCount > 0 && (
                <Badge size="sm" color="green" variant="light">
                  ✓ {successCount}
                </Badge>
              )}
              {failedCount > 0 && (
                <Badge size="sm" color="red" variant="light">
                  ✗ {failedCount}
                </Badge>
              )}
            </Group>
          </Group>
        </UnstyledButton>

        <Collapse in={!isCollapsed}>
          <Stack gap="xs" mt="sm">
            {items.map((item, index) => {
              const isPending = item.status === 'pending';
              const isProcessing = item.status === 'processing';
              const isSuccess = item.status === 'success' || item.status === 'completed';
              const isFailed = item.status === 'failed';
              
              let icon;
              let color;
              if (isPending) {
                icon = <IconCircle size={16} />;
                color = 'gray.5';
              } else if (isProcessing) {
                icon = <IconCircleDashed size={16} style={{ animation: 'spin 2s linear infinite' }} />;
                color = 'blue.6';
              } else if (isSuccess) {
                icon = <IconCircleCheckFilled size={16} />;
                color = 'green.6';
              } else if (isFailed) {
                icon = <IconX size={16} />;
                color = 'red.6';
              }

              return (
                <Box 
                  key={index}
                  p="sm"
                  bg={isProcessing ? '#f0f7ff' : '#f8f9fa'}
                  style={{ 
                    borderRadius: 6,
                    border: isProcessing ? '1px solid #228be6' : '1px solid #dee2e6'
                  }}
                >
                  <Group gap="sm" wrap="nowrap">
                    <ThemeIcon variant="transparent" size="sm" c={color}>
                      {icon}
                    </ThemeIcon>
                    <Box flex={1}>
                      <Text size="sm" fw={500} c={isPending ? 'gray.6' : 'gray.9'}>
                        {item.item?.单号 || `项目 ${item.index}`}
                      </Text>
                      {item.message && (
                        <Text size="xs" c="dimmed" lineClamp={2} mt={4}>
                          {item.message}
                        </Text>
                      )}
                      {item.error && (
                        <Text size="xs" c="red.6" lineClamp={2} mt={4}>
                          错误: {item.error}
                        </Text>
                      )}
                    </Box>
                  </Group>
                </Box>
              );
            })}
          </Stack>
        </Collapse>
      </Card>
    </Box>
  );
}

/**
 * 思考过程组件（包含所有待办项和全局工具调用）
 */
function ThinkingProcess({ data }) {
  const [isCollapsed, { toggle }] = useDisclosure(false);
  const [isSummaryClosed, { close: closeSummary }] = useDisclosure(false);
  
  if (!data || (!data.todos?.length && !data.globalTools?.length && !data.preludeTimeline?.length)) {
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

          {data.preludeTimeline?.length > 0 && (
            <Stack gap="xs">
              {data.preludeTimeline.map((item, idx) => {
                if (item.kind === 'text') {
                  const text = (item.content || '').trim();
                  if (!text) {
                    return null;
                  }
                  return (
                    <Box
                      key={`prelude-text-${idx}`}
                      bg="#ffffff"
                      p="md"
                      style={{ borderRadius: 8, border: '1px solid #dee2e6' }}
                    >
                      <Box
                        c="gray.8"
                        style={{
                          fontSize: '14px',
                          lineHeight: 1.6,
                          wordBreak: 'break-word',
                        }}
                        className="markdown-body"
                      >
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {text}
                        </ReactMarkdown>
                      </Box>
                    </Box>
                  );
                }

                if (item.kind === 'tool') {
                  const tool = item.tool;
                  let commandText = '';
                  if (tool?.name === 'execute') {
                    commandText = tool.args?.command || '';
                  } else if (tool?.name === 'read_file') {
                    commandText = `cat ${tool.args?.file_path || ''}`;
                  } else if (tool?.name === 'platform_service') {
                    commandText = `curl ${tool.args?.method || 'GET'} ${tool.args?.endpoint || ''}`;
                  } else {
                    commandText = `${tool?.name} ${JSON.stringify(tool?.args)}`;
                  }

                  return (
                    <Box
                      key={`prelude-tool-${idx}`}
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
                }

                if (item.kind === 'file') {
                  const file = item.file;
                  return (
                    <Box
                      key={`prelude-file-${idx}`}
                      bg="#f8f9fa"
                      p="md"
                      style={{ borderRadius: 8, fontFamily: 'Menlo, Monaco, Consolas, monospace', border: '1px solid #dee2e6' }}
                    >
                      <Text size="sm" c="gray.7" style={{ wordBreak: 'break-all' }}>
                        <Text span c="blue.7">$ </Text>
                        cat {file?.path}
                      </Text>
                    </Box>
                  );
                }

                return null;
              })}
            </Stack>
          )}
          
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
            const processText = (data.todoProcessText?.[index] || '').trim();
            const timeline = data.todoTimeline?.[index] || [];
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
                    
                    {/* Render executions timeline */}
                    {((timeline && timeline.length > 0) || processText || hasChildren) && (
                      <Stack gap="xs" mt="xs">
                        {(timeline && timeline.length > 0) ? (
                          timeline.map((item, idx) => {
                            if (item.kind === 'text') {
                              const text = (item.content || '').trim();
                              if (!text) {
                                return null;
                              }
                              return (
                                <Box
                                  key={`tl-text-${idx}`}
                                  bg="#ffffff"
                                  p="md"
                                  style={{ borderRadius: 8, border: '1px solid #dee2e6' }}
                                >
                                  <Box
                                    c="gray.8"
                                    style={{
                                      fontSize: '14px',
                                      lineHeight: 1.6,
                                      wordBreak: 'break-word',
                                    }}
                                    className="markdown-body"
                                  >
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                      {text}
                                    </ReactMarkdown>
                                  </Box>
                                </Box>
                              );
                            }

                            if (item.kind === 'tool') {
                              const tool = item.tool;
                              let commandText = '';
                              if (tool?.name === 'execute') {
                                commandText = tool.args?.command || '';
                              } else if (tool?.name === 'read_file') {
                                commandText = `cat ${tool.args?.file_path || ''}`;
                              } else if (tool?.name === 'write_file') {
                                commandText = `echo "..." > ${tool.args?.file_path || ''}`;
                              } else if (tool?.name === 'platform_service') {
                                commandText = `curl ${tool.args?.method || 'GET'} ${tool.args?.endpoint || ''}`;
                              } else {
                                commandText = `${tool?.name} ${JSON.stringify(tool?.args)}`;
                              }

                              return (
                                <Box
                                  key={`tl-tool-${idx}`}
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
                            }

                            if (item.kind === 'file') {
                              const file = item.file;
                              return (
                                <Box
                                  key={`tl-file-${idx}`}
                                  bg="#f8f9fa"
                                  p="md"
                                  style={{ borderRadius: 8, fontFamily: 'Menlo, Monaco, Consolas, monospace', border: '1px solid #dee2e6' }}
                                >
                                  <Text size="sm" c="gray.7" style={{ wordBreak: 'break-all' }}>
                                    <Text span c="blue.7">$ </Text>
                                    cat {file?.path}
                                  </Text>
                                </Box>
                              );
                            }

                            return null;
                          })
                        ) : (
                          <>
                            {!!processText && (
                              <Box
                                bg="#ffffff"
                                p="md"
                                style={{ borderRadius: 8, border: '1px solid #dee2e6' }}
                              >
                                <Box
                                  c="gray.8"
                                  style={{
                                    fontSize: '14px',
                                    lineHeight: 1.6,
                                    wordBreak: 'break-word',
                                  }}
                                  className="markdown-body"
                                >
                                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {processText}
                                  </ReactMarkdown>
                                </Box>
                              </Box>
                            )}
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
                          </>
                        )}
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
  const isBatchProgress = message.type === 'batch_progress';

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

  if (isBatchProgress) {
    return (
      <Box mb="lg">
        <BatchProgress data={message.batchData} />
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
  const [selectedFiles, setSelectedFiles] = useState([]);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);
  
  // 思考状态管理
  const currentTodosRef = useRef([]);
  const todoToolsRef = useRef({});
  const todoFilesRef = useRef({});
  const todoProcessTextRef = useRef({});
  const todoTimelineRef = useRef({});
  const globalToolsRef = useRef([]);
  const aiTextRef = useRef('');
  const activeTodoIndexRef = useRef(null);
  const pendingBeforeTodosTimelineRef = useRef([]);
  const finalAnswerTextRef = useRef('');
  const hasTodosStartedRef = useRef(false);
  const lastTodoIndexRef = useRef(null);
  const phaseRef = useRef(null);
  const thinkingUpdateTimerRef = useRef(null);
  
  // 批量处理进度状态管理
  const batchProgressRef = useRef(null);
  
  // 中断状态管理
  const [pendingInterrupt, setPendingInterrupt] = useState(null); // { interrupt_info, thread_id, tool_call }
  const lastToolCallRef = useRef(null); // 保存最后的工具调用

  const getActiveTodoIndex = (todos) => {
    if (!Array.isArray(todos) || todos.length === 0) {
      return null;
    }
    if (todos.every((t) => t?.status === 'completed')) {
      return null;
    }
    const inProgressIndex = todos.findIndex((t) => t?.status === 'in_progress');
    if (inProgressIndex !== -1) {
      return inProgressIndex;
    }
    const pendingIndex = todos.findIndex((t) => t?.status === 'pending');
    if (pendingIndex !== -1) {
      return pendingIndex;
    }
    return todos.length - 1;
  };

  const ensureTodoTimeline = (todoIndex) => {
    if (!todoTimelineRef.current[todoIndex]) {
      todoTimelineRef.current[todoIndex] = [];
    }
    return todoTimelineRef.current[todoIndex];
  };

  const appendTimelineText = (timeline, text) => {
    if (!text) {
      return;
    }
    const last = timeline[timeline.length - 1];
    if (last && last.kind === 'text') {
      last.content += text;
      return;
    }
    timeline.push({ kind: 'text', content: text, timestamp: new Date().toISOString() });
  };

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = [];
    const MAX_SIZE = 10 * 1024 * 1024; // 10MB
    const ALLOWED_EXTS = ['.xlsx', '.xls', '.csv'];

    files.forEach(file => {
      const ext = '.' + file.name.split('.').pop().toLowerCase();
      if (!ALLOWED_EXTS.includes(ext)) {
        alert(`不支持的文件类型: ${file.name}\n仅支持 .xlsx, .xls, .csv`);
        return;
      }
      if (file.size > MAX_SIZE) {
        alert(`文件过大 (超过 10MB): ${file.name}`);
        return;
      }
      validFiles.push(file);
    });

    if (validFiles.length > 0) {
      if (selectedFiles.length + validFiles.length > 5) {
        alert('一次最多上传 5 个文件');
        return;
      }
      setSelectedFiles(prev => [...prev, ...validFiles]);
    }
    
    // 清空 input，允许重复选择同名文件
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // 恢复中断的执行
  const handleResumeExecution = async (decision) => {
    if (!pendingInterrupt) return;
    
    try {
      const response = await fetch('http://localhost:8000/chat/resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          thread_id: pendingInterrupt.thread_id,
          decision: decision
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // 添加结果消息
        const resultMessage = {
          role: 'assistant',
          content: result.message,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, resultMessage]);
      } else {
        // 显示错误
        const errorMessage = {
          type: 'error',
          content: result.message || '操作失败',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Resume execution failed:', error);
      const errorMessage = {
        type: 'error',
        content: `恢复执行失败: ${error.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      // 清除中断状态
      setPendingInterrupt(null);
    }
  };

  // 发送消息
  const handleSend = async () => {
    if ((!inputValue.trim() && selectedFiles.length === 0) || isLoading) return;

    const content = inputValue.trim();
    const filesToSend = [...selectedFiles];
    
    setInputValue('');
    setSelectedFiles([]);
    
    let displayContent = content;
    if (filesToSend.length > 0) {
        const fileNames = filesToSend.map(f => `[文件] ${f.name}`).join('\n');
        displayContent = content ? `${content}\n${fileNames}` : fileNames;
    }

    const userMessage = {
      role: 'user',
      content: displayContent,
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
        message: content || ' ', // 确保 message 不为空
        userId: 'default_user',
        conversationId: currentConversationId,
        files: filesToSend,
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
      todoTimelineRef.current = {};
      globalToolsRef.current = [];
      aiTextRef.current = '';
      activeTodoIndexRef.current = null;
      pendingBeforeTodosTimelineRef.current = [];
      finalAnswerTextRef.current = '';
      hasTodosStartedRef.current = false;
      lastTodoIndexRef.current = null;
      phaseRef.current = null;
      batchProgressRef.current = null;

      const updateThinkingMessage = (isRunning = true) => {
        const thinkingData = {
          todos: [...currentTodosRef.current],
          todoTools: {...todoToolsRef.current},
          todoFiles: {...todoFilesRef.current},
          todoProcessText: {...todoProcessTextRef.current},
          todoTimeline: {...todoTimelineRef.current},
          globalTools: [...globalToolsRef.current],
          preludeTimeline: [...pendingBeforeTodosTimelineRef.current],
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

      const scheduleThinkingUpdate = (isRunning = true) => {
        if (thinkingUpdateTimerRef.current) {
          return;
        }
        thinkingUpdateTimerRef.current = setTimeout(() => {
          thinkingUpdateTimerRef.current = null;
          updateThinkingMessage(isRunning);
        }, 50);
      };

      for await (const event of generator) {
        if (event.type === 'phase') {
          phaseRef.current = event.phase || null;
          if (phaseRef.current === 'final') {
            activeTodoIndexRef.current = null;
          }
          updateThinkingMessage();
          continue;
        }

        if (event.type === 'token') {
          const computedActive = getActiveTodoIndex(currentTodosRef.current);
          const resolvedTodoIndex = activeTodoIndexRef.current ?? computedActive;
          const isFinalPhase = phaseRef.current === 'final' || (hasTodosStartedRef.current && computedActive === null);
          const isThinkingPhase = phaseRef.current === 'thinking' || (hasTodosStartedRef.current && !isFinalPhase);

          if (isThinkingPhase) {
            const targetIndex = resolvedTodoIndex ?? lastTodoIndexRef.current;
            if (targetIndex !== null) {
              const timeline = ensureTodoTimeline(targetIndex);
              appendTimelineText(timeline, event.content);
              scheduleThinkingUpdate();
            }
            continue;
          }

          if (isFinalPhase || !hasTodosStartedRef.current) {
            finalAnswerTextRef.current += event.content;
            aiMessage.content = finalAnswerTextRef.current;
            setMessages((prev) => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.type) {
                return [...prev.slice(0, -1), { ...aiMessage }];
              }
              return [...prev, { ...aiMessage }];
            });
            continue;
          }
        } else if (event.type === 'message') {
          const isFinalPhase = phaseRef.current === 'final' || (hasTodosStartedRef.current && getActiveTodoIndex(currentTodosRef.current) === null);
          if (!hasTodosStartedRef.current || isFinalPhase) {
            aiMessage.content = event.content;
            setMessages(prev => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.type) {
                return [...prev.slice(0, -1), { ...aiMessage }];
              } else {
                return [...prev, { ...aiMessage }];
              }
            });
          }
        } else if (event.type === 'tool') {
          const toolMessage = {
            type: 'tool',
            name: event.name,
            content: event.content,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, toolMessage]);
        } else if (event.type === 'tool_call') {
          const toolInfo = {
            name: event.name,
            args: event.args,
            timestamp: new Date().toISOString(),
          };
          
          // 保存最后的工具调用，用于中断时显示
          lastToolCallRef.current = toolInfo;

          const computedActive = getActiveTodoIndex(currentTodosRef.current);
          const resolvedTodoIndex = activeTodoIndexRef.current ?? computedActive;
          const targetIndex = resolvedTodoIndex ?? (hasTodosStartedRef.current ? lastTodoIndexRef.current : null);

          if (targetIndex !== null) {
            const todoIndex = targetIndex;
            if (!todoToolsRef.current[todoIndex]) {
              todoToolsRef.current[todoIndex] = [];
            }
            toolInfo.todoIndex = todoIndex;
            todoToolsRef.current[todoIndex].push(toolInfo);

            const timeline = ensureTodoTimeline(todoIndex);
            timeline.push({ kind: 'tool', tool: toolInfo, timestamp: toolInfo.timestamp });
          } else {
            pendingBeforeTodosTimelineRef.current.push({ kind: 'tool', tool: toolInfo, timestamp: toolInfo.timestamp });
          }
          
          updateThinkingMessage();
        } else if (event.type === 'file_read') {
          const fileRead = {
            path: event.path,
            timestamp: new Date().toISOString(),
          };
          
          const computedActive = getActiveTodoIndex(currentTodosRef.current);
          const resolvedTodoIndex = activeTodoIndexRef.current ?? computedActive;
          const targetIndex = resolvedTodoIndex ?? (hasTodosStartedRef.current ? lastTodoIndexRef.current : null);

          if (targetIndex !== null) {
            const todoIndex = targetIndex;
            if (!todoFilesRef.current[todoIndex]) {
              todoFilesRef.current[todoIndex] = [];
            }
            fileRead.todoIndex = todoIndex;
            todoFilesRef.current[todoIndex].push(fileRead);

            const timeline = ensureTodoTimeline(todoIndex);
            timeline.push({ kind: 'file', file: fileRead, timestamp: fileRead.timestamp });
          } else {
            pendingBeforeTodosTimelineRef.current.push({ kind: 'file', file: fileRead, timestamp: fileRead.timestamp });
          }
          
          updateThinkingMessage();
        } else if (event.type === 'todos') {
          const previousTodoCount = currentTodosRef.current.length;
          currentTodosRef.current = event.content;
          activeTodoIndexRef.current = getActiveTodoIndex(event.content);

          if (!hasTodosStartedRef.current && event.content?.length > 0) {
            hasTodosStartedRef.current = true;
          }
          if (event.content?.length > 0) {
            const idx = activeTodoIndexRef.current ?? getActiveTodoIndex(event.content) ?? (event.content.length - 1);
            lastTodoIndexRef.current = idx;
          }

          if (previousTodoCount === 0 && event.content?.length > 0) {
            const flushIndex = activeTodoIndexRef.current ?? 0;

            if (pendingBeforeTodosTimelineRef.current.length > 0) {
              const timeline = ensureTodoTimeline(flushIndex);
              timeline.push(...pendingBeforeTodosTimelineRef.current);
              pendingBeforeTodosTimelineRef.current = [];
            }
          }
          updateThinkingMessage();
        } else if (event.type === 'batch_progress') {
          // 批量处理进度事件
          const progressData = event.data || {};
          
          if (progressData.type === 'batch_start') {
            // 初始化批量处理进度
            batchProgressRef.current = {
              total: progressData.total,
              items: Array.from({ length: progressData.total }, (_, i) => ({
                index: i + 1,
                status: 'pending',
                item: null
              }))
            };
          } else if (progressData.type === 'item_start') {
            // 订单开始处理
            if (batchProgressRef.current) {
              const itemIndex = progressData.index - 1;
              if (itemIndex >= 0 && itemIndex < batchProgressRef.current.items.length) {
                batchProgressRef.current.items[itemIndex] = {
                  index: progressData.index,
                  status: 'processing',
                  item: progressData.item
                };
              }
            }
          } else if (progressData.type === 'item_complete') {
            // 订单处理完成
            if (batchProgressRef.current) {
              const itemIndex = progressData.index - 1;
              if (itemIndex >= 0 && itemIndex < batchProgressRef.current.items.length) {
                batchProgressRef.current.items[itemIndex] = {
                  index: progressData.index,
                  status: progressData.status,
                  item: progressData.item,
                  message: progressData.message
                };
              }
            }
          } else if (progressData.type === 'item_error') {
            // 订单处理失败
            if (batchProgressRef.current) {
              const itemIndex = progressData.index - 1;
              if (itemIndex >= 0 && itemIndex < batchProgressRef.current.items.length) {
                batchProgressRef.current.items[itemIndex] = {
                  index: progressData.index,
                  status: 'failed',
                  item: progressData.item,
                  error: progressData.error
                };
              }
            }
          }
          
          // 更新批量处理进度消息
          if (batchProgressRef.current) {
            setMessages(prev => {
              // 查找最后一个用户消息的索引
              let lastUserIndex = -1;
              for (let i = prev.length - 1; i >= 0; i--) {
                if (prev[i].role === 'user') {
                  lastUserIndex = i;
                  break;
                }
              }

              // 查找最后一个批量处理进度消息的索引
              let lastBatchProgressIndex = -1;
              for (let i = prev.length - 1; i >= 0; i--) {
                if (prev[i].type === 'batch_progress') {
                  lastBatchProgressIndex = i;
                  break;
                }
              }

              const batchProgressMessage = {
                type: 'batch_progress',
                batchData: { ...batchProgressRef.current },
                timestamp: new Date().toISOString(),
              };

              // 如果已存在批量处理进度消息且在当前轮次，更新它
              if (lastBatchProgressIndex >= 0 && lastBatchProgressIndex > lastUserIndex) {
                const newMessages = [...prev];
                newMessages[lastBatchProgressIndex] = batchProgressMessage;
                return newMessages;
              } else {
                // 否则，在最后一个用户消息之后插入新的批量处理进度消息
                return [...prev.slice(0, lastUserIndex + 1), batchProgressMessage, ...prev.slice(lastUserIndex + 1)];
              }
            });
          }
        } else if (event.type === 'interrupt') {
          // 中断事件 - 需要用户确认
          const { interrupt_info, thread_id } = event;
          
          // 保存中断信息和最后的工具调用
          setPendingInterrupt({
            interrupt_info,
            thread_id,
            tool_call: lastToolCallRef.current // 保存最后的工具调用信息
          });
          
          // 停止思考动画
          if (thinkingUpdateTimerRef.current) {
            clearTimeout(thinkingUpdateTimerRef.current);
            thinkingUpdateTimerRef.current = null;
          }
          updateThinkingMessage(false);
          
        } else if (event.type === 'done') {
          if (thinkingUpdateTimerRef.current) {
            clearTimeout(thinkingUpdateTimerRef.current);
            thinkingUpdateTimerRef.current = null;
          }
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
      {selectedFiles.length > 0 && (
        <Box px="md" pt="xs" pb={0} bg="#ffffff" style={{ borderTop: '1px solid #dee2e6' }}>
            <Box style={{ maxWidth: '800px', margin: '0 auto' }}>
                <Group gap="xs">
                    {selectedFiles.map((file, index) => (
                        <Badge 
                            key={index} 
                            variant="light" 
                            color="blue" 
                            rightSection={
                                <ActionIcon size="xs" color="blue" variant="transparent" onClick={() => handleRemoveFile(index)}>
                                    <IconX size={12} />
                                </ActionIcon>
                            }
                        >
                            {file.name}
                        </Badge>
                    ))}
                </Group>
            </Box>
        </Box>
      )}
      <Box p="md" bg="#ffffff" style={{ borderTop: selectedFiles.length > 0 ? 'none' : '1px solid #dee2e6' }}>
        <Box style={{ maxWidth: '800px', margin: '0 auto' }}>
          <input
            type="file"
            multiple
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileSelect}
            accept=".xlsx,.xls,.csv"
          />
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
                <ActionIcon 
                    onClick={() => fileInputRef.current?.click()} 
                    variant="subtle" 
                    color="gray" 
                    size="sm"
                    disabled={isLoading}
                    title="上传 Excel/CSV 文件"
                >
                    <IconPaperclip size={16} />
                </ActionIcon>
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
                  disabled={isLoading || (!inputValue.trim() && selectedFiles.length === 0)}
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

      {/* 中断确认对话框 */}
      {pendingInterrupt && (
        <Box
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <Card
            padding="xl"
            bg="#ffffff"
            withBorder
            style={{
              maxWidth: '600px',
              width: '90%',
              borderColor: '#228be6',
              borderWidth: 2,
            }}
          >
            <Stack gap="md">
              <Group gap="sm">
                <ThemeIcon variant="light" size="lg" color="orange">
                  <IconBrain size={24} />
                </ThemeIcon>
                <Title order={4} c="gray.9">⚠️ 操作需要确认</Title>
              </Group>

              <Divider />

              {pendingInterrupt.tool_call && (
                <Box>
                  <Text size="sm" fw={600} c="gray.7" mb="xs">
                    工具调用:
                  </Text>
                  <Card padding="sm" bg="#f8f9fa" withBorder>
                    <Stack gap="xs">
                      <Group gap="xs">
                        <IconTool size={16} />
                        <Text size="sm" fw={600}>{pendingInterrupt.tool_call.name}</Text>
                      </Group>
                      <Code block style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}>
                        {JSON.stringify(pendingInterrupt.tool_call.args, null, 2)}
                      </Code>
                    </Stack>
                  </Card>
                </Box>
              )}

              <Text size="sm" c="dimmed">
                此操作可能会修改系统数据，请确认是否继续执行。
              </Text>

              <Group justify="flex-end" gap="sm" mt="md">
                <ActionIcon
                  variant="subtle"
                  color="gray"
                  size="lg"
                  onClick={() => handleResumeExecution('reject')}
                >
                  <IconX size={20} />
                </ActionIcon>
                <ActionIcon
                  variant="filled"
                  color="blue"
                  size="lg"
                  onClick={() => handleResumeExecution('approve')}
                >
                  <IconCheck size={20} />
                </ActionIcon>
              </Group>
            </Stack>
          </Card>
        </Box>
      )}
    </Box>
  );
}

export default Chat;
