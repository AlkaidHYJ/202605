<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">爬虫与清洗</div>
          <h1 class="hero-title" style="margin-top: 8px;">数据采集、规则清洗与任务调度</h1>
        </div>
        <div style="display: flex; gap: 10px;">
          <el-button type="primary" @click="showTask = true">新建任务</el-button>
          <el-button @click="showRule = true">新建清洗规则</el-button>
        </div>
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
          <div class="section-heading" style="margin-bottom: 12px;">
            <div>
              <div class="metric-label">默认清洗规则</div>
              <div class="muted" style="font-size: 12px; margin-top: 6px;">运行任务时可自动清洗，或手动批量清洗。</div>
            </div>
            <el-select v-model="selectedRuleId" placeholder="选择清洗规则（可选）" clearable style="min-width: 220px;">
              <el-option v-for="r in rules" :key="r.id" :label="r.rule_name" :value="r.id" />
            </el-select>
          </div>
          <el-table :data="tasks" border style="width: 100%;">
            <el-table-column prop="task_name" label="任务名" />
            <el-table-column prop="source_url" label="源地址" show-overflow-tooltip />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">{{ statusText(row.status) }}</template>
            </el-table-column>
            <el-table-column label="进度" width="180">
              <template #default="{ row }">
                <el-progress
                  :percentage="progressPercent(row.status)"
                  :status="progressStatus(row.status)"
                  :indeterminate="Number(row.status) === 1"
                  :duration="1.2"
                  :stroke-width="8"
                />
              </template>
            </el-table-column>
            <el-table-column prop="last_run_at" label="上次运行" width="180" />
            <el-table-column label="操作" width="260">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="runTask(row)">运行</el-button>
                <el-button size="small" @click="loadResults(row)">结果</el-button>
                <el-button size="small" @click="applyCleaning(row)" :disabled="!selectedRuleId">清洗</el-button>
                <el-button size="small" @click="stopTask(row)" :disabled="Number(row.status) === 4">停止</el-button>
                <el-button size="small" type="danger" plain @click="deleteTask(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="activeTask" style="margin-top: 18px;">
            <div class="section-heading">
              <h3>任务结果</h3>
              <span class="muted">任务：{{ activeTask.task_name }}</span>
            </div>
            <el-table :data="results" border style="width: 100%;">
              <el-table-column prop="title" label="标题" show-overflow-tooltip />
              <el-table-column prop="source_url" label="源地址" show-overflow-tooltip />
              <el-table-column label="清洗状态" width="120">
                <template #default="{ row }">{{ cleanStatusText(row.clean_status) }}</template>
              </el-table-column>
              <el-table-column prop="created_at" label="采集时间" width="180" />
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button size="small" @click="openResult(row)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
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
        <el-form-item label="请求方法">
          <el-select v-model="taskForm.request_method">
            <el-option label="GET" value="GET" />
            <el-option label="POST" value="POST" />
          </el-select>
        </el-form-item>
        <el-form-item label="请求头(JSON)"><el-input v-model="taskForm.request_headers" type="textarea" :rows="3" placeholder='{"User-Agent":"Crawler"}' /></el-form-item>
        <el-form-item label="请求体"><el-input v-model="taskForm.request_body" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="解析类型">
          <el-select v-model="taskForm.parse_type">
            <el-option label="CSS" value="css" />
            <el-option label="XPath" value="xpath" />
          </el-select>
        </el-form-item>
        <el-form-item label="正文选择器"><el-input v-model="taskForm.selector" placeholder="body" /></el-form-item>
        <el-form-item label="标题选择器"><el-input v-model="taskForm.title_selector" placeholder="title" /></el-form-item>
        <el-form-item label="输出模式">
          <el-select v-model="taskForm.output_mode">
            <el-option label="Markdown" value="markdown" />
            <el-option label="手动处理" value="manual" />
          </el-select>
        </el-form-item>
        <el-form-item label="浏览器模式">
          <el-switch v-model="taskForm.use_browser" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTask = false">取消</el-button>
        <el-button type="primary" @click="createTask">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showRule" title="新建清洗规则" width="520px">
      <el-form :model="ruleForm" label-position="top">
        <el-form-item label="规则名"><el-input v-model="ruleForm.rule_name" /></el-form-item>
        <el-form-item label="归一化空白"><el-switch v-model="ruleForm.normalize_whitespace" /></el-form-item>
        <el-form-item label="移除空行"><el-switch v-model="ruleForm.remove_empty_lines" /></el-form-item>
        <el-form-item label="去重行"><el-switch v-model="ruleForm.dedupe_lines" /></el-form-item>
        <el-form-item label="最小长度"><el-input v-model.number="ruleForm.min_length" type="number" placeholder="0" /></el-form-item>
        <el-form-item label="空内容填充"><el-input v-model="ruleForm.fill_text" placeholder="暂无有效内容" /></el-form-item>
        <el-form-item label="无效关键词(逗号分隔)"><el-input v-model="ruleForm.drop_if_contains" placeholder="广告,免责声明" /></el-form-item>
        <el-form-item label="替换映射(JSON)"><el-input v-model="ruleForm.replace_map" type="textarea" :rows="3" placeholder='{"\u00a0":" "}' /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRule = false">取消</el-button>
        <el-button type="primary" @click="createRule">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showResult" title="采集结果" width="860px">
      <div v-if="resultDetail">
        <div style="font-weight: 700; margin-bottom: 8px;">{{ resultDetail.title || '未命名' }}</div>
        <div class="muted" style="margin-bottom: 12px;">{{ resultDetail.source_url }}</div>
        <el-tabs>
          <el-tab-pane label="清洗后">
            <pre style="white-space: pre-wrap; padding: 16px; border-radius: 16px; background: rgba(15, 23, 42, 0.05);">
{{ resultDetail.cleaned_markdown || '暂无清洗结果' }}
            </pre>
          </el-tab-pane>
          <el-tab-pane label="清洗前">
            <pre style="white-space: pre-wrap; padding: 16px; border-radius: 16px; background: rgba(15, 23, 42, 0.05);">
{{ resultDetail.markdown_content || '暂无原始内容' }}
            </pre>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { crawlerApi } from '../api'

const tasks = ref([])
const rules = ref([])
const results = ref([])
const showTask = ref(false)
const showRule = ref(false)
const showResult = ref(false)
const activeTask = ref(null)
const selectedRuleId = ref(null)
const resultDetail = ref(null)
let pollTimer = null

const taskForm = reactive({
  task_name: '',
  source_url: '',
  schedule_cron: '',
  request_method: 'GET',
  request_headers: '',
  request_body: '',
  parse_type: 'css',
  selector: 'body',
  title_selector: 'title',
  output_mode: 'markdown',
  use_browser: false,
})

const ruleForm = reactive({
  rule_name: '',
  normalize_whitespace: true,
  remove_empty_lines: true,
  dedupe_lines: false,
  min_length: 0,
  fill_text: '',
  drop_if_contains: '',
  replace_map: '',
})

const runningCount = computed(() => tasks.value.filter((task) => Number(task.status) === 1).length)

async function load() {
  const [t, r] = await Promise.all([crawlerApi.tasks(), crawlerApi.rules()])
  if (t.code === 0) tasks.value = t.data || []
  if (r.code === 0) rules.value = r.data || []
}

async function createTask() {
  let headers = {}
  if (taskForm.request_headers.trim()) {
    try {
      headers = JSON.parse(taskForm.request_headers)
    } catch (err) {
      ElMessage.error('请求头不是有效 JSON')
      return
    }
  }

  const parse_config = {
    request: {
      method: taskForm.request_method,
      headers,
      body: taskForm.request_body || null,
    },
    parse: {
      type: taskForm.parse_type,
      selector: taskForm.selector,
      title_selector: taskForm.title_selector,
    },
    output: {
      mode: taskForm.output_mode,
    },
    runtime: {
      use_browser: taskForm.use_browser,
    },
  }

  await crawlerApi.createTask({
    task_name: taskForm.task_name,
    source_url: taskForm.source_url,
    schedule_cron: taskForm.schedule_cron,
    parse_config,
  })
  ElMessage.success('已创建')
  showTask.value = false
  load()
}

async function createRule() {
  let replaceMap = {}
  if (ruleForm.replace_map.trim()) {
    try {
      replaceMap = JSON.parse(ruleForm.replace_map)
    } catch (err) {
      ElMessage.error('替换映射不是有效 JSON')
      return
    }
  }

  const rule_dag = {
    normalize_whitespace: ruleForm.normalize_whitespace,
    remove_empty_lines: ruleForm.remove_empty_lines,
    dedupe_lines: ruleForm.dedupe_lines,
    min_length: Number(ruleForm.min_length || 0),
    fill_text: ruleForm.fill_text || '',
    drop_if_contains: ruleForm.drop_if_contains
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean),
    replace_map: replaceMap,
  }
  await crawlerApi.createRule({ rule_name: ruleForm.rule_name, rule_dag })
  ElMessage.success('已创建清洗规则')
  showRule.value = false
  load()
}

async function runTask(task) {
  const payload = selectedRuleId.value ? { rule_id: selectedRuleId.value } : {}
  task.status = 1
  const res = await crawlerApi.runTask(task.id, payload)
  if (res.code === 0) {
    ElMessage.success('任务已执行')
    await loadResults(task)
    startPolling()
  } else {
    ElMessage.error(res.message || '任务执行失败')
  }
  load()
}

async function applyCleaning(task) {
  if (!selectedRuleId.value) {
    ElMessage.warning('请选择清洗规则')
    return
  }
  const res = await crawlerApi.applyRuleToTask(task.id, { rule_id: selectedRuleId.value })
  if (res.code === 0) {
    ElMessage.success('已应用清洗规则')
    await loadResults(task)
  }
}

async function loadResults(task) {
  activeTask.value = task
  const res = await crawlerApi.taskResults(task.id)
  if (res.code === 0) results.value = res.data || []
}

async function openResult(row) {
  const res = await crawlerApi.resultDetail(row.id)
  if (res.code === 0) {
    resultDetail.value = res.data
    showResult.value = true
  }
}

function statusText(status) {
  const value = Number(status)
  if (value === 1) return '运行中'
  if (value === 2) return '成功'
  if (value === 3) return '失败'
  if (value === 4) return '已停止'
  return '待运行'
}

function progressPercent(status) {
  const value = Number(status)
  if (value === 1) return 60
  if (value === 2) return 100
  if (value === 3) return 100
  return 0
}

function progressStatus(status) {
  const value = Number(status)
  if (value === 3) return 'exception'
  if (value === 2) return 'success'
  if (value === 4) return 'warning'
  return ''
}

function cleanStatusText(status) {
  const value = Number(status)
  if (value === 1) return '已清洗'
  if (value === 2) return '无效'
  return '未清洗'
}

async function stopTask(task) {
  const res = await crawlerApi.stopTask(task.id)
  if (res.code === 0) {
    ElMessage.success('任务已停止')
    load()
  }
}

async function deleteTask(task) {
  const confirmed = window.confirm(`确认删除任务「${task.task_name}」？该任务的采集结果也会一并删除。`)
  if (!confirmed) return
  const res = await crawlerApi.deleteTask(task.id)
  if (res.code === 0) {
    ElMessage.success('任务已删除')
    if (activeTask.value?.id === task.id) {
      activeTask.value = null
      results.value = []
    }
    load()
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    await load()
    if (runningCount.value === 0) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }, 4000)
}

onMounted(load)
</script>
