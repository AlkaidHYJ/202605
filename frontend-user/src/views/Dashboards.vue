<template>
  <div class="dash-shell">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">数字大屏</div>
          <h1 class="hero-title" style="margin-top: 8px;">爬虫任务可视化结果</h1>
        </div>
        <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">{{ report.total }} 条数据</div>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">
        顶部选择一条爬虫任务，查看该任务对应的数字化结果与统计图表。
      </p>
    </section>

    <section class="control-bar glass-card">
      <div>
        <div class="metric-label">选择任务</div>
        <div class="muted" style="font-size: 12px; margin-top: 6px;">切换后会更新右侧报表与中间内容</div>
      </div>
      <el-select v-model="selectedTaskId" filterable placeholder="选择爬虫任务" style="min-width: 320px;">
        <el-option v-for="task in taskOptions" :key="task.id" :label="task.task_name" :value="task.id" />
      </el-select>
    </section>

    <section class="report-shell">
      <div class="report-head">
        <div>
          <div class="report-title">采集结果 · 数字化报告</div>
          <div class="muted" style="margin-top: 8px;">{{ selectedTaskLabel }}</div>
        </div>
        <div class="pill">{{ report.date_range || '暂无日期范围' }}</div>
      </div>

      <div class="report-stats">
        <div class="report-card"><div class="report-label">新闻总数</div><b>{{ report.total }}</b></div>
        <div class="report-card"><div class="report-label">爬取成功</div><b>{{ report.cleaned }}</b></div>
        <div class="report-card"><div class="report-label">日期范围</div><b class="report-small">{{ report.date_range || '暂无' }}</b></div>
        <div class="report-card"><div class="report-label">平均正文字数</div><b>{{ report.avg_length }}</b></div>
        <div class="report-card"><div class="report-label">清洗后</div><b>{{ report.cleaned_ready }}</b></div>
        <div class="report-card"><div class="report-label">清洗前</div><b>{{ report.raw_count }}</b></div>
      </div>

      <div class="visual-grid">
        <section class="panel-box">
          <h2>高频词数字化图</h2>
          <div class="keyword-bars">
            <div v-for="item in keywordBars" :key="item.word" class="keyword-row">
              <span class="keyword-word">{{ item.word }}</span>
              <div class="keyword-track"><div class="keyword-fill" :style="{ width: item.percent + '%' }" /></div>
              <span class="keyword-count">{{ item.count }}</span>
            </div>
            <div v-if="keywordBars.length === 0" class="empty-note">暂无关键词数据</div>
          </div>
        </section>

        <section class="earth-panel">
          <iframe class="earth-frame" src="/3d_earth/index.html" title="3D Earth" loading="lazy" />
          <div class="earth-overlay">
            <div class="earth-title">Global Data Stream</div>
            <div class="earth-subtitle">Crawler to Cleaned Markdown</div>
          </div>
          <div class="earth-summary">
            <div class="summary-card">
              <span>新闻总数</span>
              <b>{{ report.total }}</b>
            </div>
            <div class="summary-card">
              <span>爬取成功</span>
              <b>{{ report.cleaned }}</b>
            </div>
            <div class="summary-card">
              <span>日期范围</span>
              <b>{{ report.date_range || '暂无' }}</b>
            </div>
            <div class="summary-card">
              <span>平均正文字数</span>
              <b>{{ report.avg_length }}</b>
            </div>
          </div>
        </section>

        <section class="panel-box">
          <h2>来源分布饼状图</h2>
          <div class="pie-wrap" v-if="sourceSeries.length">
            <div class="pie-chart" :style="{ background: pieBackground }" />
            <div class="pie-legend">
              <div v-for="item in sourceSeries" :key="item.name" class="legend-row">
                <span class="legend-dot" :style="{ background: item.color }" />
                <span class="legend-name">{{ item.name }}</span>
                <span class="legend-count">{{ item.count }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-note">暂无来源数据</div>
        </section>
      </div>
    </section>

    <section class="data-grid">
      <div class="glass-card data-panel">
        <div class="section-heading">
          <h3>最新结果</h3>
          <span class="muted">{{ results.length }} 条</span>
        </div>
        <div class="result-list">
          <div v-for="item in results" :key="item.id" class="result-card">
            <div class="result-title">{{ item.title || '未命名' }}</div>
            <div class="result-meta">{{ item.source_url }}</div>
            <div class="result-snippet">{{ snippet(item.markdown) }}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="split-grid">
      <div class="glass-card" style="padding: 20px;">
        <div class="section-heading">
          <h3>大屏模板</h3>
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
          <div style="margin-top: 8px; line-height: 1.8;">选择不同爬虫任务后，顶部报表和图表会同步刷新。</div>
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
import { computed, onMounted, ref, watch } from 'vue'
import { crawlerApi, dashboardApi } from '../api'

const list = ref([])
const taskOptions = ref([])
const results = ref([])
const report = ref({ total: 0, cleaned: 0, raw_count: 0, cleaned_ready: 0, avg_length: 0, date_range: '' })
const visible = ref(false)
const current = ref(null)
const selectedTaskId = ref(null)

const selectedTaskLabel = computed(() => {
  const task = taskOptions.value.find((item) => item.id === selectedTaskId.value)
  return task ? `当前任务：${task.task_name}` : '请选择一条爬虫任务'
})

onMounted(async () => {
  const [dashRes, taskRes] = await Promise.all([dashboardApi.list(), crawlerApi.publicTasks()])
  if (dashRes.code === 0) list.value = dashRes.data || []
  if (taskRes.code === 0) {
    taskOptions.value = taskRes.data || []
    if (taskOptions.value.length > 0) {
      selectedTaskId.value = taskOptions.value[0].id
    }
  }
})

watch(selectedTaskId, async (taskId) => {
  if (!taskId) {
    results.value = []
    report.value = { total: 0, cleaned: 0, raw_count: 0, cleaned_ready: 0, avg_length: 0, date_range: '' }
    return
  }
  const [resultRes, reportRes] = await Promise.all([
    crawlerApi.publicResults(taskId),
    crawlerApi.publicReport(taskId),
  ])
  if (resultRes.code === 0) {
    results.value = resultRes.data || []
  }
  if (reportRes.code === 0 && reportRes.data) {
    report.value = {
      ...reportRes.data,
      raw_count: reportRes.data.total || 0,
      cleaned_ready: reportRes.data.cleaned || 0,
    }
  }
}, { immediate: true })

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

function snippet(markdown) {
  if (!markdown) return '暂无内容'
  return markdown.split('\n').filter((line) => line.trim()).slice(0, 3).join(' ').slice(0, 160)
}

const sourceSeries = computed(() => {
  const counts = {}
  results.value.forEach((item) => {
    const host = (() => {
      try { return new URL(item.source_url).hostname } catch { return '其他' }
    })()
    counts[host] = (counts[host] || 0) + 1
  })
  const palette = ['#b10001', '#e76f51', '#2a9d8f', '#264653', '#f4a261', '#6d597a']
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, count], index) => ({ name, count, color: palette[index % palette.length] }))
})

const pieBackground = computed(() => {
  const total = sourceSeries.value.reduce((sum, item) => sum + item.count, 0) || 1
  let acc = 0
  const parts = sourceSeries.value.map((item) => {
    const start = (acc / total) * 100
    acc += item.count
    const end = (acc / total) * 100
    return `${item.color} ${start}% ${end}%`
  })
  return `conic-gradient(${parts.join(', ')})`
})

const keywordBars = computed(() => {
  const text = results.value.map((item) => item.title || '').join(' ')
  const words = text
    .replace(/[\s\d\p{P}\p{S}]/gu, ' ')
    .split(' ')
    .map((word) => word.trim())
    .filter((word) => word.length >= 2)
  const counter = {}
  words.forEach((word) => {
    counter[word] = (counter[word] || 0) + 1
  })
  return Object.keys(counter)
    .sort((a, b) => counter[b] - counter[a])
    .slice(0, 10)
    .map((word) => ({ word, count: counter[word] }))
    .map((item) => ({ ...item, percent: Math.max(12, Math.min(100, item.count * 24)) }))
})
</script>

<style scoped>
.dash-shell { display: grid; gap: 20px; }
.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
}

.report-shell {
  background: #f7f5f2;
  border-radius: 20px;
  padding: 20px;
  border: 1px solid rgba(177, 0, 1, 0.12);
}

.report-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.report-title {
  font-size: 18px;
  font-weight: 800;
  color: #b10001;
  border-bottom: 2px solid #b10001;
  padding-bottom: 8px;
}

.report-stats {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.report-card {
  background: #fff;
  padding: 14px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.report-card b {
  display: block;
  font-size: 22px;
  color: #b10001;
  margin-top: 6px;
}

.report-small { font-size: 14px !important; line-height: 1.5; }
.report-label { color: #666; font-size: 12px; }

.visual-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(420px, 1.25fr) minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
}

.panel-box {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.panel-box h2 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #333;
}

.keyword-bars { display: grid; gap: 8px; }
.keyword-row {
  display: grid;
  grid-template-columns: 88px 1fr 28px;
  gap: 10px;
  align-items: center;
}
.keyword-word { font-size: 12px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.keyword-track { height: 10px; background: #f1e7e7; border-radius: 999px; overflow: hidden; }
.keyword-fill { height: 100%; background: linear-gradient(90deg, #b10001, #d94841); border-radius: 999px; }
.keyword-count { font-size: 12px; color: #b10001; text-align: right; font-weight: 700; }

.earth-panel {
  position: relative;
  min-height: 540px;
  border-radius: 26px;
  overflow: hidden;
  background: radial-gradient(circle at top, rgba(15, 23, 42, 0.7), rgba(15, 23, 42, 0.95));
  box-shadow: 0 30px 70px rgba(15, 23, 42, 0.3);
}

.earth-frame { width: 100%; height: 100%; border: none; display: block; }

.earth-overlay {
  position: absolute;
  top: 18px;
  left: 18px;
  padding: 10px 14px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.55);
  color: #e2e8f0;
  backdrop-filter: blur(10px);
}

.earth-title { font-size: 14px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.earth-subtitle { margin-top: 6px; font-size: 12px; color: rgba(226, 232, 240, 0.8); }

.earth-summary {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 16px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.summary-card {
  padding: 12px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.62);
  color: #fff;
  backdrop-filter: blur(10px);
}
.summary-card span { display: block; font-size: 12px; color: rgba(226, 232, 240, 0.72); }
.summary-card b { display: block; margin-top: 8px; font-size: 14px; line-height: 1.4; }

.pie-wrap { display: grid; gap: 14px; }
.pie-chart {
  width: 220px;
  height: 220px;
  margin: 0 auto;
  border-radius: 50%;
  border: 12px solid #fff;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.05);
}
.pie-legend { display: grid; gap: 8px; }
.legend-row { display: grid; grid-template-columns: 12px 1fr 28px; gap: 10px; align-items: center; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; }
.legend-name { font-size: 12px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.legend-count { font-size: 12px; color: #b10001; font-weight: 700; text-align: right; }

.data-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.data-panel { padding: 20px; }
.result-list { display: grid; gap: 12px; max-height: 420px; overflow-y: auto; padding-right: 4px; }
.result-card { padding: 12px 14px; border-radius: 16px; background: rgba(15, 23, 42, 0.04); border: 1px solid rgba(148, 163, 184, 0.2); }
.result-title { font-weight: 800; margin-bottom: 6px; }
.result-meta { font-size: 12px; color: var(--muted); margin-bottom: 8px; }
.result-snippet { font-size: 13px; color: #0f172a; line-height: 1.6; }
.compare-block { padding: 12px 14px; border-radius: 16px; background: rgba(15, 23, 42, 0.04); border: 1px solid rgba(148, 163, 184, 0.2); }
.compare-title { font-size: 12px; font-weight: 800; color: #b10001; margin-bottom: 8px; }
.compare-pre { margin: 0; white-space: pre-wrap; line-height: 1.7; font-size: 12px; color: #0f172a; }
.empty-note { color: var(--muted); font-size: 12px; }

.split-grid { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr); gap: 16px; }
.dashboard-card {
  cursor: pointer;
  border-radius: 18px;
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
}
.dashboard-top { display: flex; align-items: start; justify-content: space-between; gap: 12px; }
.dashboard-title { font-size: 16px; font-weight: 800; }
.dashboard-preview {
  margin-top: 16px;
  min-height: 88px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.03);
  color: var(--muted);
  line-height: 1.7;
}
.instruction-box { padding: 14px 16px; border-radius: 16px; background: rgba(15, 23, 42, 0.03); }
.screen {
  min-height: 74vh;
  padding: 24px;
  border-radius: 24px;
  background: linear-gradient(180deg, #0f172a, #1e293b);
  color: #e2e8f0;
}
.screen-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 20px; }
.screen-title { font-size: 22px; font-weight: 900; }
.screen-subtitle { margin-top: 6px; color: rgba(226, 232, 240, 0.7); }
.screen-json { margin: 0; padding: 18px; border-radius: 18px; background: rgba(15, 23, 42, 0.5); color: #bfdbfe; white-space: pre-wrap; overflow-x: auto; }

@media (max-width: 1280px) {
  .report-stats,
  .visual-grid,
  .data-grid,
  .split-grid {
    grid-template-columns: 1fr;
  }

  .earth-panel { min-height: 440px; }
  .earth-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 860px) {
  .control-bar { flex-direction: column; align-items: stretch; }
  .keyword-row { grid-template-columns: 72px 1fr 24px; }
}
</style>
