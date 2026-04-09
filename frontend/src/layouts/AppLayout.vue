<script setup>
import { ref, reactive, onMounted, useTemplateRef, computed, provide } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { Bot, Waypoints, LibraryBig, BarChart3, CircleCheck, Menu, X } from 'lucide-vue-next';
import { onLongPress } from '@vueuse/core'

import { useConfigStore } from '@/stores/config'
import { useDatabaseStore } from '@/stores/database'
import { useInfoStore } from '@/stores/info'
import { useTaskerStore } from '@/stores/tasker'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import UserInfoComponent from '@/components/UserInfoComponent.vue'
import DebugComponent from '@/components/DebugComponent.vue'
import TaskCenterDrawer from '@/components/TaskCenterDrawer.vue'
import SettingsModal from '@/components/SettingsModal.vue'

const configStore = useConfigStore()
const databaseStore = useDatabaseStore()
const infoStore = useInfoStore()
const taskerStore = useTaskerStore()
const userStore = useUserStore()
const { activeCount: activeCountRef, isDrawerOpen } = storeToRefs(taskerStore)

const layoutSettings = reactive({
  showDebug: false,
})

const showDebugModal = ref(false)
const htmlRefHook = useTemplateRef('htmlRefHook')
const showSettingsModal = ref(false)
const mobileMenuOpen = ref(false)

const openSettingsModal = () => {
  showSettingsModal.value = true
}

onLongPress(
  htmlRefHook,
  () => {
    showDebugModal.value = true
  },
  {
    delay: 1000,
    modifiers: { prevent: true }
  }
)

const handleDebugModalClose = () => {
  showDebugModal.value = false
}

const getRemoteConfig = () => {
  configStore.refreshConfig()
}

const getRemoteDatabase = () => {
  databaseStore.loadDatabases()
}

onMounted(async () => {
  await infoStore.loadInfoConfig()
  getRemoteConfig()
  getRemoteDatabase()
  taskerStore.loadTasks()
})

const route = useRoute()

const activeTaskCount = computed(() => activeCountRef.value || 0)

const allNavItems = [{
    name: '智能体',
    path: '/agent',
    icon: Bot,
    activeIcon: Bot,
    adminOnly: true,
  }, {
    name: '图谱',
    path: '/graph',
    icon: Waypoints,
    activeIcon: Waypoints,
    adminOnly: true,
  }, {
    name: '知识库',
    path: '/database',
    icon: LibraryBig,
    activeIcon: LibraryBig,
    adminOnly: true,
  }, {
    name: '仪表盘',
    path: '/dashboard',
    icon: BarChart3,
    activeIcon: BarChart3,
    adminOnly: true,
  }
]

const mainList = computed(() =>
  allNavItems.filter(item => !item.adminOnly || userStore.isAdmin)
)

provide('settingsModal', {
  openSettingsModal
})
</script>

<template>
  <div class="app-layout">
    <header class="top-navbar">
      <div class="navbar-left">
        <router-link to="/" class="navbar-logo">
          <img :src="infoStore.organization.avatar" alt="logo" />
          <span class="logo-text">{{ infoStore.branding.name || '金析智策' }}</span>
        </router-link>
      </div>

      <nav class="navbar-center">
        <RouterLink
          v-for="(item, index) in mainList"
          :key="index"
          :to="item.path"
          v-show="!item.hidden"
          class="nav-tab"
          active-class="active">
          <component class="nav-tab-icon" :is="route.path.startsWith(item.path) ? item.activeIcon : item.icon" :size="18"/>
          <span class="nav-tab-label">{{ item.name }}</span>
        </RouterLink>
        <div
          class="nav-tab task-tab"
          :class="{ active: isDrawerOpen }"
          @click="taskerStore.openDrawer()"
        >
          <a-badge
            :count="activeTaskCount"
            :overflow-count="99"
            size="small"
          >
            <CircleCheck class="nav-tab-icon" :size="18" />
          </a-badge>
          <span class="nav-tab-label">任务</span>
        </div>
      </nav>

      <div class="navbar-right">
        <div ref="htmlRefHook" class="debug-trigger"></div>
        <UserInfoComponent />
      </div>

      <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen">
        <component :is="mobileMenuOpen ? X : Menu" :size="22" />
      </button>
    </header>

    <div v-if="mobileMenuOpen" class="mobile-nav-overlay" @click="mobileMenuOpen = false">
      <nav class="mobile-nav-panel" @click.stop>
        <RouterLink
          v-for="(item, index) in mainList"
          :key="index"
          :to="item.path"
          class="mobile-nav-item"
          active-class="active"
          @click="mobileMenuOpen = false"
        >
          <component :is="item.icon" :size="20"/>
          <span>{{ item.name }}</span>
        </RouterLink>
      </nav>
    </div>

    <main class="main-content">
      <router-view v-slot="{ Component, route }" id="app-router-view">
        <keep-alive v-if="route.meta.keepAlive !== false">
          <component :is="Component" />
        </keep-alive>
        <component :is="Component" v-else />
      </router-view>
    </main>

    <a-modal
      v-model:open="showDebugModal"
      title="调试面板"
      width="90%"
      :footer="null"
      @cancel="handleDebugModalClose"
      :maskClosable="true"
      :destroyOnClose="true"
      class="debug-modal"
    >
      <DebugComponent />
    </a-modal>
    <TaskCenterDrawer />
    <SettingsModal
      v-model:visible="showSettingsModal"
      @close="() => showSettingsModal = false"
    />
  </div>
</template>

<style lang="less" scoped>
@navbar-height: 56px;
@nav-bg: #1a1a1a;
@nav-bg-hover: #252525;
@nav-bg-active: #2a2218;
@nav-border: #2a2a2a;
@nav-text: #a0a0a0;
@nav-text-bright: #e0e0e0;
@nav-text-dim: #606060;
@nav-accent: #ff9933;

.app-layout {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  min-width: var(--min-width);
}

.top-navbar {
  display: flex;
  align-items: center;
  height: @navbar-height;
  padding: 0 20px;
  background: @nav-bg;
  border-bottom: 1px solid @nav-border;
  flex-shrink: 0;
  z-index: 100;
  gap: 8px;
  user-select: none;
}

.navbar-left {
  display: flex;
  align-items: center;
  flex-shrink: 0;

  .navbar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: @nav-text-bright;
    font-weight: 700;
    font-size: 16px;
    padding: 4px 12px 4px 0;
    border-right: 1px solid @nav-border;
    margin-right: 8px;

    img {
      width: 30px;
      height: 30px;
      border-radius: 8px;
    }

    .logo-text {
      white-space: nowrap;
      letter-spacing: -0.01em;
    }
  }
}

.navbar-center {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
  justify-content: flex-start;
  padding-left: 4px;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  text-decoration: none;
  color: @nav-text;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s ease;
  cursor: pointer;
  white-space: nowrap;

  .nav-tab-icon {
    flex-shrink: 0;
  }

  &:hover {
    background: @nav-bg-hover;
    color: @nav-text-bright;
  }

  &.active {
    background: @nav-bg-active;
    color: @nav-accent;
    font-weight: 600;
  }

  &.task-tab {
    .nav-tab-icon {
      display: flex;
    }
  }
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;

  .debug-trigger {
    width: 8px;
    height: 30px;
    cursor: default;
  }
}

.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  padding: 6px;
  color: @nav-text;
  cursor: pointer;
  border-radius: 8px;

  &:hover {
    background: @nav-bg-hover;
    color: @nav-text-bright;
  }
}

.mobile-nav-overlay {
  display: none;
}

.main-content {
  flex: 1;
  overflow: hidden;

  #app-router-view {
    height: 100%;
    overflow-y: auto;
  }
}

@media (max-width: 768px) {
  .navbar-center {
    display: none;
  }

  .navbar-right {
    margin-left: auto;
  }

  .mobile-menu-btn {
    display: flex;
    align-items: center;
  }

  .mobile-nav-overlay {
    display: block;
    position: fixed;
    inset: @navbar-height 0 0 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
    animation: fadeIn 0.15s ease;

    .mobile-nav-panel {
      background: @nav-bg;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      border-bottom: 1px solid @nav-border;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);

      .mobile-nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        border-radius: 10px;
        text-decoration: none;
        color: @nav-text;
        font-size: 15px;
        font-weight: 500;

        &.active {
          background: @nav-bg-active;
          color: @nav-accent;
        }

        &:hover {
          background: @nav-bg-hover;
          color: @nav-text-bright;
        }
      }
    }
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
