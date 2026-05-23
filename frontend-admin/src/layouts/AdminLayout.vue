<template>
  <el-container class="app-shell">
    <el-aside width="264px" class="sidebar sidebar-card">
      <div class="sidebar-brand">
        <div class="brand-mark">OC</div>
        <div>
          <div class="brand-title">OpsControl</div>
          <div class="brand-subtitle">企业管理后台</div>
        </div>
      </div>

      <el-menu
        class="sidebar-menu"
        :default-active="route.path"
        router
        background-color="transparent"
        text-color="rgba(255,255,255,.72)"
        active-text-color="#fff"
      >
        <el-menu-item index="/users"><el-icon><User /></el-icon>用户组织</el-menu-item>
        <el-menu-item index="/groups"><el-icon><Collection /></el-icon>群组管理</el-menu-item>
        <el-menu-item index="/models"><el-icon><Cpu /></el-icon>模型管理</el-menu-item>
        <el-menu-item index="/skills"><el-icon><MagicStick /></el-icon>技能管理</el-menu-item>
        <el-menu-item index="/agents"><el-icon><Avatar /></el-icon>数字员工</el-menu-item>
        <el-menu-item index="/messages"><el-icon><ChatLineSquare /></el-icon>消息合规</el-menu-item>
        <el-menu-item index="/sensitive"><el-icon><Warning /></el-icon>敏感词库</el-menu-item>
        <el-menu-item index="/crawler"><el-icon><Download /></el-icon>爬虫与清洗</el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <div class="pill">管理员控制台</div>
        <div class="muted" style="margin-top: 10px; font-size: 12px; line-height: 1.7;">用于统管组织、消息审计和数据采集流程。</div>
        <el-button class="logout-btn" link @click="logout">退出登录</el-button>
      </div>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div>
          <div class="muted" style="font-size: 12px;">企业级管控中心</div>
          <div class="topbar-title">{{ currentTitle }}</div>
        </div>
        <div class="topbar-actions">
          <el-tag effect="light" round type="danger">审计在线</el-tag>
          <div class="profile-chip">
            <el-avatar :size="32">{{ userInitial }}</el-avatar>
            <div>
              <div class="profile-name">{{ userName }}</div>
              <div class="muted" style="font-size: 12px;">全局管理员</div>
            </div>
          </div>
        </div>
      </el-header>

      <el-main class="page-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const userName = computed(() => auth.user?.username || 'admin')
const userInitial = computed(() => (userName.value ? userName.value.slice(0, 1).toUpperCase() : 'A'))
const currentTitle = computed(() => {
  const titles = {
    '/users': '用户组织',
    '/groups': '群组管理',
    '/models': '模型管理',
    '/skills': '技能管理',
    '/agents': '数字员工',
    '/messages': '消息合规',
    '/sensitive': '敏感词库',
    '/crawler': '爬虫与清洗',
  }
  return titles[route.path] || '企业级管控中心'
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  padding: 20px 16px 16px;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.brand-mark {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, #4f46e5, #0ea5e9);
  color: #fff;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.brand-title {
  font-weight: 800;
  font-size: 18px;
  color: #fff;
}

.brand-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.66);
  margin-top: 2px;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  margin: 4px 0;
  border-radius: 14px;
  height: 48px;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.14);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.sidebar-footer {
  margin-top: auto;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
}

.logout-btn {
  color: #fff;
  margin-top: 14px;
  padding: 0;
}

.topbar {
  height: 76px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px);
}

.topbar-title {
  margin-top: 4px;
  font-size: 22px;
  font-weight: 900;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.profile-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px 8px 8px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.04);
}

.profile-name {
  font-size: 13px;
  font-weight: 700;
}
</style>
