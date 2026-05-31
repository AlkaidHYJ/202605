<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">技能中心</div>
          <h1 class="hero-title" style="margin-top: 8px;">管理模型调用的技能、函数和技能包</h1>
        </div>
        <div style="display:flex; gap: 10px; flex-wrap: wrap;">
          <el-button @click="showTemplateGuide = !showTemplateGuide">模板说明</el-button>
          <el-button @click="openAiCreate">AI创建技能</el-button>
          <el-button type="primary" @click="openCreate">新建技能</el-button>
        </div>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">function 类型支持参数定义与 Python 沙箱代码；skill 类型支持上传或粘贴 SKILL.md 内容。</p>
      <div v-if="showTemplateGuide" class="template-guide">
        <div class="template-guide-title">新建技能时建议填写什么</div>
        <div class="template-guide-grid">
          <div class="instruction-box">
            <div class="metric-label">描述</div>
            <div style="margin-top: 8px; line-height: 1.8;">写清楚这个技能在什么场景下使用、能解决什么问题、返回什么内容。</div>
          </div>
          <div class="instruction-box">
            <div class="metric-label">function 类型</div>
            <div style="margin-top: 8px; line-height: 1.8;">填写参数定义 JSON，再提供可在沙箱中执行的 Python 代码，代码里建议定义 main(args)。</div>
          </div>
          <div class="instruction-box">
            <div class="metric-label">skill 类型</div>
            <div style="margin-top: 8px; line-height: 1.8;">可以直接上传 SKILL.md，或把 SKILL.md 内容粘贴到表单里，后端会保存为可执行技能包。</div>
          </div>
          <div class="instruction-box">
            <div class="metric-label">AI 创建</div>
            <div style="margin-top: 8px; line-height: 1.8;">选择模型和技能分类，输入你的要求，生成后会自动回填到手动创建表单。</div>
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

      <div class="skill-card-grid" v-if="skills.length">
        <article v-for="row in skills" :key="row.id" class="skill-card">
          <div class="skill-card-header">
            <div>
              <div class="skill-card-title">{{ row.skill_name }}</div>
              <div class="skill-card-subtitle">ID {{ row.id }} · {{ skillModelLabel(row) }}</div>
            </div>
            <el-tag :type="row.skill_type === 1 ? 'success' : 'info'" effect="light" round>
              {{ skillTypeLabel(row.skill_type) }}
            </el-tag>
          </div>
          <p class="skill-card-description">{{ row.description || '暂无描述，请补充该技能的使用场景和输出内容。' }}</p>
          <div class="skill-card-meta-row">
            <el-tag size="small" effect="plain">{{ skillConfigSummary(row) }}</el-tag>
            <el-tag size="small" effect="plain">{{ skillStatusLabel(row.status) }}</el-tag>
          </div>
          <div class="skill-card-footer">
            <div class="skill-card-hint">{{ skillConfigPreview(row) }}</div>
            <div class="skill-card-actions">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" @click="openRun(row)">运行调试</el-button>
              <el-button size="small" @click="openAutoGenerate(row)">自动生成</el-button>
              <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
            </div>
          </div>
        </article>
      </div>

      <el-empty v-if="!skills.length" description="暂无技能，请先创建 function 或 skill 技能" />

      <el-table v-if="skills.length" :data="skills" border style="width: 100%;">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="skill_name" label="技能名称" />
        <el-table-column prop="skill_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.skill_type === 1 ? 'success' : 'info'" effect="light" round>
              {{ skillTypeLabel(row.skill_type) }}
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

  <input ref="skillFileInput" type="file" accept=".md,.txt" style="display:none;" @change="onSkillFileChange" />

  <el-dialog v-model="showForm" :title="formTitle" width="760px">
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
        <el-select v-model="form.skill_type" style="width: 100%;" @change="onFormSkillTypeChange">
          <el-option :value="1" label="function" />
          <el-option :value="2" label="skill" />
        </el-select>
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" rows="3" placeholder="写清楚什么时候会用到这个技能，输出给谁看" />
      </el-form-item>
      <template v-if="form.skill_type === 1">
        <el-form-item label="参数定义 JSON">
          <el-input v-model="form.schema_json" type="textarea" rows="10" placeholder='例如：{"type":"object","properties":{"keyword":{"type":"string"}},"required":["keyword"]}' />
        </el-form-item>
        <el-form-item label="自定义 Python 代码">
          <el-input v-model="form.function_code" type="textarea" rows="14" placeholder='def main(args):\n    return {"ok": True}' />
        </el-form-item>
        <div class="template-helper">沙箱默认允许常用标准库与 httpx；建议定义 main(args)，并返回 dict、list、str、数字或布尔值。</div>
      </template>
      <template v-else>
        <el-form-item label="SKILL.md 内容">
          <el-input v-model="form.skill_md" type="textarea" rows="16" placeholder="# SKILL.md\n\n## Goal\n..." />
        </el-form-item>
        <div style="display:flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 12px;">
          <el-button @click="pickSkillFile">上传 SKILL.md</el-button>
          <span class="template-helper" style="margin-top: 0;">已选择：{{ form.skill_package_name || '未上传文件' }}</span>
        </div>
      </template>
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

  <el-dialog v-model="showAuto" title="AI 创建技能" width="720px">
    <el-form :model="autoForm" label-position="top">
      <el-form-item label="模型">
        <el-select v-model="autoForm.model_id" style="width: 100%;" filterable no-data-text="暂无可用模型，请先到模型管理新增">
          <el-option v-for="model in models" :key="model.id" :label="model.model_name" :value="model.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="技能名称"><el-input v-model="autoForm.skill_name" /></el-form-item>
      <el-form-item label="技能分类">
        <el-select v-model="autoForm.skill_type" style="width: 100%;" @change="onAutoSkillTypeChange">
          <el-option :value="1" label="function" />
          <el-option :value="2" label="skill" />
        </el-select>
      </el-form-item>
      <el-form-item label="你的要求">
        <el-input v-model="autoForm.description_hint" type="textarea" rows="5" placeholder="例如：做一个可以根据关键词查询公开接口并返回结果的函数技能" />
      </el-form-item>
      <div v-if="generating" style="margin-bottom: 12px;">
        <el-progress :percentage="generationProgress" :status="generationProgress >= 100 ? 'success' : undefined" />
        <div class="template-helper" style="margin-top: 8px;">{{ generationText }}</div>
      </div>
    </el-form>
    <template #footer>
      <el-button @click="showAuto = false" :disabled="generating">取消</el-button>
      <el-button type="primary" :loading="generating" @click="autoGenerate">生成</el-button>
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
const generating = ref(false)
const generationProgress = ref(0)
const generationText = ref('正在请求模型生成技能内容...')
const runResult = ref('')
const selectedTemplate = ref('')
const skillFileInput = ref(null)
let generationTimer = null

const form = reactive({
  id: null,
  skill_name: '',
  skill_type: 1,
  description: '',
  schema_json: '',
  function_code: '',
  skill_md: '',
  skill_package_name: '',
  model_id: '',
  status: 1,
})
const autoForm = reactive({ model_id: null, skill_name: '', skill_type: 1, description_hint: '' })
const runForm = reactive({ skill_id: null, skill_name: '', argsJson: '{}' })

const templateCatalog = {
  today: {
    skill_name: 'get_today_in_history',
    description: '查询历史上的今天事件，适合日常知识问答和内容生成场景。',
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
    function_code: `import httpx


def main(args):
    value = args.get('type', 'json')
    with httpx.Client(timeout=10) as client:
        resp = client.get('https://api.52vmy.cn/api/wl/today', params={'type': value})
        resp.raise_for_status()
        return resp.json()
`,
    skill_md: `# 历史上的今天\n\n## 目标\n查询历史上的今天事件。\n\n## 输入\n- type: 返回格式，支持 json 或 text。\n\n## 输出\n返回适合用户阅读的事件列表。\n`,
  },
  weather: {
    skill_name: 'get_weather_forecast',
    description: '查询天气预报，适合日程提醒、出行建议和客服问答场景。',
    input_schema: {
      type: 'object',
      properties: {
        city: {
          type: 'string',
          description: '城市名称，例如 北京、上海、深圳',
        },
      },
      required: ['city'],
    },
    function_code: `import httpx


def main(args):
    city = args.get('city')
    if not city:
        raise ValueError('city is required')
    with httpx.Client(timeout=10) as client:
        resp = client.get('https://api.52vmy.cn/api/wl/weather', params={'city': city})
        resp.raise_for_status()
        return resp.json()
`,
    skill_md: `# 天气预报\n\n## 目标\n查询指定城市的天气情况。\n\n## 输入\n- city: 城市名称。\n\n## 输出\n返回天气描述、温度和预报信息。\n`,
  },
  kfc: {
    skill_name: 'get_kfc_copywriting',
    description: '获取 KFC 风格文案，适合营销、社交内容和创意生成场景。',
    input_schema: {
      type: 'object',
      properties: {},
      required: [],
    },
    function_code: `import httpx


def main(args):
    with httpx.Client(timeout=10) as client:
        resp = client.get('https://api.52vmy.cn/api/wl/yan/kfc')
        resp.raise_for_status()
        return resp.json()
`,
    skill_md: `# KFC 文案\n\n## 目标\n生成 KFC 风格文案。\n\n## 输入\n- 无\n\n## 输出\n返回一段可直接使用的文案。\n`,
  },
  generic_get: {
    skill_name: 'http_get_skill',
    description: '通用 GET 技能模板，适合快速接入公开 API。',
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
    function_code: `import httpx


def main(args):
    params = {'your_param': args.get('your_param')}
    with httpx.Client(timeout=10) as client:
        resp = client.get('https://your-api.example.com/path', params=params)
        resp.raise_for_status()
        return resp.json()
`,
    skill_md: `# 通用 GET 技能模板\n\n## 目标\n快速接入一个公开 API。\n\n## 输入\n- your_param: 请按接口文档填写。\n\n## 输出\n返回接口响应结果。\n`,
  },
}

const formTitle = computed(() => (form.id ? '编辑技能' : '新建技能'))

function cloneTemplateText(text) {
  return typeof text === 'string' ? text : JSON.stringify(text, null, 2)
}

function parseJsonOrNull(text) {
  if (!text || !text.trim()) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

function normalizeSchemaText(row, config) {
  if (config && typeof config.input_schema !== 'undefined') {
    return cloneTemplateText(config.input_schema)
  }
  if (config && typeof config.parameters !== 'undefined') {
    return cloneTemplateText(config.parameters)
  }
  if (config && typeof config.runtime !== 'undefined') {
    return cloneTemplateText(config.runtime)
  }
  if (typeof row.schema_json === 'string' && row.schema_json.trim()) {
    return row.schema_json
  }
  return ''
}

function normalizeSkillConfig(raw) {
  const parsed = parseJsonOrNull(raw)
  return parsed && typeof parsed === 'object' ? parsed : {}
}

function skillTypeLabel(type) {
  return Number(type) === 1 ? 'function' : 'skill'
}

function skillStatusLabel(status) {
  return Number(status) === 1 ? '启用' : '禁用'
}

function skillModelLabel(row) {
  return row?.model_id ? `模型 ${row.model_id}` : '未绑定模型'
}

function skillConfigSummary(row) {
  const config = normalizeSkillConfig(row?.schema_json)
  if (Number(row?.skill_type) === 1) {
    const schema = config.input_schema || config.parameters || config.runtime
    if (!schema || typeof schema !== 'object') {
      return 'function · 未配置参数'
    }
    const keys = Object.keys(schema.properties || {})
    return keys.length ? `function · 参数 ${keys.join(', ')}` : 'function · 参数已配置'
  }
  return config.skill_package_name ? `skill · ${config.skill_package_name}` : 'skill · SKILL.md'
}

function skillConfigPreview(row) {
  const config = normalizeSkillConfig(row?.schema_json)
  if (Number(row?.skill_type) === 1) {
    const code = config.function_code || ''
    if (!code.trim()) {
      return '请补充 Python 沙箱代码，建议定义 main(args)。'
    }
    return code.trim().split('\n').slice(0, 2).join(' · ')
  }
  const skillMd = config.skill_md || config.skill_package_content || ''
  if (!skillMd.trim()) {
    return '请补充 SKILL.md 内容或上传技能包。'
  }
  return skillMd.trim().split('\n').find((line) => line.trim()) || 'SKILL.md 内容已配置'
}

function resetTypeSpecificFields(type) {
  if (Number(type) === 1) {
    form.skill_md = ''
    form.skill_package_name = ''
  } else {
    form.schema_json = ''
    form.function_code = ''
  }
}

function onFormSkillTypeChange(type) {
  selectedTemplate.value = ''
  resetTypeSpecificFields(type)
}

function onAutoSkillTypeChange(type) {
  if (Number(type) === 1) {
    autoForm.description_hint = autoForm.description_hint || '请生成一个 function call 技能，包含参数定义和可直接在沙箱执行的 Python 代码。'
  } else {
    autoForm.description_hint = autoForm.description_hint || '请生成一个 skill 技能，输出完整的 SKILL.md 内容。'
  }
}

function applySkillDraft(draft) {
  const skillType = Number(draft.skill_type) === 2 ? 2 : 1
  Object.assign(form, {
    id: null,
    skill_name: draft.skill_name || '',
    skill_type: skillType,
    description: draft.description || '',
    schema_json: skillType === 1 ? (draft.schema_json || '{}') : '',
    function_code: skillType === 1 ? (draft.function_code || '') : '',
    skill_md: skillType === 2 ? (draft.skill_md || '# SKILL.md\n\n## Goal\n') : '',
    skill_package_name: skillType === 2 ? (draft.skill_package_name || 'SKILL.md') : '',
    model_id: draft.model_id ?? '',
    status: draft.status ?? 1,
  })
  selectedTemplate.value = ''
  showForm.value = true
}

function startGenerationProgress() {
  stopGenerationProgress()
  generating.value = true
  generationProgress.value = 8
  generationText.value = '正在请求模型生成技能内容...'
  generationTimer = setInterval(() => {
    if (generationProgress.value < 90) {
      generationProgress.value += generationProgress.value < 40 ? 8 : 4
    }
  }, 220)
}

function stopGenerationProgress() {
  if (generationTimer) {
    clearInterval(generationTimer)
    generationTimer = null
  }
  generating.value = false
}

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
  const res = await adminApi.models({ page: 1, page_size: 100 })
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
    function_code: '',
    skill_md: '',
    skill_package_name: '',
    model_id: '',
    status: 1,
  })
  selectedTemplate.value = ''
  showForm.value = true
}

function openAiCreate() {
  loadModels().finally(() => {
    Object.assign(autoForm, {
      model_id: models.value[0]?.id || null,
      skill_name: '',
      skill_type: 1,
      description_hint: '',
    })
    onAutoSkillTypeChange(autoForm.skill_type)
    generationProgress.value = 0
    generationText.value = '正在请求模型生成技能内容...'
    showAuto.value = true
    if (!models.value.length) {
      ElMessage.warning('暂无可用模型，请先到模型管理新增后再进行 AI 创建')
    }
  })
}

function applyTemplate(templateKey) {
  if (!templateKey) return
  const template = templateCatalog[templateKey]
  if (!template) return
  selectedTemplate.value = templateKey
  form.skill_name = template.skill_name
  form.description = template.description
  form.status = 1
  if (form.skill_type === 2) {
    form.schema_json = ''
    form.function_code = ''
    form.skill_md = template.skill_md
    form.skill_package_name = 'SKILL.md'
  } else {
    form.schema_json = JSON.stringify(template.input_schema, null, 2)
    form.function_code = template.function_code
    form.skill_md = ''
    form.skill_package_name = ''
  }
}

function openEdit(row) {
  const config = normalizeSkillConfig(row.schema_json)
  Object.assign(form, {
    id: row.id,
    skill_name: row.skill_name,
    skill_type: row.skill_type,
    description: row.description || '',
    schema_json: row.skill_type === 1 ? normalizeSchemaText(row, config) : '',
    function_code: row.skill_type === 1 ? (config.function_code || '') : '',
    skill_md: row.skill_type === 2 ? (config.skill_md || config.skill_package_content || '') : '',
    skill_package_name: row.skill_type === 2 ? (config.skill_package_name || 'SKILL.md') : '',
    model_id: row.model_id || '',
    status: row.status,
  })
  selectedTemplate.value = ''
  showForm.value = true
}

async function save() {
  if (form.skill_type === 1) {
    const parsed = parseJsonOrNull(form.schema_json)
    if (!parsed) {
      ElMessage.warning('function 类型需要填写合法的参数定义 JSON')
      return
    }
    if (!form.function_code.trim()) {
      ElMessage.warning('function 类型需要填写 Python 代码')
      return
    }
  } else if (!form.skill_md.trim()) {
    ElMessage.warning('skill 类型需要填写 SKILL.md 内容或上传技能包')
    return
  }

  const payloadConfig = {
    description: form.description,
  }
  if (form.skill_type === 1) {
    const parsed = parseJsonOrNull(form.schema_json)
    if (form.id && !form.function_code.trim() && parsed && parsed.runtime && !parsed.input_schema) {
      Object.assign(payloadConfig, parsed)
    } else {
      payloadConfig.input_schema = parsed
      payloadConfig.function_code = form.function_code
    }
  } else {
    payloadConfig.skill_md = form.skill_md
    payloadConfig.skill_package_name = form.skill_package_name || 'SKILL.md'
  }

  const payload = {
    skill_name: form.skill_name,
    skill_type: form.skill_type,
    description: form.description,
    schema_json: JSON.stringify(payloadConfig, null, 2),
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
  onAutoSkillTypeChange(autoForm.skill_type)
  generationProgress.value = 0
  generationText.value = '正在请求模型生成技能内容...'
  showAuto.value = true
}

async function autoGenerate() {
  if (!autoForm.model_id) {
    ElMessage.warning('请选择模型')
    return
  }
  if (!autoForm.skill_name.trim()) {
    ElMessage.warning('请输入技能名称')
    return
  }

  startGenerationProgress()
  try {
    const res = await adminApi.autoGenerateSkill({
      model_id: autoForm.model_id,
      skill_name: autoForm.skill_name,
      skill_type: autoForm.skill_type,
      description_hint: autoForm.description_hint || null,
    })
    if (res.code === 0) {
      const data = res.data || {}
      generationProgress.value = 100
      generationText.value = '生成完成，正在打开手动创建界面...'
      await new Promise((resolve) => setTimeout(resolve, 250))
      stopGenerationProgress()
      showAuto.value = false
      const skillType = Number(autoForm.skill_type) === 2 ? 2 : 1
      applySkillDraft({
        skill_name: autoForm.skill_name,
        skill_type: skillType,
        description: data.description || '',
        schema_json: skillType === 1 ? (data.schema_json || data.schema_json_text || '{}') : '',
        function_code: skillType === 1 ? (data.function_code || 'def main(args):\n    return {"ok": True}') : '',
        skill_md: skillType === 2 ? (data.skill_md || '# SKILL.md\n\n## Goal\n') : '',
        skill_package_name: skillType === 2 ? 'SKILL.md' : '',
        model_id: autoForm.model_id,
        status: 1,
      })
      ElMessage.success('已生成技能草稿')
      return
    }
    throw new Error('生成失败')
  } catch (err) {
    const msg = err?.response?.data?.detail || err?.message || '生成失败'
    ElMessage.error(msg)
  } finally {
    stopGenerationProgress()
  }
}

function pickSkillFile() {
  skillFileInput.value?.click?.()
}

function onSkillFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    form.skill_md = String(reader.result || '')
    form.skill_package_name = file.name || 'SKILL.md'
    ElMessage.success('已读取 SKILL.md 内容')
  }
  reader.readAsText(file, 'utf-8')
  event.target.value = ''
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

.skill-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.skill-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.94));
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.skill-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.skill-card-title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.4;
}

.skill-card-subtitle {
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
}

.skill-card-description {
  margin: 12px 0 0;
  line-height: 1.8;
  color: rgba(15, 23, 42, 0.8);
}

.skill-card-meta-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.skill-card-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
}

.skill-card-hint {
  flex: 1;
  min-width: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
  overflow: hidden;
  line-clamp: 2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.skill-card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
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
