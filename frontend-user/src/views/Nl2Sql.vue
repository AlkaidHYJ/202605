<template>
  <div class="soft-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">NL2SQL · 智能问数</div>
      <h1 class="hero-title" style="margin-top: 16px;">用自然语言直接得到 SQL、表格和图表</h1>
      <p class="hero-subtitle" style="margin-top: 10px; max-width: 780px; line-height: 1.8;">
        系统会先生成 SQL，再通过 SELECT 沙箱校验并执行。你可以在结果区域在表格与图表之间切换。
      </p>
      <div class="soft-grid three" style="margin-top: 18px;">
        <div class="login-stat"><div class="metric-label">安全校验</div><div class="metric-value" style="color: #fff; font-size: 24px;">SELECT</div></div>
        <div class="login-stat"><div class="metric-label">执行时延</div><div class="metric-value" style="color: #fff; font-size: 24px;">&lt; 10s</div></div>
        <div class="login-stat"><div class="metric-label">结果格式</div><div class="metric-value" style="color: #fff; font-size: 24px;">表 / 图</div></div>
      </div>
    </section>

    <section class="split-grid">
      <div class="glass-card" style="padding: 20px;">
        <div class="section-heading">
          <h3>输入问题</h3>
          <span class="muted">支持中文自然语言描述</span>
        </div>

        <el-input
          v-model="question"
          type="textarea"
          :rows="4"
          placeholder="例如：按区域统计销售额"
          class="query-input"
        />

        <div style="display:flex; gap: 10px; flex-wrap: wrap; margin-top: 12px;">
          <el-tag v-for="preset in presets" :key="preset" round effect="plain" class="preset-tag" @click="question = preset">
            {{ preset }}
          </el-tag>
        </div>

        <div style="display:flex; gap: 12px; align-items: center; margin-top: 16px; flex-wrap: wrap;">
          <el-button type="primary" :loading="loading" @click="runQuery">执行问数</el-button>
          <el-radio-group v-if="result" v-model="viewMode" @change="renderChart">
            <el-radio-button value="table">表格</el-radio-button>
            <el-radio-button value="chart">图表</el-radio-button>
          </el-radio-group>
        </div>

        <el-alert
          title="提示：如果返回结果为空，请换一个更明确的指标或时间范围。"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 16px;"
        />
      </div>

      <div class="stack-grid">
        <div class="glass-card" style="padding: 20px;">
          <div class="section-heading">
            <h3>问数结果</h3>
            <span class="muted">SQL / 解释 / 结果</span>
          </div>
          <div v-if="!result" class="muted" style="min-height: 220px; display: grid; place-items: center;">
            运行一次问数后，这里会显示结果。
          </div>
          <div v-else class="result-stack">
            <div class="result-card">
              <div class="metric-label">SQL</div>
              <code class="sql-block">{{ result.sql }}</code>
            </div>
            <div class="result-card">
              <div class="metric-label">解释</div>
              <div style="margin-top: 8px; line-height: 1.8;">{{ result.interpretation }}</div>
            </div>
          </div>
        </div>

        <div class="glass-card" style="padding: 20px; min-height: 420px;">
          <div class="section-heading">
            <h3>结果展示</h3>
            <span class="muted">{{ viewMode === 'table' ? '表格' : '图表' }}</span>
          </div>
          <el-table v-if="result && viewMode === 'table'" :data="result.rows" border size="small" style="width: 100%;">
            <el-table-column v-for="col in result.columns" :key="col" :prop="col" :label="col" />
          </el-table>
          <div v-else ref="chartRef" class="chart-box"></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { nl2sqlApi } from '../api'

const question = ref('按区域统计销售额')
const loading = ref(false)
const result = ref(null)
const viewMode = ref('table')
const chartRef = ref(null)
const chart = ref(null)
const presets = ['按区域统计销售额', '按月份统计订单数', '按部门统计客户数']

async function runQuery() {
  loading.value = true
  result.value = null
  try {
    const res = await nl2sqlApi.query({ question: question.value })
    if (res.code !== 0) {
      ElMessage.warning(res.message || '查询失败')
      return
    }
    result.value = res.data
    viewMode.value = res.data.chart_type === 'bar' ? 'chart' : 'table'
    await nextTick()
    renderChart()
  } catch (e) {
    ElMessage.error(String(e))
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value || !result.value?.rows?.length || viewMode.value !== 'chart') return
  if (!chart.value) chart.value = echarts.init(chartRef.value)
  const cols = result.value.columns
  chart.value.setOption({
    grid: { left: 24, right: 18, top: 30, bottom: 20, containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: result.value.rows.map((r) => r[cols[0]]), axisLabel: { color: '#64748b' } },
    yAxis: { type: 'value', axisLabel: { color: '#64748b' } },
    series: [{ type: 'bar', data: result.value.rows.map((r) => r[cols[1]]), itemStyle: { borderRadius: [8, 8, 0, 0] } }],
  })
}

watch(viewMode, () => {
  nextTick().then(renderChart)
})

onBeforeUnmount(() => {
  chart.value?.dispose()
  chart.value = null
})
</script>

<style scoped>
.query-input :deep(textarea) {
  border-radius: 18px;
  border-color: rgba(148, 163, 184, 0.26);
  background: rgba(255, 255, 255, 0.88);
}

.preset-tag {
  cursor: pointer;
  user-select: none;
}

.result-stack {
  display: grid;
  gap: 14px;
}

.result-card {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.03);
}

.sql-block {
  display: block;
  margin-top: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #0f172a;
  color: #dbeafe;
  white-space: pre-wrap;
  line-height: 1.7;
  overflow-x: auto;
}

.chart-box {
  width: 100%;
  height: 360px;
}
</style>
