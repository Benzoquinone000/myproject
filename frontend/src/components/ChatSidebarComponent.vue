<template>
  <div class="chat-sidebar" :class="{'sidebar-open': chatUIStore.isSidebarOpen, 'no-transition': isInitialRender}">
    <div class="sidebar-content">
      <div class="sidebar-header">
        <div class="header-title">对话历史</div>
        <div class="header-actions">
          <div class="toggle-sidebar nav-btn" v-if="chatUIStore.isSidebarOpen" @click="toggleCollapse">
            <PanelLeftClose size="20" color="#999"/>
          </div>
        </div>
      </div>
      <div class="conversation-list-top">
        <button type="text" @click="createNewChat" class="new-chat-btn" :disabled="chatUIStore.creatingNewChat">
          <LoaderCircle v-if="chatUIStore.creatingNewChat" size="20" class="loading-icon" />
          <MessageSquarePlus v-else size="20" />
          创建新对话
        </button>
      </div>
      <div class="conversation-list">
        <template v-if="Object.keys(groupedChats).length > 0">
          <div v-for="(group, groupName) in groupedChats" :key="groupName" class="chat-group">
            <div class="chat-group-title">{{ groupName }}</div>
            <div
              v-for="chat in group"
              :key="chat.id"
              class="conversation-item"
              :class="{ 'active': currentChatId === chat.id }"
              @click="selectChat(chat)"
            >
              <div class="conversation-title">{{ chat.title || '新的对话' }}</div>
              <div class="actions-mask"></div>
              <div class="conversation-actions">
                <a-dropdown :trigger="['click']" @click.stop>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item key="rename" @click.stop="renameChat(chat.id)" :icon="h(EditOutlined)">
                        重命名
                      </a-menu-item>
                      <a-menu-item key="delete" @click.stop="deleteChat(chat.id)" :icon="h(DeleteOutlined)">
                        删除
                      </a-menu-item>
                    </a-menu>
                  </template>
                  <a-button type="text" class="more-btn" @click.stop>
                    <MoreOutlined />
                  </a-button>
                </a-dropdown>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="empty-list">
          暂无对话历史
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, h } from 'vue';
import {
  DeleteOutlined,
  EditOutlined,
  MoreOutlined
} from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import { PanelLeftClose, MessageSquarePlus, LoaderCircle } from 'lucide-vue-next';
import dayjs, { parseToShanghai } from '@/utils/time';
import { useChatUIStore } from '@/stores/chatUI';
import { useInfoStore } from '@/stores/info';
import { storeToRefs } from 'pinia';

// 使用 chatUI store
const chatUIStore = useChatUIStore();
const infoStore = useInfoStore();

const { branding } = storeToRefs(infoStore);

const props = defineProps({
  currentAgentId: {
    type: String,
    default: null
  },
  currentChatId: {
    type: String,
    default: null
  },
  chatsList: {
    type: Array,
    default: () => []
  },
  isInitialRender: {
    type: Boolean,
    default: false
  },
  singleMode: {
    type: Boolean,
    default: true
  },
  agents: {
    type: Array,
    default: () => []
  },
  selectedAgentId: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['create-chat', 'select-chat', 'delete-chat', 'rename-chat', 'toggle-sidebar', 'open-agent-modal']);



const groupedChats = computed(() => {
  const groups = {
    '今天': [],
    '七天内': [],
    '三十天内': [],
  };

  // 确保使用北京时间进行比较
  const now = dayjs().tz('Asia/Shanghai');
  const today = now.startOf('day');
  const sevenDaysAgo = now.subtract(7, 'day').startOf('day');
  const thirtyDaysAgo = now.subtract(30, 'day').startOf('day');

  // Sort chats by creation date, newest first
  const sortedChats = [...props.chatsList].sort((a, b) => {
    const dateA = parseToShanghai(b.created_at);
    const dateB = parseToShanghai(a.created_at);
    if (!dateA || !dateB) return 0;
    return dateA.diff(dateB);
  });

  sortedChats.forEach(chat => {
    // 将后端时间当作UTC时间处理，然后转换为北京时间
    const chatDate = parseToShanghai(chat.created_at);
    if (!chatDate) {
      return;
    }
    if (chatDate.isAfter(today)) {
      groups['今天'].push(chat);
    } else if (chatDate.isAfter(sevenDaysAgo)) {
      groups['七天内'].push(chat);
    } else if (chatDate.isAfter(thirtyDaysAgo)) {
      groups['三十天内'].push(chat);
    } else {
      const monthKey = chatDate.format('YYYY-MM');
      if (!groups[monthKey]) {
        groups[monthKey] = [];
      }
      groups[monthKey].push(chat);
    }
  });

  // Remove empty groups
  for (const key in groups) {
    if (groups[key].length === 0) {
      delete groups[key];
    }
  }

  return groups;
});


const createNewChat = () => {
  emit('create-chat');
};

const selectChat = (chat) => {
  emit('select-chat', chat.id);
};

const deleteChat = (chatId) => {
  emit('delete-chat', chatId);
};

const renameChat = async (chatId) => {
  try {
    const chat = props.chatsList.find(c => c.id === chatId);
    if (!chat) return;

    let newTitle = chat.title;
    Modal.confirm({
      title: '重命名对话',
      content: h('div', { style: { marginTop: '12px' } }, [
        h('input', {
          value: newTitle,
          style: { width: '100%', padding: '4px 8px', border: '1px solid var(--gray-150)', background: 'var(--gray-0)', borderRadius: '4px' },
          onInput: (e) => { newTitle = e.target.value; }
        })
      ]),
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        if (!newTitle.trim()) {
          message.warning('标题不能为空');
          return Promise.reject();
        }
        emit('rename-chat', { chatId, title: newTitle });
      },
      onCancel: () => {}
    });
  } catch (error) {
    console.error('重命名对话失败:', error);
  }
};

const toggleCollapse = () => {
  emit('toggle-sidebar');
};


</script>

<style lang="less" scoped>
@sidebar-bg: #1a1a1a;
@sidebar-bg-hover: #252525;
@sidebar-bg-active: #2a2218;
@sidebar-border: #2a2a2a;
@sidebar-text: #b0b0b0;
@sidebar-text-bright: #e0e0e0;
@sidebar-text-dim: #707070;
@sidebar-accent: #ff9933;

.chat-sidebar {
  width: 0;
  height: 100%;
  background-color: @sidebar-bg;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  border: none;
  overflow: hidden;

  .sidebar-content {
    width: 280px;
    min-width: 280px;
    height: 100%;
    display: flex;
    flex-direction: column;
    opacity: 1;
    transform: translateX(0);
    transition: opacity 0.2s ease, transform 0.3s ease;
  }

  &:not(.sidebar-open) .sidebar-content {
    opacity: 0;
    transform: translateX(-12px);
  }

  &.floating-sidebar .sidebar-content {
    width: 100%;
    min-width: 0;
    max-width: 300px;
  }

  &.no-transition {
    transition: none !important;
  }

  &.sidebar-open {
    width: 280px;
    max-width: 300px;
    border-right: 1px solid @sidebar-border;
  }

  .sidebar-header {
    height: var(--header-height);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px;
    border-bottom: 1px solid @sidebar-border;
    flex-shrink: 0;

    .header-title {
      font-weight: 700;
      font-size: 13px;
      color: @sidebar-text-dim;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .conversation-list-top {
    padding: 10px 12px;

    .new-chat-btn {
      width: 100%;
      padding: 10px 12px;
      border-radius: 8px;
      background-color: rgba(255, 153, 51, 0.1);
      color: @sidebar-accent;
      border: 1px solid rgba(255, 153, 51, 0.2);
      transition: all 0.2s ease;
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;

      &:hover:not(:disabled) {
        background-color: rgba(255, 153, 51, 0.18);
        border-color: rgba(255, 153, 51, 0.35);
      }

      &:disabled {
        cursor: not-allowed;
        opacity: 0.5;
      }

      .loading-icon {
        animation: spin 1s linear infinite;
      }
    }
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .conversation-list {
    flex: 1;
    overflow-y: auto;
    padding: 4px 8px;

    .chat-group {
      margin-bottom: 12px;
    }

    .chat-group-title {
      padding: 6px 8px 4px;
      font-size: 11px;
      color: @sidebar-text-dim;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .conversation-item {
      display: flex;
      align-items: center;
      padding: 8px 10px;
      border-radius: 8px;
      margin: 1px 0;
      cursor: pointer;
      transition: all 0.15s ease;
      position: relative;
      overflow: hidden;

      .conversation-title {
        flex: 1;
        font-size: 13px;
        color: @sidebar-text;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: color 0.15s ease;
      }

      .actions-mask {
        position: absolute;
        right: 0;
        top: 0;
        bottom: 0;
        width: 60px;
        background: linear-gradient(to right, transparent, @sidebar-bg 20px);
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
      }

      .conversation-actions {
        display: flex;
        align-items: center;
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        opacity: 0;
        transition: opacity 0.2s ease;

        .more-btn {
          color: @sidebar-text-dim;
          background-color: transparent !important;
          padding: 0;
          &:hover {
            color: @sidebar-accent;
            background-color: transparent !important;
          }
        }
      }

      &:hover {
        background-color: @sidebar-bg-hover;

        .conversation-title {
          color: @sidebar-text-bright;
        }

        .actions-mask {
          background: linear-gradient(to right, transparent, @sidebar-bg-hover 20px);
        }

        .actions-mask, .conversation-actions {
          opacity: 1;
        }
      }

      &.active {
        background-color: @sidebar-bg-active;
        border-left: 3px solid @sidebar-accent;

        .conversation-title {
          color: @sidebar-accent;
          font-weight: 600;
        }

        .actions-mask {
          background: linear-gradient(to right, transparent, @sidebar-bg-active 20px);
        }
      }
    }

    .empty-list {
      text-align: center;
      margin-top: 20px;
      color: @sidebar-text-dim;
      font-size: 13px;
    }
  }
}

.conversation-list::-webkit-scrollbar {
  width: 4px;
}
.conversation-list::-webkit-scrollbar-track {
  background: transparent;
}
.conversation-list::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 4px;
}
.conversation-list::-webkit-scrollbar-thumb:hover {
  background: #444;
}

.toggle-sidebar.nav-btn {
  cursor: pointer;
  height: 2.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
  transition: background-color 0.2s;

  svg {
    stroke: @sidebar-text;
  }

  &:hover {
    background-color: @sidebar-bg-hover;

    svg {
      stroke: @sidebar-accent;
    }
  }
}
</style>
