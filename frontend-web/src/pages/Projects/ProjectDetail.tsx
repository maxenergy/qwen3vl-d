import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Descriptions,
  Button,
  Space,
  Typography,
  Tag,
  Spin,
  Alert,
} from 'antd'
import {
  ArrowLeftOutlined,
  PictureOutlined,
  TagsOutlined,
  BgColorsOutlined,
  DatabaseOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { projectsApi } from '@/api'

const { Title } = Typography

const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = parseInt(id || '0')

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.getProject(projectId).then(res => res.data),
    enabled: !!projectId,
  })

  if (isLoading) {
    return <Spin size="large" />
  }

  if (error || !project) {
    return <Alert message="加载失败" type="error" />
  }

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/projects')}
        style={{ marginBottom: 16 }}
      >
        返回
      </Button>

      <Card>
        <Title level={2}>{project.name}</Title>

        <Descriptions bordered column={2} style={{ marginTop: 16 }}>
          <Descriptions.Item label="项目 ID">{project.id}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={project.status === 'active' ? 'green' : 'default'}>
              {project.status === 'active' ? '活跃' : '归档'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>
            {project.description || '暂无描述'}
          </Descriptions.Item>
          <Descriptions.Item label="标签数">{project.label_count || 0}</Descriptions.Item>
          <Descriptions.Item label="图片数">{project.image_count || 0}</Descriptions.Item>
          <Descriptions.Item label="标注数">{project.annotation_count || 0}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(project.created_at).toLocaleString('zh-CN')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="检测标签" style={{ marginTop: 16 }}>
        <Space wrap>
          {project.labels && project.labels.length > 0 ? (
            project.labels.map(label => (
              <Tag key={label.id} color={label.color}>
                {label.name}
              </Tag>
            ))
          ) : (
            <span style={{ color: '#999' }}>暂无标签</span>
          )}
        </Space>
      </Card>

      <Card title="快速操作" style={{ marginTop: 16 }}>
        <Space wrap>
          <Button
            type="primary"
            icon={<PictureOutlined />}
            onClick={() => navigate(`/projects/${projectId}/generation`)}
          >
            图片生成
          </Button>
          <Button
            icon={<TagsOutlined />}
            onClick={() => navigate(`/projects/${projectId}/images`)}
          >
            图片审核
          </Button>
          <Button
            icon={<BgColorsOutlined />}
            onClick={() => navigate(`/projects/${projectId}/annotation`)}
          >
            标注管理
          </Button>
          <Button
            icon={<DatabaseOutlined />}
            onClick={() => navigate(`/projects/${projectId}/datasets`)}
          >
            数据集
          </Button>
          <Button
            icon={<RocketOutlined />}
            onClick={() => navigate(`/projects/${projectId}/training`)}
          >
            训练管理
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default ProjectDetail
