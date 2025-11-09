import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Progress,
  Tag,
  Space,
  message,
  Typography,
  Statistic,
  Row,
  Col,
} from 'antd'
import { PlusOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons'
import { annotationApi, imagesApi, projectsApi } from '@/api'
import type { AnnotationTask } from '@/types'

const { Title } = Typography
const { TextArea } = Input

const Annotation = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['annotation-tasks', projectId],
    queryFn: () => annotationApi.getTasks(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const { data: images } = useQuery({
    queryKey: ['images', projectId, 'approved'],
    queryFn: () => imagesApi.getImages(parseInt(projectId!), { review_status: 'approved' }).then(res => res.data),
    enabled: !!projectId,
  })

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.getProject(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const { data: stats } = useQuery({
    queryKey: ['annotation-stats', projectId],
    queryFn: () => annotationApi.getStatistics(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const handleCreate = async (values: any) => {
    try {
      await annotationApi.createTask(parseInt(projectId!), values)
      message.success('标注任务创建成功')
      setIsModalOpen(false)
      form.resetFields()
      refetch()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          pending: 'default',
          running: 'processing',
          completed: 'success',
          failed: 'error',
          cancelled: 'default',
        }
        return <Tag color={colorMap[status] || 'default'}>{status}</Tag>
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 200,
      render: (progress: number, record: AnnotationTask) => (
        <div>
          <Progress
            percent={progress || 0}
            size="small"
            status={record.status === 'failed' ? 'exception' : undefined}
          />
          <div style={{ fontSize: 12, color: '#666' }}>
            {record.annotated_images || 0} / {record.total_images} 张
            {record.total_annotations && ` (${record.total_annotations} 个标注)`}
          </div>
        </div>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: AnnotationTask) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>标注管理</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalOpen(true)}
        >
          创建任务
        </Button>
      </div>

      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总标注数"
                value={stats.total_annotations}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已校验"
                value={stats.verified_count}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均置信度"
                value={(stats.avg_confidence * 100).toFixed(1)}
                suffix="%"
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="标签类型"
                value={Object.keys(stats.by_label || {}).length}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Table
        columns={columns}
        dataSource={data?.items || []}
        loading={isLoading}
        rowKey="id"
        pagination={{
          total: data?.total || 0,
          pageSize: data?.per_page || 20,
          current: data?.page || 1,
        }}
      />

      <Modal
        title="创建标注任务"
        open={isModalOpen}
        onOk={() => form.submit()}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
        }}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{
            confidence_threshold: 0.5,
          }}
        >
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="例如：annotate_batch_001" />
          </Form.Item>
          <Form.Item
            name="description"
            label="任务描述"
          >
            <TextArea rows={2} placeholder="任务的详细描述" />
          </Form.Item>
          <Form.Item
            name="image_ids"
            label="选择图片"
            rules={[{ required: true, message: '请选择图片' }]}
          >
            <Select
              mode="multiple"
              placeholder="选择要标注的图片"
              showSearch
              optionFilterProp="children"
            >
              {images?.items.map(img => (
                <Select.Option key={img.id} value={img.id}>
                  {img.filename}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="label_ids"
            label="选择标签"
            rules={[{ required: true, message: '请选择标签' }]}
          >
            <Select
              mode="multiple"
              placeholder="选择要检测的标签"
            >
              {project?.labels?.map(label => (
                <Select.Option key={label.id} value={label.id}>
                  <Tag color={label.color}>{label.name}</Tag>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="confidence_threshold"
            label="置信度阈值"
          >
            <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Annotation
