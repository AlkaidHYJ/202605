<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="login-hero hero-block">
        <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">管理端 · OpsControl</div>
        <h1 class="hero-title" style="margin-top: 18px;">企业级管控与审计中枢</h1>
        <p class="hero-subtitle" style="margin-top: 12px; max-width: 520px; line-height: 1.8;">
          面向组织、群组、消息合规与爬虫任务的统一运营控制台。支持审计、禁言、解散和敏感词管理。
        </p>

        <div class="soft-grid three" style="margin-top: 22px;">
          <div class="login-stat"><div class="metric-label">总群组</div><div class="metric-value" style="color: #fff; font-size: 24px;">12.4k</div></div>
          <div class="login-stat"><div class="metric-label">今日告警</div><div class="metric-value" style="color: #fff; font-size: 24px;">158</div></div>
          <div class="login-stat"><div class="metric-label">在线节点</div><div class="metric-value" style="color: #fff; font-size: 24px;">42</div></div>
        </div>
      </section>

      <section class="login-panel glass-card">
        <div class="card-title">登录到管理后台</div>
        <div class="section-note" style="margin-top: 8px;">请输入管理员账号进入控制台。</div>

        <el-form label-position="top" class="login-form" @submit.prevent="submit">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="admin" size="large" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" show-password size="large" />
          </el-form-item>
          <el-button type="primary" size="large" native-type="submit" :loading="loading" class="login-btn">进入后台</el-button>
        </el-form>

        <div class="demo-box">
          <div class="section-note">演示账号</div>
          <div class="demo-row"><span>管理端</span><strong>admin / admin123</strong></div>
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
const form = reactive({ username: 'admin', password: 'admin123' })

async function submit() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    router.push('/users')
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
