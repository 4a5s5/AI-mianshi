<template>
  <div class="history">
    <h2 class="page-title">历史记录</h2>

    <!-- 切换标签 -->
    <div class="page-card">
      <el-radio-group v-model="activeTab" @change="loadHistory">
        <el-radio-button label="single">单题练习</el-radio-button>
        <el-radio-button label="paper">套卷练习</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 趋势图 -->
    <div class="page-card">
      <h3>分数趋势</h3>
      <div ref="chartRef" class="trend-chart"></div>
    </div>

    <!-- 历史列表 -->
    <div class="page-card">
      <div class="history-header">
        <h3>练习记录</h3>
        <el-button
          v-if="selectedIds.length > 0"
          type="primary"
          @click="analyzeSelected"
          :loading="analyzing"
        >
          AI 综合分析 ({{ selectedIds.length }})
        </el-button>
      </div>

      <el-skeleton v-if="loading" :rows="5" animated />

      <template v-else>
        <el-empty v-if="Object.keys(historyData).length === 0" description="暂无练习记录" />

        <div v-else class="history-list">
          <div v-for="(records, date) in historyData" :key="date" class="date-group">
            <div class="date-header">{{ date }}</div>
            <div class="records">
              <div
                v-for="record in records"
                :key="record.id"
                class="record-item"
              >
                <el-checkbox
                  :model-value="selectedIds.includes(record.id)"
                  @change="toggleSelect(record.id)"
                />
                <div class="record-content" @click="viewRecord(record)">
                  <div class="record-question">{{ truncate(record.question_content, 60) }}</div>
                  <div class="record-meta">
                    <span>用时: {{ formatDuration(record.duration_seconds) }}</span>
                  </div>
                </div>
                <div class="record-score" :class="getScoreClass(record.analysis?.score)">
                  {{ record.analysis?.score ?? '-' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadHistory"
        style="margin-top: 20px; justify-content: center"
      />
    </div>

    <!-- 记录详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="练习详情" width="90%" style="max-width: 700px">
      <template v-if="selectedRecord">
        <div class="detail-section">
          <h4>题目</h4>
          <p>{{ selectedRecord.question_content }}</p>
        </div>
        <div class="detail-section">
          <h4>我的作答</h4>
          <p>{{ selectedRecord.transcript }}</p>
        </div>
        <div class="detail-section">
          <h4>用时</h4>
          <p>{{ formatDuration(selectedRecord.duration_seconds) }}</p>
        </div>
        <div v-if="selectedRecord.analysis" class="detail-section">
          <h4>AI 分析 (得分: {{ selectedRecord.analysis.score }})</h4>
          <div class="analysis-content markdown-content" v-html="formatMarkdown(selectedRecord.analysis.feedback || '')"></div>
        </div>
      </template>
    </el-dialog>

    <!-- AI 分析结果弹窗 -->
    <el-dialog v-model="showAnalysisDialog" title="AI 综合分析" width="90%" style="max-width: 800px">
      <el-skeleton v-if="analyzing" :rows="10" animated />
      <div v-else class="analysis-content markdown-content" v-html="formatMarkdown(analysisResult)"></div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { historyApi, answerApi, type AnswerWithAnalysis } from '@/api/answers'

const activeTab = ref<'single' | 'paper'>('single')
const loading = ref(false)
const analyzing = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const historyData = ref<Record<string, AnswerWithAnalysis[]>>({})
const selectedIds = ref<number[]>([])
const selectedRecord = ref<AnswerWithAnalysis | null>(null)
const showDetailDialog = ref(false)
const showAnalysisDialog = ref(false)
const analysisResult = ref('')
const chartRef = ref<HTMLElement | null>(null)

let chartInstance: echarts.ECharts | null = null

// 截断文本
function truncate(text: string | undefined, length: number): string {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}

// 格式化时长
function formatDuration(seconds: number | undefined): string {
  if (!seconds) return '0秒'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) {
    return `${mins}分${secs}秒`
  }
  return `${secs}秒`
}

// 分数样式
function getScoreClass(score: number | undefined): string {
  if (score === undefined) return ''
  if (score >= 80) return 'good'
  if (score >= 60) return 'medium'
  return 'poor'
}

// 格式化 Markdown (安全版本，防 XSS)
function formatMarkdown(text: string): string {
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
    .replace(/^-\s+(.*)/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>')
}

// 加载历史记录
async function loadHistory() {
  loading.value = true
  selectedIds.value = []

  try {
    const api = activeTab.value === 'single' ? historyApi.getSingle : historyApi.getPaper
    const data = await api({ page: currentPage.value, page_size: pageSize.value })
    historyData.value = data.items
    total.value = data.total

    // 加载趋势图
    loadTrends()
  } catch (e) {
    console.error('加载历史失败', e)
  } finally {
    loading.value = false
  }
}

// 加载趋势数据
async function loadTrends() {
  try {
    const data = await historyApi.getTrends(activeTab.value, 30)
    updateChart(data.trends)
  } catch (e) {
    console.error('加载趋势失败', e)
  }
}

// 更新图表
function updateChart(trends: Array<{ date: string; avg_score: number; count: number }>) {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: trends.map(t => t.date.slice(5))
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100
    },
    series: [{
      type: 'line',
      data: trends.map(t => t.avg_score),
      smooth: true,
      lineStyle: { color: '#409eff' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      }
    }],
    grid: { left: 40, right: 20, top: 20, bottom: 30 }
  }

  chartInstance.setOption(option)
}

// 切换选择
function toggleSelect(id: number) {
  const index = selectedIds.value.indexOf(id)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(id)
  }
}

// 查看记录详情
function viewRecord(record: AnswerWithAnalysis) {
  selectedRecord.value = record
  showDetailDialog.value = true
}

// AI 综合分析
async function analyzeSelected() {
  if (selectedIds.value.length === 0) return

  analyzing.value = true
  showAnalysisDialog.value = true

  try {
    const analysisType = activeTab.value === 'single' ? 'history_single_analyze' : 'history_paper_analyze'
    const result = await answerApi.historyAnalyze(selectedIds.value, analysisType)
    analysisResult.value = result.feedback
  } catch (e) {
    analysisResult.value = '分析失败，请稍后重试'
  } finally {
    analyzing.value = false
  }
}

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  loadHistory()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.history {
  max-width: 900px;
  margin: 0 auto;
}

.trend-chart {
  height: 200px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.history-header h3 {
  margin: 0;
}

.date-group {
  margin-bottom: 20px;
}

.date-header {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
  padding-left: 5px;
}

.records {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.record-content {
  flex: 1;
  cursor: pointer;
}

.record-question {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.record-meta {
  font-size: 12px;
  color: #909399;
}

.record-score {
  font-size: 24px;
  font-weight: bold;
  color: #909399;
  min-width: 50px;
  text-align: right;
}

.record-score.good { color: #67c23a; }
.record-score.medium { color: #e6a23c; }
.record-score.poor { color: #f56c6c; }

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  color: #909399;
  margin-bottom: 8px;
}

.detail-section p {
  line-height: 1.8;
}

.analysis-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}
</style>
