import request from './request'

export interface ImportTask {
  id: number
  file_name: string
  import_type: string
  status: string
  result_summary?: string
  error_message?: string
  created_at: string
}

export interface ImportSettings {
  max_import_chars: number
}

export const importApi = {
  importSingle(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<any, { message: string; import_id: number; file_name: string }>(
      '/import/single',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
      }
    )
  },

  importPaper(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<any, { message: string; import_id: number; file_name: string }>(
      '/import/paper',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
      }
    )
  },

  importText(content: string, importType: string = 'single') {
    return request.post<any, { message: string; import_id: number; file_name: string }>(
      '/import/text',
      { content, import_type: importType },
      { timeout: 60000 }
    )
  },

  getStatus(importId: number) {
    return request.get<any, ImportTask>(`/import/status/${importId}`)
  },

  getHistory() {
    return request.get<any, ImportTask[]>('/import/history')
  },

  getSettings() {
    return request.get<any, ImportSettings>('/import/settings')
  },

  updateSettings(data: { max_import_chars: number }) {
    return request.put<any, ImportSettings>('/import/settings', data)
  }
}
