import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { MessageOutlined, ThunderboltOutlined } from '@ant-design/icons';
import Chat from './components/Chat';
import WorkflowDemo from './pages/WorkflowDemo';
import './App.css';

const { Header, Content } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ color: 'white', fontSize: 20, fontWeight: 'bold', marginRight: 40 }}>
            智能入湖平台
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            defaultSelectedKeys={['chat']}
            style={{ flex: 1, minWidth: 0 }}
          >
            <Menu.Item key="chat" icon={<MessageOutlined />}>
              <Link to="/">对话</Link>
            </Menu.Item>
            <Menu.Item key="workflow" icon={<ThunderboltOutlined />}>
              <Link to="/workflow">工作流演示</Link>
            </Menu.Item>
          </Menu>
        </Header>
        <Content>
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/workflow" element={<WorkflowDemo />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  );
}

export default App;
