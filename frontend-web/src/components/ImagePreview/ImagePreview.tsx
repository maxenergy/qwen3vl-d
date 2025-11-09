import { useState } from 'react'
import { Modal, Image as AntImage, Space, Button } from 'antd'
import { ZoomInOutlined, ZoomOutOutlined, RotateLeftOutlined, RotateRightOutlined } from '@ant-design/icons'

export interface ImagePreviewProps {
  src: string
  alt?: string
  visible: boolean
  onClose: () => void
  annotations?: Array<{
    id: number
    label: string
    bbox: [number, number, number, number]
    confidence?: number
    color?: string
  }>
  showAnnotations?: boolean
}

const ImagePreview = ({
  src,
  alt = 'Preview',
  visible,
  onClose,
  annotations = [],
  showAnnotations = false,
}: ImagePreviewProps) => {
  const [scale, setScale] = useState(1)
  const [rotation, setRotation] = useState(0)

  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.2, 3))
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.2, 0.5))
  const handleRotateLeft = () => setRotation(prev => prev - 90)
  const handleRotateRight = () => setRotation(prev => prev + 90)

  const handleClose = () => {
    setScale(1)
    setRotation(0)
    onClose()
  }

  return (
    <Modal
      open={visible}
      onCancel={handleClose}
      width="90vw"
      style={{ top: 20 }}
      footer={null}
      bodyStyle={{
        padding: 0,
        height: '85vh',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{
        padding: 16,
        borderBottom: '1px solid #f0f0f0',
        background: '#fafafa',
      }}>
        <Space>
          <Button
            icon={<ZoomInOutlined />}
            onClick={handleZoomIn}
            disabled={scale >= 3}
          >
            放大
          </Button>
          <Button
            icon={<ZoomOutOutlined />}
            onClick={handleZoomOut}
            disabled={scale <= 0.5}
          >
            缩小
          </Button>
          <Button
            icon={<RotateLeftOutlined />}
            onClick={handleRotateLeft}
          >
            左旋转
          </Button>
          <Button
            icon={<RotateRightOutlined />}
            onClick={handleRotateRight}
          >
            右旋转
          </Button>
        </Space>
      </div>
      <div style={{
        flex: 1,
        overflow: 'auto',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: '#000',
        position: 'relative',
      }}>
        <div style={{
          transform: `scale(${scale}) rotate(${rotation}deg)`,
          transition: 'transform 0.3s ease',
        }}>
          <AntImage
            src={src}
            alt={alt}
            preview={false}
            style={{ maxWidth: '100%', maxHeight: '70vh' }}
          />
        </div>
        {showAnnotations && annotations.length > 0 && (
          <svg
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
            }}
          >
            {annotations.map(ann => (
              <g key={ann.id}>
                <rect
                  x={`${ann.bbox[0] * 100}%`}
                  y={`${ann.bbox[1] * 100}%`}
                  width={`${ann.bbox[2] * 100}%`}
                  height={`${ann.bbox[3] * 100}%`}
                  fill="none"
                  stroke={ann.color || '#1890ff'}
                  strokeWidth="2"
                />
                <text
                  x={`${ann.bbox[0] * 100}%`}
                  y={`${ann.bbox[1] * 100}%`}
                  dy="-5"
                  fill={ann.color || '#1890ff'}
                  fontSize="12"
                  fontWeight="bold"
                >
                  {ann.label} {ann.confidence !== undefined && `(${(ann.confidence * 100).toFixed(1)}%)`}
                </text>
              </g>
            ))}
          </svg>
        )}
      </div>
    </Modal>
  )
}

export default ImagePreview
