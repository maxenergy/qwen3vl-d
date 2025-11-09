import { Card, Row, Col, Statistic, Typography } from 'antd'
import {
  ProjectOutlined,
  PictureOutlined,
  TagsOutlined,
  RocketOutlined,
} from '@ant-design/icons'

const { Title } = Typography

const Dashboard = () => {
  return (
    <div>
      <Title level={2}>Dashboard</Title>
      <p style={{ marginBottom: 24, color: '#666' }}>
        项目概览和统计信息
      </p>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="项目总数"
              value={0}
              prefix={<ProjectOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="生成图片"
              value={0}
              prefix={<PictureOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="标注数量"
              value={0}
              prefix={<TagsOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="训练模型"
              value={0}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="快速开始" style={{ marginTop: 24 }}>
        <ol style={{ paddingLeft: 20 }}>
          <li style={{ marginBottom: 12 }}>创建项目并定义检测类别</li>
          <li style={{ marginBottom: 12 }}>使用 Hunyuan Image 生成数据集图片</li>
          <li style={{ marginBottom: 12 }}>使用 Qwen3-VL 自动标注目标</li>
          <li style={{ marginBottom: 12 }}>生成 YOLO/COCO 格式数据集</li>
          <li style={{ marginBottom: 12 }}>训练 YOLO 模型</li>
        </ol>
      </Card>
    </div>
  )
}

export default Dashboard
