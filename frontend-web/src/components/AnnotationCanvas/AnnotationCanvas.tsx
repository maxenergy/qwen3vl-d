import { useRef, useEffect, useState, useCallback } from 'react'
import { Card, Space, Button, Checkbox, Slider, Tag } from 'antd'
import { ZoomInOutlined, ZoomOutOutlined, RedoOutlined } from '@ant-design/icons'

export interface Annotation {
  id: number
  label: string
  bbox: [number, number, number, number] // [x, y, w, h] in relative coordinates (0-1)
  confidence?: number
  color?: string
  verified?: boolean
}

export interface AnnotationCanvasProps {
  imageUrl: string
  annotations: Annotation[]
  width?: number
  height?: number
  onAnnotationClick?: (annotation: Annotation) => void
  showConfidence?: boolean
  showLabels?: boolean
  minConfidence?: number
}

const AnnotationCanvas = ({
  imageUrl,
  annotations,
  width = 800,
  height = 600,
  onAnnotationClick,
  showConfidence = true,
  showLabels = true,
  minConfidence = 0,
}: AnnotationCanvasProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement | null>(null)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [scale, setScale] = useState(1)
  const [confidenceThreshold, setConfidenceThreshold] = useState(minConfidence)
  const [showVerifiedOnly, setShowVerifiedOnly] = useState(false)

  const drawAnnotations = useCallback(() => {
    const canvas = canvasRef.current
    const image = imageRef.current
    if (!canvas || !image || !imageLoaded) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw image
    const imgAspect = image.width / image.height
    const canvasAspect = canvas.width / canvas.height

    let drawWidth, drawHeight, offsetX = 0, offsetY = 0

    if (imgAspect > canvasAspect) {
      drawWidth = canvas.width * scale
      drawHeight = drawWidth / imgAspect
      offsetY = (canvas.height - drawHeight) / 2
    } else {
      drawHeight = canvas.height * scale
      drawWidth = drawHeight * imgAspect
      offsetX = (canvas.width - drawWidth) / 2
    }

    ctx.drawImage(image, offsetX, offsetY, drawWidth, drawHeight)

    // Filter annotations
    const filteredAnnotations = annotations.filter(ann => {
      if (ann.confidence !== undefined && ann.confidence < confidenceThreshold) return false
      if (showVerifiedOnly && !ann.verified) return false
      return true
    })

    // Draw annotations
    filteredAnnotations.forEach(ann => {
      const x = offsetX + ann.bbox[0] * drawWidth
      const y = offsetY + ann.bbox[1] * drawHeight
      const w = ann.bbox[2] * drawWidth
      const h = ann.bbox[3] * drawHeight

      // Draw bounding box
      ctx.strokeStyle = ann.color || '#1890ff'
      ctx.lineWidth = ann.verified ? 3 : 2
      ctx.strokeRect(x, y, w, h)

      // Draw semi-transparent fill for verified annotations
      if (ann.verified) {
        ctx.fillStyle = ann.color ? ann.color + '20' : '#1890ff20'
        ctx.fillRect(x, y, w, h)
      }

      // Draw label background
      if (showLabels) {
        const labelText = ann.label + (showConfidence && ann.confidence !== undefined
          ? ` ${(ann.confidence * 100).toFixed(1)}%`
          : '')

        ctx.font = 'bold 14px Arial'
        const textWidth = ctx.measureText(labelText).width
        const padding = 6

        ctx.fillStyle = ann.color || '#1890ff'
        ctx.fillRect(x, y - 24, textWidth + padding * 2, 24)

        // Draw label text
        ctx.fillStyle = '#fff'
        ctx.fillText(labelText, x + padding, y - 6)
      }
    })
  }, [imageLoaded, annotations, scale, confidenceThreshold, showVerifiedOnly, showConfidence, showLabels])

  useEffect(() => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => {
      imageRef.current = image
      setImageLoaded(true)
    }
    image.src = imageUrl
  }, [imageUrl])

  useEffect(() => {
    drawAnnotations()
  }, [drawAnnotations])

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onAnnotationClick || !imageRef.current || !imageLoaded) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const image = imageRef.current
    const imgAspect = image.width / image.height
    const canvasAspect = canvas.width / canvas.height

    let drawWidth, drawHeight, offsetX = 0, offsetY = 0

    if (imgAspect > canvasAspect) {
      drawWidth = canvas.width * scale
      drawHeight = drawWidth / imgAspect
      offsetY = (canvas.height - drawHeight) / 2
    } else {
      drawHeight = canvas.height * scale
      drawWidth = drawHeight * imgAspect
      offsetX = (canvas.width - drawWidth) / 2
    }

    // Check which annotation was clicked (in reverse order to match drawing order)
    for (let i = annotations.length - 1; i >= 0; i--) {
      const ann = annotations[i]
      const annX = offsetX + ann.bbox[0] * drawWidth
      const annY = offsetY + ann.bbox[1] * drawHeight
      const annW = ann.bbox[2] * drawWidth
      const annH = ann.bbox[3] * drawHeight

      if (x >= annX && x <= annX + annW && y >= annY && y <= annY + annH) {
        onAnnotationClick(ann)
        break
      }
    }
  }

  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.1, 2))
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.1, 0.5))
  const handleReset = () => {
    setScale(1)
    setConfidenceThreshold(minConfidence)
    setShowVerifiedOnly(false)
  }

  const filteredCount = annotations.filter(ann => {
    if (ann.confidence !== undefined && ann.confidence < confidenceThreshold) return false
    if (showVerifiedOnly && !ann.verified) return false
    return true
  }).length

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space wrap>
          <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} disabled={scale >= 2}>
            放大
          </Button>
          <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} disabled={scale <= 0.5}>
            缩小
          </Button>
          <Button icon={<RedoOutlined />} onClick={handleReset}>
            重置
          </Button>
          <Checkbox
            checked={showVerifiedOnly}
            onChange={(e) => setShowVerifiedOnly(e.target.checked)}
          >
            只显示已验证
          </Checkbox>
          <Tag color="blue">
            显示: {filteredCount} / {annotations.length} 个标注
          </Tag>
        </Space>

        {showConfidence && (
          <div style={{ width: 300 }}>
            <div style={{ marginBottom: 8 }}>
              置信度阈值: {(confidenceThreshold * 100).toFixed(0)}%
            </div>
            <Slider
              min={0}
              max={100}
              value={confidenceThreshold * 100}
              onChange={(value) => setConfidenceThreshold(value / 100)}
            />
          </div>
        )}

        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          onClick={handleCanvasClick}
          style={{
            border: '1px solid #d9d9d9',
            borderRadius: 4,
            cursor: onAnnotationClick ? 'pointer' : 'default',
            maxWidth: '100%',
          }}
        />
      </Space>
    </Card>
  )
}

export default AnnotationCanvas
