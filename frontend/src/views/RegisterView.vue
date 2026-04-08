<template>
  <div class="register-view">
    <div class="register-split">
      <!-- 左侧装饰面板 -->
      <div class="register-decor">
        <div class="decor-content">
          <div class="decor-logo">{{ infoStore.organization.name || '金析智策' }}</div>
          <h2 class="decor-title">加入我们<br/>共筑数据智能决策能力</h2>
          <p class="decor-desc">注册后即可使用金融数据分析智能体、知识库与图谱等完整能力</p>
        </div>
        <div class="decor-bg-circle c1"></div>
        <div class="decor-bg-circle c2"></div>
      </div>

      <!-- 右侧注册表单 -->
      <div class="register-form-side">
        <div class="form-top-action">
          <a-button type="text" size="small" class="back-login-btn" @click="goToLogin">
            ← 返回登录
          </a-button>
        </div>

        <div class="register-form-wrapper">
          <header class="form-header">
            <p class="form-eyebrow">新用户注册</p>
            <h1 class="form-title">创建账号</h1>
            <p class="form-subtitle" v-if="brandSubtitle">{{ brandSubtitle }}</p>
          </header>

          <div class="form-body">
            <a-form :model="registerForm" @finish="handleRegister" layout="vertical">
              <a-form-item label="用户名" name="username"
                :rules="[
                  { required: true, message: '请输入用户名' },
                  { min: 2, max: 20, message: '用户名长度必须在2-20个字符之间' }
                ]">
                <a-input v-model:value="registerForm.username" placeholder="请输入用户名（2-20个字符）" :maxlength="20" size="large">
                  <template #prefix><user-outlined /></template>
                </a-input>
              </a-form-item>

              <a-form-item label="手机号（可选）" name="phone_number"
                :rules="[{
                  validator: async (rule, value) => {
                    if (!value || value.trim() === '') return;
                    if (!/^1[3-9]\d{9}$/.test(value)) throw new Error('请输入正确的手机号格式');
                  }
                }]">
                <a-input v-model:value="registerForm.phone_number" placeholder="可用于登录，可不填写" :max-length="11" size="large">
                  <template #prefix><phone-outlined /></template>
                </a-input>
              </a-form-item>

              <a-form-item label="密码" name="password"
                :rules="[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码长度不能少于6个字符' }
                ]">
                <a-input-password v-model:value="registerForm.password" placeholder="请输入密码（至少6个字符）" size="large">
                  <template #prefix><lock-outlined /></template>
                </a-input-password>
              </a-form-item>

              <a-form-item label="确认密码" name="confirmPassword"
                :rules="[
                  { required: true, message: '请确认密码' },
                  { validator: validateConfirmPassword }
                ]">
                <a-input-password v-model:value="registerForm.confirmPassword" placeholder="请再次输入密码" size="large">
                  <template #prefix><lock-outlined /></template>
                </a-input-password>
              </a-form-item>

              <a-form-item>
                <a-button type="primary" html-type="submit" :loading="loading" block size="large">注册</a-button>
              </a-form-item>
            </a-form>

            <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

            <div class="login-tips">
              <p>已有账号？<a @click="goToLogin">立即登录</a></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { useInfoStore } from '@/stores/info';
import { message } from 'ant-design-vue';
import { UserOutlined, LockOutlined, PhoneOutlined } from '@ant-design/icons-vue';

const router = useRouter();
const userStore = useUserStore();
const infoStore = useInfoStore();

const brandSubtitle = computed(() => {
  const raw = infoStore.branding?.subtitle ?? '';
  return raw.trim() || '多智能体协同研判 · 知识图谱与 RAG';
});

const loading = ref(false);
const errorMessage = ref('');
const registerForm = reactive({ username: '', phone_number: '', password: '', confirmPassword: '' });

const validateConfirmPassword = async (rule, value) => {
  if (value === '') throw new Error('请确认密码');
  if (value !== registerForm.password) throw new Error('两次输入的密码不一致');
};

const goToLogin = () => router.push('/login');

onMounted(() => {
  infoStore.loadInfoConfig();
});

const handleRegister = async () => {
  try {
    loading.value = true; errorMessage.value = '';
    if (registerForm.phone_number && !/^1[3-9]\d{9}$/.test(registerForm.phone_number)) {
      errorMessage.value = '请输入正确的手机号格式'; return;
    }
    const response = await fetch('/api/auth/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: registerForm.username.trim(), password: registerForm.password,
        phone_number: registerForm.phone_number || null, role: 'user'
      })
    });
    if (!response.ok) { const error = await response.json(); throw new Error(error.detail || '注册失败'); }
    message.success('注册成功，请登录');
    router.push('/login');
  } catch (error) { errorMessage.value = error.message || '注册失败，请重试'; }
  finally { loading.value = false; }
};
</script>

<style lang="less" scoped>
.register-view {
  height: 100vh;
  width: 100%;
}

.register-split {
  display: flex;
  height: 100%;
}

.register-decor {
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

    .decor-logo { font-size: 28px; font-weight: 800; margin-bottom: 32px; }
    .decor-title { font-size: 2rem; font-weight: 700; line-height: 1.3; margin: 0 0 16px; }
    .decor-desc { font-size: 15px; opacity: 0.85; line-height: 1.6; margin: 0; }
  }

  .decor-bg-circle {
    position: absolute; border-radius: 50%; opacity: 0.1;
    &.c1 { width: 400px; height: 400px; background: #fff; top: -100px; right: -80px; }
    &.c2 { width: 300px; height: 300px; background: #fff; bottom: -60px; left: -40px; }
  }
}

.register-form-side {
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

  .back-login-btn {
    color: var(--gray-600);
    font-size: 14px;
    &:hover { color: var(--main-color); background: transparent; }
  }
}

.register-form-wrapper {
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
  .form-eyebrow { font-size: 13px; font-weight: 600; color: var(--main-color); text-transform: uppercase; letter-spacing: 0.1em; margin: 0 0 8px; }
  .form-title { font-size: 26px; font-weight: 700; color: var(--gray-1000); margin: 0 0 8px; }
  .form-subtitle { font-size: 14px; color: var(--gray-600); margin: 0; }
}

.form-body {
  :deep(.ant-form-item) { margin-bottom: 20px; }
  :deep(.ant-input-affix-wrapper) { padding: 10px 12px; }
  :deep(.ant-btn-lg) { height: 44px; font-size: 15px; font-weight: 600; }
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

.login-tips {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: var(--gray-600);

  a { color: var(--main-color); cursor: pointer; text-decoration: none; font-weight: 600; &:hover { text-decoration: underline; } }
}

@media (max-width: 768px) {
  .register-decor { display: none; }
}
</style>
