import request from './request'

export interface ModelConfig {
  id: number
  name: string
  base_url: string
  model_name: string
  role: string
  is_active: boolean
  api_key_masked?: string
  created_at: string
  updated_at: string
}

export interface Prompt {
  id: number
  prompt_type: string
  title: string
  content: string
  updated_at: string
}

export interface SpeechConfig {
  id: number
  provider: string
  whisper_api_url?: string
  whisper_api_key?: string
  is_active: boolean
  updated_at: string
}

export const modelApi = {
  list(role?: string) {
    return request.get<any, ModelConfig[]>('/models', { params: { role } })
  },

  create(data: {
    name: string
    base_url: string
    api_key: string
    model_name: string
    role: string
  }) {
    return request.post<any, ModelConfig>('/models', data)
  },

  update(id: number, data: Partial<ModelConfig> & { api_key?: string }) {
    return request.put<any, ModelConfig>(`/models/${id}`, data)
  },

  delete(id: number) {
    return request.delete(`/models/${id}`)
  },

  activate(id: number) {
    return request.post(`/models/${id}/activate`)
  },

  fetchModels(base_url: string, api_key: string) {
    return request.post<any, { models: string[] }>('/models/fetch-models', { base_url, api_key })
  }
}

export const promptApi = {
  list() {
    return request.get<any, Prompt[]>('/prompts')
  },

  get(id: number) {
    return request.get<any, Prompt>(`/prompts/${id}`)
  },

  update(id: number, data: { title?: string; content?: string }) {
    return request.put<any, Prompt>(`/prompts/${id}`, data)
  }
}

export const speechApi = {
  getConfig() {
    return request.get<any, SpeechConfig>('/speech/config')
  },

  updateConfig(data: {
    provider: string
    whisper_api_url?: string
    whisper_api_key?: string
  }) {
    return request.put<any, SpeechConfig>('/speech/config', data)
  }
}
