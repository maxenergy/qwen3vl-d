// API Types

export interface Project {
  id: number
  name: string
  description?: string
  status: 'active' | 'archived'
  created_at: string
  updated_at: string
  labels: Label[]
  label_count?: number
  image_count?: number
  annotation_count?: number
}

export interface Label {
  id: number
  name: string
  color: string
  description?: string
  is_active: boolean
  project_id: number
}

export interface GenerationTask {
  id: number
  name: string
  prompt: string
  negative_prompt?: string
  mode: 'text_to_image' | 'image_to_image'
  resolution: '640x640' | '1024x1024' | '1280x1280'
  batch_size: number
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  progress?: number
  generated_count?: number
  created_at: string
  updated_at?: string
}

export interface Image {
  id: number
  filename: string
  file_path: string
  resolution: string
  file_size: number
  prompt?: string
  review_status: 'pending' | 'approved' | 'rejected'
  review_notes?: string
  created_at: string
  generation_task_id?: number
  project_id: number
}

export interface AnnotationTask {
  id: number
  name: string
  description?: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  progress?: number
  total_images: number
  annotated_images?: number
  total_annotations?: number
  created_at: string
  updated_at?: string
  project_id: number
}

export interface Annotation {
  id: number
  label_id: number
  label_name?: string
  bbox: [number, number, number, number]
  confidence: number
  is_verified: boolean
  verification_notes?: string
  image_id: number
  task_id: number
  created_at: string
}

export interface DatasetVersion {
  id: number
  version: string
  description?: string
  status: 'pending' | 'building' | 'ready' | 'failed'
  total_images: number
  total_annotations: number
  train_count: number
  val_count: number
  test_count: number
  export_formats: string[]
  created_at: string
  project_id: number
}

export interface TrainingTask {
  id: number
  name: string
  yolo_version: string
  dataset_id: number
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  progress?: number
  current_epoch?: number
  total_epochs: number
  current_metrics?: TrainingMetrics
  best_metrics?: TrainingMetrics
  created_at: string
  updated_at?: string
  project_id: number
}

export interface TrainingMetrics {
  train_loss?: number
  val_loss?: number
  precision?: number
  recall?: number
  mAP50?: number
  mAP50_95?: number
}

export interface Model {
  id: number
  name: string
  yolo_version: string
  model_path: string
  model_size_mb: number
  metrics: TrainingMetrics
  is_best: boolean
  is_deployed: boolean
  created_at: string
  training_task_id: number
  project_id: number
}

// API Response Types
export interface PagedResponse<T> {
  total: number
  page: number
  per_page: number
  pages: number
  items: T[]
}

export interface ApiError {
  error: {
    code: string
    message: string
    details?: any
    timestamp: string
  }
}
