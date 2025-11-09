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
  InputNumber,
  Tag,
  Space,
  message,
  Typography,
  Descriptions,
  Select,
  Switch,
} from 'antd'
import { PlusOutlined, DownloadOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { datasetsApi } from '@/api'
import type { DatasetVersion } from '@/types'

const { Title } = Typography
const { TextArea } = Input

const Datasets = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState<DatasetVersion | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => datasetsApi.getDatasets(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const { data: quickStats } = useQuery({
    queryKey: ['dataset-quick-stats', projectId],
    queryFn: () => datasetsApi.getQuickStats(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const handleCreate = async (values: any) => {
    try {
      await datasetsApi.createDataset(parseInt(projectId!), {
        ...values,
        split_config: {
          train_ratio: values.train_ratio / 100,
          val_ratio: values.val_ratio / 100,
          test_ratio: values.test_ratio / 100,
        },
      })
      message.success('数据集创建成功')
      setIsModalOpen(false)
      form.resetFields()
      refetch()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleExport = async (datasetId: number, format: 'yolo' | 'coco') => {
    try {
      const result = await datasetsApi.exportDataset(parseInt(projectId!), datasetId, { format })
      message.success(`导出成功，文件大小: ${result.data.file_size_mb.toFixed(2)} MB`)
      window.open(result.data.download_url, '_blank')
    } catch (error) {
      message.error('导出失败')
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
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 120,
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
          building: 'processing',
          ready: 'success',
          failed: 'error',
        }
        const textMap: Record<string, string> = {
          pending: '等待中',
          building: '构建中',
          ready: '就绪',
          failed: '失败',
        }
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
      },
    },
    {
      title: '图片数',
      dataIndex: 'total_images',
      key: 'total_images',
      width: 100,
      render: (total: number, record: DatasetVersion) => (
        <span>
          {total}
          <div style={{ fontSize: 12, color: '#666' }}>
            训练:{record.train_count} 验证:{record.val_count} 测试:{record.test_count}
          </div>
        </span>
      ),
    },
    {
      title: '标注数',
      dataIndex: 'total_annotations',
      key: 'total_annotations',
      width: 100,
    },
    {
      title: '格式',
      dataIndex: 'export_formats',
      key: 'export_formats',
      width: 120,
      render: (formats: string[]) => (
        <>
          {formats?.map(f => <Tag key={f}>{f.toUpperCase()}</Tag>)}
        </>
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
      width: 250,
      render: (_: any, record: DatasetVersion) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedDataset(record)
              setIsDetailOpen(true)
            }}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleExport(record.id, 'yolo')}
            disabled={record.status !== 'ready'}
          >
            YOLO
          </Button>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleExport(record.id, 'coco')}
            disabled={record.status !== 'ready'}
          >
            COCO
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
        <Title level={2}>数据集管理</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalOpen(true)}
        >
          创建数据集
        </Button>
      </div>

      {quickStats && (
        <Card style={{ marginBottom: 16 }}>
          <Descriptions column={3}>
            <Descriptions.Item label="数据集总数">{quickStats.total_datasets}</Descriptions.Item>
            <Descriptions.Item label="最新版本">{quickStats.latest_version || 'N/A'}</Descriptions.Item>
            <Descriptions.Item label="总大小">{quickStats.total_size_gb.toFixed(2)} GB</Descriptions.Item>
          </Descriptions>
        </Card>
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
        title="创建数据集"
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
            train_ratio: 80,
            val_ratio: 10,
            test_ratio: 10,
            export_formats: ['yolo', 'coco'],
          }}
        >
          <Form.Item
            name="version"
            label="版本号"
            rules={[{ required: true, message: '请输入版本号' }]}
          >
            <Input placeholder="例如：v1.0" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={2} placeholder="数据集描述" />
          </Form.Item>
          <Form.Item label="数据集划分比例">
            <Space>
              <Form.Item
                name="train_ratio"
                noStyle
                rules={[{ required: true }]}
              >
                <InputNumber min={0} max={100} addonAfter="% 训练" />
              </Form.Item>
              <Form.Item
                name="val_ratio"
                noStyle
                rules={[{ required: true }]}
              >
                <InputNumber min={0} max={100} addonAfter="% 验证" />
              </Form.Item>
              <Form.Item
                name="test_ratio"
                noStyle
                rules={[{ required: true }]}
              >
                <InputNumber min={0} max={100} addonAfter="% 测试" />
              </Form.Item>
            </Space>
          </Form.Item>
          <Form.Item
            name="export_formats"
            label="导出格式"
          >
            <Select mode="multiple">
              <Select.Option value="yolo">YOLO</Select.Option>
              <Select.Option value="coco">COCO</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="数据集详情"
        open={isDetailOpen}
        onCancel={() => setIsDetailOpen(false)}
        footer={null}
        width={700}
      >
        {selectedDataset && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="版本">{selectedDataset.version}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedDataset.status === 'ready' ? 'success' : 'default'}>
                {selectedDataset.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="总图片数">{selectedDataset.total_images}</Descriptions.Item>
            <Descriptions.Item label="总标注数">{selectedDataset.total_annotations}</Descriptions.Item>
            <Descriptions.Item label="训练集">{selectedDataset.train_count}</Descriptions.Item>
            <Descriptions.Item label="验证集">{selectedDataset.val_count}</Descriptions.Item>
            <Descriptions.Item label="测试集">{selectedDataset.test_count}</Descriptions.Item>
            <Descriptions.Item label="导出格式">
              {selectedDataset.export_formats?.map(f => (
                <Tag key={f}>{f.toUpperCase()}</Tag>
              ))}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间" span={2}>
              {new Date(selectedDataset.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default Datasets
