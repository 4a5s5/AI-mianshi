import { ref, onUnmounted } from 'vue'
import { useAppStore } from '@/store/app'
import request from '@/api/request'

export interface RecorderResult {
  transcript: string
  duration: number
}

export function useRecorder() {
  const appStore = useAppStore()

  const isRecording = ref(false)
  const isSupported = ref(true)
  const transcript = ref('')
  const error = ref<string | null>(null)
  const isTranscribing = ref(false)

  let recognition: SpeechRecognition | null = null
  let mediaRecorder: MediaRecorder | null = null
  let audioChunks: Blob[] = []
  let startTime: number = 0

  // 检查浏览器支持
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    isSupported.value = false
  }

  // 使用 Web Speech API
  function startWebSpeech(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!SpeechRecognition) {
        reject(new Error('浏览器不支持语音识别'))
        return
      }

      recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'zh-CN'

      recognition.onstart = () => {
        isRecording.value = true
        startTime = Date.now()
        resolve()
      }

      recognition.onresult = (event) => {
        let finalTranscript = ''
        let interimTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i]
          if (result.isFinal) {
            finalTranscript += result[0].transcript
          } else {
            interimTranscript += result[0].transcript
          }
        }

        if (finalTranscript) {
          transcript.value += finalTranscript
        }
      }

      recognition.onerror = (event) => {
        error.value = `语音识别错误: ${event.error}`
        isRecording.value = false
      }

      recognition.onend = () => {
        isRecording.value = false
      }

      recognition.start()
    })
  }

  // 停止 Web Speech API
  function stopWebSpeech(): Promise<RecorderResult> {
    return new Promise((resolve) => {
      const duration = Math.floor((Date.now() - startTime) / 1000)

      if (!recognition) {
        isRecording.value = false
        resolve({ transcript: transcript.value, duration })
        return
      }

      // 超时保护，避免 onend 永不触发
      const timeout = setTimeout(() => {
        isRecording.value = false
        recognition = null
        resolve({ transcript: transcript.value, duration })
      }, 3000)

      // 等待 onend 事件，确保所有 pending 的 onresult 已触发
      recognition.onend = () => {
        clearTimeout(timeout)
        isRecording.value = false
        recognition = null
        resolve({ transcript: transcript.value, duration })
      }

      recognition.stop()
    })
  }

  // 使用 MediaRecorder 录音（用于 Whisper API）
  async function startMediaRecorder(): Promise<void> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      audioChunks = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      mediaRecorder.start(1000) // 每秒收集一次数据
      isRecording.value = true
      startTime = Date.now()
    } catch (e) {
      error.value = '无法访问麦克风'
      throw e
    }
  }

  // 停止 MediaRecorder 并上传到 Whisper API
  async function stopMediaRecorder(): Promise<RecorderResult> {
    return new Promise(async (resolve) => {
      if (!mediaRecorder) {
        resolve({ transcript: '', duration: 0 })
        return
      }

      const duration = Math.floor((Date.now() - startTime) / 1000)

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })

        // 停止所有音轨
        mediaRecorder?.stream.getTracks().forEach(track => track.stop())
        mediaRecorder = null
        isRecording.value = false

        // 上传到 Whisper API
        if (audioBlob.size > 0) {
          isTranscribing.value = true
          try {
            const formData = new FormData()
            formData.append('file', audioBlob, 'recording.webm')

            const response = await request.post<any, { transcript: string }>(
              '/speech/transcribe',
              formData,
              {
                headers: {
                  'Content-Type': 'multipart/form-data'
                },
                timeout: 120000 // 2 分钟超时
              }
            )

            transcript.value = response.transcript
            resolve({ transcript: response.transcript, duration })
          } catch (e: unknown) {
            const axiosError = e as { response?: { data?: { detail?: string } } }
            error.value = axiosError.response?.data?.detail || '转写失败'
            resolve({ transcript: '', duration })
          } finally {
            isTranscribing.value = false
          }
        } else {
          resolve({ transcript: '', duration })
        }
      }

      mediaRecorder.stop()
    })
  }

  // 开始录音
  async function start(): Promise<void> {
    error.value = null
    transcript.value = ''

    const provider = appStore.speechConfig?.provider || 'web_speech'

    if (provider === 'web_speech') {
      await startWebSpeech()
    } else {
      await startMediaRecorder()
    }
  }

  // 停止录音
  async function stop(): Promise<RecorderResult> {
    const provider = appStore.speechConfig?.provider || 'web_speech'

    if (provider === 'web_speech') {
      return stopWebSpeech()
    } else {
      return await stopMediaRecorder()
    }
  }

  // 清理
  onUnmounted(() => {
    if (recognition) {
      recognition.stop()
    }
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
      mediaRecorder.stream.getTracks().forEach(track => track.stop())
    }
  })

  return {
    isRecording,
    isSupported,
    isTranscribing,
    transcript,
    error,
    start,
    stop
  }
}
