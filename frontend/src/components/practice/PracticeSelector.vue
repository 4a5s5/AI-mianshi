<template>
  <div class="page-card">
    <h3>选择练习方式</h3>
    <div class="select-options">
      <el-button type="primary" size="large" @click="handleRandom">
        <el-icon><Refresh /></el-icon>
        随机抽取题目
      </el-button>
      <el-button size="large" @click="showCustomInput = true">
        <el-icon><Edit /></el-icon>
        自由输入题目
      </el-button>
    </div>

    <!-- 题型筛选 -->
    <div class="category-filter">
      <span>题型筛选：</span>
      <el-select v-model="category" placeholder="全部题型" clearable style="width: 150px">
        <el-option label="综合分析" value="综合分析" />
        <el-option label="组织协调" value="组织协调" />
        <el-option label="应急应变" value="应急应变" />
        <el-option label="人际关系" value="人际关系" />
        <el-option label="自我认知" value="自我认知" />
      </el-select>
    </div>

    <!-- 自定义输入 -->
    <el-dialog v-model="showCustomInput" title="输入题目" width="90%" style="max-width: 600px">
      <el-form label-position="top">
        <el-form-item label="题目内容">
          <el-input
            v-model="customQuestion"
            type="textarea"
            :rows="5"
            placeholder="请输入面试题目..."
          />
        </el-form-item>
        <el-form-item label="题目分类">
          <el-select v-model="customCategory" placeholder="请选择题型" style="width: 100%">
            <el-option label="综合分析" value="综合分析" />
            <el-option label="组织协调" value="组织协调" />
            <el-option label="应急应变" value="应急应变" />
            <el-option label="人际关系" value="人际关系" />
            <el-option label="自我认知" value="自我认知" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCustomInput = false">取消</el-button>
        <el-button type="primary" @click="submitCustom" :disabled="!customQuestion.trim() || !customCategory" :loading="loading">
          {{ loading ? '保存中...' : '确定' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Refresh, Edit } from '@element-plus/icons-vue'

defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  random: [category: string | undefined]
  custom: [data: { content: string, category: string }]
}>()

const category = ref('')
const showCustomInput = ref(false)
const customQuestion = ref('')
const customCategory = ref('综合分析')

function handleRandom() {
  emit('random', category.value || undefined)
}

function submitCustom() {
  if (customQuestion.value.trim() && customCategory.value) {
    emit('custom', {
      content: customQuestion.value.trim(),
      category: customCategory.value
    })
    showCustomInput.value = false
    customQuestion.value = ''
  }
}
</script>

<style scoped>
.select-options {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.select-options .el-button {
  flex: 1;
  height: 60px;
  font-size: 16px;
}

.category-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #606266;
}

@media (max-width: 768px) {
  .select-options {
    flex-direction: column;
  }

  .select-options .el-button {
    height: 50px;
  }
}
</style>
