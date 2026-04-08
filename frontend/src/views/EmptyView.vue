<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h2 class="error-title">页面未找到</h2>
      <p class="error-desc">您访问的页面不存在或已被移除</p>
      <router-link to="/" class="back-btn">返回首页</router-link>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped lang="less">
.not-found-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--main-5);
}

.not-found-content {
  text-align: center;
  padding: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, var(--main-400), var(--main-600));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 8px;
}

.error-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--gray-900);
  margin: 0 0 12px;
}

.error-desc {
  font-size: 15px;
  color: var(--gray-600);
  margin: 0 0 32px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  padding: 10px 28px;
  background: var(--main-500);
  color: #fff;
  text-decoration: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;

  &:hover {
    background: var(--main-600);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(255, 126, 0, 0.3);
  }
}
</style>
