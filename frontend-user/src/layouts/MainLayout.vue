<template>
  <el-container class="app-shell">
    <el-aside width="264px" class="sidebar sidebar-card">
      <div class="sidebar-brand">
        <div class="brand-mark">EC</div>
        <div>
          <div class="brand-title">Enterprise Core</div>
          <div class="brand-subtitle">用户工作台</div>
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
        <el-menu-item index="/workspace"><el-icon><HomeFilled /></el-icon>工作台</el-menu-item>
        <el-menu-item index="/nl2sql"><el-icon><DataAnalysis /></el-icon>智能问数</el-menu-item>
        <el-menu-item index="/im"><el-icon><ChatDotRound /></el-icon>即时通讯</el-menu-item>
        <el-menu-item index="/agents"><el-icon><Avatar /></el-icon>数字员工</el-menu-item>
        <el-menu-item index="/dashboards"><el-icon><Monitor /></el-icon>数字大屏</el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <div class="pill">支持中心</div>
        <div class="muted" style="margin-top: 10px; font-size: 12px; line-height: 1.7;">
          面向业务与运营团队的采-洗-析-问-协一体化工作台。
        </div>
        <el-button class="logout-btn" link @click="onLogout">退出登录</el-button>
      </div>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div>
          <div class="muted" style="font-size: 12px;">个人工作空间</div>
          <div class="topbar-title">{{ currentTitle }}</div>
        </div>

        <div class="topbar-actions">
          <el-tag effect="light" round type="success">在线</el-tag>
          <el-dropdown trigger="click" @command="onProfileCommand">
            <div class="profile-chip profile-chip-clickable">
              <el-avatar :size="32">{{ userInitial }}</el-avatar>
              <div>
                <div class="profile-name">{{ userName }}</div>
                <div class="muted" style="font-size: 12px;">账号切换</div>
              </div>
              <el-icon class="profile-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="switch">切换账号</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
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
import { ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const userName = computed(() => auth.user?.real_name || auth.user?.username || '访客')
const userInitial = computed(() => (userName.value ? userName.value.slice(0, 1) : 'U'))
const currentTitle = computed(() => {
  const titles = {
    '/workspace': '个人工作台',
    '/nl2sql': '智能问数',
    '/im': '即时通讯',
    '/agents': '数字员工广场',
    '/dashboards': '数字大屏',
  }
  return titles[route.path] || '个人工作台'
})

function onLogout() {
  auth.logout()
  router.push('/login')
}

function onProfileCommand(command) {
  if (command === 'switch') {
    onLogout()
    return
  }
  if (command === 'logout') {
    onLogout()
  }
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

.profile-chip-clickable {
  cursor: pointer;
}

.profile-arrow {
  font-size: 12px;
  color: var(--muted);
}

.profile-name {
  font-size: 13px;
  font-weight: 700;
}
</style>
