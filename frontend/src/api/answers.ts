import request from './request'

export interface Answer {
  id: number
  mode: string
  question_id: number
  paper_id?: number
  paper_session_id?: string
  transcript?: string
  duration_seconds?: number
  started_at: string
  finished_at?: string
  practice_date: string
  created_at: string
}

export interface AnalysisResult {
  id: number
  answer_id: number
  analysis_type: string
  score?: number
  score_details?: string
  feedback?: string
  model_answer?: string
  model_name: string
  created_at: string
}

export interface AnswerWithAnalysis extends Answer {
  analysis?: AnalysisResult
  question_content?: string
}

export const answerApi = {
  create(data: {
    mode: string
    question_id: number
    paper_id?: number
    paper_session_id?: string
    transcript?: string
    duration_seconds?: number
    started_at: string
    finished_at?: string
  }) {
    return request.post<any, Answer>('/answers', data)
  },

  get(id: number) {
    return request.get<any, AnswerWithAnalysis>(`/answers/${id}`)
  },

  analyze(id: number) {
    return request.post<any, { message: string; answer_id: number }>(`/answers/${id}/analyze`)
  },

  getAnalysis(id: number, options?: { _silent?: boolean }) {
    return request.get<any, AnalysisResult>(`/answers/${id}/analysis`, options)
  },

  historyAnalyze(answer_ids: number[], analysis_type: string) {
    return request.post<any, { feedback: string; model_name: string }>('/answers/history-analyze', {
      answer_ids,
      analysis_type
    })
  },

  analyzePaper(paper_session_id: string) {
    return request.post<any, { feedback: string; model_name: string }>('/answers/paper-analyze', {
      paper_session_id
    })
  }
}

export const historyApi = {
  getSingle(params: { page?: number; page_size?: number }) {
    return request.get<any, any>('/history/single', { params })
  },

  getPaper(params: { page?: number; page_size?: number }) {
    return request.get<any, any>('/history/paper', { params })
  },

  getTrends(mode: string = 'single', days: number = 30) {
    return request.get<any, { trends: Array<{ date: string; avg_score: number; count: number }>; mode: string }>(
      '/history/trends',
      { params: { mode, days } }
    )
  }
}
