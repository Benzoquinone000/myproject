<template>
  <div class="login-view" :class="{ 'has-alert': serverStatus === 'error' }">
    <div v-if="serverStatus === 'error'" class="server-status-alert">
      <div class="alert-content">
        <exclamation-circle-outlined class="alert-icon" />
        <div class="alert-text">
          <div class="alert-title">服务端连接失败</div>
          <div class="alert-message">{{ serverError }}</div>
        </div>
        <a-button type="link" size="small" @click="checkServerHealth" :loading="healthChecking">
          重试
        </a-button>
      </div>
    </div>

    <div class="login-split">
      <!-- 左侧装饰面板 -->
      <div class="login-decor">
        <div class="decor-content">
          <div class="decor-logo">{{ infoStore.organization.name || '金析智策' }}</div>
          <h2 class="decor-title">{{ infoStore.branding.tagline || '金融数据分析与决策支持' }}</h2>
          <p class="decor-desc">{{ decorDesc }}</p>
          <div class="decor-features">
            <div class="decor-feat">
              <div class="feat-dot"></div>
              <span>金融多智能体协同分析</span>
            </div>
            <div class="decor-feat">
              <div class="feat-dot"></div>
              <span>文档 + 图谱 + 向量混合检索</span>
            </div>
            <div class="decor-feat">
              <div class="feat-dot"></div>
              <span>可视化与研报式决策辅助</span>
            </div>
          </div>
        </div>
        <div class="decor-bg-circle c1"></div>
        <div class="decor-bg-circle c2"></div>
      </div>

      <!-- 右侧表单 -->
      <div class="login-form-side">
        <div class="form-top-action">
          <a-button type="text" size="small" class="back-home-btn" @click="goHome">
            ← 返回首页
          </a-button>
        </div>

        <div class="login-form-wrapper">
          <header class="form-header">
            <p class="form-eyebrow" v-if="!isFirstRun">欢迎回来</p>
            <h1 class="form-title">{{ isFirstRun ? '系统初始化' : '登录账号' }}</h1>
            <p class="form-subtitle" v-if="!isFirstRun">{{ brandSubtitle }}</p>
          </header>

          <div class="form-body" :class="{ 'is-initializing': isFirstRun }">
            <!-- 初始化管理员表单 -->
            <div v-if="isFirstRun" class="init-form">
              <div class="init-notice">
                <p>首次使用，请创建超级管理员账户</p>
              </div>
              <a-form :model="adminForm" @finish="handleInitialize" layout="vertical">
                <a-form-item label="用户ID" name="user_id"
                  :rules="[
                    { required: true, message: '请输入用户ID' },
                    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户ID只能包含字母、数字和下划线' },
                    { min: 3, max: 20, message: '用户ID长度必须在3-20个字符之间' }
                  ]">
                  <a-input v-model:value="adminForm.user_id" placeholder="请输入用户ID（3-20个字符）" :maxlength="20" />
                </a-form-item>

                <a-form-item label="手机号（可选）" name="phone_number"
                  :rules="[{
                    validator: async (rule, value) => {
                      if (!value || value.trim() === '') return;
                      if (!/^1[3-9]\d{9}$/.test(value)) throw new Error('请输入正确的手机号格式');
                    }
                  }]">
                  <a-input v-model:value="adminForm.phone_number" placeholder="可用于登录，可不填写" :max-length="11" />
                </a-form-item>

                <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
                  <a-input-password v-model:value="adminForm.password" />
                </a-form-item>

                <a-form-item label="确认密码" name="confirmPassword"
                  :rules="[{ required: true, message: '请确认密码' }, { validator: validateConfirmPassword }]">
                  <a-input-password v-model:value="adminForm.confirmPassword" />
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" html-type="submit" :loading="loading" block size="large">创建管理员账户</a-button>
                </a-form-item>
              </a-form>
            </div>

            <!-- 登录表单 -->
            <div v-else class="login-form">
              <a-form :model="loginForm" @finish="handleLogin" layout="vertical">
                <a-form-item label="登录账号" name="loginId" :rules="[{ required: true, message: '请输入用户ID或手机号' }]">
                  <a-input v-model:value="loginForm.loginId" placeholder="用户ID或手机号" size="large">
                    <template #prefix><user-outlined /></template>
                  </a-input>
                </a-form-item>

                <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
                  <a-input-password v-model:value="loginForm.password" size="large">
                    <template #prefix><lock-outlined /></template>
                  </a-input-password>
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" html-type="submit" :loading="loading" :disabled="isLocked" block size="large">
                    <span v-if="isLocked">账户已锁定 {{ formatTime(lockRemainingTime) }}</span>
                    <span v-else>登录</span>
                  </a-button>
                </a-form-item>
              </a-form>
            </div>

            <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

            <div class="register-tips" v-if="!isFirstRun">
              <p>还没有账号？<a @click="goToRegister">立即注册</a></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { useInfoStore } from '@/stores/info';
import { useAgentStore } from '@/stores/agent';
import { message } from 'ant-design-vue';
import { healthApi } from '@/apis/system_api';
import { UserOutlined, LockOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
const router = useRouter();
const userStore = useUserStore();
const infoStore = useInfoStore();
const agentStore = useAgentStore();

const decorDesc = computed(() => {
  const d = infoStore.branding?.description?.trim();
  return d || '智能体赋能的数据智能分析，服务研报、对比与风险管理等金融场景。';
});
const brandSubtitle = computed(() => {
  const raw = infoStore.branding?.subtitle ?? '';
  return raw.trim() || '多智能体协同研判 · 知识图谱与 RAG';
});

const isFirstRun = ref(false);
const loading = ref(false);
const errorMessage = ref('');
const serverStatus = ref('loading');
const serverError = ref('');
const healthChecking = ref(false);
const isLocked = ref(false);
const lockRemainingTime = ref(0);
const lockCountdown = ref(null);

const loginForm = reactive({ loginId: '', password: '' });
const adminForm = reactive({ user_id: '', password: '', confirmPassword: '', phone_number: '' });

const goHome = () => router.push('/');
const goToRegister = () => router.push('/register');

const clearLockCountdown = () => {
  if (lockCountdown.value) { clearInterval(lockCountdown.value); lockCountdown.value = null; }
};

const startLockCountdown = (remainingSeconds) => {
  clearLockCountdown();
  isLocked.value = true;
  lockRemainingTime.value = remainingSeconds;
  lockCountdown.value = setInterval(() => {
    lockRemainingTime.value--;
    if (lockRemainingTime.value <= 0) { clearLockCountdown(); isLocked.value = false; errorMessage.value = ''; }
  }, 1000);
};

const formatTime = (seconds) => {
  if (seconds < 60) return `${seconds}秒`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`;
  return `${Math.floor(seconds / 86400)}天${Math.floor((seconds % 86400) / 3600)}小时`;
};

const validateConfirmPassword = async (rule, value) => {
  if (value === '') throw new Error('请确认密码');
  if (value !== adminForm.password) throw new Error('两次输入的密码不一致');
};

const handleLogin = async () => {
  if (isLocked.value) { message.warning(`账户被锁定，请等待 ${formatTime(lockRemainingTime.value)}`); return; }
  try {
    loading.value = true; errorMessage.value = ''; clearLockCountdown();
    await userStore.login({ loginId: loginForm.loginId, password: loginForm.password });
    message.success('登录成功');
    const redirectPath = sessionStorage.getItem('redirect') || '/';
    sessionStorage.removeItem('redirect');
    if (redirectPath === '/') {
      if (userStore.isAdmin) { router.push('/agent'); return; }
      try {
        await agentStore.initialize();
        if (agentStore.defaultAgentId) { router.push(`/agent/${agentStore.defaultAgentId}`); return; }
        const agentIds = Object.keys(agentStore.agents);
        if (agentIds.length > 0) { router.push(`/agent/${agentIds[0]}`); return; }
        router.push('/');
      } catch { router.push('/'); }
    } else { router.push(redirectPath); }
  } catch (error) {
    if (error.status === 423) {
      let remainingTime = 0;
      if (error.headers?.get) { const h = error.headers.get('X-Lock-Remaining'); if (h) remainingTime = parseInt(h); }
      if (remainingTime === 0) { const m = error.message.match(/(\d+)\s*秒/); if (m) remainingTime = parseInt(m[1]); }
      if (remainingTime > 0) { startLockCountdown(remainingTime); errorMessage.value = `由于多次登录失败，账户已被锁定 ${formatTime(remainingTime)}`; }
      else { errorMessage.value = error.message || '账户被锁定，请稍后再试'; }
    } else { errorMessage.value = error.message || '登录失败，请检查用户名和密码'; }
  } finally { loading.value = false; }
};

const handleInitialize = async () => {
  try {
    loading.value = true; errorMessage.value = '';
    if (adminForm.password !== adminForm.confirmPassword) { errorMessage.value = '两次输入的密码不一致'; return; }
    await userStore.initialize({ user_id: adminForm.user_id, password: adminForm.password, phone_number: adminForm.phone_number || null });
    message.success('管理员账户创建成功'); router.push('/');
  } catch (error) { errorMessage.value = error.message || '初始化失败，请重试'; }
  finally { loading.value = false; }
};

const checkFirstRunStatus = async () => {
  try { loading.value = true; isFirstRun.value = await userStore.checkFirstRun(); }
  catch { errorMessage.value = '系统出错，请稍后重试'; }
  finally { loading.value = false; }
};

const checkServerHealth = async () => {
  try {
    healthChecking.value = true;
    const response = await healthApi.checkHealth();
    serverStatus.value = response.status === 'ok' ? 'ok' : 'error';
    if (response.status !== 'ok') serverError.value = response.message || '服务端状态异常';
  } catch (error) { serverStatus.value = 'error'; serverError.value = error.message || '无法连接到服务端'; }
  finally { healthChecking.value = false; }
};

onMounted(async () => {
  if (userStore.isLoggedIn) { router.push('/'); return; }
  await infoStore.loadInfoConfig();
  await checkServerHealth();
  await checkFirstRunStatus();
});

onUnmounted(() => { clearLockCountdown(); });
</script>

<style lang="less" scoped>
.login-view {
  height: 100vh;
  width: 100%;
  position: relative;

  &.has-alert {
    padding-top: 60px;
  }
}

.server-status-alert {
  position: absolute;
  top: 0; left: 0; right: 0;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--color-error-500), var(--color-error-100));
  color: var(--gray-0);
  z-index: 1000;

  .alert-content {
    display: flex;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;

    .alert-icon { font-size: 20px; margin-right: 12px; }
    .alert-text {
      flex: 1;
      .alert-title { font-weight: 600; font-size: 16px; }
      .alert-message { font-size: 14px; opacity: 0.9; }
    }
  }
}

.login-split {
  display: flex;
  height: 100%;
}

.login-decor {
  flex: 0 0 45%;
  background: linear-gradient(145deg, var(--main-600), var(--main-500), var(--main-400));
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 48px;

  .decor-content {
    position: relative;
    z-index: 2;
    color: #fff;
    max-width: 380px;

    .decor-logo {
      font-size: 28px;
      font-weight: 800;
      margin-bottom: 32px;
      letter-spacing: 0.02em;
    }

    .decor-title {
      font-size: 2rem;
      font-weight: 700;
      line-height: 1.3;
      margin: 0 0 16px;
    }

    .decor-desc {
      font-size: 15px;
      opacity: 0.85;
      line-height: 1.6;
      margin: 0 0 32px;
    }

    .decor-features {
      display: flex;
      flex-direction: column;
      gap: 14px;

      .decor-feat {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 14px;
        font-weight: 500;

        .feat-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.7);
          flex-shrink: 0;
        }
      }
    }
  }

  .decor-bg-circle {
    position: absolute;
    border-radius: 50%;
    opacity: 0.1;

    &.c1 { width: 400px; height: 400px; background: #fff; top: -100px; right: -80px; }
    &.c2 { width: 300px; height: 300px; background: #fff; bottom: -60px; left: -40px; }
  }
}

.login-form-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--main-0);
  overflow-y: auto;

  .form-top-action {
    padding: 20px 24px;
    display: flex;
    justify-content: flex-end;
  }

  .back-home-btn {
    color: var(--gray-600);
    font-size: 14px;
    &:hover { color: var(--main-color); background: transparent; }
  }
}

.login-form-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 400px;
  width: 100%;
  margin: 0 auto;
  padding: 0 24px 48px;
}

.form-header {
  margin-bottom: 32px;

  .form-eyebrow {
    font-size: 13px;
    font-weight: 600;
    color: var(--main-color);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0 0 8px;
  }

  .form-title {
    font-size: 26px;
    font-weight: 700;
    color: var(--gray-1000);
    margin: 0 0 8px;
  }

  .form-subtitle {
    font-size: 14px;
    color: var(--gray-600);
    margin: 0;
  }
}

.login-form, .init-form {
  :deep(.ant-form-item) { margin-bottom: 20px; }
  :deep(.ant-input-affix-wrapper) { padding: 10px 12px; }
  :deep(.ant-btn-lg) { height: 44px; font-size: 15px; font-weight: 600; }
}

.init-form {
  .init-notice {
    background: var(--main-50);
    border: 1px solid var(--main-200);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 20px;
    p { margin: 0; color: var(--main-700); font-size: 14px; font-weight: 500; }
  }
}

.error-message {
  margin-top: 16px;
  padding: 10px 12px;
  background: var(--color-error-50);
  border: 1px solid color-mix(in srgb, var(--color-error-500) 25%, transparent);
  border-radius: 8px;
  color: var(--color-error-700);
  font-size: 14px;
}

.register-tips {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: var(--gray-600);

  a {
    color: var(--main-color);
    cursor: pointer;
    text-decoration: none;
    font-weight: 600;
    &:hover { text-decoration: underline; }
  }
}

@media (max-width: 768px) {
  .login-decor { display: none; }
  .login-form-side { flex: 1; }
}
</style>
