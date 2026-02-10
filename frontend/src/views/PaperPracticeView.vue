<template>
  <div class="paper-practice">
    <h2 class="page-title">套卷练习</h2>

    <!-- 步骤1: 选择套卷 -->
    <div v-if="step === 'select'" class="page-card">
      <h3>选择练习套卷</h3>

      <!-- 从题库选择 -->
      <div class="paper-list" v-if="papers.length > 0">
        <div
          v-for="paper in papers"
          :key="paper.id"
          class="paper-item"
          @click="selectPaper(paper)"
        >
          <div class="paper-info">
            <span class="paper-title">{{ paper.title }}</span>
            <span class="paper-meta">{{ paper.items.length }} 道题 | {{ formatTime(paper.time_limit_seconds) }}</span>
          </div>
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>

      <el-empty v-else description="暂无套卷，请先在题库中创建" />

      <!-- 自定义套卷 -->
      <el-divider>或</el-divider>

      <el-button @click="showCustomPaper = true">
        <el-icon><Plus /></el-icon>
        自定义套卷
      </el-button>

      <!-- 自定义套卷弹窗 -->
      <el-dialog v-model="showCustomPaper" title="自定义套卷" width="90%" style="max-width: 700px">
        <el-form label-position="top">
          <el-form-item label="套卷标题">
            <el-input v-model="customPaperTitle" placeholder="请输入套卷标题" />
          </el-form-item>
          <el-form-item label="总时限（分钟）">
            <el-input-number v-model="customTimeLimit" :min="5" :max="60" />
          </el-form-item>
          <el-form-item label="题目（每行一道）">
            <el-input
              v-model="customQuestions"
              type="textarea"
              :rows="8"
              placeholder="请输入题目，每行一道题..."
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCustomPaper = false">取消</el-button>
          <el-button type="primary" @click="startCustomPaper" :disabled="!customQuestions.trim() || !customPaperTitle.trim()">
            开始练习
          </el-button>
        </template>
      </el-dialog>
    </div>

    <!-- 步骤2: 练习中 -->
    <div v-if="step === 'practice'" class="page-card">
      <!-- 总计时 -->
      <div class="paper-timer">
        <span class="timer-label">剩余时间</span>
        <span
          class="timer-display"
          :class="{ warning: paperTimer.isWarning.value, danger: paperTimer.seconds.value <= 10 }"
        >
          {{ paperTimer.formatted.value }}
        </span>
      </div>

      <!-- 题目导航 -->
      <div class="question-nav">
        <div
          v-for="(q, index) in practiceStore.paperQuestions"
          :key="index"
          class="nav-item"
          :class="{
            active: practiceStore.currentQuestionIndex === index,
            answered: isQuestionAnswered(index)
          }"
          @click="switchQuestion(index)"
        >
          {{ index + 1 }}
        </div>
      </div>

      <!-- 当前题目 -->
      <div class="question-section">
        <div class="question-header">
          <span class="question-number">第 {{ practiceStore.currentQuestionIndex + 1 }} 题</span>
          <el-tag v-if="getCurrentQuestion()?.category" type="info">
            {{ getCurrentQuestion()?.category }}
          </el-tag>
        </div>
        <div class="question-content">
          {{ getCurrentQuestion()?.content }}
        </div>
      </div>

      <!-- 单题计时 -->
      <div class="answer-timer">
        <span class="timer-label">本题用时</span>
        <span class="timer-display small" :class="{ recording: practiceStore.isRecording }">
          {{ questionTimer.formatted.value }}
        </span>
      </div>

      <!-- 录音控制 -->
      <div class="record-section">
        <button
          type="button"
          class="record-btn"
          :class="{ idle: !practiceStore.isRecording && !recorder.isTranscribing.value, recording: practiceStore.isRecording, transcribing: recorder.isTranscribing.value }"
          :aria-label="practiceStore.isRecording ? '结束录音' : '开始录音'"
          :aria-pressed="practiceStore.isRecording"
          :disabled="recorder.isTranscribing.value"
          @click="toggleRecording"
        >
          <el-icon :size="28">
            <Loading v-if="recorder.isTranscribing.value" class="spin-icon" />
            <Microphone v-else-if="!practiceStore.isRecording" />
            <VideoPause v-else />
          </el-icon>
        </button>
        <p class="record-hint">
          {{ recorder.isTranscribing.value ? '正在转写...' : (practiceStore.isRecording ? '点击结束本题' : '点击开始作答') }}
        </p>
      </div>

      <!-- 转写文本 -->
      <div class="transcript-section">
        <el-input
          v-model="currentTranscript"
          type="textarea"
          :rows="4"
          placeholder="作答内容..."
        />
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button @click="confirmEnd">面试结束</el-button>
      </div>
    </div>

    <!-- 步骤3: 分析结果 -->
    <div v-if="step === 'result'" class="page-card">
      <h3>套卷分析结果</h3>

      <!-- 流式输出中 -->
      <div v-if="isStreaming && streamContent" class="analysis-content markdown-content streaming">
        <div v-html="streamHtml"></div>
        <span class="cursor">▌</span>
      </div>

      <el-skeleton v-else-if="isAnalyzing" :rows="10" animated />

      <div v-else class="result-content">
        <!-- 各题得分概览 -->
        <div class="score-overview">
          <div
            v-for="(answer, index) in paperAnswers"
            :key="index"
            class="score-item"
          >
            <span class="score-label">第 {{ index + 1 }} 题</span>
            <span class="score-value">{{ answer.score ?? '-' }}</span>
          </div>
        </div>

        <!-- 详细分析 -->
        <div v-if="paperAnalysis" class="analysis-content markdown-content">
          <div v-html="safeAnalysisHtml"></div>
        </div>
      </div>

      <div class="result-actions">
        <el-button @click="handleRegeneratePaperAnalysis" :disabled="isAnalyzing || isStreaming">重新生成</el-button>
        <el-button @click="handleRetry" :disabled="isStreaming">再次练习</el-button>
        <el-button @click="reset" :disabled="isStreaming">换题练习</el-button>
        <el-button type="primary" @click="$router.push('/history')" :disabled="isStreaming">查看历史</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Plus, Microphone, VideoPause, Loading } from '@element-plus/icons-vue'
import { usePracticeStore } from '@/store/practice'
import { useAppStore } from '@/store/app'
import { useTimer } from '@/composables/useTimer'
import { useRecorder } from '@/composables/useRecorder'
import { paperApi, type Paper } from '@/api/papers'
import { questionApi, type Question } from '@/api/questions'
import { answerApi } from '@/api/answers'
import { v4 as uuidv4 } from 'uuid'

const route = useRoute()
const practiceStore = usePracticeStore()
const appStore = useAppStore()
const paperTimer = useTimer('countdown', 0)
const questionTimer = useTimer('countup')
const recorder = useRecorder()

const step = ref<'select' | 'practice' | 'result'>('select')
const papers = ref<Paper[]>([])
const showCustomPaper = ref(false)
const customPaperTitle = ref('自定义练习套卷')
const customTimeLimit = ref(15)
const customQuestions = ref('')
const currentTranscript = ref('')
const isAnalyzing = ref(false)
const isStreaming = ref(false)
const streamContent = ref('')
const paperAnalysis = ref('')
const paperAnswers = ref<Array<{ questionId: number; transcript: string; duration: number; score?: number; answerId?: number }>>([])

// 安全的 HTML 输出 (防 XSS)
const safeAnalysisHtml = computed(() => {
  const text = paperAnalysis.value || ''
  // 先转义 HTML 特殊字符
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
  // 再应用简单 markdown 格式化
  return escaped
    .replace(/###\s*(.*)/g, '<h4>$1</h4>')
    .replace(/##\s*(.*)/g, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
})

// 流式内容 HTML
const streamHtml = computed(() => {
  const text = streamContent.value || ''
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
  return escaped
    .replace(/###\s*(.*)/g, '<h4>$1</h4>')
    .replace(/##\s*(.*)/g, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
})

// 格式化时间
function formatTime(seconds: number | undefined): string {
  if (!seconds) return '无限制'
  const mins = Math.floor(seconds / 60)
  return `${mins} 分钟`
}

// 加载套卷列表
async function loadPapers() {
  try {
    const data = await paperApi.list()
    papers.value = data.items
  } catch (e) {
    console.error('加载套卷失败', e)
  }
}

// 选择套卷
async function selectPaper(paper: Paper) {
  // 加载套卷题目
  const questions: Question[] = []
  for (const item of paper.items) {
    try {
      const q = await questionApi.get(item.question_id)
      questions.push(q)
    } catch (e) {
      console.error('加载题目失败', e)
    }
  }

  if (questions.length === 0) {
    ElMessage.warning('套卷中没有题目')
    return
  }

  startPractice(questions, paper.time_limit_seconds || 900)
}

// 开始自定义套卷
async function startCustomPaper() {
  const lines = customQuestions.value.split('\n').filter(l => l.trim())
  if (lines.length < 1) {
    ElMessage.warning('请至少输入一道题目')
    return
  }

  // 先将自定义题目保存到数据库，获取真实 ID
  const questions: Question[] = []
  const questionIds: number[] = []
  for (const content of lines) {
    try {
      const savedQuestion = await questionApi.create({
        content: content.trim(),
        category: '自定义'
      })
      questions.push(savedQuestion)
      questionIds.push(savedQuestion.id)
    } catch (e) {
      console.error('保存自定义题目失败', e)
      ElMessage.error('保存题目失败，请重试')
      return
    }
  }

  // 保存套卷到数据库
  try {
    await paperApi.create({
      title: customPaperTitle.value,
      time_limit_seconds: customTimeLimit.value * 60,
      question_ids: questionIds
    })
  } catch (e) {
    console.error('保存套卷失败', e)
    // 继续练习，不阻塞用户
  }

  showCustomPaper.value = false
  startPractice(questions, customTimeLimit.value * 60)
}

// 开始练习
function startPractice(questions: Question[], timeLimit: number) {
  practiceStore.resetPaper()
  practiceStore.mode = 'paper'
  practiceStore.paperSessionId = uuidv4()
  practiceStore.paperQuestions = questions
  practiceStore.paperTimeLimit = timeLimit
  practiceStore.currentQuestionIndex = 0

  // 初始化每题答案
  paperAnswers.value = questions.map(q => ({
    questionId: q.id,
    transcript: '',
    duration: 0
  }))

  // 设置倒计时
  paperTimer.reset(timeLimit)
  paperTimer.start()

  step.value = 'practice'
}

// 获取当前题目
function getCurrentQuestion(): Question | undefined {
  return practiceStore.paperQuestions[practiceStore.currentQuestionIndex]
}

// 检查题目是否已作答
function isQuestionAnswered(index: number): boolean {
  return !!paperAnswers.value[index]?.transcript
}

// 切换题目
function switchQuestion(index: number) {
  // 保存当前题目的答案
  saveCurrentAnswer()

  practiceStore.currentQuestionIndex = index
  currentTranscript.value = paperAnswers.value[index]?.transcript || ''
  questionTimer.reset()
}

// 保存当前题目答案
function saveCurrentAnswer() {
  const index = practiceStore.currentQuestionIndex
  if (paperAnswers.value[index]) {
    paperAnswers.value[index].transcript = currentTranscript.value
    paperAnswers.value[index].duration += questionTimer.seconds.value
  }
}

// 切换录音
async function toggleRecording() {
  if (!practiceStore.isRecording) {
    try {
      await recorder.start()
      practiceStore.isRecording = true
      questionTimer.start()
    } catch (e) {
      ElMessage.error('无法启动录音')
    }
  } else {
    const result = await recorder.stop()
    practiceStore.isRecording = false
    questionTimer.pause()

    if (result.transcript) {
      currentTranscript.value += result.transcript
    }
  }
}

// 确认结束
async function confirmEnd() {
  try {
    await ElMessageBox.confirm('确定结束本次面试吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    finishPractice()
  } catch {
    // 取消
  }
}

// 完成练习
async function finishPractice() {
  // 停止录音
  if (practiceStore.isRecording) {
    await recorder.stop()
    practiceStore.isRecording = false
  }

  // 保存当前答案
  saveCurrentAnswer()
  paperTimer.stop()
  questionTimer.stop()

  step.value = 'result'
  isAnalyzing.value = true
  isStreaming.value = true
  streamContent.value = ''
  paperAnalysis.value = ''

  try {
    // 提交每道题的作答
    const answerIds: number[] = []
    for (let i = 0; i < paperAnswers.value.length; i++) {
      const ans = paperAnswers.value[i]
      const question = practiceStore.paperQuestions[i]

      if (ans.transcript) {
        const answer = await answerApi.create({
          mode: 'paper',
          question_id: question.id,
          paper_session_id: practiceStore.paperSessionId,
          transcript: ans.transcript,
          duration_seconds: ans.duration,
          started_at: new Date().toISOString(),
          finished_at: new Date().toISOString()
        })

        answerIds.push(answer.id)
        paperAnswers.value[i].answerId = answer.id

        // 触发单题分析（后台执行）
        answerApi.analyze(answer.id).catch(console.error)
      }
    }

    // 调用套卷流式分析 API
    if (practiceStore.paperSessionId) {
      await startPaperStreamAnalysis(practiceStore.paperSessionId)
    } else {
      paperAnalysis.value = '套卷分析已提交，各题分析结果可在历史记录中查看。'
      isAnalyzing.value = false
      isStreaming.value = false
    }
  } catch (e) {
    console.error('提交失败', e)
    ElMessage.error('提交失败')
    paperAnalysis.value = '分析失败，请稍后在历史记录中查看各题结果。'
    isAnalyzing.value = false
    isStreaming.value = false
  }
}

// 流式分析套卷
async function startPaperStreamAnalysis(sessionId: string) {
  try {
    const response = await fetch(`/api/v1/answers/paper-analyze/stream/${sessionId}`)

    if (response.status === 409) {
      ElMessage.warning('分析正在进行中，请稍候')
      isStreaming.value = false
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
              paperAnalysis.value = data.full_content
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
    console.error('流式分析失败', e)
    ElMessage.error('分析请求失败')
    isStreaming.value = false
    isAnalyzing.value = false
  }
}

// 重置
function reset() {
  practiceStore.resetPaper()
  paperTimer.reset()
  questionTimer.reset()
  step.value = 'select'
  paperAnalysis.value = ''
  paperAnswers.value = []
  currentTranscript.value = ''
}

// 再次练习（保留题目，重置状态）
function handleRetry() {
  const questions = [...practiceStore.paperQuestions]
  const timeLimit = practiceStore.paperTimeLimit

  if (questions.length === 0) {
    ElMessage.warning('无法重试，题目信息丢失')
    reset()
    return
  }

  paperTimer.reset(timeLimit)
  paperTimer.start()
  questionTimer.reset()
  currentTranscript.value = ''

  paperAnswers.value = questions.map(q => ({
    questionId: q.id,
    transcript: '',
    duration: 0
  }))

  practiceStore.currentQuestionIndex = 0
  isAnalyzing.value = false
  paperAnalysis.value = ''
  step.value = 'practice'
}

// 重新生成套卷分析
async function handleRegeneratePaperAnalysis() {
  if (!practiceStore.paperSessionId) {
    ElMessage.warning('无法重新生成，请重新作答')
    return
  }

  isAnalyzing.value = true
  isStreaming.value = true
  streamContent.value = ''
  paperAnalysis.value = ''

  await startPaperStreamAnalysis(practiceStore.paperSessionId)
}

onMounted(async () => {
  loadPapers()
  appStore.loadSpeechConfig()

  // 处理从题库进入的情况
  const questionIdsParam = route.query.questionIds as string
  const timeLimitParam = route.query.timeLimit as string

  if (questionIdsParam) {
    const ids = questionIdsParam.split(',').map(Number)
    const timeLimit = Number(timeLimitParam) || 900

    const questions: Question[] = []
    for (const id of ids) {
      try {
        const q = await questionApi.get(id)
        questions.push(q)
      } catch (e) {
        console.error('加载题目失败', e)
      }
    }

    if (questions.length > 0) {
      startPractice(questions, timeLimit)
    } else {
      ElMessage.error('题目加载失败')
    }
  }
})
</script>

<style scoped>
.paper-practice {
  max-width: 800px;
  margin: 0 auto;
}

.paper-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.paper-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.paper-item:hover {
  background: #e6f0ff;
}

.paper-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.paper-title {
  font-size: 16px;
  font-weight: 500;
}

.paper-meta {
  font-size: 13px;
  color: #909399;
}

.paper-timer {
  text-align: center;
  margin-bottom: 20px;
}

.question-nav {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
}

.nav-item {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  cursor: pointer;
  font-size: 14px;
}

.nav-item.active {
  background: #409eff;
  color: #fff;
}

.nav-item.answered {
  background: #67c23a;
  color: #fff;
}

.question-section {
  margin-bottom: 20px;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.question-number {
  font-weight: 500;
}

.question-content {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  line-height: 1.8;
}

.answer-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin: 15px 0;
}

.timer-display.small {
  font-size: 24px;
}

.record-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 20px 0;
}

.record-btn {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.record-btn.idle {
  background: #409eff;
  color: #fff;
}

.record-btn.recording {
  background: #f56c6c;
  color: #fff;
  animation: pulse 1.5s infinite;
}

.record-btn.transcribing {
  background: #e6a23c;
  color: #fff;
  cursor: wait;
}

.record-btn:disabled {
  cursor: wait;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.record-hint {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}

.transcript-section {
  margin: 15px 0;
}

.action-buttons {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.score-overview {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.score-label {
  font-size: 12px;
  color: #909399;
}

.score-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.analysis-content {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.7); }
  70% { box-shadow: 0 0 0 20px rgba(245, 108, 108, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0); }
}
</style>
