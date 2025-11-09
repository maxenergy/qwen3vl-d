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
} from 'antd'
import { PlusOutlined, PlayCircleOutlined } from '@ant-design/icons'
import { generationApi } from '@/api'
import type { GenerationTask } from '@/types'

const { Title } = Typography
const { TextArea } = Input

const Generation = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['generation-tasks', projectId],
    queryFn: () => generationApi.getTasks(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const handleCreate = async (values: any) => {
    try {
      await generationApi.createTask(parseInt(projectId!), values)
      message.success('生成任务创建成功')
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
      title: '分辨率',
      dataIndex: 'resolution',
      key: 'resolution',
      width: 120,
    },
    {
      title: '数量',
      dataIndex: 'batch_size',
      key: 'batch_size',
      width: 80,
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
      width: 150,
      render: (progress: number, record: GenerationTask) => (
        <div>
          <Progress
            percent={progress || 0}
            size="small"
            status={record.status === 'failed' ? 'exception' : undefined}
          />
          <div style={{ fontSize: 12, color: '#666' }}>
            {record.generated_count || 0} / {record.batch_size}
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
      width: 100,
      render: (_: any, record: GenerationTask) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<PlayCircleOutlined />}
          >
            查看
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>图片生成</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalOpen(true)}
        >
          创建任务
        </Button>
      </div>

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
        title="创建生成任务"
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
            resolution: '640x640',
            mode: 'text_to_image',
            batch_size: 10,
          }}
        >
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="例如：batch_001" />
          </Form.Item>
          <Form.Item
            name="prompt"
            label="提示词"
            rules={[{ required: true, message: '请输入提示词' }]}
          >
            <TextArea rows={4} placeholder="描述要生成的图片内容" />
          </Form.Item>
          <Form.Item
            name="resolution"
            label="分辨率"
          >
            <Select>
              <Select.Option value="640x640">640x640</Select.Option>
              <Select.Option value="1024x1024">1024x1024</Select.Option>
              <Select.Option value="1280x1280">1280x1280</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="batch_size"
            label="生成数量"
          >
            <InputNumber min={1} max={1000} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Generation
