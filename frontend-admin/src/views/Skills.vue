<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">技能中心</div>
          <h1 class="hero-title" style="margin-top: 8px;">管理模型调用的技能与函数</h1>
        </div>
        <div style="display:flex; gap: 10px; flex-wrap: wrap;">
          <el-button @click="showTemplateGuide = !showTemplateGuide">模板说明</el-button>
          <el-button type="primary" @click="openCreate">新建技能</el-button>
        </div>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">支持 function / skill 两种类型，自动生成技能说明与参数结构。</p>
      <div v-if="showTemplateGuide" class="template-guide">
        <div class="template-guide-title">新建技能时建议填写什么</div>
        <div class="template-guide-grid">
          <div class="instruction-box">
            <div class="metric-label">描述</div>
            <div style="margin-top: 8px; line-height: 1.8;">写清楚这个技能在什么场景下使用、能解决什么问题、返回什么内容。</div>
          </div>
          <div class="instruction-box">
            <div class="metric-label">schema_json</div>
            <div style="margin-top: 8px; line-height: 1.8;">写成 JSON，对应 runtime（如何请求）、input_schema（参数）、response（如何判断成功和提取结果）。</div>
          </div>
        </div>
        <div class="template-quick-actions">
          <el-button size="small" @click="applyTemplate('today')">历史上的今天</el-button>
          <el-button size="small" @click="applyTemplate('kfc')">KFC 文案</el-button>
          <el-button size="small" @click="applyTemplate('generic_get')">通用 GET 模板</el-button>
        </div>
      </div>
    </section>

    <div class="glass-card" style="padding: 20px;">
      <div class="toolbar" style="margin-bottom: 12px;">
        <el-input v-model="keyword" placeholder="搜索技能名称" style="max-width: 220px;" @keyup.enter="load" />
        <el-select v-model="skillType" placeholder="类型" style="max-width: 180px;">
          <el-option label="全部" :value="null" />
          <el-option label="function" :value="1" />
          <el-option label="skill" :value="2" />
        </el-select>
        <el-button type="primary" @click="load">搜索</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
      <el-table :data="skills" border style="width: 100%;">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="skill_name" label="技能名称" />
        <el-table-column prop="skill_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.skill_type === 1 ? 'success' : 'info'" effect="light" round>
              {{ row.skill_type === 1 ? 'function' : 'skill' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_id" label="模型 ID" width="120" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'warning'" effect="light" round>{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="290">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" @click="openRun(row)">运行调试</el-button>
            <el-button size="small" @click="openAutoGenerate(row)">自动生成</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display: flex; justify-content: flex-end; margin-top: 12px;">
        <el-pagination
          background
          layout="prev, pager, next, sizes, total"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="onPageChange"
          @size-change="onSizeChange"
        />
      </div>
    </div>
  </div>

  <el-dialog v-model="showForm" :title="formTitle" width="620px">
    <el-form :model="form" label-position="top">
      <el-form-item label="快速模板">
        <el-select v-model="selectedTemplate" placeholder="选择一个模板自动填充" style="width: 100%;" @change="applyTemplate">
          <el-option label="不使用模板" value="" />
          <el-option label="历史上的今天" value="today" />
          <el-option label="KFC 文案" value="kfc" />
          <el-option label="通用 GET 模板" value="generic_get" />
        </el-select>
      </el-form-item>
      <el-form-item label="技能名称"><el-input v-model="form.skill_name" /></el-form-item>
      <el-form-item label="技能类型">
        <el-select v-model="form.skill_type" style="width: 100%;">
          <el-option :value="1" label="function" />
          <el-option :value="2" label="skill" />
        </el-select>
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" rows="3" placeholder="写清楚什么时候会用到这个技能，输出给谁看" />
      </el-form-item>
      <el-form-item label="schema_json">
        <el-input v-model="form.schema_json" type="textarea" rows="10" placeholder='可直接粘贴模板 JSON，例如：{"runtime": {...}}' />
      </el-form-item>
      <el-form-item label="模型 ID"><el-input v-model="form.model_id" /></el-form-item>
      <el-form-item label="状态">
        <el-select v-model="form.status" style="width: 100%;">
          <el-option :value="1" label="启用" />
          <el-option :value="0" label="禁用" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showForm = false">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showAuto" title="自动生成技能" width="620px">
    <el-form :model="autoForm" label-position="top">
      <el-form-item label="模型">
        <el-select v-model="autoForm.model_id" style="width: 100%;">
          <el-option v-for="model in models" :key="model.id" :label="model.model_name" :value="model.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="技能名称"><el-input v-model="autoForm.skill_name" /></el-form-item>
      <el-form-item label="技能类型">
        <el-select v-model="autoForm.skill_type" style="width: 100%;">
          <el-option :value="1" label="function" />
          <el-option :value="2" label="skill" />
        </el-select>
      </el-form-item>
      <el-form-item label="补充说明"><el-input v-model="autoForm.description_hint" type="textarea" rows="3" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAuto = false">取消</el-button>
      <el-button type="primary" @click="autoGenerate">生成</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showRun" title="运行技能调试" width="680px">
    <el-form label-position="top">
      <el-form-item label="技能名称">
        <el-input :model-value="runForm.skill_name" disabled />
      </el-form-item>
      <el-form-item label="参数 JSON">
        <el-input v-model="runForm.argsJson" type="textarea" rows="6" placeholder='例如: {"type":"json"}' />
      </el-form-item>
      <el-form-item v-if="runResult" label="执行结果">
        <el-input :model-value="runResult" type="textarea" rows="10" readonly />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showRun = false">关闭</el-button>
      <el-button type="primary" @click="runSkillTest">运行</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api'

const skills = ref([])
const models = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const skillType = ref(null)

const showForm = ref(false)
const showAuto = ref(false)
const showRun = ref(false)
const showTemplateGuide = ref(false)
const runResult = ref('')
const selectedTemplate = ref('')
const form = reactive({
  id: null,
  skill_name: '',
  skill_type: 1,
  description: '',
  schema_json: '',
  model_id: '',
  status: 1,
})
const autoForm = reactive({ model_id: null, skill_name: '', skill_type: 1, description_hint: '' })
const runForm = reactive({ skill_id: null, skill_name: '', argsJson: '{}' })

const templateCatalog = {
  today: {
    skill_name: 'get_today_in_history',
    description: '查询历史上的今天事件，适合日常知识问答和内容生成场景。',
    schema_json: {
      runtime: {
        provider: 'http',
        method: 'GET',
        url: 'https://api.52vmy.cn/api/wl/today',
        query_template: {
          type: '{type}',
        },
        timeout_seconds: 10,
      },
      input_schema: {
        type: 'object',
        properties: {
          type: {
            type: 'string',
            enum: ['json', 'text'],
            default: 'json',
            description: '返回格式，默认 json',
          },
        },
        required: [],
      },
      response: {
        success_code_path: 'code',
        success_code_equals: 200,
        data_path: 'data',
      },
    },
  },
  kfc: {
    skill_name: 'get_kfc_copywriting',
    description: '获取 KFC 风格文案，适合营销、社交内容和创意生成场景。',
    schema_json: {
      runtime: {
        provider: 'http',
        method: 'GET',
        url: 'https://api.52vmy.cn/api/wl/yan/kfc',
        timeout_seconds: 10,
      },
      input_schema: {
        type: 'object',
        properties: {},
        required: [],
      },
      response: {
        success_code_path: 'code',
        success_code_equals: 200,
        data_path: 'content',
      },
    },
  },
  generic_get: {
    skill_name: 'http_get_skill',
    description: '通用 GET 技能模板，适合快速接入公开 API。',
    schema_json: {
      runtime: {
        provider: 'http',
        method: 'GET',
        url: 'https://your-api.example.com/path',
        query_template: {
          your_param: '{your_param}',
        },
        timeout_seconds: 10,
      },
      input_schema: {
        type: 'object',
        properties: {
          your_param: {
            type: 'string',
            description: '请求参数，请按接口文档填写',
          },
        },
        required: [],
      },
      response: {
        success_code_path: 'code',
        success_code_equals: 200,
        data_path: 'data',
      },
    },
  },
}

function templateSummary(templateKey) {
  const template = templateCatalog[templateKey]
  if (!template) return ''
  return `${template.skill_name} · ${template.description}`
}

const formTitle = computed(() => (form.id ? '编辑技能' : '新建技能'))

async function load() {
  const res = await adminApi.skills({
    keyword: keyword.value || undefined,
    skill_type: skillType.value ?? undefined,
    page: page.value,
    page_size: pageSize.value,
  })
  if (res.code === 0) {
    skills.value = res.data.items || []
    total.value = res.data.total || 0
  }
}

async function loadModels() {
  const res = await adminApi.models({ page: 1, page_size: 200 })
  if (res.code === 0) models.value = res.data.items || []
}

function reset() {
  keyword.value = ''
  skillType.value = null
  page.value = 1
  load()
}

function openCreate() {
  Object.assign(form, {
    id: null,
    skill_name: '',
    skill_type: 1,
    description: '',
    schema_json: '',
    model_id: '',
    status: 1,
  })
  selectedTemplate.value = ''
  showForm.value = true
}

function applyTemplate(templateKey) {
  if (!templateKey) return
  const template = templateCatalog[templateKey]
  if (!template) return
  selectedTemplate.value = templateKey
  form.skill_name = template.skill_name
  form.description = template.description
  form.schema_json = JSON.stringify(template.schema_json, null, 2)
  form.skill_type = 1
  form.status = 1
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id,
    skill_name: row.skill_name,
    skill_type: row.skill_type,
    description: row.description || '',
    schema_json: row.schema_json || '',
    model_id: row.model_id || '',
    status: row.status,
  })
  selectedTemplate.value = ''
  showForm.value = true
}

async function save() {
  const payload = {
    skill_name: form.skill_name,
    skill_type: form.skill_type,
    description: form.description,
    schema_json: form.schema_json,
    model_id: form.model_id || null,
    status: form.status,
  }
  if (form.id) {
    await adminApi.updateSkill(form.id, payload)
    ElMessage.success('技能已更新')
  } else {
    await adminApi.createSkill(payload)
    ElMessage.success('技能已创建')
  }
  showForm.value = false
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除技能 ${row.skill_name}？`)
  await adminApi.deleteSkill(row.id)
  ElMessage.success('已删除')
  load()
}

function openAutoGenerate(row) {
  Object.assign(autoForm, {
    model_id: models.value[0]?.id || null,
    skill_name: row?.skill_name || form.skill_name || '',
    skill_type: row?.skill_type || form.skill_type || 1,
    description_hint: '',
  })
  showAuto.value = true
}

async function autoGenerate() {
  const res = await adminApi.autoGenerateSkill({
    model_id: autoForm.model_id,
    skill_name: autoForm.skill_name,
    skill_type: autoForm.skill_type,
    description_hint: autoForm.description_hint || null,
  })
  if (res.code === 0) {
    form.description = res.data.description || ''
    form.schema_json = res.data.schema_json || ''
    form.skill_name = autoForm.skill_name
    form.skill_type = autoForm.skill_type
    showAuto.value = false
    showForm.value = true
    ElMessage.success('已生成技能描述')
  }
}

function openRun(row) {
  runForm.skill_id = row.id
  runForm.skill_name = row.skill_name
  runForm.argsJson = '{}'
  runResult.value = ''
  showRun.value = true
}

async function runSkillTest() {
  let args = {}
  try {
    args = JSON.parse(runForm.argsJson || '{}')
  } catch {
    ElMessage.error('参数 JSON 格式错误')
    return
  }
  try {
    const res = await adminApi.runSkill(runForm.skill_id, { args })
    runResult.value = JSON.stringify(res.data || {}, null, 2)
    ElMessage.success('执行完成')
  } catch (err) {
    const msg = err?.response?.data?.detail || err?.message || '执行失败'
    ElMessage.error(msg)
  }
}

function onPageChange(val) {
  page.value = val
  load()
}

function onSizeChange(val) {
  pageSize.value = val
  page.value = 1
  load()
}

onMounted(() => {
  load()
  loadModels()
})
</script>

<style scoped>
.template-guide {
  margin-top: 16px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.template-guide-title {
  font-size: 14px;
  font-weight: 800;
  margin-bottom: 12px;
}

.template-guide-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.template-quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.template-helper {
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
}

@media (max-width: 900px) {
  .template-guide-grid {
    grid-template-columns: 1fr;
  }
}
</style>
