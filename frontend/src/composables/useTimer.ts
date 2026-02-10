import { ref, computed, onUnmounted } from 'vue'

export type TimerMode = 'countup' | 'countdown'

export function useTimer(mode: TimerMode = 'countup', initialSeconds: number = 0) {
  const seconds = ref(mode === 'countdown' ? initialSeconds : 0)
  const isRunning = ref(false)
  const warningThreshold = ref(30) // 最后 30 秒警告

  let intervalId: number | null = null

  // 格式化时间
  const formatted = computed(() => {
    const mins = Math.floor(seconds.value / 60)
    const secs = seconds.value % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  })

  // 是否在警告状态
  const isWarning = computed(() => {
    if (mode === 'countdown') {
      return seconds.value <= warningThreshold.value && seconds.value > 0
    }
    return false
  })

  // 是否已超时
  const isTimeout = computed(() => {
    return mode === 'countdown' && seconds.value <= 0
  })

  // 开始计时
  function start() {
    if (isRunning.value) return

    isRunning.value = true
    intervalId = window.setInterval(() => {
      if (mode === 'countup') {
        seconds.value++
      } else {
        if (seconds.value > 0) {
          seconds.value--
        } else {
          stop()
        }
      }
    }, 1000)
  }

  // 暂停计时
  function pause() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
    isRunning.value = false
  }

  // 停止计时
  function stop() {
    pause()
  }

  // 重置计时
  function reset(newInitialSeconds?: number) {
    stop()
    if (mode === 'countdown') {
      seconds.value = newInitialSeconds ?? initialSeconds
    } else {
      seconds.value = 0
    }
  }

  // 设置时间
  function setSeconds(value: number) {
    seconds.value = value
  }

  // 设置警告阈值
  function setWarningThreshold(value: number) {
    warningThreshold.value = value
  }

  // 清理
  onUnmounted(() => {
    if (intervalId) {
      clearInterval(intervalId)
    }
  })

  return {
    seconds,
    formatted,
    isRunning,
    isWarning,
    isTimeout,
    start,
    pause,
    stop,
    reset,
    setSeconds,
    setWarningThreshold
  }
}
