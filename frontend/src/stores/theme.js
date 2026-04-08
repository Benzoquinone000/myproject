import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { theme } from 'ant-design-vue'

export const useThemeStore = defineStore('theme', () => {
  // 从 localStorage 读取保存的主题，默认为浅色
  const isDark = ref(localStorage.getItem('theme') === 'dark')

  // 公共主题配置
  const commonTheme = {
    token: {
      fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif",
      colorPrimary: '#ff7e00',
      borderRadius: 10,
      wireframe: false,
      fontSize: 14,
      controlHeight: 36,
    },
    components: {
      Button: {
        borderRadius: 8,
        controlHeight: 36,
        fontWeight: 500,
      },
      Input: {
        borderRadius: 8,
        controlHeight: 40,
      },
      Select: {
        borderRadius: 8,
      },
      Card: {
        borderRadius: 12,
      },
      Modal: {
        borderRadius: 14,
      },
    },
  }

  // 浅色主题配置
  const lightTheme = {
    ...commonTheme,
  }

  // 深色主题配置
  const darkTheme = {
    ...commonTheme,
    algorithm: theme.darkAlgorithm,
  }

  // 当前主题配置
  const currentTheme = ref(isDark.value ? darkTheme : lightTheme)

  // 设置主题
  function setTheme(dark) {
    isDark.value = dark
    currentTheme.value = dark ? darkTheme : lightTheme
    localStorage.setItem('theme', dark ? 'dark' : 'light')
    updateDocumentTheme()
  }

  // 更新 document 的主题类
  function updateDocumentTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // 初始化时设置主题
  updateDocumentTheme()

  return {
    isDark,
    currentTheme,
    setTheme,
  }
})
