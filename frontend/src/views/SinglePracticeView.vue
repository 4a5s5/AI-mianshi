<template>
  <div class="single-practice">
    <h2 class="page-title">单题练习</h2>

    <!-- 步骤1: 选择题目 -->
    <PracticeSelector
      v-if="step === 'select'"
      :loading="isCreatingQuestion"
      @random="handleRandom"
      @custom="handleCustom"
    />

    <!-- 步骤2: 作答 -->
    <PracticeSession
      v-else-if="step === 'answer'"
      :question="currentQuestion!"
      @back="reset"
      @complete="handleComplete"
    />

    <!-- 步骤3: 分析结果 -->
    <PracticeResult
      v-else
      :analysis="analysisResult"
      :loading="isAnalyzing && !isStreaming"
      :streaming="isStreaming"
      :stream-content="streamContent"
      @restart="reset"
      @retry="handleRetry"
      @regenerate="handleRegenerate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import PracticeSelector from '@/components/practice/PracticeSelector.vue'
import PracticeSession from '@/components/practice/PracticeSession.vue'
import PracticeResult from '@/components/practice/PracticeResult.vue'
import { questionApi } from '@/api/questions'
import { answerApi, type AnalysisResult } from '@/api/answers'

const route = useRoute()

interface Question {
  id: number
  content: string
  category?: string
}

type Step = 'select' | 'answer' | 'result'

const step = ref<Step>('select')
const currentQuestion = ref<Question | null>(null)
const isAnalyzing = ref(false)
const analysisResult = ref<AnalysisResult | null>(null)
const isCreatingQuestion = ref(false)
const isStreaming = ref(false)
const streamContent = ref('')
const lastAnswerId = ref<number | null>(null)

async function handleRandom(category?: string) {
  try {
    const question = await questionApi.random(category)
    currentQuestion.value = question
    step.value = 'answer'
  } catch (e: unknown) {
    const err = e as { response?: { status?: number } }
    if (err.response?.status === 404) {
      ElMessage.warning('题库为空，请先添加题目')
    }
  }
}

async function handleCustom(data: { content: string, category: string }) {
  const { content, category } = data
  isCreatingQuestion.value = true
  try {
    // 检查是否存在相同内容的题目
    const res = await questionApi.list({ keyword: content })
    const existing = res.items.find(q => q.content === content)

    if (existing) {
      currentQuestion.value = existing
    } else {
      const question = await questionApi.create({
        content,
        category: category || '自定义'
      })
      currentQuestion.value = question
    }
    step.value = 'answer'
  } catch (e) {
    ElMessage.error('题目处理失败，请重试')
  } finally {
    isCreatingQuestion.value = false
  }
}

async function handleComplete(data: { transcript: string; duration: number }) {
  step.value = 'result'
  isAnalyzing.value = true
  isStreaming.value = true
  streamContent.value = ''

  try {
    const answer = await answerApi.create({
      mode: 'single',
      question_id: currentQuestion.value?.id || 0,
      transcript: data.transcript,
      duration_seconds: data.duration,
      started_at: new Date().toISOString(),
      finished_at: new Date().toISOString()
    })

    lastAnswerId.value = answer.id
    await startStreamAnalysis(answer.id)
  } catch (e) {
    ElMessage.error('提交分析失败')
    isAnalyzing.value = false
    isStreaming.value = false
  }
}

async function startStreamAnalysis(answerId: number) {
  try {
    const response = await fetch(`/api/v1/answers/${answerId}/analysis/stream`)

    if (response.status === 409) {
      ElMessage.warning('分析正在进行中，请稍候')
      isStreaming.value = false
      await pollAnalysisResult(answerId)
      return
    }

    if (!response.ok) {
      throw new Error('请求失败')
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.content) {
              streamContent.value += data.content
            }
            if (data.full_content !== undefined) {
              analysisResult.value = {
                feedback: data.full_content,
                score: data.score
              }
              isStreaming.value = false
              isAnalyzing.value = false
            }
            if (data.message) {
              ElMessage.error(data.message)
              isStreaming.value = false
              isAnalyzing.value = false
            }
          } catch {
            // 忽略解析错误
          }
        }
      }
    }
  } catch (e) {
    ElMessage.error('分析请求失败')
    isStreaming.value = false
    isAnalyzing.value = false
  }
}

async function pollAnalysisResult(answerId: number) {
  const maxAttempts = 60
  let attempts = 0

  const poll = async () => {
    try {
      const result = await answerApi.getAnalysis(answerId, { _silent: true })
      analysisResult.value = result
      isAnalyzing.value = false
    } catch (e: unknown) {
      const err = e as { response?: { status?: number } }
      if (err.response?.status === 404 && attempts < maxAttempts) {
        attempts++
        setTimeout(poll, 1000)
      } else {
        ElMessage.error('获取分析结果失败')
        isAnalyzing.value = false
      }
    }
  }

  poll()
}

function reset() {
  step.value = 'select'
  currentQuestion.value = null
  analysisResult.value = null
  isAnalyzing.value = false
}

function handleRetry() {
  analysisResult.value = null
  isAnalyzing.value = false
  isStreaming.value = false
  streamContent.value = ''
  step.value = 'answer'
}

async function handleRegenerate() {
  if (!lastAnswerId.value) {
    ElMessage.warning('无法重新生成，请重新作答')
    return
  }

  analysisResult.value = null
  isAnalyzing.value = true
  isStreaming.value = true
  streamContent.value = ''

  await startStreamAnalysis(lastAnswerId.value)
}

onMounted(async () => {
  const questionId = route.query.questionId as string
  if (questionId) {
    try {
      const question = await questionApi.get(Number(questionId))
      currentQuestion.value = question
      step.value = 'answer'
    } catch (e) {
      ElMessage.error('题目加载失败')
    }
  }
})
</script>

<style scoped>
.single-practice {
  max-width: 800px;
  margin: 0 auto;
}
</style>
