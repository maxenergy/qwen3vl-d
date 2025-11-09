import apiClient from './client'
import type { AnnotationTask, Annotation, PagedResponse } from '@/types'

export const annotationApi = {
  // Annotation Tasks
  getTasks: (projectId: number, params?: { page?: number; per_page?: number; status?: string }) =>
    apiClient.get<PagedResponse<AnnotationTask>>(`/projects/${projectId}/annotation/tasks`, { params }),

  getTask: (projectId: number, taskId: number) =>
    apiClient.get<AnnotationTask>(`/projects/${projectId}/annotation/tasks/${taskId}`),

  createTask: (projectId: number, data: {
    name: string
    description?: string
    image_ids: number[]
    label_ids: number[]
    confidence_threshold?: number
    model?: string
    prompt_template?: string
  }) =>
    apiClient.post<AnnotationTask>(`/projects/${projectId}/annotation/tasks`, data),

  deleteTask: (projectId: number, taskId: number) =>
    apiClient.delete(`/projects/${projectId}/annotation/tasks/${taskId}`),

  // Annotations
  getTaskAnnotations: (projectId: number, taskId: number, params?: { page?: number; per_page?: number }) =>
    apiClient.get<PagedResponse<any>>(`/projects/${projectId}/annotation/tasks/${taskId}/annotations`, { params }),

  getImageAnnotations: (projectId: number, imageId: number) =>
    apiClient.get<{ image_id: number; annotations: Annotation[] }>(`/projects/${projectId}/images/${imageId}/annotations`),

  getAnnotation: (projectId: number, annotationId: number) =>
    apiClient.get<Annotation>(`/projects/${projectId}/annotations/${annotationId}`),

  reviewAnnotation: (projectId: number, annotationId: number, data: {
    is_correct: boolean
    correction_bbox?: [number, number, number, number]
    notes?: string
  }) =>
    apiClient.patch<Annotation>(`/projects/${projectId}/annotations/${annotationId}/review`, data),

  deleteAnnotation: (projectId: number, annotationId: number) =>
    apiClient.delete(`/projects/${projectId}/annotations/${annotationId}`),

  batchDelete: (projectId: number, data: { annotation_ids: number[] }) =>
    apiClient.post(`/projects/${projectId}/annotations/batch-delete`, data),

  batchByLabel: (projectId: number, data: { label_id: number; action: string; task_id?: number }) =>
    apiClient.post(`/projects/${projectId}/annotations/batch-by-label`, data),

  getStatistics: (projectId: number) =>
    apiClient.get<{
      total_annotations: number
      by_label: Record<string, number>
      verified_count: number
      avg_confidence: number
    }>(`/projects/${projectId}/annotations/statistics`),
}
