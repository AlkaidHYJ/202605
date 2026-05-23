<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">数字员工</div>
          <h1 class="hero-title" style="margin-top: 8px;">配置可复用的 AI 员工模板</h1>
        </div>
        <el-button type="primary" @click="openCreate">新建员工</el-button>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">支持选择模型、绑定技能、生成提示词，快速上线数字员工。</p>
    </section>

    <div class="glass-card" style="padding: 20px;">
      <div class="toolbar" style="margin-bottom: 12px;">
        <el-input v-model="keyword" placeholder="搜索员工名称" style="max-width: 220px;" @keyup.enter="load" />
        <el-button type="primary" @click="load">搜索</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
      <el-table :data="agents" border style="width: 100%;">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="agent_name" label="员工名称" />
        <el-table-column label="模型" width="180">
          <template #default="{ row }">
            {{ modelLabel(row.model_id) }}
          </template>
        </el-table-column>
        <el-table-column label="技能" min-width="240">
          <template #default="{ row }">
            <el-space wrap>
              <el-tag v-for="name in skillLabels(row.skill_ids)" :key="name" effect="light" round>
                {{ name }}
              </el-tag>
              <span v-if="!skillLabels(row.skill_ids).length" class="muted">未绑定</span>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" effect="light" round>{{ row.status === 1 ? '上线' : '测试' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" @click="openPrompt(row)">生成提示词</el-button>
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
      <el-form-item label="员工名称"><el-input v-model="form.agent_name" /></el-form-item>
      <el-form-item label="系统提示词">
        <el-input v-model="form.persona" type="textarea" rows="3" />
      </el-form-item>
      <el-form-item label="模型">
        <el-select v-model="form.model_id" style="width: 100%;" filterable clearable no-data-text="暂无可用模型，请先到模型管理新增">
          <el-option v-for="model in models" :key="model.id" :label="model.model_name" :value="model.model_id" />
        </el-select>
      </el-form-item>
      <el-form-item label="技能">
        <el-select v-model="form.skill_ids" multiple style="width: 100%;" filterable clearable no-data-text="暂无可用技能，请先到技能管理新增">
          <el-option v-for="skill in skills" :key="skill.id" :label="skill.skill_name" :value="skill.id" />
        </el-select>
      </el-form-item>
      <div class="member-hint">
        <span v-if="!models.length">模型列表为空，请先到模型管理新建模型。</span>
        <span v-if="!skills.length" :style="!models.length ? 'margin-left: 8px;' : ''">技能列表为空，请先到技能管理新建技能。</span>
      </div>
      <el-form-item label="状态">
        <el-select v-model="form.status" style="width: 100%;">
          <el-option :value="0" label="测试" />
          <el-option :value="1" label="上线" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showForm = false">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showPrompt" title="生成提示词" width="620px">
    <el-form :model="promptForm" label-position="top">
      <el-form-item label="已选技能">
        <el-select v-model="promptForm.skill_ids" multiple style="width: 100%;" filterable clearable no-data-text="暂无可用技能">
          <el-option v-for="skill in skills" :key="skill.id" :label="skill.skill_name" :value="skill.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="基础提示词"><el-input v-model="promptForm.base_prompt" type="textarea" rows="3" /></el-form-item>
      <el-form-item v-if="promptText" label="生成结果">
        <el-input :model-value="promptText" type="textarea" rows="4" readonly />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showPrompt = false">关闭</el-button>
      <el-button type="primary" @click="generatePrompt">生成</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api'

const agents = ref([])
const skills = ref([])
const models = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')

const showForm = ref(false)
const showPrompt = ref(false)
const promptText = ref('')
const form = reactive({ id: null, agent_name: '', persona: '', model_id: '', skill_ids: [], status: 0 })
const promptForm = reactive({ skill_ids: [], base_prompt: '' })

const formTitle = computed(() => (form.id ? '编辑员工' : '新建员工'))

async function load() {
  const res = await adminApi.agents({
    keyword: keyword.value || undefined,
    page: page.value,
    page_size: pageSize.value,
  })
  if (res.code === 0) {
    agents.value = res.data.items || []
    total.value = res.data.total || 0
  }
}

async function loadSkills() {
  const res = await adminApi.skills({ page: 1, page_size: 100 })
  if (res.code === 0) skills.value = res.data.items || []
}

async function loadModels() {
  const res = await adminApi.models({ page: 1, page_size: 100 })
  if (res.code === 0) models.value = res.data.items || []
}

function reset() {
  keyword.value = ''
  page.value = 1
  load()
}

async function openCreate() {
  await Promise.all([loadModels(), loadSkills()])
  Object.assign(form, { id: null, agent_name: '', persona: '', model_id: '', skill_ids: [], status: 0 })
  showForm.value = true
}

async function openEdit(row) {
  await Promise.all([loadModels(), loadSkills()])
  Object.assign(form, {
    id: row.id,
    agent_name: row.agent_name,
    persona: row.persona || '',
    model_id: row.model_id || '',
    skill_ids: parseSkillIds(row.skill_ids),
    status: row.status ?? 0,
  })
  showForm.value = true
}

async function save() {
  if (!form.model_id) {
    ElMessage.warning('请选择模型')
    return
  }
  const payload = {
    agent_name: form.agent_name,
    persona: form.persona,
    model_id: form.model_id || null,
    skill_ids: form.skill_ids,
    status: form.status,
  }
  if (form.id) {
    await adminApi.updateAgent(form.id, payload)
    ElMessage.success('员工已更新')
  } else {
    await adminApi.createAgent(payload)
    ElMessage.success('员工已创建')
  }
  showForm.value = false
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除员工 ${row.agent_name}？`)
  await adminApi.deleteAgent(row.id)
  ElMessage.success('已删除')
  load()
}

function openPrompt(row) {
  promptForm.skill_ids = parseSkillIds(row.skill_ids)
  promptForm.base_prompt = row.persona || ''
  promptText.value = ''
  showPrompt.value = true
}

function parseSkillIds(raw) {
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  try {
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

function modelLabel(modelId) {
  const match = models.value.find((model) => model.model_id === modelId)
  return match ? `${match.model_name} (${modelId})` : (modelId || '-')
}

function skillLabels(rawSkillIds) {
  const ids = parseSkillIds(rawSkillIds)
  const nameMap = new Map(skills.value.map((item) => [item.id, item.skill_name]))
  return ids.map((id) => nameMap.get(id) || `技能${id}`)
}

async function generatePrompt() {
  const res = await adminApi.generateAgentPrompt({
    skill_ids: promptForm.skill_ids,
    base_prompt: promptForm.base_prompt || null,
  })
  if (res.code === 0) promptText.value = res.data.prompt || ''
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
  loadSkills()
  loadModels()
})
</script>

<style scoped>
.member-hint {
  margin-top: 8px;
  color: var(--muted);
  font-size: 12px;
}
</style>
