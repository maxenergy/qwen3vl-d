import apiClient from './client'
import type { TrainingTask, Model, PagedResponse, TrainingMetrics } from '@/types'

export const trainingApi = {
  // Training Tasks
  getTasks: (projectId: number, params?: { page?: number; per_page?: number; status?: string }) =>
    apiClient.get<PagedResponse<TrainingTask>>(`/projects/${projectId}/training/tasks`, { params }),

  getTask: (projectId: number, taskId: number) =>
    apiClient.get<TrainingTask>(`/projects/${projectId}/training/tasks/${taskId}`),

  createTask: (projectId: number, data: {
    name: string
    dataset_id: number
    yolo_version: string
    epochs?: number
    batch_size?: number
    image_size?: number
    optimizer?: string
    lr0?: number
    device?: string
  }) =>
    apiClient.post<TrainingTask>(`/projects/${projectId}/training/tasks`, data),

  stopTask: (projectId: number, taskId: number) =>
    apiClient.post<{ message: string; current_epoch: number }>(
      `/projects/${projectId}/training/tasks/${taskId}/stop`
    ),

  deleteTask: (projectId: number, taskId: number) =>
    apiClient.delete(`/projects/${projectId}/training/tasks/${taskId}`),

  // Models
  getModels: (projectId: number, params?: { sort_by?: string; order?: string }) =>
    apiClient.get<{ total: number; models: Model[] }>(`/projects/${projectId}/models`, { params }),

  getModel: (projectId: number, modelId: number) =>
    apiClient.get<Model>(`/projects/${projectId}/models/${modelId}`),

  // Hyperparameters
  getPresets: () =>
    apiClient.get<{
      presets: Array<{
        name: string
        description: string
        params: Record<string, any>
      }>
    }>('/training/hyperparameters/presets'),
}
