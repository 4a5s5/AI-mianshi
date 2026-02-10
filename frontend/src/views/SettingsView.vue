<template>
  <div class="settings">
    <h2 class="page-title">系统设置</h2>

    <!-- AI 模型配置 -->
    <div class="page-card">
      <div class="section-header">
        <h3>AI 模型配置</h3>
        <el-button type="primary" size="small" @click="showAddModel = true">
          <el-icon><Plus /></el-icon>
          添加配置
        </el-button>
      </div>

      <!-- 作答分析模型 -->
      <div class="model-section">
        <h4>作答分析模型</h4>
        <el-empty v-if="analyzeModels.length === 0" description="暂无配置" :image-size="60" />
        <div v-else class="model-list">
          <div
            v-for="model in analyzeModels"
            :key="model.id"
            class="model-item"
            :class="{ active: model.is_active }"
          >
            <div class="model-info">
              <span class="model-name">{{ model.name }}</span>
              <span class="model-detail">{{ model.model_name }}</span>
            </div>
            <div class="model-actions">
              <el-button
                v-if="!model.is_active"
                text
                size="small"
                @click="activateModel(model.id)"
              >
                激活
              </el-button>
              <el-tag v-else type="success" size="small">已激活</el-tag>
              <el-button text size="small" @click="editModel(model)">编辑</el-button>
              <el-button text size="small" type="danger" @click="deleteModel(model.id)">删除</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 题库导入模型 -->
      <div class="model-section">
        <h4>题库导入模型</h4>
        <el-empty v-if="importModels.length === 0" description="暂无配置" :image-size="60" />
        <div v-else class="model-list">
          <div
            v-for="model in importModels"
            :key="model.id"
            class="model-item"
            :class="{ active: model.is_active }"
          >
            <div class="model-info">
              <span class="model-name">{{ model.name }}</span>
              <span class="model-detail">{{ model.model_name }}</span>
            </div>
            <div class="model-actions">
              <el-button
                v-if="!model.is_active"
                text
                size="small"
                @click="activateModel(model.id)"
              >
                激活
              </el-button>
              <el-tag v-else type="success" size="small">已激活</el-tag>
              <el-button text size="small" @click="editModel(model)">编辑</el-button>
              <el-button text size="small" type="danger" @click="deleteModel(model.id)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 语音转写配置 -->
    <div class="page-card">
      <h3>语音转写配置</h3>
      <el-form label-position="top">
        <el-form-item label="转写方式">
          <el-radio-group v-model="speechProvider" @change="saveSpeechConfig">
            <el-radio label="web_speech">浏览器语音识别 (免费)</el-radio>
            <el-radio label="whisper">OpenAI Whisper API</el-radio>
          </el-radio-group>
        </el-form-item>

        <template v-if="speechProvider === 'whisper'">
          <el-form-item label="Whisper API URL">
            <el-input v-model="whisperUrl" placeholder="https://api.openai.com/v1" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="whisperKey" type="password" show-password />
          </el-form-item>
          <el-button type="primary" @click="saveSpeechConfig">保存</el-button>
        </template>
      </el-form>
    </div>

    <!-- 提示词管理 -->
    <div class="page-card">
      <h3>提示词管理</h3>
      <div class="prompt-list">
        <div
          v-for="prompt in prompts"
          :key="prompt.id"
          class="prompt-item"
          @click="editPrompt(prompt)"
        >
          <span class="prompt-title">{{ prompt.title }}</span>
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 添加/编辑模型弹窗 -->
    <el-dialog
      v-model="showAddModel"
      :title="editingModel ? '编辑模型配置' : '添加模型配置'"
      width="90%"
      style="max-width: 500px"
    >
      <el-form :model="modelForm" label-position="top">
        <el-form-item label="配置名称" required>
          <el-input v-model="modelForm.name" placeholder="如：GPT-4 分析" />
        </el-form-item>
        <el-form-item label="用途" required>
          <el-radio-group v-model="modelForm.role">
            <el-radio label="analyze">作答分析</el-radio>
            <el-radio label="import">题库导入</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="API Base URL" required>
          <el-input v-model="modelForm.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key" :required="!editingModel">
          <el-input
            v-model="modelForm.api_key"
            type="password"
            show-password
            :placeholder="editingModel ? (editingModel.api_key_masked || '留空则保持原密钥') : '请输入 API Key'"
          />
          <div v-if="editingModel" class="form-tip">留空则保持原密钥</div>
        </el-form-item>
        <el-form-item label="模型">
          <div class="model-select-row">
            <el-select v-model="modelForm.model_name" placeholder="选择模型" style="flex: 1">
              <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
            </el-select>
            <el-button @click="fetchModels" :loading="fetchingModels">获取模型</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeModelDialog">取消</el-button>
        <el-button type="primary" @click="saveModel" :loading="savingModel">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑提示词弹窗 -->
    <el-dialog
      v-model="showEditPrompt"
      :title="editingPrompt?.title || '编辑提示词'"
      width="90%"
      style="max-width: 800px"
    >
      <el-form label-position="top">
        <el-form-item label="提示词内容">
          <el-input
            v-model="promptContent"
            type="textarea"
            :rows="15"
            placeholder="输入提示词..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditPrompt = false">取消</el-button>
        <el-button type="primary" @click="savePrompt" :loading="savingPrompt">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowRight } from '@element-plus/icons-vue'
import { modelApi, promptApi, speechApi, type ModelConfig, type Prompt } from '@/api/config'
import { useAppStore } from '@/store/app'

const appStore = useAppStore()

const models = ref<ModelConfig[]>([])
const prompts = ref<Prompt[]>([])
const showAddModel = ref(false)
const showEditPrompt = ref(false)
const editingModel = ref<ModelConfig | null>(null)
const editingPrompt = ref<Prompt | null>(null)
const promptContent = ref('')
const savingModel = ref(false)
const savingPrompt = ref(false)
const fetchingModels = ref(false)
const availableModels = ref<string[]>([])

// 语音配置
const speechProvider = ref('web_speech')
const whisperUrl = ref('')
const whisperKey = ref('')

// 按用途分组模型
const analyzeModels = computed(() => models.value.filter(m => m.role === 'analyze'))
const importModels = computed(() => models.value.filter(m => m.role === 'import'))

const modelForm = reactive({
  name: '',
  role: 'analyze',
  base_url: '',
  api_key: '',
  model_name: ''
})

// 加载模型配置
async function loadModels() {
  try {
    models.value = await modelApi.list()
  } catch (e) {
    console.error('加载模型配置失败', e)
  }
}

// 加载提示词
async function loadPrompts() {
  try {
    prompts.value = await promptApi.list()
  } catch (e) {
    console.error('加载提示词失败', e)
  }
}

// 加载语音配置
async function loadSpeechConfig() {
  try {
    const config = await speechApi.getConfig()
    speechProvider.value = config.provider
    whisperUrl.value = config.whisper_api_url || ''
    whisperKey.value = config.whisper_api_key || ''
  } catch (e) {
    console.error('加载语音配置失败', e)
  }
}

// 获取可用模型
async function fetchModels() {
  if (!modelForm.base_url || !modelForm.api_key) {
    ElMessage.warning('请先填写 API URL 和 Key')
    return
  }

  fetchingModels.value = true
  try {
    const result = await modelApi.fetchModels(modelForm.base_url, modelForm.api_key)
    availableModels.value = result.models
    if (result.models.length > 0) {
      ElMessage.success(`获取到 ${result.models.length} 个模型`)
    } else {
      ElMessage.warning('未获取到模型')
    }
  } catch (e) {
    ElMessage.error('获取模型列表失败')
  } finally {
    fetchingModels.value = false
  }
}

// 编辑模型
function editModel(model: ModelConfig) {
  editingModel.value = model
  Object.assign(modelForm, {
    name: model.name,
    role: model.role,
    base_url: model.base_url,
    api_key: '',
    model_name: model.model_name
  })
  showAddModel.value = true
}

// 保存模型
async function saveModel() {
  if (!modelForm.name || !modelForm.base_url || !modelForm.model_name) {
    ElMessage.warning('请填写完整信息')
    return
  }

  if (!editingModel.value && !modelForm.api_key) {
    ElMessage.warning('请填写 API Key')
    return
  }

  savingModel.value = true
  try {
    if (editingModel.value) {
      const updateData: {
        name: string
        base_url: string
        model_name: string
        api_key?: string
      } = {
        name: modelForm.name,
        base_url: modelForm.base_url,
        model_name: modelForm.model_name
      }
      if (modelForm.api_key) {
        updateData.api_key = modelForm.api_key
      }
      await modelApi.update(editingModel.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      await modelApi.create(modelForm)
      ElMessage.success('添加成功')
    }
    closeModelDialog()
    loadModels()
  } catch (e) {
    console.error('保存失败', e)
  } finally {
    savingModel.value = false
  }
}

// 激活模型
async function activateModel(id: number) {
  try {
    await modelApi.activate(id)
    ElMessage.success('已激活')
    loadModels()
  } catch (e) {
    console.error('激活失败', e)
  }
}

// 删除模型
async function deleteModel(id: number) {
  try {
    await ElMessageBox.confirm('确定删除该配置吗？', '提示', {
      type: 'warning'
    })
    await modelApi.delete(id)
    ElMessage.success('已删除')
    loadModels()
  } catch {
    // 取消
  }
}

// 关闭模型弹窗
function closeModelDialog() {
  showAddModel.value = false
  editingModel.value = null
  Object.assign(modelForm, {
    name: '',
    role: 'analyze',
    base_url: '',
    api_key: '',
    model_name: ''
  })
  availableModels.value = []
}

// 编辑提示词
function editPrompt(prompt: Prompt) {
  editingPrompt.value = prompt
  promptContent.value = prompt.content
  showEditPrompt.value = true
}

// 保存提示词
async function savePrompt() {
  if (!editingPrompt.value) return

  savingPrompt.value = true
  try {
    await promptApi.update(editingPrompt.value.id, { content: promptContent.value })
    ElMessage.success('保存成功')
    showEditPrompt.value = false
    loadPrompts()
  } catch (e) {
    console.error('保存失败', e)
  } finally {
    savingPrompt.value = false
  }
}

// 保存语音配置
async function saveSpeechConfig() {
  try {
    await speechApi.updateConfig({
      provider: speechProvider.value,
      whisper_api_url: whisperUrl.value || undefined,
      whisper_api_key: whisperKey.value || undefined
    })
    ElMessage.success('保存成功')
    appStore.loadSpeechConfig()
  } catch (e) {
    console.error('保存失败', e)
  }
}

onMounted(() => {
  loadModels()
  loadPrompts()
  loadSpeechConfig()
})
</script>

<style scoped>
.settings {
  max-width: 800px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
}

.model-section {
  margin-bottom: 25px;
}

.model-section h4 {
  color: #909399;
  margin-bottom: 10px;
  font-size: 14px;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 2px solid transparent;
}

.model-item.active {
  border-color: #67c23a;
  background: #f0f9eb;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.model-name {
  font-weight: 500;
}

.model-detail {
  font-size: 12px;
  color: #909399;
}

.model-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.model-select-row {
  display: flex;
  gap: 10px;
}

.prompt-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.prompt-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.prompt-item:hover {
  background: #e6f0ff;
}

.prompt-title {
  font-weight: 500;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
