import apiClient from './client'
import type { Image, PagedResponse } from '@/types'

export const imagesApi = {
  getImages: (projectId: number, params?: { page?: number; per_page?: number; review_status?: string }) =>
    apiClient.get<PagedResponse<Image>>(`/projects/${projectId}/images`, { params }),

  getImage: (projectId: number, imageId: number) =>
    apiClient.get<Image>(`/projects/${projectId}/images/${imageId}`),

  reviewImage: (projectId: number, imageId: number, data: { status: string; notes?: string }) =>
    apiClient.patch<Image>(`/projects/${projectId}/images/${imageId}/review`, data),

  batchReview: (projectId: number, data: { image_ids: number[]; status: string }) =>
    apiClient.post(`/projects/${projectId}/images/review/batch`, data),

  deleteImage: (projectId: number, imageId: number) =>
    apiClient.delete(`/projects/${projectId}/images/${imageId}`),

  batchDelete: (projectId: number, data: { image_ids: number[] }) =>
    apiClient.post(`/projects/${projectId}/images/delete/batch`, data),

  getStatistics: (projectId: number) =>
    apiClient.get<{
      total: number
      pending: number
      approved: number
      rejected: number
      avg_file_size_mb: number
    }>(`/projects/${projectId}/images/statistics`),
}
