import apiClient from './client'
import type { Project, Label, PagedResponse } from '@/types'

export const projectsApi = {
  // Projects
  getProjects: (params?: { page?: number; per_page?: number; status?: string }) =>
    apiClient.get<PagedResponse<Project>>('/projects', { params }),

  getProject: (id: number) =>
    apiClient.get<Project>(`/projects/${id}`),

  createProject: (data: { name: string; description?: string; labels?: Partial<Label>[] }) =>
    apiClient.post<Project>('/projects', data),

  updateProject: (id: number, data: Partial<Project>) =>
    apiClient.patch<Project>(`/projects/${id}`, data),

  deleteProject: (id: number) =>
    apiClient.delete(`/projects/${id}`),

  // Labels
  getLabels: (projectId: number) =>
    apiClient.get<Label[]>(`/projects/${projectId}/labels`),

  createLabel: (projectId: number, data: Omit<Label, 'id' | 'project_id'>) =>
    apiClient.post<Label>(`/projects/${projectId}/labels`, data),

  updateLabel: (labelId: number, data: Partial<Label>) =>
    apiClient.patch<Label>(`/labels/${labelId}`, data),

  deleteLabel: (labelId: number) =>
    apiClient.delete(`/labels/${labelId}`),
}
