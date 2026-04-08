<template>
  <BaseToolCall :tool-call="toolCall" :hide-params="true">
    <template #header>
      <div class="sep-header">
        <span class="note">知识图谱</span>
        <span class="separator" v-if="query">|</span>
        <span class="description">{{ query }}</span>
      </div>
    </template>
    <template #result="{ resultContent }">
      <div class="knowledge-graph-result">
        <div class="result-summary">
          找到 {{ totalNodes }} 个节点, {{ totalRelations }} 个关系
        </div>

        <!-- 图谱可视化容器 -->
        <div class="graph-visualization" ref="graphContainerRef" v-show="totalNodes > 0 || totalRelations > 0">
          <GraphCanvas :graph-data="graphData" ref="graphContainer" style="height: 360px;">
            <template #top>
              <div class="graph-controls">
                <a-button
                  @click="refreshGraph"
                  :loading="isRefreshing"
                  title="重新渲染图谱"
                  class="refresh-btn"
                >
                  <ReloadOutlined v-if="!isRefreshing" />
                </a-button>
                </div>
            </template>
          </GraphCanvas>
        </div>
      </div>
    </template>
  </BaseToolCall>
</template>

<script setup>
import { computed, ref, watch, nextTick, onMounted } from 'vue';
import BaseToolCall from '../BaseToolCall.vue';
import { DeploymentUnitOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import GraphCanvas from '@/components/GraphCanvas.vue'

const props = defineProps({
  toolCall: {
    type: Object,
    required: true
  }
});

const parseData = (content) => {
  if (typeof content === 'string') {
    try {
      return JSON.parse(content);
    } catch (error) {
      return { triples: [] };
    }
  }
  return content || { triples: [] };
};

const graphContainer = ref(null)
const graphContainerRef = ref(null)
const isVisible = ref(false)
const isRefreshing = ref(false)
const lastResultContent = ref(null)

// 关键：graphData 必须在 tool 结果 content 稳定后才更新。
// GraphCanvas 内部会 watch props.graphData（deep），如果这里在流式中不断生成新的 graphData 对象，
// 即使 triples 内容相同也会触发重渲染，从而造成你看到的“来回晃动/闪烁”。
const graphData = ref({ nodes: [], edges: [] })
let graphUpdateTimer = null

const query = computed(() => {
  const args = props.toolCall.args || props.toolCall.function?.arguments;
  if (!args) return '';
  let parsedArgs = args;
  if (typeof args === 'string') {
    try {
      parsedArgs = JSON.parse(args);
    } catch (e) {
      return '';
    }
  }
  // Try common keys for KG queries
  if (typeof parsedArgs === 'object') {
    return parsedArgs.query || parsedArgs.keywords || parsedArgs.q || parsedArgs.entities || '';
  }
  return '';
});

const buildGraphData = (content) => {
  const data = parseData(content)
  const nodes = new Map()
  const edges = []
  let edgeId = 0

  // 处理新格式数据：只关注 triples 字段
  if (data && typeof data === 'object' && 'triples' in data) {
    const { triples = [] } = data

    triples.forEach(triple => {
      if (Array.isArray(triple) && triple.length >= 3) {
        const [source, relation, target] = triple

        if (source && typeof source === 'string') {
          if (!nodes.has(source)) {
            nodes.set(source, { id: source, name: source })
          }
        }

        if (target && typeof target === 'string') {
          if (!nodes.has(target)) {
            nodes.set(target, { id: target, name: target })
          }
        }

        if (
          source && target && relation &&
          typeof source === 'string' &&
          typeof target === 'string' &&
          typeof relation === 'string'
        ) {
          edges.push({
            source_id: source,
            target_id: target,
            type: relation,
            id: `edge_${edgeId++}`,
          })
        }
      }
    })
  }

  return {
    nodes: Array.from(nodes.values()),
    edges,
  }
}

// 统计信息
const totalNodes = computed(() => graphData.value.nodes.length)
const totalRelations = computed(() => graphData.value.edges.length)

// 检查容器是否可见
const checkVisibility = () => {
  if (graphContainerRef.value) {
    const rect = graphContainerRef.value.getBoundingClientRect();
    isVisible.value = rect.width > 0 && rect.height > 0;
  }
};

// 只在 tool 的最终结果 content 变化时刷新，避免流式过程中 loading/success 多次更新导致图谱闪烁
watch(
  () => props.toolCall?.tool_call_result?.content,
  (newContent) => {
    // 流式过程中可能经历 loading 阶段导致 content 变为 null/空。
    // 为避免 v-show 在 empty/non-empty 间反复切换造成闪烁，content 为空时如果之前已有结果则保持旧图谱不清空。
    if (!newContent) {
      if (lastResultContent.value) return
      graphData.value = { nodes: [], edges: [] }
      lastResultContent.value = null
      return
    }
    if (newContent === lastResultContent.value) return

    // 防抖：避免流式阶段 content 多次小幅更新导致图谱反复重绘
    if (graphUpdateTimer) clearTimeout(graphUpdateTimer)
    graphUpdateTimer = setTimeout(() => {
      lastResultContent.value = newContent
      graphData.value = buildGraphData(newContent)
    }, 250)
  },
  { deep: false, immediate: true }
)

// 组件挂载后确保图表正确初始化
onMounted(() => {
  checkVisibility();
  if (graphData.value.nodes.length > 0 || graphData.value.edges.length > 0) {
    nextTick(() => {
      if (graphContainer.value && typeof graphContainer.value.refreshGraph === 'function') {
        setTimeout(() => {
          graphContainer.value.refreshGraph();
        }, 300);
      }
    });
  }

  const visibilityChecker = setInterval(() => {
    checkVisibility();
    if (isVisible.value && graphContainer.value && typeof graphContainer.value.refreshGraph === 'function') {
      graphContainer.value.refreshGraph();
      clearInterval(visibilityChecker);
    }
  }, 500);

  setTimeout(() => {
    clearInterval(visibilityChecker);
  }, 5000);
});

const refreshGraph = () => {
  isRefreshing.value = true;
  if (graphContainer.value && typeof graphContainer.value.refreshGraph === 'function') {
    setTimeout(() => {
      graphContainer.value.refreshGraph();
      setTimeout(() => {
        isRefreshing.value = false;
      }, 500);
    }, 300);
  } else {
    isRefreshing.value = false;
  }
};

defineExpose({ refreshGraph });
</script>

<style lang="less" scoped>
.knowledge-graph-result {
  background: var(--gray-0);
  border-radius: 8px;
  // border: 1px solid var(--gray-200);

  .result-summary {
    padding: 12px 16px;
    background: var(--gray-25);
    font-size: 12px;
    color: var(--gray-600);
    border-bottom: 1px solid var(--gray-100);
  }

  .graph-visualization {
    margin: 8px;
    background: var(--gray-0);
    border-radius: 6px;
    border: 1px solid var(--gray-200);
    min-height: 350px;

    .graph-controls {
      position: absolute;
      top: 8px;
      right: 8px;
      z-index: 1000;

      .refresh-btn {
        width: 24px;
        height: 24px;
        min-width: 24px;
        padding: 0;
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid var(--gray-300);
        color: var(--gray-600);
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;

        &:hover {
          background: rgba(255, 255, 255, 1);
          border-color: var(--main-color);
          color: var(--main-color);
        }
      }
    }
  }

  .kg-details {
    margin: 8px;
    background: var(--gray-0);
    border-radius: 6px;
    border: 1px solid var(--gray-200);

    :deep(.ant-collapse-header) {
      background: var(--gray-50) !important;
      border-radius: 4px !important;
      margin-bottom: 2px;
      font-size: 13px;
    }

    .entities-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 6px 0;

      .entity-tag {
        margin: 0;
        cursor: default;
        font-size: 11px;
        padding: 2px 6px;
      }
    }

    .relations-list {
      display: flex;
      flex-direction: column;
      gap: 6px;

      .relation-item {
        padding: 8px 10px;
        background: var(--gray-50);
        border-radius: 4px;
        border-left: 2px solid var(--main-color);

        .relation-content {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;

          .entity-name {
            font-weight: 500;
            color: var(--main-color);
            background: var(--main-50);
            padding: 2px 6px;
            border-radius: 10px;
          }

          .relation-type {
            color: var(--main-color);
            font-weight: 500;
            background: var(--gray-100);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid var(--gray-300);
          }
        }
      }
    }

    .raw-data {
      background: var(--gray-50);
      padding: 10px;
      border-radius: 4px;
      font-size: 11px;
      line-height: 1.4;
      max-height: 200px;
      overflow-y: auto;
      margin: 0;
      color: var(--gray-700);
    }
  }
}

</style>