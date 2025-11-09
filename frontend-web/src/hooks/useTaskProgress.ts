import { useState, useCallback } from 'react'
import useWebSocket, { WebSocketMessage } from './useWebSocket'

export interface TaskProgress {
  task_id: number
  task_type: 'generation' | 'annotation' | 'training'
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  current: number
  total: number
  message?: string
  metrics?: Record<string, any>
}

export interface UseTaskProgressOptions {
  projectId: number
  taskId?: number
  taskType?: 'generation' | 'annotation' | 'training'
  onProgressUpdate?: (progress: TaskProgress) => void
  enabled?: boolean
}

const useTaskProgress = ({
  projectId,
  taskId,
  taskType,
  onProgressUpdate,
  enabled = true,
}: UseTaskProgressOptions) => {
  const [progress, setProgress] = useState<TaskProgress | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      try {
        if (message.type === 'task_progress') {
          const progressData = message.data as TaskProgress

          // Filter by task if specified
          if (taskId && progressData.task_id !== taskId) return
          if (taskType && progressData.task_type !== taskType) return

          setProgress(progressData)
          onProgressUpdate?.(progressData)
        } else if (message.type === 'error') {
          setError(message.data?.message || 'Unknown error')
        }
      } catch (err) {
        console.error('[TaskProgress] Error handling message:', err)
        setError('Failed to process progress update')
      }
    },
    [taskId, taskType, onProgressUpdate]
  )

  const handleOpen = useCallback(() => {
    console.log('[TaskProgress] WebSocket connected')
    setError(null)
  }, [])

  const handleError = useCallback(() => {
    setError('WebSocket connection error')
  }, [])

  // Construct WebSocket URL based on environment
  const wsUrl = (() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.VITE_API_BASE_URL?.replace(/^https?:\/\//, '') || 'localhost:8000'

    let url = `${protocol}//${host}/api/ws/projects/${projectId}/progress`

    if (taskId) {
      url += `?task_id=${taskId}`
    }
    if (taskType) {
      url += taskId ? `&task_type=${taskType}` : `?task_type=${taskType}`
    }

    return url
  })()

  const { isConnected, sendMessage, reconnect } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    onOpen: handleOpen,
    onError: handleError,
    enabled,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
  })

  const subscribeToTask = useCallback(
    (newTaskId: number, newTaskType: 'generation' | 'annotation' | 'training') => {
      sendMessage({
        type: 'subscribe',
        task_id: newTaskId,
        task_type: newTaskType,
      })
    },
    [sendMessage]
  )

  const unsubscribeFromTask = useCallback(
    (taskIdToUnsub: number) => {
      sendMessage({
        type: 'unsubscribe',
        task_id: taskIdToUnsub,
      })
    },
    [sendMessage]
  )

  return {
    progress,
    isConnected,
    error,
    subscribeToTask,
    unsubscribeFromTask,
    reconnect,
  }
}

export default useTaskProgress
