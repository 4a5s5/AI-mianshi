import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Question } from '@/api/questions'
import type { AnalysisResult } from '@/api/answers'

export interface PracticeState {
  mode: 'single' | 'paper'
  currentQuestion: Question | null
  transcript: string
  isRecording: boolean
  startTime: Date | null
  endTime: Date | null
  duration: number
  analysis: AnalysisResult | null
  isAnalyzing: boolean
}

export const usePracticeStore = defineStore('practice', () => {
  // 练习状态
  const mode = ref<'single' | 'paper'>('single')
  const currentQuestion = ref<Question | null>(null)
  const transcript = ref('')
  const isRecording = ref(false)
  const startTime = ref<Date | null>(null)
  const endTime = ref<Date | null>(null)
  const duration = ref(0)
  const analysis = ref<AnalysisResult | null>(null)
  const isAnalyzing = ref(false)

  // 套卷相关
  const paperSessionId = ref('')
  const paperQuestions = ref<Question[]>([])
  const currentQuestionIndex = ref(0)
  const paperTimeLimit = ref(0) // 秒
  const paperRemainingTime = ref(0)
  const paperAnswers = ref<Array<{
    questionId: number
    transcript: string
    duration: number
  }>>([])

  // 重置状态
  function reset() {
    currentQuestion.value = null
    transcript.value = ''
    isRecording.value = false
    startTime.value = null
    endTime.value = null
    duration.value = 0
    analysis.value = null
    isAnalyzing.value = false
  }

  // 重置套卷状态
  function resetPaper() {
    paperSessionId.value = ''
    paperQuestions.value = []
    currentQuestionIndex.value = 0
    paperTimeLimit.value = 0
    paperRemainingTime.value = 0
    paperAnswers.value = []
    reset()
  }

  // 开始作答
  function startAnswer() {
    startTime.value = new Date()
    endTime.value = null
    duration.value = 0
    isRecording.value = true
  }

  // 结束作答
  function stopAnswer() {
    endTime.value = new Date()
    isRecording.value = false
    if (startTime.value && endTime.value) {
      duration.value = Math.floor((endTime.value.getTime() - startTime.value.getTime()) / 1000)
    }
  }

  // 设置题目
  function setQuestion(question: Question) {
    currentQuestion.value = question
    transcript.value = ''
    analysis.value = null
  }

  // 更新转写文本
  function updateTranscript(text: string) {
    transcript.value = text
  }

  // 追加转写文本
  function appendTranscript(text: string) {
    transcript.value += text
  }

  return {
    // 状态
    mode,
    currentQuestion,
    transcript,
    isRecording,
    startTime,
    endTime,
    duration,
    analysis,
    isAnalyzing,
    // 套卷相关
    paperSessionId,
    paperQuestions,
    currentQuestionIndex,
    paperTimeLimit,
    paperRemainingTime,
    paperAnswers,
    // 方法
    reset,
    resetPaper,
    startAnswer,
    stopAnswer,
    setQuestion,
    updateTranscript,
    appendTranscript
  }
})
