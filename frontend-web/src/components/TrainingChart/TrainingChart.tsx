import { Card, Select, Space, Empty } from 'antd'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useState } from 'react'

export interface TrainingMetrics {
  epoch: number
  train_loss?: number
  val_loss?: number
  map50?: number
  map50_95?: number
  precision?: number
  recall?: number
  [key: string]: number | undefined
}

export interface TrainingChartProps {
  data: TrainingMetrics[]
  title?: string
  height?: number
  defaultMetrics?: string[]
}

const METRIC_OPTIONS = [
  { value: 'train_loss', label: '训练损失', color: '#ff4d4f' },
  { value: 'val_loss', label: '验证损失', color: '#ff7a45' },
  { value: 'map50', label: 'mAP@50', color: '#1890ff' },
  { value: 'map50_95', label: 'mAP@50-95', color: '#52c41a' },
  { value: 'precision', label: '精确率', color: '#722ed1' },
  { value: 'recall', label: '召回率', color: '#eb2f96' },
]

const TrainingChart = ({
  data,
  title = '训练指标',
  height = 400,
  defaultMetrics = ['train_loss', 'val_loss', 'map50_95'],
}: TrainingChartProps) => {
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(defaultMetrics)

  if (!data || data.length === 0) {
    return (
      <Card title={title}>
        <Empty description="暂无训练数据" />
      </Card>
    )
  }

  // Get available metrics from the data
  const availableMetrics = METRIC_OPTIONS.filter(option =>
    data.some(d => d[option.value] !== undefined)
  )

  const filteredMetrics = selectedMetrics.filter(metric =>
    availableMetrics.some(m => m.value === metric)
  )

  return (
    <Card
      title={title}
      extra={
        <Space>
          <Select
            mode="multiple"
            style={{ minWidth: 300 }}
            placeholder="选择要显示的指标"
            value={filteredMetrics}
            onChange={setSelectedMetrics}
            options={availableMetrics}
            maxTagCount="responsive"
          />
        </Space>
      }
    >
      {filteredMetrics.length === 0 ? (
        <Empty description="请选择要显示的指标" />
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="epoch"
              label={{ value: 'Epoch', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              label={{ value: '数值', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              formatter={(value: any) => {
                if (typeof value === 'number') {
                  return value.toFixed(4)
                }
                return value
              }}
            />
            <Legend />
            {filteredMetrics.map(metric => {
              const config = METRIC_OPTIONS.find(m => m.value === metric)
              return (
                <Line
                  key={metric}
                  type="monotone"
                  dataKey={metric}
                  name={config?.label || metric}
                  stroke={config?.color || '#1890ff'}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              )
            })}
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}

export default TrainingChart
