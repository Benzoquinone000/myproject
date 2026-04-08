<template>
  <div class="home-wrapper">
    <header class="home-topbar">
      <div class="topbar-left">
        <router-link to="/" class="home-logo">
          <span class="logo-mark">{{ infoStore.organization.name || '金析智策' }}</span>
        </router-link>
      </div>
      <nav class="topbar-nav" v-if="userStore.isLoggedIn && userStore.isAdmin">
        <router-link to="/agent" class="topbar-link">智能体</router-link>
        <router-link to="/graph" class="topbar-link">知识图谱</router-link>
        <router-link to="/database" class="topbar-link">知识库</router-link>
        <router-link to="/dashboard" class="topbar-link">仪表盘</router-link>
      </nav>
      <div class="topbar-right">
        <UserInfoComponent :show-button="true" />
      </div>
    </header>

    <div class="home-body">
      <section class="hero-block">
        <div class="hero-badge">{{ infoStore.branding.hero_badge || '大数据 · 多智能体 · 决策支持' }}</div>
        <h1 class="hero-title">{{ heroHeadline }}</h1>
        <p class="hero-desc">{{ infoStore.branding.subtitle }}</p>
        <div class="hero-btns">
          <button class="btn-primary" @click="goToChat">
            <Bot :size="18" />
            开始对话
          </button>
          <router-link to="/database" class="btn-outline" v-if="userStore.isLoggedIn && userStore.isAdmin">
            <LibraryBig :size="18" />
            管理知识库
          </router-link>
        </div>
      </section>

      <section class="features-block">
        <div class="features-grid">
          <div class="feature-card" v-for="(feat, i) in featureCards" :key="i">
            <div class="feature-icon-wrap" :style="{ background: feat.bg }">
              <component :is="feat.icon" :size="22" :color="feat.color" />
            </div>
            <h3 class="feature-title">{{ feat.title }}</h3>
            <p class="feature-desc">{{ feat.desc }}</p>
          </div>
        </div>
      </section>

      <section class="workflow-block">
        <h2 class="section-title">工作流程</h2>
        <div class="workflow-steps">
          <div class="workflow-step" v-for="(step, i) in workflowSteps" :key="i">
            <div class="step-number">{{ i + 1 }}</div>
            <h4 class="step-title">{{ step.title }}</h4>
            <p class="step-desc">{{ step.desc }}</p>
          </div>
        </div>
      </section>
    </div>

    <footer class="home-footer">
      <span>{{ infoStore.footer.copyright }}</span>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useInfoStore } from '@/stores/info'
import { useAgentStore } from '@/stores/agent'
import UserInfoComponent from '@/components/UserInfoComponent.vue'
import { Bot, LibraryBig, Waypoints, Search, FileText, Brain, LineChart } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const infoStore = useInfoStore()
const agentStore = useAgentStore()

/** 首页主标题：优先 tagline，其次 name */
const heroHeadline = computed(() => {
  const t = infoStore.branding?.tagline?.trim()
  if (t) return t
  return infoStore.branding?.name || '金融数据分析与决策支持'
})

const featureCards = [
  { title: '金融多智能体', desc: '数据获取、指标分析、图表与研报分工协作，服务投研与风控话术场景', icon: Brain, bg: 'var(--main-50)', color: 'var(--main-600)' },
  { title: '数据与知识融合', desc: '向量检索与知识图谱联合，支撑公告、研报等非结构化资料的问答与溯源', icon: Search, bg: '#eef2ff', color: '#4f46e5' },
  { title: '图谱与实体关系', desc: '从文档抽取实体与关系，构建可浏览、可推理的金融领域知识结构', icon: Waypoints, bg: '#f0fdf4', color: '#16a34a' },
  { title: '可视化与报告', desc: '结合工具与 MCP 输出图表与结构化结论，便于汇报与决策复核', icon: LineChart, bg: '#fef3c7', color: '#d97706' },
]

const workflowSteps = [
  { title: '接入数据与知识', desc: '上传财报、研报等文档入库，或配置工具/MCP 拉取行情与新闻' },
  { title: '构建与检索', desc: '向量化与图谱构建完成，RAG 与图查询为智能体提供上下文' },
  { title: '选用金融智能体', desc: '在智能体列表中选择「金融数据分析智能体」并配置模型与工具' },
  { title: '分析与决策支持', desc: '通过多轮对话完成分析、对比、可视化与报告式输出' },
]

const goToChat = async () => {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', '/')
    router.push('/login')
    return
  }
  if (userStore.isAdmin) {
    router.push('/agent')
    return
  }
  try {
    const defaultAgent = agentStore.defaultAgent
    if (defaultAgent?.id) {
      router.push(`/agent/${defaultAgent.id}`)
    } else {
      router.push('/agent')
    }
  } catch (error) {
    router.push('/')
  }
}

onMounted(async () => {
  await infoStore.loadInfoConfig()
})
</script>

<style lang="less" scoped>
.home-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--main-5);
}

.home-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 60px;
  background: var(--color-trans-light);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--gray-100);
  position: sticky;
  top: 0;
  z-index: 50;

  .topbar-left {
    .home-logo {
      text-decoration: none;

      .logo-mark {
        font-size: 20px;
        font-weight: 800;
        background: linear-gradient(135deg, var(--main-600), var(--main-400));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
      }
    }
  }

  .topbar-nav {
    display: flex;
    gap: 4px;

    .topbar-link {
      padding: 6px 16px;
      text-decoration: none;
      color: var(--gray-700);
      font-size: 14px;
      font-weight: 500;
      border-radius: 8px;
      transition: all 0.15s;

      &:hover {
        background: var(--gray-50);
        color: var(--gray-1000);
      }

      &.router-link-active {
        background: var(--main-50);
        color: var(--main-600);
      }
    }
  }
}

.home-body {
  flex: 1;
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px;
  width: 100%;
}

.hero-block {
  text-align: center;
  padding: 80px 0 48px;

  .hero-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    background: var(--main-50);
    color: var(--main-600);
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 24px;
    border: 1px solid var(--main-100);
  }

  .hero-title {
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 800;
    line-height: 1.2;
    color: var(--gray-1000);
    margin: 0 0 16px;
    letter-spacing: -0.02em;
  }

  .hero-desc {
    font-size: 1.1rem;
    color: var(--gray-600);
    margin: 0 0 32px;
    max-width: 480px;
    margin-left: auto;
    margin-right: auto;
  }

  .hero-btns {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
  }
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: linear-gradient(135deg, var(--main-500), var(--main-600));
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 12px rgba(255, 126, 0, 0.25);

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(255, 126, 0, 0.35);
  }
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: var(--main-0);
  color: var(--gray-800);
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--main-300);
    color: var(--main-600);
    background: var(--main-10);
  }
}

.features-block {
  padding: 24px 0 48px;

  .features-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;

    @media (max-width: 900px) {
      grid-template-columns: repeat(2, 1fr);
    }

    @media (max-width: 520px) {
      grid-template-columns: 1fr;
    }
  }

  .feature-card {
    background: var(--main-0);
    border: 1px solid var(--gray-100);
    border-radius: 14px;
    padding: 24px 20px;
    transition: all 0.2s;

    &:hover {
      box-shadow: 0 8px 24px var(--shadow-1);
      transform: translateY(-2px);
    }

    .feature-icon-wrap {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 16px;
    }

    .feature-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--gray-1000);
      margin: 0 0 8px;
    }

    .feature-desc {
      font-size: 13px;
      color: var(--gray-600);
      line-height: 1.55;
      margin: 0;
    }
  }
}

.workflow-block {
  padding: 32px 0 64px;

  .section-title {
    text-align: center;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--gray-1000);
    margin: 0 0 32px;
  }

  .workflow-steps {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;

    @media (max-width: 800px) {
      grid-template-columns: repeat(2, 1fr);
    }

    @media (max-width: 480px) {
      grid-template-columns: 1fr;
    }
  }

  .workflow-step {
    text-align: center;
    padding: 24px 16px;
    position: relative;

    .step-number {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--main-500);
      color: #fff;
      font-weight: 700;
      font-size: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 16px;
    }

    .step-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--gray-1000);
      margin: 0 0 8px;
    }

    .step-desc {
      font-size: 13px;
      color: var(--gray-600);
      margin: 0;
      line-height: 1.5;
    }
  }
}

.home-footer {
  text-align: center;
  padding: 20px;
  color: var(--gray-500);
  font-size: 13px;
  border-top: 1px solid var(--gray-100);
}

@media (max-width: 768px) {
  .home-topbar {
    padding: 0 16px;

    .topbar-nav {
      display: none;
    }
  }

  .hero-block {
    padding: 48px 0 32px;
  }
}
</style>
