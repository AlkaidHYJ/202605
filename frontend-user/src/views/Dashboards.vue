<template>
  <div class="soft-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">数字大屏</div>
          <h1 class="hero-title" style="margin-top: 8px;">已发布的大屏与预览模板</h1>
        </div>
        <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">{{ list.length }} 个发布项</div>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">点击卡片打开全屏预览，查看数据大屏配置内容与 JSON 结构。</p>
    </section>

    <section class="split-grid">
      <div class="glass-card" style="padding: 20px;">
        <div class="section-heading">
          <h3>大屏列表</h3>
          <span class="muted">点击卡片进行预览</span>
        </div>
        <div class="soft-grid two">
          <el-card v-for="d in list" :key="d.id" shadow="never" class="dashboard-card" @click="open(d)">
            <div class="dashboard-top">
              <div>
                <div class="dashboard-title">{{ d.title }}</div>
                <div class="muted" style="margin-top: 6px; font-size: 12px;">刷新间隔：{{ d.refresh_interval }}s</div>
              </div>
              <div class="pill">预览</div>
            </div>
            <div class="dashboard-preview">{{ summaryText(d.config_json) }}</div>
          </el-card>
        </div>
      </div>

      <aside class="glass-card" style="padding: 20px;">
        <div class="section-heading">
          <h3>使用说明</h3>
          <span class="muted">大屏预览</span>
        </div>
        <div class="instruction-box">
          <div class="metric-label">预览方式</div>
          <div style="margin-top: 8px; line-height: 1.8;">点击任意卡片即可打开全屏预览，查看完整配置 JSON。</div>
        </div>
        <div class="instruction-box" style="margin-top: 14px;">
          <div class="metric-label">刷新策略</div>
          <div style="margin-top: 8px; line-height: 1.8;">刷新间隔由后台配置控制，适合在企业总览屏上展示实时数据。</div>
        </div>
      </aside>
    </section>

    <el-dialog v-model="visible" fullscreen :title="current?.title">
      <div class="screen" v-if="current">
        <div class="screen-head">
          <div>
            <div class="screen-title">{{ current.title }}</div>
            <div class="screen-subtitle">刷新间隔：{{ current.refresh_interval }}s</div>
          </div>
          <el-button @click="visible = false">关闭预览</el-button>
        </div>
        <pre class="screen-json">{{ formatConfig(current.config_json) }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { dashboardApi } from '../api'

const list = ref([])
const visible = ref(false)
const current = ref(null)

onMounted(async () => {
  const res = await dashboardApi.list()
  if (res.code === 0) list.value = res.data || []
})

function open(d) {
  current.value = d
  visible.value = true
}

function formatConfig(json) {
  try {
    return JSON.stringify(JSON.parse(json), null, 2)
  } catch {
    return json
  }
}

function summaryText(json) {
  try {
    const data = JSON.parse(json)
    return Object.keys(data || {}).slice(0, 3).join(' · ') || '配置预览'
  } catch {
    return '配置预览'
  }
}
</script>

<style scoped>
.dashboard-card {
  cursor: pointer;
  border-radius: 18px;
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.dashboard-top {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-title {
  font-size: 16px;
  font-weight: 800;
}

.dashboard-preview {
  margin-top: 16px;
  min-height: 88px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.03);
  color: var(--muted);
  line-height: 1.7;
}

.instruction-box {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.03);
}

.screen {
  min-height: 74vh;
  padding: 24px;
  border-radius: 24px;
  background: linear-gradient(180deg, #0f172a, #1e293b);
  color: #e2e8f0;
}

.screen-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}

.screen-title {
  font-size: 22px;
  font-weight: 900;
}

.screen-subtitle {
  margin-top: 6px;
  color: rgba(226, 232, 240, 0.7);
}

.screen-json {
  margin: 0;
  padding: 18px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.5);
  color: #bfdbfe;
  white-space: pre-wrap;
  overflow-x: auto;
}
</style>
