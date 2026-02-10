import request from './request'

export interface Question {
  id: number
  category: string
  content: string
  analysis?: string
  reference_answer?: string
  image_url?: string
  tags?: string
  source?: string
  created_at: string
  updated_at: string
}

export interface QuestionListResponse {
  items: Question[]
  total: number
  page: number
  page_size: number
}

export const questionApi = {
  list(params: { page?: number; page_size?: number; category?: string; keyword?: string }) {
    return request.get<any, QuestionListResponse>('/questions', { params })
  },

  get(id: number) {
    return request.get<any, Question>(`/questions/${id}`)
  },

  create(data: Partial<Question>) {
    return request.post<any, Question>('/questions', data)
  },

  update(id: number, data: Partial<Question>) {
    return request.put<any, Question>(`/questions/${id}`, data)
  },

  delete(id: number) {
    return request.delete(`/questions/${id}`)
  },

  random(category?: string) {
    return request.get<any, Question>('/questions/random/single', { params: { category } })
  },

  batchDelete(ids: number[]) {
    return request.post<any, { deleted_count: number; message: string }>('/questions/batch-delete', { ids })
  }
}
