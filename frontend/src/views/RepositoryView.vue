<template>
  <div class="repository">
    <h2 class="page-title">题库管理</h2>

    <!-- 操作栏 -->
    <div class="page-card">
      <div class="toolbar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索题目..."
          style="width: 250px"
          clearable
          @clear="loadQuestions"
          @keyup.enter="loadQuestions"
        >
          <template #append>
            <el-button @click="loadQuestions">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>

        <el-select v-model="filterCategory" placeholder="题型筛选" clearable multiple collapse-tags @change="loadQuestions">
          <el-option label="综合分析" value="综合分析" />
          <el-option label="组织协调" value="组织协调" />
          <el-option label="应急应变" value="应急应变" />
          <el-option label="人际关系" value="人际关系" />
          <el-option label="自我认知" value="自我认知" />
        </el-select>

        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加题目
        </el-button>

        <el-button @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>
          导入题库
        </el-button>

        <!-- 批量操作按钮组 -->
        <template v-if="selectedQuestions.length > 0">
          <el-divider direction="vertical" />
          <span class="selected-count">已选 {{ selectedQuestions.length }} 题</span>
          <el-button type="danger" @click="handleBatchDelete">删除选中</el-button>
          <el-button type="primary" @click="handleStartPractice">开始练习</el-button>
        </template>
      </div>
    </div>

    <!-- 题目列表 -->
    <div class="page-card">
      <el-table :data="questions" v-loading="loading" style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="category" label="题型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="题目">
          <template #default="{ row }">
            <span class="question-text">{{ truncate(row.content, 80) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button text size="small" @click="viewQuestion(row)">查看</el-button>
            <el-button text size="small" @click="editQuestion(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click="deleteQuestion(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadQuestions"
        style="margin-top: 20px; justify-content: center"
      />
    </div>

    <!-- 添加/编辑题目弹窗 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingQuestion ? '编辑题目' : '添加题目'"
      width="90%"
      style="max-width: 700px"
    >
      <el-form :model="questionForm" label-position="top">
        <el-form-item label="题型" required>
          <el-select v-model="questionForm.category" style="width: 100%">
            <el-option label="综合分析" value="综合分析" />
            <el-option label="组织协调" value="组织协调" />
            <el-option label="应急应变" value="应急应变" />
            <el-option label="人际关系" value="人际关系" />
            <el-option label="自我认知" value="自我认知" />
          </el-select>
        </el-form-item>
        <el-form-item label="题目内容" required>
          <el-input v-model="questionForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="解析">
          <el-input v-model="questionForm.analysis" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="参考答案">
          <el-input v-model="questionForm.reference_answer" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="questionForm.tags" placeholder="用逗号分隔多个标签" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeAddDialog">取消</el-button>
        <el-button type="primary" @click="saveQuestion" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看题目弹窗 -->
    <el-dialog v-model="showViewDialog" title="题目详情" width="90%" style="max-width: 700px">
      <template v-if="viewingQuestion">
        <div class="detail-item">
          <label>题型：</label>
          <el-tag>{{ viewingQuestion.category }}</el-tag>
        </div>
        <div class="detail-item">
          <label>题目：</label>
          <p>{{ viewingQuestion.content }}</p>
        </div>
        <div v-if="viewingQuestion.analysis" class="detail-item">
          <label>解析：</label>
          <p>{{ viewingQuestion.analysis }}</p>
        </div>
        <div v-if="viewingQuestion.reference_answer" class="detail-item">
          <label>参考答案：</label>
          <p>{{ viewingQuestion.reference_answer }}</p>
        </div>
      </template>
    </el-dialog>

    <!-- 导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="导入题库" width="90%" style="max-width: 600px" @close="resetImport" :close-on-click-modal="!importing">
      <el-form label-position="top">
        <el-form-item label="导入类型">
          <el-radio-group v-model="importType" :disabled="importing">
            <el-radio label="single">单题导入</el-radio>
            <el-radio label="paper">套卷导入</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="导入方式">
          <el-radio-group v-model="importMode" :disabled="importing">
            <el-radio label="file">文件上传</el-radio>
            <el-radio label="text">文本输入</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="importMode === 'file'" label="上传文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            multiple
            accept=".txt,.pdf"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :disabled="importing"
          >
            <el-button :disabled="importing">选择文件 (TXT/PDF，可多选)</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item v-else label="文本内容">
          <el-input
            v-model="importTextContent"
            type="textarea"
            :rows="10"
            placeholder="请粘贴题目内容..."
            :disabled="importing"
          />
        </el-form-item>
      </el-form>

      <!-- 多文件导入进度 -->
      <div v-if="importTasks.length > 0" class="import-progress">
        <h4>导入进度</h4>
        <div v-for="(task, index) in importTasks" :key="index" class="import-task-item">
          <div class="import-task-info">
            <span class="import-task-name">{{ task.fileName }}</span>
            <el-tag
              :type="task.status === 'success' ? 'success' : task.status === 'failed' ? 'danger' : task.status === 'processing' ? '' : 'info'"
              size="small"
            >
              {{ task.status === 'pending' ? '等待中' : task.status === 'uploading' ? '上传中' : task.status === 'processing' ? '处理中' : task.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </div>
          <div v-if="task.message" class="import-task-message" :class="{ error: task.status === 'failed' }">
            {{ task.message }}
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showImportDialog = false" :disabled="importing">取消</el-button>
        <el-button
          type="primary"
          @click="doImport"
          :loading="importing"
          :disabled="importMode === 'file' ? importFiles.length === 0 : !importTextContent.trim()"
        >
          {{ importing ? '导入中...' : '开始导入' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 练习时限设置弹窗 -->
    <el-dialog v-model="showTimeLimitDialog" title="设置练习时限" width="400px">
      <el-form label-position="top">
        <el-form-item label="时限（分钟）">
          <el-input-number v-model="practiceTimeLimit" :min="1" :max="60" style="width: 100%" />
        </el-form-item>
        <p style="color: #909399; font-size: 14px;">
          已选择 {{ selectedQuestions.length }} 道题目，将以套卷模式进行练习
        </p>
      </el-form>
      <template #footer>
        <el-button @click="showTimeLimitDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmStartPractice">开始练习</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Upload } from '@element-plus/icons-vue'
import { questionApi, type Question } from '@/api/questions'
import { importApi } from '@/api/import'

const router = useRouter()

const questions = ref<Question[]>([])
const loading = ref(false)
const saving = ref(false)
const importing = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterCategory = ref<string[]>([])
const selectedQuestions = ref<Question[]>([])

const showAddDialog = ref(false)
const showViewDialog = ref(false)
const showImportDialog = ref(false)
const editingQuestion = ref<Question | null>(null)
const viewingQuestion = ref<Question | null>(null)
const importType = ref('single')
const importFiles = ref<File[]>([])
const importMode = ref('file')
const importTextContent = ref('')
const showTimeLimitDialog = ref(false)
const practiceTimeLimit = ref(15)

// 多文件导入任务状态
interface ImportTaskStatus {
  fileName: string
  status: 'pending' | 'uploading' | 'processing' | 'success' | 'failed'
  message: string
}
const importTasks = ref<ImportTaskStatus[]>([])

const questionForm = reactive({
  category: '',
  content: '',
  analysis: '',
  reference_answer: '',
  tags: ''
})

// 截断文本
function truncate(text: string, length: number): string {
  return text.length > length ? text.slice(0, length) + '...' : text
}

// 加载题目列表
async function loadQuestions() {
  loading.value = true
  try {
    const data = await questionApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
      category: filterCategory.value.length > 0 ? filterCategory.value.join(',') : undefined,
      keyword: searchKeyword.value || undefined
    })
    questions.value = data.items
    total.value = data.total
  } catch (e) {
    console.error('加载题目失败', e)
  } finally {
    loading.value = false
  }
}

// 查看题目
function viewQuestion(question: Question) {
  viewingQuestion.value = question
  showViewDialog.value = true
}

// 编辑题目
function editQuestion(question: Question) {
  editingQuestion.value = question
  Object.assign(questionForm, {
    category: question.category,
    content: question.content,
    analysis: question.analysis || '',
    reference_answer: question.reference_answer || '',
    tags: question.tags || ''
  })
  showAddDialog.value = true
}

// 删除题目
async function deleteQuestion(question: Question) {
  try {
    await ElMessageBox.confirm('确定删除该题目吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await questionApi.delete(question.id)
    ElMessage.success('删除成功')
    loadQuestions()
  } catch {
    // 取消
  }
}

// 保存题目
async function saveQuestion() {
  if (!questionForm.category || !questionForm.content) {
    ElMessage.warning('请填写题型和题目内容')
    return
  }

  saving.value = true
  try {
    if (editingQuestion.value) {
      await questionApi.update(editingQuestion.value.id, questionForm)
      ElMessage.success('更新成功')
    } else {
      await questionApi.create(questionForm)
      ElMessage.success('添加成功')
    }
    closeAddDialog()
    loadQuestions()
  } catch (e) {
    console.error('保存失败', e)
  } finally {
    saving.value = false
  }
}

// 关闭添加弹窗
function closeAddDialog() {
  showAddDialog.value = false
  editingQuestion.value = null
  Object.assign(questionForm, {
    category: '',
    content: '',
    analysis: '',
    reference_answer: '',
    tags: ''
  })
}

// 处理文件选择
function handleFileChange(file: { raw: File }) {
  importFiles.value.push(file.raw)
}

// 处理文件移除
function handleFileRemove(file: { raw: File }) {
  const index = importFiles.value.indexOf(file.raw)
  if (index > -1) {
    importFiles.value.splice(index, 1)
  }
}

// 等待单个导入任务完成
async function waitForImportTask(importId: number): Promise<{ success: boolean; message: string }> {
  const maxAttempts = 300
  let attempts = 0

  return new Promise((resolve) => {
    const poll = async () => {
      try {
        const status = await importApi.getStatus(importId)
        if (status.status === 'success') {
          resolve({ success: true, message: status.result_summary || '导入成功' })
        } else if (status.status === 'failed') {
          resolve({ success: false, message: status.error_message || '导入失败' })
        } else if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 1000)
        } else {
          resolve({ success: false, message: '导入超时，请在导入历史中查看结果' })
        }
      } catch {
        resolve({ success: false, message: '查询导入状态失败' })
      }
    }
    poll()
  })
}

// 执行导入
async function doImport() {
  importing.value = true
  importTasks.value = []

  try {
    if (importMode.value === 'text') {
      // 文本模式：单次导入，逻辑不变
      if (!importTextContent.value.trim()) {
        ElMessage.warning('请输入文本内容')
        importing.value = false
        return
      }
      importTasks.value = [{ fileName: '文本导入', status: 'uploading', message: '' }]
      const result = await importApi.importText(importTextContent.value, importType.value)
      importTasks.value[0].status = 'processing'
      const taskResult = await waitForImportTask(result.import_id)
      importTasks.value[0].status = taskResult.success ? 'success' : 'failed'
      importTasks.value[0].message = taskResult.message
      if (taskResult.success) {
        loadQuestions()
      }
    } else {
      // 文件模式：串行逐文件上传+等待
      if (importFiles.value.length === 0) {
        ElMessage.warning('请选择文件')
        importing.value = false
        return
      }

      // 初始化所有任务状态
      importTasks.value = importFiles.value.map(f => ({
        fileName: f.name,
        status: 'pending' as const,
        message: ''
      }))

      let successCount = 0
      let failCount = 0

      // 串行处理每个文件
      for (let i = 0; i < importFiles.value.length; i++) {
        const file = importFiles.value[i]
        importTasks.value[i].status = 'uploading'

        try {
          let result
          if (importType.value === 'single') {
            result = await importApi.importSingle(file)
          } else {
            result = await importApi.importPaper(file)
          }

          importTasks.value[i].status = 'processing'

          // 等待后台处理完成
          const taskResult = await waitForImportTask(result.import_id)
          importTasks.value[i].status = taskResult.success ? 'success' : 'failed'
          importTasks.value[i].message = taskResult.message

          if (taskResult.success) {
            successCount++
          } else {
            failCount++
          }
        } catch (e) {
          importTasks.value[i].status = 'failed'
          importTasks.value[i].message = '上传失败'
          failCount++
        }
      }

      // 汇总结果
      if (successCount > 0) {
        loadQuestions()
      }
      if (failCount === 0) {
        ElMessage.success(`全部 ${successCount} 个文件导入成功`)
      } else if (successCount === 0) {
        ElMessage.error(`全部 ${failCount} 个文件导入失败`)
      } else {
        ElMessage.warning(`${successCount} 个成功，${failCount} 个失败`)
      }
    }
  } catch (e) {
    console.error('导入失败', e)
  } finally {
    importing.value = false
  }
}

// 重置导入弹窗
function resetImport() {
  importFiles.value = []
  importTextContent.value = ''
  importTasks.value = []
}

// 处理表格选择变化
function handleSelectionChange(selection: Question[]) {
  selectedQuestions.value = selection
}

// 批量删除
async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedQuestions.value.length} 道题目吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await questionApi.batchDelete(selectedQuestions.value.map(q => q.id))
    ElMessage.success('删除成功')
    selectedQuestions.value = []
    await loadQuestions()
  } catch {
    // 取消
  }
}

// 开始练习
function handleStartPractice() {
  if (selectedQuestions.value.length === 1) {
    router.push({
      path: '/practice/single',
      query: { questionId: selectedQuestions.value[0].id.toString() }
    })
  } else {
    showTimeLimitDialog.value = true
  }
}

function confirmStartPractice() {
  showTimeLimitDialog.value = false
  router.push({
    path: '/practice/paper',
    query: {
      questionIds: selectedQuestions.value.map(q => q.id).join(','),
      timeLimit: (practiceTimeLimit.value * 60).toString()
    }
  })
}

onMounted(() => {
  loadQuestions()
})
</script>

<style scoped>
.repository {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 15px;
}

.toolbar {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: center;
}

.question-text {
  color: #606266;
}

.selected-count {
  color: #409eff;
  font-weight: 500;
}

.detail-item {
  margin-bottom: 15px;
}

.detail-item label {
  font-weight: 500;
  color: #909399;
  display: block;
  margin-bottom: 5px;
}

.detail-item p {
  line-height: 1.8;
  color: #303133;
}

.import-progress {
  margin-top: 15px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.import-progress h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
}

.import-task-item {
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.import-task-item:last-child {
  border-bottom: none;
}

.import-task-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.import-task-name {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 70%;
}

.import-task-message {
  font-size: 12px;
  color: #67c23a;
  margin-top: 4px;
}

.import-task-message.error {
  color: #f56c6c;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
  }

  .toolbar .el-input {
    width: 100% !important;
  }
}
</style>
