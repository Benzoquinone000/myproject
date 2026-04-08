<template>
  <div class="page-header">
    <div class="page-header-inner">
      <div class="header-left" v-if="$slots.left">
        <slot name="left"></slot>
      </div>
      <div class="header-main">
        <div class="header-title-row">
          <h1 class="page-title">{{ title }}</h1>
          <loading-outlined v-if="loading" class="loading-icon" />
          <slot name="behind-title"></slot>
        </div>
        <slot name="description">
          <p class="page-desc" v-if="description">{{ description }}</p>
        </slot>
      </div>
      <div class="header-actions" v-if="$slots.actions">
        <slot name="actions"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { LoadingOutlined } from '@ant-design/icons-vue';
const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  loading: { type: Boolean, default: false }
});
</script>

<style scoped lang="less">
.page-header {
  background: var(--main-0);
  padding: 16px 24px;
  border-bottom: 1px solid var(--gray-100);
  position: sticky;
  top: 0;
  z-index: 50;
}

.page-header-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-main {
  flex: 1;
  min-width: 0;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--gray-1000);
  letter-spacing: -0.01em;
}

.loading-icon {
  color: var(--main-color);
  font-size: 16px;
}

.page-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--gray-600);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
</style>
