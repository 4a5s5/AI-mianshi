<template>
  <div class="dashboard">
    <h2 class="page-title">首页</h2>

    <!-- 快速开始 -->
    <div class="page-card">
      <h3>快速开始</h3>
      <div class="quick-actions">
        <el-button type="primary" size="large" @click="$router.push('/practice/single')">
          <el-icon><Microphone /></el-icon>
          单题练习
        </el-button>
        <el-button type="success" size="large" @click="$router.push('/practice/paper')">
          <el-icon><Document /></el-icon>
          套卷练习
        </el-button>
      </div>
    </div>

    <!-- 分数趋势 -->
    <div class="page-card">
      <div class="card-header">
        <h3>最近练习趋势</h3>
        <el-radio-group v-model="trendMode" size="small">
          <el-radio-button label="single">单题</el-radio-button>
          <el-radio-button label="paper">套卷</el-radio-button>
        </el-radio-group>
      </div>
      <div ref="chartRef" class="trend-chart"></div>
    </div>

    <!-- 最近练习 -->
    <div class="page-card">
      <h3>最近练习记录</h3>
      <el-empty v-if="recentRecords.length === 0" description="暂无练习记录" />
      <div v-else class="recent-list">
        <div
          v-for="record in recentRecords"
          :key="record.id"
          class="recent-item"
        >
          <div class="record-info">
            <span class="record-date">{{ record.practice_date }}</span>
            <span class="record-question">{{ truncate(record.question_content, 50) }}</span>
          </div>
          <div class="record-score" :class="getScoreClass(record.analysis?.score)">
            {{ record.analysis?.score ?? '-' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Microphone, Document } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { historyApi, type AnswerWithAnalysis } from '@/api/answers'

interface TrendItem {
  date: string
  avg_score: number
  count: number
}

interface TooltipParams {
  name: string
  value: number
  dataIndex: number
}

const trendMode = ref<'single' | 'paper'>('single')
const chartRef = ref<HTMLElement | null>(null)
const recentRecords = ref<AnswerWithAnalysis[]>([])

let chartInstance: echarts.ECharts | null = null

const handleResize = () => {
  chartInstance?.resize()
}

// 截断文本
function truncate(text: string | undefined, length: number): string {
  if (!text) return ''
  return text.length > length ? text.slice(0, length) + '...' : text
}

// 分数样式
function getScoreClass(score: number | undefined): string {
  if (score === undefined) return ''
  if (score >= 80) return 'good'
  if (score >= 60) return 'medium'
  return 'poor'
}

// 加载趋势数据
async function loadTrends() {
  try {
    const data = await historyApi.getTrends(trendMode.value, 30)
    updateChart(data.trends)
  } catch (e) {
    console.error('加载趋势失败', e)
  }
}

// 更新图表
function updateChart(trends: TrendItem[]) {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const data = (params as TooltipParams[])[0]
        return `${data.name}<br/>平均分: ${data.value}<br/>练习次数: ${trends[data.dataIndex]?.count || 0}`
      }
    },
    xAxis: {
      type: 'category',
      data: trends.map(t => t.date.slice(5)), // MM-DD
      axisLabel: { fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { fontSize: 11 }
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
      },
      itemStyle: { color: '#409eff' }
    }],
    grid: {
      left: 40,
      right: 20,
      top: 20,
      bottom: 30
    }
  }

  chartInstance.setOption(option)
}

// 加载最近记录
async function loadRecentRecords() {
  try {
    const data = await historyApi.getSingle({ page: 1, page_size: 5 })
    // 从分组数据中提取记录
    const records: AnswerWithAnalysis[] = []
    Object.values(data.items as Record<string, AnswerWithAnalysis[]>).forEach(dateRecords => {
      records.push(...dateRecords)
    })
    recentRecords.value = records.slice(0, 5)
  } catch (e) {
    console.error('加载最近记录失败', e)
  }
}

// 监听模式切换
watch(trendMode, () => {
  loadTrends()
})

onMounted(() => {
  loadTrends()
  loadRecentRecords()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard {
  max-width: 900px;
  margin: 0 auto;
}

.quick-actions {
  display: flex;
  gap: 20px;
  margin-top: 15px;
}

.quick-actions .el-button {
  flex: 1;
  height: 60px;
  font-size: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-header h3 {
  margin: 0;
}

.trend-chart {
  height: 250px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f5f7fa;
  border-radius: 6px;
}

.record-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.record-date {
  font-size: 12px;
  color: #909399;
}

.record-question {
  font-size: 14px;
  color: #303133;
}

.record-score {
  font-size: 24px;
  font-weight: bold;
  color: #909399;
}

.record-score.good {
  color: #67c23a;
}

.record-score.medium {
  color: #e6a23c;
}

.record-score.poor {
  color: #f56c6c;
}

@media (max-width: 768px) {
  .quick-actions {
    flex-direction: column;
  }

  .quick-actions .el-button {
    height: 50px;
  }
}
</style>
