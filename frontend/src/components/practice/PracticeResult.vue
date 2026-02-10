<template>
  <div class="page-card">
    <div class="result-header">
      <h3>AI 分析结果</h3>
      <div v-if="analysis" class="score-display" :class="scoreClass">
        {{ analysis.score }} 分
      </div>
    </div>

    <!-- 流式输出中 -->
    <div v-if="streaming && streamContent" class="analysis-content markdown-content streaming">
      <div v-html="streamHtml"></div>
      <span class="cursor">▌</span>
    </div>

    <el-skeleton v-else-if="loading" :rows="10" animated />

    <div v-else-if="analysis" class="analysis-content markdown-content">
      <div v-html="safeHtml"></div>
    </div>

    <div class="result-actions">
      <el-button @click="emit('regenerate')" :disabled="streaming || loading">重新生成</el-button>
      <el-button @click="emit('retry')" :disabled="streaming">再次练习</el-button>
      <el-button @click="emit('restart')" :disabled="streaming">换题练习</el-button>
      <el-button type="primary" @click="goHistory" :disabled="streaming">查看历史记录</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { AnalysisResult } from '@/api/answers'

const props = defineProps<{
  analysis: AnalysisResult | null
  loading: boolean
  streaming?: boolean
  streamContent?: string
}>()

const emit = defineEmits<{
  restart: []
  retry: []
  regenerate: []
}>()

const router = useRouter()

const scoreClass = computed(() => {
  const score = props.analysis?.score
  if (score === undefined) return ''
  if (score >= 80) return 'good'
  if (score >= 60) return 'medium'
  return 'poor'
})

const safeHtml = computed(() => {
  const text = props.analysis?.feedback || ''
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
  return escaped
    .replace(/###\s*(.*)/g, '<h4>$1</h4>')
    .replace(/##\s*(.*)/g, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^-\s+(.*)/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>')
})

const streamHtml = computed(() => {
  const text = props.streamContent || ''
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
  return escaped
    .replace(/###\s*(.*)/g, '<h4>$1</h4>')
    .replace(/##\s*(.*)/g, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^-\s+(.*)/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>')
})

function goHistory() {
  router.push('/history')
}
</script>

<style scoped>
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.score-display {
  font-size: 24px;
  font-weight: bold;
}

.score-display.good {
  color: #67c23a;
}

.score-display.medium {
  color: #e6a23c;
}

.score-display.poor {
  color: #f56c6c;
}

.analysis-content {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  max-height: 500px;
  overflow-y: auto;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

.streaming .cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
