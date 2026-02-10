<template>
  <div class="page-card">
    <div class="question-section">
      <div class="question-header">
        <el-tag v-if="question?.category" type="info">
          {{ question.category }}
        </el-tag>
        <el-button text @click="emit('back')">
          <el-icon><Back /></el-icon>
          返回选题
        </el-button>
      </div>
      <div class="question-content">
        {{ question?.content }}
      </div>
    </div>

    <!-- 计时器 -->
    <div class="timer-section">
      <span class="timer-label">作答时长</span>
      <span class="timer-display" :class="{ recording: isRecording }">
        {{ formattedTime }}
      </span>
    </div>

    <!-- 录音控制 -->
    <div class="record-section">
      <button
        type="button"
        class="record-btn"
        :class="{ idle: !isRecording, recording: isRecording }"
        :aria-label="isRecording ? '结束录音' : '开始录音'"
        :aria-pressed="isRecording"
        @click="toggleRecording"
      >
        <el-icon :size="32">
          <Microphone v-if="!isRecording" />
          <VideoPause v-else />
        </el-icon>
      </button>
      <p class="record-hint">
        {{ isRecording ? '点击结束作答' : '点击开始作答' }}
      </p>
    </div>

    <!-- 转写文本 -->
    <div class="transcript-section">
      <h4>作答内容</h4>
      <el-input
        v-model="transcript"
        type="textarea"
        :rows="6"
        placeholder="录音转写内容将显示在这里，您也可以手动编辑..."
      />
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="emit('back')">取消</el-button>
      <el-button
        type="primary"
        @click="submitAnswer"
        :disabled="!transcript.trim()"
      >
        面试结束，提交分析
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone, VideoPause, Back } from '@element-plus/icons-vue'
import { useTimer } from '@/composables/useTimer'
import { useRecorder } from '@/composables/useRecorder'
import { useAppStore } from '@/store/app'

export interface Question {
  id: number
  content: string
  category?: string
}

const props = defineProps<{
  question: Question
}>()

const emit = defineEmits<{
  back: []
  complete: [data: { transcript: string; duration: number }]
}>()

const appStore = useAppStore()
const timer = useTimer('countup')
const recorder = useRecorder()

const isRecording = ref(false)
const transcript = ref('')

const formattedTime = computed(() => timer.formatted.value)

async function toggleRecording() {
  if (!isRecording.value) {
    try {
      await recorder.start()
      isRecording.value = true
      timer.start()
    } catch (e) {
      ElMessage.error('无法启动录音，请检查麦克风权限')
    }
  } else {
    const result = await recorder.stop()
    isRecording.value = false
    timer.stop()
    if (result.transcript) {
      transcript.value = result.transcript
    }
  }
}

async function submitAnswer() {
  if (!transcript.value.trim()) {
    ElMessage.warning('请先进行作答')
    return
  }

  if (isRecording.value) {
    const result = await recorder.stop()
    isRecording.value = false
    timer.stop()
    if (result.transcript) {
      transcript.value = result.transcript
    }
  }

  emit('complete', {
    transcript: transcript.value,
    duration: timer.seconds.value
  })
}

onMounted(() => {
  appStore.loadSpeechConfig()
})
</script>

<style scoped>
.question-section {
  margin-bottom: 20px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.question-content {
  font-size: 16px;
  line-height: 1.8;
  color: #303133;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.timer-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin: 20px 0;
}

.timer-label {
  color: #909399;
}

.timer-display {
  font-size: 36px;
  font-weight: bold;
  font-family: 'Courier New', monospace;
}

.timer-display.recording {
  color: #f56c6c;
}

.record-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 30px 0;
}

.record-btn {
  width: 100px;
  height: 100px;
  border: none;
  border-radius: 50%;
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

.record-btn.idle:hover {
  background: #66b1ff;
}

.record-btn.recording {
  background: #f56c6c;
  color: #fff;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.7); }
  70% { box-shadow: 0 0 0 25px rgba(245, 108, 108, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0); }
}

.record-hint {
  margin-top: 10px;
  color: #909399;
}

.transcript-section {
  margin: 20px 0;
}

.transcript-section h4 {
  margin-bottom: 10px;
  color: #606266;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .timer-display {
    font-size: 28px;
  }

  .record-btn {
    width: 80px;
    height: 80px;
  }
}
</style>
