import apiClient from './client'
import type { GenerationTask, Image, PagedResponse } from '@/types'

export const generationApi = {
  // Generation Tasks
  getTasks: (projectId: number, params?: { page?: number; per_page?: number; status?: string }) =>
    apiClient.get<PagedResponse<GenerationTask>>(`/projects/${projectId}/generation/tasks`, { params }),

  getTask: (projectId: number, taskId: number) =>
    apiClient.get<GenerationTask>(`/projects/${projectId}/generation/tasks/${taskId}`),

  createTask: (projectId: number, data: {
    name: string
    prompt: string
    negative_prompt?: string
    mode?: string
    resolution?: string
    batch_size: number
    template_name?: string
    params?: Record<string, any>
  }) =>
    apiClient.post<GenerationTask>(`/projects/${projectId}/generation/tasks`, data),

  deleteTask: (projectId: number, taskId: number) =>
    apiClient.delete(`/projects/${projectId}/generation/tasks/${taskId}`),

  getTaskImages: (projectId: number, taskId: number, params?: { page?: number; per_page?: number }) =>
    apiClient.get<PagedResponse<Image>>(`/projects/${projectId}/generation/tasks/${taskId}/images`, { params }),

  // Templates
  getTemplates: () =>
    apiClient.get<{ templates: any[] }>('/templates'),

  getTemplate: (name: string) =>
    apiClient.get(`/templates/${name}`),
}
