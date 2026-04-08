<template>
  <a-drawer
    :open="isOpen"
    :width="620"
    title="任务中心"
    placement="right"
    @close="handleClose"
    class="task-drawer-dark"
    :root-class-name="'task-drawer-dark'"
  >
    <div class="task-center">
      <div class="task-toolbar">
        <div class="task-filter-group">
          <a-segmented
            v-model:value="statusFilter"
            :options="taskFilterOptions"
          />
        </div>
        <div class="task-toolbar-actions">
          <a-button
            type="text"
            @click="handleRefresh"
            :loading="loadingState"
          >
            刷新
          </a-button>
        </div>
      </div>

      <a-alert
        v-if="lastErrorState"
        type="error"
        show-icon
        class="task-alert"
        :message="lastErrorState.message || '加载任务信息失败'"
      />

      <div v-if="hasTasks" class="task-list">
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          class="task-card"
          :class="taskCardClasses(task)"
          @click="handleTaskCardClick(task)"
        >
          <div class="task-card-header">
            <div class="task-card-info">
              <div class="task-card-title">{{ task.name }}</div>
              <div class="task-card-subtitle">
                <span class="task-card-id">#{{ formatTaskId(task.id) }}</span>
                <span class="task-card-type">{{ taskTypeLabel(task.type) }}</span>
                <span class="task-card-id" v-if="getTaskDuration(task)">{{ getTaskDuration(task) }}</span>
              </div>
            </div>
            <a-tag :color="statusColor(task.status)" class="task-card-status">
              {{ statusLabel(task.status) }}

            </a-tag>
          </div>

          <div v-if="!isTaskCompleted(task)" class="task-card-progress">
            <a-progress
              :percent="Math.round(task.progress || 0)"
              :status="progressStatus(task.status)"
              :stroke-width="6"
              />
            <!-- <span class="task-card-progress-value">{{ Math.round(task.progress || 0) }}%</span> -->
          </div>

          <div v-if="task.message && !isTaskCompleted(task)" class="task-card-message">
            {{ task.message }}
          </div>
          <div v-if="task.error" class="task-card-error">
            {{ task.error }}
          </div>

          <div class="task-card-footer">
            <div class="task-card-timestamps">
              <span v-if="task.started_at">开始: {{ formatTime(task.started_at) }}</span>
              <span v-if="task.completed_at">完成: {{ formatTime(task.completed_at) }}</span>
              <span v-if="!task.started_at">创建: {{ formatTime(task.created_at, 'short') }}</span>
            </div>
            <div class="task-card-actions">
              <a-button type="link" size="small" @click="handleDetail(task.id)" style="color: var(--gray-500);">
                详情
              </a-button>
              <a-button
                type="link"
                size="small"
                danger
                v-if="canCancel(task)"
                :disabled="!canCancel(task)"
                @click="handleCancel(task.id)"
              >
                取消
              </a-button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="task-empty">
        <div class="task-empty-icon">🗂️</div>
        <div class="task-empty-title">暂无任务</div>
        <div class="task-empty-subtitle">当你提交知识库导入或其他后台任务时，会在这里展示实时进度（仅展示最近的 100 个任务）。</div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
import { computed, h, onBeforeUnmount, watch, ref } from 'vue'
import { Modal } from 'ant-design-vue'
import { useTaskerStore } from '@/stores/tasker'
import { storeToRefs } from 'pinia'
import { formatFullDateTime, formatRelative, parseToShanghai } from '@/utils/time'

const taskerStore = useTaskerStore()
const {
  isDrawerOpen,
  sortedTasks,
  loading,
  lastError,
  activeCount,
  totalCount,
  successCount,
  failedCount
} = storeToRefs(taskerStore)
const isOpen = isDrawerOpen

const tasks = computed(() => sortedTasks.value)
const loadingState = computed(() => Boolean(loading.value))
const lastErrorState = computed(() => lastError.value)
const statusFilter = ref('all')
const inProgressCount = computed(() => activeCount.value || 0)
const completedCount = computed(() => successCount.value || 0)
const failedTaskCount = computed(() => failedCount.value || 0)
const totalTaskCount = computed(() => totalCount.value || 0)
const taskFilterOptions = computed(() => [
  {
    label: () =>
      h('span', { class: 'task-filter-option' }, [
        '全部',
        h('span', { class: 'filter-count' }, totalTaskCount.value)
      ]),
    value: 'all'
  },
  {
    label: () =>
      h('span', { class: 'task-filter-option' }, [
        '进行中',
        h('span', { class: 'filter-count' }, inProgressCount.value)
      ]),
    value: 'active'
  },
  {
    label: () =>
      h('span', { class: 'task-filter-option' }, [
        '已完成',
        h('span', { class: 'filter-count' }, completedCount.value)
      ]),
    value: 'success'
  },
  {
    label: () =>
      h('span', { class: 'task-filter-option' }, [
        '失败',
        h('span', { class: 'filter-count' }, failedTaskCount.value)
      ]),
    value: 'failed'
  }
])

const filteredTasks = computed(() => {
  const list = tasks.value
  switch (statusFilter.value) {
    case 'active':
      return list.filter((task) => ACTIVE_CLASS_STATUSES.has(task.status))
    case 'success':
      return list.filter((task) => task.status === 'success')
    case 'failed':
      return list.filter((task) => FAILED_STATUSES.has(task.status))
    default:
      return list
  }
})

const hasTasks = computed(() => filteredTasks.value.length > 0)

const ACTIVE_CLASS_STATUSES = new Set(['pending', 'queued', 'running'])
const FAILED_STATUSES = new Set(['failed', 'cancelled'])
const TASK_TYPE_LABELS = {
  knowledge_ingest: '知识库导入',
  knowledge_rechunks: '文档重新分块',
  graph_task: '图谱处理',
  agent_job: '智能体任务'
}

function taskCardClasses(task) {
  return {
    'task-card--active': ACTIVE_CLASS_STATUSES.has(task.status),
    'task-card--success': task.status === 'success',
    'task-card--failed': task.status === 'failed'
  }
}

function taskTypeLabel(type) {
  if (!type) return '后台任务'
  return TASK_TYPE_LABELS[type] || type
}

function formatTaskId(id) {
  if (!id) return '--'
  return id.slice(0, 8)
}

watch(
  isOpen,
  (open) => {
    if (open) {
      taskerStore.loadTasks()
      taskerStore.startPolling()
    } else {
      taskerStore.stopPolling()
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  taskerStore.stopPolling()
})

function handleClose() {
  taskerStore.closeDrawer()
}

function handleRefresh() {
  taskerStore.loadTasks()
}

function handleTaskCardClick(task) {
  console.log('Task clicked:', task)
}

function handleDetail(taskId) {
  const task = tasks.value.find(item => item.id === taskId)
  if (!task) {
    return
  }
  const detail = h('div', { class: 'task-detail' }, [
    h('p', [h('strong', '状态：'), statusLabel(task.status)]),
    h('p', [h('strong', '进度：'), `${Math.round(task.progress || 0)}%`]),
    h('p', [h('strong', '更新时间：'), formatTime(task.updated_at)]),
    h('p', [h('strong', '描述：'), task.message || '-']),
    h('p', [h('strong', '错误：'), task.error || '-'])
  ])
  Modal.info({
    title: task.name,
    width: 520,
    content: detail
  })
}

function handleCancel(taskId) {
  taskerStore.cancelTask(taskId)
}

function formatTime(value, mode = 'full') {
  if (!value) return '-'
  if (mode === 'short') {
    return formatRelative(value)
  }
  return formatFullDateTime(value)
}

function getTaskDuration(task) {
  if (!task.started_at || !task.completed_at) return null
  try {
    const start = parseToShanghai(task.started_at)
    const end = parseToShanghai(task.completed_at)
    if (!start || !end) {
      return null
    }

    const diffSeconds = Math.max(0, Math.floor(end.diff(start, 'second')))
    const hours = Math.floor(diffSeconds / 3600)
    const minutes = Math.floor((diffSeconds % 3600) / 60)
    const seconds = diffSeconds % 60

    if (hours > 0) {
      return `${hours}小时${minutes}分钟`
    }
    if (minutes > 0) {
      return `${minutes}分钟${seconds}秒`
    }
    if (seconds > 0) {
      return `${seconds}秒`
    }
    return '小于1秒'
  } catch {
    return null
  }
}

function isTaskCompleted(task) {
  return ['success', 'failed', 'cancelled'].includes(task.status)
}

function getCompletionIcon(status) {
  const icons = {
    success: '✓',
    failed: '✗',
    cancelled: '○'
  }
  return icons[status] || '?'
}

function statusLabel(status) {
  const map = {
    pending: '等待中',
    queued: '已排队',
    running: '进行中',
    success: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return map[status] || status
}

function statusColor(status) {
  const map = {
    pending: 'blue',
    queued: 'blue',
    running: 'processing',
    success: 'green',
    failed: 'red',
    cancelled: 'gray'
  }
  return map[status] || 'default'
}

function progressStatus(status) {
  if (status === 'failed') return 'exception'
  if (status === 'cancelled') return 'normal'
  return 'active'
}

function canCancel(task) {
  return ['pending', 'running', 'queued'].includes(task.status) && !task.cancel_requested
}

</script>
<style scoped lang="less">
@dk-bg: #1a1a1a;
@dk-card: #222222;
@dk-card-hover: #2a2a2a;
@dk-border: #2e2e2e;
@dk-text: #c8c8c8;
@dk-text-dim: #777;
@dk-text-bright: #e8e8e8;
@dk-accent: #ff9933;

.task-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.task-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
  flex-wrap: wrap;
}

.task-filter-group {
  flex-shrink: 0;
}

.task-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

:deep(.filter-count) {
  margin-left: 2px;
  font-size: 12px;
  color: @dk-text-dim;
}

.task-toolbar-actions :deep(.ant-btn) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 10px;
  color: @dk-text-dim;
  &:hover { color: @dk-accent; }
}

.task-alert {
  margin-bottom: 4px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-card {
  background: @dk-card;
  border: 1px solid @dk-border;
  border-radius: 10px;
  padding: 14px 16px;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-card:hover {
  border-color: #3a3a3a;
  background: @dk-card-hover;
}

.task-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.task-card-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.task-card-title {
  font-size: 14px;
  font-weight: 600;
  color: @dk-text-bright;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

.task-card-subtitle {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: @dk-text-dim;
}

.task-card-id {
  letter-spacing: 0.04em;
}

.task-card-type {
  padding: 0 8px;
  border-radius: 999px;
  background-color: #2a2a2a;
  color: @dk-text-dim;
  line-height: 20px;
}

.task-card-status {
  margin-top: 2px;
}

.task-card-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-card-progress :deep(.ant-progress) {
  flex: 1;

  .ant-progress-bg {
    background: @dk-accent;
  }

  .ant-progress-inner {
    background: #2a2a2a;
  }
}

.task-card-progress-value {
  font-size: 12px;
  font-weight: 500;
  color: @dk-text-dim;
  width: 48px;
  text-align: right;
}

.task-card-message,
.task-card-error {
  font-size: 13px;
  line-height: 1.45;
  border-radius: 6px;
  padding: 10px 12px;
}

.task-card-message {
  background: #252525;
  color: @dk-text;
}

.task-card-error {
  background: rgba(255, 77, 79, 0.1);
  color: #ff6b6b;
}

.task-card-footer {
  margin-top: 2px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
}

.task-card-timestamps {
  display: flex;
  flex-direction: row;
  gap: 10px;
  font-size: 12px;
  color: #555;
}

.task-card-actions {
  display: flex;
  gap: 6px;

  :deep(.ant-btn-link) {
    color: @dk-text-dim;
    &:hover { color: @dk-accent; }
  }
}

.task-card-completion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 8px;
  background: #252525;
  border: 1px solid @dk-border;
}

.completion-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

.completion-badge--success { color: #52c41a; }
.completion-badge--success .completion-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(82, 196, 26, 0.15); font-size: 14px;
}

.completion-badge--failed { color: #ff4d4f; }
.completion-badge--failed .completion-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(255, 77, 79, 0.15); font-size: 14px;
}

.completion-badge--cancelled { color: @dk-text-dim; }
.completion-badge--cancelled .completion-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 50%;
  background: #2a2a2a; font-size: 14px;
}

.task-duration {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: @dk-text-dim;
}

.duration-label { font-weight: 500; }
.duration-value {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-weight: 600; color: @dk-text;
}

.task-empty {
  margin-top: 32px;
  padding: 40px 30px;
  border-radius: 14px;
  background: #222;
  border: 1px dashed #3a3a3a;
  text-align: center;
  color: @dk-text-dim;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.task-empty-icon { font-size: 28px; }
.task-empty-title { font-size: 16px; font-weight: 600; color: @dk-text; }
.task-empty-subtitle { font-size: 13px; max-width: 320px; line-height: 1.5; color: #555; }
</style>

<style lang="less">
.task-drawer-dark {
  .ant-drawer-content {
    background: #1a1a1a;
  }

  .ant-drawer-header {
    background: #1a1a1a;
    border-bottom: 1px solid #2a2a2a;

    .ant-drawer-title {
      color: #e0e0e0;
      font-weight: 700;
    }

    .ant-drawer-close {
      color: #777;
      &:hover { color: #ff9933; }
    }
  }

  .ant-drawer-body {
    background: #1a1a1a;
  }

  .ant-segmented {
    background: #252525;
    color: #999;

    .ant-segmented-item {
      color: #999;
      &:hover { color: #ccc; }
    }

    .ant-segmented-item-selected {
      background: #333;
      color: #ff9933;
      font-weight: 600;
    }

    .ant-segmented-thumb {
      background: #333;
    }
  }
}
</style>
