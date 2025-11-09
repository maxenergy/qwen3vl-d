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
  Descriptions,
  Row,
  Col,
  Statistic,
} from 'antd'
import { PlusOutlined, EyeOutlined, StopOutlined, DeleteOutlined, RocketOutlined } from '@ant-design/icons'
import { trainingApi, datasetsApi } from '@/api'
import type { TrainingTask, Model } from '@/types'

const { Title } = Typography
const { TextArea } = Input

const Training = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedTask, setSelectedTask] = useState<TrainingTask | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['training-tasks', projectId],
    queryFn: () => trainingApi.getTasks(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const { data: models } = useQuery({
    queryKey: ['models', projectId],
    queryFn: () => trainingApi.getModels(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets', projectId, 'ready'],
    queryFn: () => datasetsApi.getDatasets(parseInt(projectId!)).then(res => res.data),
    enabled: !!projectId,
  })

  const { data: presets } = useQuery({
    queryKey: ['training-presets'],
    queryFn: () => trainingApi.getPresets().then(res => res.data),
  })

  const handleCreate = async (values: any) => {
    try {
      await trainingApi.createTask(parseInt(projectId!), values)
      message.success('训练任务创建成功')
      setIsModalOpen(false)
      form.resetFields()
      refetch()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleStop = async (taskId: number) => {
    try {
      await trainingApi.stopTask(parseInt(projectId!), taskId)
      message.success('训练已停止')
      refetch()
    } catch (error) {
      message.error('停止失败')
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
      title: 'YOLO版本',
      dataIndex: 'yolo_version',
      key: 'yolo_version',
      width: 120,
      render: (version: string) => <Tag color="blue">{version}</Tag>,
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
      render: (progress: number, record: TrainingTask) => (
        <div>
          <Progress
            percent={progress || 0}
            size="small"
            status={record.status === 'failed' ? 'exception' : undefined}
          />
          <div style={{ fontSize: 12, color: '#666' }}>
            Epoch: {record.current_epoch || 0} / {record.total_epochs}
          </div>
        </div>
      ),
    },
    {
      title: '当前指标',
      key: 'metrics',
      width: 200,
      render: (_: any, record: TrainingTask) => (
        record.current_metrics ? (
          <div style={{ fontSize: 12 }}>
            <div>mAP50: {(record.current_metrics.mAP50 || 0).toFixed(3)}</div>
            <div>Precision: {(record.current_metrics.precision || 0).toFixed(3)}</div>
            <div>Recall: {(record.current_metrics.recall || 0).toFixed(3)}</div>
          </div>
        ) : <span style={{ color: '#999' }}>暂无</span>
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
      width: 200,
      render: (_: any, record: TrainingTask) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedTask(record)
              setIsDetailOpen(true)
            }}
          >
            详情
          </Button>
          {record.status === 'running' && (
            <Button
              type="link"
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => handleStop(record.id)}
            >
              停止
            </Button>
          )}
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

  const modelColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'YOLO版本',
      dataIndex: 'yolo_version',
      key: 'yolo_version',
      width: 120,
      render: (version: string) => <Tag color="blue">{version}</Tag>,
    },
    {
      title: 'mAP50',
      dataIndex: ['metrics', 'mAP50'],
      key: 'mAP50',
      width: 100,
      render: (val: number) => val?.toFixed(3) || '-',
    },
    {
      title: 'mAP50-95',
      dataIndex: ['metrics', 'mAP50_95'],
      key: 'mAP50_95',
      width: 120,
      render: (val: number) => val?.toFixed(3) || '-',
    },
    {
      title: '模型大小',
      dataIndex: 'model_size_mb',
      key: 'model_size_mb',
      width: 120,
      render: (size: number) => `${size.toFixed(2)} MB`,
    },
    {
      title: '状态',
      key: 'status',
      width: 120,
      render: (_: any, record: Model) => (
        <Space>
          {record.is_best && <Tag color="gold">最佳</Tag>}
          {record.is_deployed && <Tag color="green">已部署</Tag>}
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>模型训练</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalOpen(true)}
        >
          创建训练
        </Button>
      </div>

      {models && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="训练任务"
                value={data?.total || 0}
                prefix={<RocketOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已训练模型"
                value={models.total}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="最佳 mAP50"
                value={Math.max(...(models.models?.map(m => m.metrics?.mAP50 || 0) || [0]))}
                precision={3}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="运行中任务"
                value={data?.items?.filter(t => t.status === 'running').length || 0}
                valueStyle={{ color: '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card title="训练任务" style={{ marginBottom: 16 }}>
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
      </Card>

      <Card title="训练完成的模型">
        <Table
          columns={modelColumns}
          dataSource={models?.models || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="创建训练任务"
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
            yolo_version: 'yolov8n',
            epochs: 100,
            batch_size: 16,
            image_size: 640,
          }}
        >
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="例如：yolov8_baseline" />
          </Form.Item>
          <Form.Item
            name="dataset_id"
            label="选择数据集"
            rules={[{ required: true, message: '请选择数据集' }]}
          >
            <Select placeholder="选择数据集版本">
              {datasets?.items
                ?.filter(d => d.status === 'ready')
                .map(dataset => (
                  <Select.Option key={dataset.id} value={dataset.id}>
                    {dataset.version} ({dataset.total_images} 张图片)
                  </Select.Option>
                ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="yolo_version"
            label="YOLO 版本"
          >
            <Select>
              <Select.OptGroup label="YOLOv8">
                <Select.Option value="yolov8n">YOLOv8n (最快)</Select.Option>
                <Select.Option value="yolov8s">YOLOv8s</Select.Option>
                <Select.Option value="yolov8m">YOLOv8m</Select.Option>
                <Select.Option value="yolov8l">YOLOv8l</Select.Option>
                <Select.Option value="yolov8x">YOLOv8x (最准)</Select.Option>
              </Select.OptGroup>
              <Select.OptGroup label="YOLOv11">
                <Select.Option value="yolov11n">YOLOv11n (最快)</Select.Option>
                <Select.Option value="yolov11s">YOLOv11s</Select.Option>
                <Select.Option value="yolov11m">YOLOv11m</Select.Option>
                <Select.Option value="yolov11l">YOLOv11l</Select.Option>
                <Select.Option value="yolov11x">YOLOv11x (最准)</Select.Option>
              </Select.OptGroup>
            </Select>
          </Form.Item>
          <Space style={{ width: '100%' }} direction="vertical">
            <Form.Item
              name="epochs"
              label="训练轮数"
            >
              <InputNumber min={1} max={1000} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="batch_size"
              label="批大小"
            >
              <InputNumber min={1} max={128} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="image_size"
              label="图片大小"
            >
              <Select>
                <Select.Option value={320}>320</Select.Option>
                <Select.Option value={416}>416</Select.Option>
                <Select.Option value={640}>640</Select.Option>
                <Select.Option value={1280}>1280</Select.Option>
              </Select>
            </Form.Item>
          </Space>
        </Form>
      </Modal>

      <Modal
        title="训练任务详情"
        open={isDetailOpen}
        onCancel={() => setIsDetailOpen(false)}
        footer={null}
        width={700}
      >
        {selectedTask && (
          <div>
            <Descriptions bordered column={2} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="任务名称">{selectedTask.name}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={selectedTask.status === 'completed' ? 'success' : 'default'}>
                  {selectedTask.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="YOLO 版本">{selectedTask.yolo_version}</Descriptions.Item>
              <Descriptions.Item label="数据集 ID">{selectedTask.dataset_id}</Descriptions.Item>
              <Descriptions.Item label="总轮数">{selectedTask.total_epochs}</Descriptions.Item>
              <Descriptions.Item label="当前轮数">{selectedTask.current_epoch || 0}</Descriptions.Item>
              <Descriptions.Item label="进度">
                <Progress percent={selectedTask.progress || 0} />
              </Descriptions.Item>
            </Descriptions>

            {selectedTask.current_metrics && (
              <Card title="当前指标" size="small">
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="mAP50">
                    {selectedTask.current_metrics.mAP50?.toFixed(4)}
                  </Descriptions.Item>
                  <Descriptions.Item label="mAP50-95">
                    {selectedTask.current_metrics.mAP50_95?.toFixed(4)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Precision">
                    {selectedTask.current_metrics.precision?.toFixed(4)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Recall">
                    {selectedTask.current_metrics.recall?.toFixed(4)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Train Loss">
                    {selectedTask.current_metrics.train_loss?.toFixed(4)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Val Loss">
                    {selectedTask.current_metrics.val_loss?.toFixed(4)}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            )}

            {selectedTask.best_metrics && (
              <Card title="最佳指标" size="small" style={{ marginTop: 16 }}>
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="mAP50">
                    {selectedTask.best_metrics.mAP50?.toFixed(4)}
                  </Descriptions.Item>
                  <Descriptions.Item label="mAP50-95">
                    {selectedTask.best_metrics.mAP50_95?.toFixed(4)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Precision">
                    {selectedTask.best_metrics.precision?.toFixed(4)}
                  </Descriptions.Item>
                  <Descriptions.Item label="Recall">
                    {selectedTask.best_metrics.recall?.toFixed(4)}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Training
