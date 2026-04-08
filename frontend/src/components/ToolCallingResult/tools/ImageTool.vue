<template>
  <BaseToolCall :tool-call="toolCall" :default-expanded="true">
    <template #result>
      <div class="image-result">
        <template v-if="imageUrl">
          <img
            :src="imageUrl"
            alt="图表生成结果"
            referrerpolicy="no-referrer"
            loading="lazy"
            @error="imgError = true"
            @load="imgError = false"
          />
          <a
            v-if="!imgError && isHttpUrl"
            :href="imageUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="image-open-link"
          >
            在新标签页打开图片
          </a>
        </template>
        <div v-else class="image-fallback">无法从工具返回中解析图片地址</div>
      </div>
    </template>
  </BaseToolCall>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import BaseToolCall from '../BaseToolCall.vue';
import { extractChartImageUrl } from '@/utils/toolResultImages';

const props = defineProps({
  toolCall: {
    type: Object,
    required: true
  }
});

const imgError = ref(false);

const imageUrl = computed(() =>
  extractChartImageUrl(props.toolCall.tool_call_result?.content)
);

const isHttpUrl = computed(() => {
  const u = imageUrl.value;
  return u && /^https?:\/\//i.test(u);
});

watch(
  () => props.toolCall.tool_call_result?.content,
  () => {
    imgError.value = false;
  }
);
</script>

<style lang="less" scoped>
.image-result {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 8px;

  img {
    max-width: 100%;
    border-radius: 4px;
    border: 1px solid var(--gray-150);
    background: var(--gray-25);
  }

  .image-open-link {
    font-size: 12px;
    color: var(--main-700);
  }

  .image-fallback {
    font-size: 12px;
    color: var(--gray-600);
    padding: 8px;
  }
}
</style>
