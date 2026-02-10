import { defineStore } from 'pinia'
import { ref } from 'vue'
import { speechApi, type SpeechConfig } from '@/api/config'

export const useAppStore = defineStore('app', () => {
  // 语音配置
  const speechConfig = ref<SpeechConfig | null>(null)

  // 加载语音配置
  async function loadSpeechConfig() {
    try {
      speechConfig.value = await speechApi.getConfig()
    } catch (e) {
      console.error('加载语音配置失败', e)
    }
  }

  // 更新语音配置
  async function updateSpeechConfig(data: {
    provider: string
    whisper_api_url?: string
    whisper_api_key?: string
  }) {
    speechConfig.value = await speechApi.updateConfig(data)
  }

  return {
    speechConfig,
    loadSpeechConfig,
    updateSpeechConfig
  }
})
