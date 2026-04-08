import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { brandApi } from '@/apis/system_api'

export const useInfoStore = defineStore('info', () => {
  // 状态
  const infoConfig = ref({})
  const isLoading = ref(false)
  const isLoaded = ref(false)
  const debugMode = ref(false)

  // 计算属性 - 组织信息
  const organization = computed(() => infoConfig.value.organization || {
    name: "金析智策",
    logo: "/favicon.svg",
    avatar: "/avatar.jpg"
  })

  // 计算属性 - 品牌信息（与后端 info.template.yaml 默认一致；离线时前端仍有合理展示）
  const branding = computed(() => infoConfig.value.branding || {
    name: "金析智策",
    title: "金析智策 — 智能体赋能的金融数据分析与决策支持系统",
    tagline: "金融数据分析与决策支持",
    hero_badge: "大数据 · 多智能体 · 决策支持",
    subtitle: "多智能体协同研判 · 知识图谱与 RAG · 服务研报与风险管理场景",
    description: "融合非结构化金融文档、向量检索与图谱推理，支持行情、财报与新闻等多源数据的智能分析与可视化决策辅助。"
  })

  // 计算属性 - 功能特性
  const features = computed(() => infoConfig.value.features || [{
    label: "金融多智能体",
    value: "协同",
    description: "数据、分析、可视化与报告子智能体协同完成研判链路",
    icon: "brain"
  }, {
    label: "数据与知识",
    value: "RAG+图谱",
    description: "向量检索与知识图谱联合增强金融问答与溯源",
    icon: "search"
  }, {
    label: "多源数据",
    value: "可扩展",
    description: "工具与 MCP 对接行情、新闻与内部知识库",
    icon: "graph"
  }, {
    label: "决策辅助",
    value: "可追溯",
    description: "结构化要点、图表与引用路径，便于复核与展示",
    icon: "docs"
  }])

  const actions = computed(() => infoConfig.value.actions || [{
    name: "金融智能体",
    icon: "start",
    url: "/agent"
  }, {
    name: "知识库",
    icon: "docs",
    url: "/database"
  }, {
    name: "知识图谱",
    icon: "graph",
    url: "/graph"
  }, {
    name: "仪表盘",
    icon: "dashboard",
    url: "/dashboard"
  }])

  // 计算属性 - 页脚信息
  const footer = computed(() => infoConfig.value.footer || {
    copyright: "© 金析智策 2026"
  })

  // 动作方法
  function setInfoConfig(newConfig) {
    infoConfig.value = newConfig
    isLoaded.value = true
  }

  function setDebugMode(enabled) {
    debugMode.value = enabled
  }

  function toggleDebugMode() {
    debugMode.value = !debugMode.value
  }

  async function loadInfoConfig(force = false) {
    // 如果已经加载过且不强制刷新，则不重新加载
    if (isLoaded.value && !force) {
      return infoConfig.value
    }

    try {
      isLoading.value = true
      const response = await brandApi.getInfoConfig()

      if (response.success && response.data) {
        setInfoConfig(response.data)
        console.debug('信息配置加载成功:', response.data)
        return response.data
      } else {
        console.warn('信息配置加载失败，使用默认配置')
        return null
      }
    } catch (error) {
      console.error('加载信息配置时发生错误:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function reloadInfoConfig() {
    try {
      isLoading.value = true
      const response = await brandApi.reloadInfoConfig()

      if (response.success && response.data) {
        setInfoConfig(response.data)
        console.debug('信息配置重新加载成功:', response.data)
        return response.data
      } else {
        console.warn('信息配置重新加载失败')
        return null
      }
    } catch (error) {
      console.error('重新加载信息配置时发生错误:', error)
      return null
    } finally {
      isLoading.value = false
    }
  }

    return {
    // 状态
    infoConfig,
    isLoading,
    isLoaded,
    debugMode,

    // 计算属性
    organization,
    branding,
    features,
    footer,
    actions,

    // 方法
    setInfoConfig,
    setDebugMode,
    toggleDebugMode,
    loadInfoConfig,
    reloadInfoConfig
  }
})
