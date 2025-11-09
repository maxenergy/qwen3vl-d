import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, theme } from 'antd'
import {
  DashboardOutlined,
  ProjectOutlined,
  PictureOutlined,
  TagsOutlined,
  DatabaseOutlined,
  RocketOutlined,
} from '@ant-design/icons'

const { Header, Content, Sider } = Layout

const MainLayout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/projects',
      icon: <ProjectOutlined />,
      label: '项目管理',
    },
    {
      key: 'generation',
      icon: <PictureOutlined />,
      label: '图片生成',
      disabled: true,
    },
    {
      key: 'images',
      icon: <TagsOutlined />,
      label: '图片审核',
      disabled: true,
    },
    {
      key: 'annotation',
      icon: <TagsOutlined />,
      label: '标注管理',
      disabled: true,
    },
    {
      key: 'datasets',
      icon: <DatabaseOutlined />,
      label: '数据集',
      disabled: true,
    },
    {
      key: 'training',
      icon: <RocketOutlined />,
      label: '模型训练',
      disabled: true,
    },
  ]

  // Get selected key from location
  const selectedKey = '/' + location.pathname.split('/')[1]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{
          height: 32,
          margin: 16,
          color: '#fff',
          fontSize: 18,
          fontWeight: 'bold',
          textAlign: 'center'
        }}>
          {collapsed ? 'AI' : 'AI 标注工具'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[selectedKey]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => {
            if (key.startsWith('/')) {
              navigate(key)
            }
          }}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }}>
          <div style={{
            paddingLeft: 24,
            fontSize: 20,
            fontWeight: 600
          }}>
            AI Auto-Annotation Tool
          </div>
        </Header>
        <Content style={{ margin: '24px 16px 0' }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
