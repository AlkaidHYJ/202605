<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">爬虫与清洗</div>
          <h1 class="hero-title" style="margin-top: 8px;">数据采集、规则清洗与任务调度</h1>
        </div>
        <el-button type="primary" @click="showTask = true">新建任务</el-button>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">对外部数据源执行定时采集，并通过清洗规则保持入库质量。</p>
    </section>

    <div class="metric-grid">
      <div class="metric-card"><div class="metric-label">爬虫任务</div><span class="metric-value">{{ tasks.length }}</span></div>
      <div class="metric-card"><div class="metric-label">清洗规则</div><span class="metric-value">{{ rules.length }}</span></div>
      <div class="metric-card"><div class="metric-label">运行中</div><span class="metric-value">{{ runningCount }}</span></div>
      <div class="metric-card"><div class="metric-label">失败重试</div><span class="metric-value">03</span></div>
    </div>

    <div class="glass-card" style="padding: 20px;">
      <el-tabs>
        <el-tab-pane label="爬虫任务">
          <div class="soft-grid two" style="margin-bottom: 16px;">
            <div class="instruction-box">
              <div class="metric-label">任务概览</div>
              <div style="margin-top: 8px; line-height: 1.8;">定时执行外部采集任务，适合资讯、网页和定制接口场景。</div>
            </div>
            <div class="instruction-box">
              <div class="metric-label">调度说明</div>
              <div style="margin-top: 8px; line-height: 1.8;">Cron 表达式用于控制执行频率，例如每 6 小时同步一次。</div>
            </div>
          </div>
          <el-table :data="tasks" border style="width: 100%;">
            <el-table-column prop="task_name" label="任务名" />
            <el-table-column prop="source_url" label="源地址" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="清洗规则">
          <el-table :data="rules" border style="width: 100%;">
            <el-table-column prop="rule_name" label="规则名" />
            <el-table-column prop="version" label="版本" width="80" />
            <el-table-column prop="status" label="状态" width="100" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="showTask" title="新建爬虫任务" width="520px">
      <el-form :model="taskForm" label-position="top">
        <el-form-item label="任务名"><el-input v-model="taskForm.task_name" /></el-form-item>
        <el-form-item label="源URL"><el-input v-model="taskForm.source_url" /></el-form-item>
        <el-form-item label="Cron"><el-input v-model="taskForm.schedule_cron" placeholder="0 */6 * * *" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTask = false">取消</el-button>
        <el-button type="primary" @click="createTask">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { crawlerApi } from '../api'

const tasks = ref([])
const rules = ref([])
const showTask = ref(false)
const taskForm = reactive({ task_name: '', source_url: '', schedule_cron: '' })

const runningCount = computed(() => tasks.value.filter((task) => String(task.status).includes('运行') || String(task.status).includes('进行')).length)

async function load() {
  const [t, r] = await Promise.all([crawlerApi.tasks(), crawlerApi.rules()])
  if (t.code === 0) tasks.value = t.data || []
  if (r.code === 0) rules.value = r.data || []
}

async function createTask() {
  await crawlerApi.createTask(taskForm)
  ElMessage.success('已创建')
  showTask.value = false
  load()
}

onMounted(load)
</script>
