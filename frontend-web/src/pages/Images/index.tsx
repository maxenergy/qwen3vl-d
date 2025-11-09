import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Radio,
  Typography,
  message,
} from 'antd'
import { CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons'
import { imagesApi } from '@/api'
import type { Image } from '@/types'

const { Title } = Typography

const Images = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [reviewStatus, setReviewStatus] = useState<string>('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['images', projectId, reviewStatus],
    queryFn: () => imagesApi.getImages(parseInt(projectId!), {
      review_status: reviewStatus || undefined,
    }).then(res => res.data),
    enabled: !!projectId,
  })

  const handleReview = async (imageId: number, status: string) => {
    try {
      await imagesApi.reviewImage(parseInt(projectId!), imageId, { status })
      message.success(`已${status === 'approved' ? '批准' : '拒绝'}`)
      refetch()
    } catch (error) {
      message.error('操作失败')
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
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
    },
    {
      title: '分辨率',
      dataIndex: 'resolution',
      key: 'resolution',
      width: 120,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 120,
      render: (size: number) => `${(size / 1024 / 1024).toFixed(2)} MB`,
    },
    {
      title: '审核状态',
      dataIndex: 'review_status',
      key: 'review_status',
      width: 100,
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          pending: 'default',
          approved: 'success',
          rejected: 'error',
        }
        const textMap: Record<string, string> = {
          pending: '待审核',
          approved: '已批准',
          rejected: '已拒绝',
        }
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>
      },
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
      render: (_: any, record: Image) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
          >
            查看
          </Button>
          {record.review_status === 'pending' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => handleReview(record.id, 'approved')}
              >
                批准
              </Button>
              <Button
                type="link"
                size="small"
                danger
                icon={<CloseOutlined />}
                onClick={() => handleReview(record.id, 'rejected')}
              >
                拒绝
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={2}>图片审核</Title>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>审核状态：</span>
          <Radio.Group
            value={reviewStatus}
            onChange={(e) => setReviewStatus(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value="">全部</Radio.Button>
            <Radio.Button value="pending">待审核</Radio.Button>
            <Radio.Button value="approved">已批准</Radio.Button>
            <Radio.Button value="rejected">已拒绝</Radio.Button>
          </Radio.Group>
        </Space>
      </Card>

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
    </div>
  )
}

export default Images
