import apiClient from './client'
import type { DatasetVersion, PagedResponse } from '@/types'

export const datasetsApi = {
  // Dataset Versions
  getDatasets: (projectId: number, params?: { page?: number; per_page?: number }) =>
    apiClient.get<PagedResponse<DatasetVersion>>(`/projects/${projectId}/datasets`, { params }),

  getDataset: (projectId: number, datasetId: number) =>
    apiClient.get<DatasetVersion>(`/projects/${projectId}/datasets/${datasetId}`),

  createDataset: (projectId: number, data: {
    version: string
    description?: string
    split_config?: {
      train_ratio: number
      val_ratio: number
      test_ratio: number
    }
    augmentation_config?: Record<string, any>
    export_formats?: string[]
  }) =>
    apiClient.post<DatasetVersion>(`/projects/${projectId}/datasets`, data),

  deleteDataset: (projectId: number, datasetId: number) =>
    apiClient.delete(`/projects/${projectId}/datasets/${datasetId}`),

  exportDataset: (projectId: number, datasetId: number, data: {
    format: 'yolo' | 'coco'
    include_augmented?: boolean
  }) =>
    apiClient.post<{ download_url: string; file_size_mb: number }>(
      `/projects/${projectId}/datasets/${datasetId}/export`,
      data
    ),

  regenerateDataset: (projectId: number, datasetId: number, data: {
    regenerate_splits?: boolean
    regenerate_augmentation?: boolean
  }) =>
    apiClient.post(`/projects/${projectId}/datasets/${datasetId}/regenerate`, data),

  getStatistics: (projectId: number, datasetId: number) =>
    apiClient.get<{
      total_images: number
      total_annotations: number
      split_distribution: Record<string, number>
      label_distribution: Record<string, number>
    }>(`/projects/${projectId}/datasets/${datasetId}/statistics`),

  getQuickStats: (projectId: number) =>
    apiClient.get<{
      total_datasets: number
      latest_version: string
      total_size_gb: number
    }>(`/projects/${projectId}/datasets/quick-stats`),
}
