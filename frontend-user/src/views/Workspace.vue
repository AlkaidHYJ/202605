<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 10px;">
        <div>
          <div class="hero-subtitle">今天是 2026 年 5 月 22 日</div>
          <h1 class="hero-title" style="margin-top: 10px;">早安，振宇</h1>
        </div>
        <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">当前效率 94%</div>
      </div>
      <p class="hero-subtitle" style="max-width: 720px;">今天你有 4 个待办事项和 2 个 AI 处理中的任务。先从高频入口切入，快速完成数据洞察与协作。</p>

      <div class="metric-grid" style="margin-top: 22px;">
        <div class="metric-card">
          <div class="metric-label">已完成任务</div>
          <span class="metric-value">128</span>
          <div class="metric-desc">同比提升 12%</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">平均响应时长</div>
          <span class="metric-value">1.2h</span>
          <div class="metric-desc">较上周下降 2%</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">AI 协同节省时间</div>
          <span class="metric-value">42.5h</span>
          <div class="metric-desc">本周新增 8 个流程</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">待处理 AI</div>
          <span class="metric-value">08</span>
          <div class="metric-desc">当前正在处理</div>
        </div>
      </div>
    </section>

    <section class="soft-grid two">
      <div class="glass-card" style="padding: 20px;">
        <div class="section-heading">
          <h3>快速入口</h3>
          <span class="muted">一键进入核心能力</span>
        </div>
        <div class="soft-grid two">
          <el-card v-for="item in shortcuts" :key="item.path" shadow="never" class="shortcut-card" @click="$router.push(item.path)">
            <el-icon :size="28" class="shortcut-icon"><component :is="item.icon" /></el-icon>
            <div class="shortcut-title">{{ item.title }}</div>
            <div class="muted" style="margin-top: 8px; font-size: 12px; line-height: 1.7;">{{ item.desc }}</div>
          </el-card>
        </div>
      </div>

      <div class="glass-card" style="padding: 20px;">
        <div class="section-heading">
          <h3>最近问数</h3>
          <span class="muted">最近 5 条记录</span>
        </div>
        <el-empty v-if="!history.length" description="暂无记录" />
        <div v-else class="history-list">
          <div v-for="h in history" :key="h.id" class="history-item">
            <div class="history-dot"></div>
            <div>
              <div class="history-question">{{ h.question }}</div>
              <div class="muted" style="font-size: 12px; margin-top: 4px;">{{ h.created_at }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { nl2sqlApi } from '../api'

const history = ref([])
const shortcuts = [
  { title: '智能问数', path: '/nl2sql', icon: 'DataAnalysis', desc: '自然语言转 SQL，直接生成结果表与图表。' },
  { title: '即时通讯', path: '/im', icon: 'ChatDotRound', desc: '群聊协作与数字员工会话入口。' },
  { title: '数字员工', path: '/agents', icon: 'Avatar', desc: '在员工广场中选择合适的 AI 角色。' },
  { title: '数字大屏', path: '/dashboards', icon: 'Monitor', desc: '查看已发布的大屏列表和全屏预览。' },
]

onMounted(async () => {
  try {
    const res = await nl2sqlApi.history()
    if (res.code === 0) history.value = res.data?.slice(0, 5) || []
  } catch {
    history.value = []
  }
})
</script>

<style scoped>
.shortcut-card {
  cursor: pointer;
  border-radius: 18px;
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.shortcut-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.shortcut-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(29, 78, 216, 0.08);
  color: var(--primary);
}

.shortcut-title {
  margin-top: 12px;
  font-size: 16px;
  font-weight: 800;
}

.history-list {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.history-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.03);
}

.history-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 6px;
  background: linear-gradient(135deg, var(--primary), #7c3aed);
  flex: none;
}

.history-question {
  font-weight: 700;
}
</style>
