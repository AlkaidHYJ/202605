<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="login-hero hero-block">
        <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">用户端 · 采-洗-析-问-协</div>
        <h1 class="hero-title" style="margin-top: 18px;">企业智能数据洞察与数字员工协同平台</h1>
        <p class="hero-subtitle" style="margin-top: 12px; max-width: 520px; line-height: 1.8;">
          将数据检索、即时协作、智能问数与数字员工整合在一个统一工作台中，支持业务团队快速完成分析与决策。
        </p>

        <div class="soft-grid three" style="margin-top: 22px;">
          <div class="login-stat">
            <div class="metric-label">分析时效</div>
            <div class="metric-value" style="color: #fff; font-size: 24px;">2 分钟</div>
          </div>
          <div class="login-stat">
            <div class="metric-label">协作入口</div>
            <div class="metric-value" style="color: #fff; font-size: 24px;">IM / Agents</div>
          </div>
          <div class="login-stat">
            <div class="metric-label">数据屏幕</div>
            <div class="metric-value" style="color: #fff; font-size: 24px;">实时同步</div>
          </div>
        </div>
      </section>

      <section class="login-panel glass-card">
        <div class="card-title">{{ mode === 'login' ? '登录到用户端' : '注册新账号' }}</div>
        <div class="section-note" style="margin-top: 8px;">可选择登录已有账号或注册新账号。</div>

        <div class="mode-tabs">
          <button :class="['tab-btn', mode === 'login' ? 'active' : '']" @click="mode = 'login'">登录</button>
          <button :class="['tab-btn', mode === 'register' ? 'active' : '']" @click="mode = 'register'">注册</button>
        </div>

        <el-form ref="formRef" :model="form" label-position="top" class="login-form" @submit.prevent="onSubmit">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="user01" size="large" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" show-password size="large" />
          </el-form-item>
          <el-form-item v-if="mode === 'register'" label="姓名">
            <el-input v-model="form.real_name" placeholder="请输入姓名" size="large" />
          </el-form-item>

          <el-button type="primary" size="large" native-type="submit" :loading="loading" class="login-btn">
            {{ mode === 'login' ? '进入工作台' : '完成注册' }}
          </el-button>
        </el-form>

        <div class="demo-box">
          <div class="section-note">演示账号</div>
          <div class="demo-row"><span>用户端</span><strong>user01 / user123</strong></div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const mode = ref('login')
const form = reactive({ username: 'user01', password: 'user123', real_name: '' })

async function onSubmit() {
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(form.username, form.password)
      router.push('/workspace')
    } else {
      await auth.register({
        username: form.username,
        password: form.password,
        real_name: form.real_name || null,
      })
      ElMessage.success('注册成功，请使用新账号登录')
      mode.value = 'login'
      form.password = ''
    }
  } catch (e) {
    ElMessage.error(String(e))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.login-shell {
  width: min(1180px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(360px, 0.85fr);
  gap: 20px;
}

.login-hero {
  min-height: 640px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-stat {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.login-panel {
  padding: 30px;
  align-self: center;
}

.login-form {
  margin-top: 24px;
}

.login-btn {
  width: 100%;
  margin-top: 12px;
  height: 46px;
  border-radius: 14px;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  padding: 6px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.04);
  margin-top: 16px;
}

.tab-btn {
  flex: 1;
  border: none;
  padding: 8px 0;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  background: transparent;
  color: var(--muted);
}

.tab-btn.active {
  background: #fff;
  color: var(--primary);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08);
}

.demo-box {
  margin-top: 22px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.03);
}

.demo-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  color: var(--muted);
}

@media (max-width: 980px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .login-hero {
    min-height: auto;
  }
}
</style>
