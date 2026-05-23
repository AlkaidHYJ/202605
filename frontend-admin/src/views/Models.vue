<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">模型中心</div>
          <h1 class="hero-title" style="margin-top: 8px;">统一管理与测试大模型能力</h1>
        </div>
        <el-button type="primary" @click="openCreate">新建模型</el-button>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">支持 OpenAI 兼容接口的模型配置、默认模型设置与对话测试。</p>
    </section>

    <div class="glass-card" style="padding: 20px;">
      <div class="toolbar" style="margin-bottom: 12px;">
        <el-input v-model="keyword" placeholder="搜索模型名称/ID" style="max-width: 260px;" @keyup.enter="load" />
        <el-button type="primary" @click="load">搜索</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
      <el-table :data="models" border style="width: 100%;">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="model_name" label="模型名称" />
        <el-table-column prop="model_type" label="类型" width="120" />
        <el-table-column prop="model_id" label="模型 ID" />
        <el-table-column prop="is_default" label="默认" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_default ? 'success' : 'info'" effect="light" round>{{ row.is_default ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'warning'" effect="light" round>{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" @click="openTest(row)">测试</el-button>
            <el-button size="small" @click="setDefault(row)">设为默认</el-button>
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

  <el-dialog v-model="showForm" :title="formTitle" width="560px">
    <el-form :model="form" label-position="top">
      <el-form-item label="模型名称"><el-input v-model="form.model_name" /></el-form-item>
      <el-form-item label="模型分类">
        <el-select v-model="form.model_type" style="width: 100%;">
          <el-option label="文本" value="text" />
          <el-option label="图片" value="image" />
          <el-option label="音频" value="audio" />
          <el-option label="视频" value="video" />
          <el-option label="embedding" value="embedding" />
          <el-option label="rerank" value="rerank" />
        </el-select>
      </el-form-item>
      <el-form-item label="Base URL"><el-input v-model="form.base_url" placeholder="https://api.openai.com" /></el-form-item>
      <el-form-item label="API Key"><el-input v-model="form.api_key" show-password /></el-form-item>
      <el-form-item label="模型 ID"><el-input v-model="form.model_id" placeholder="gpt-4o-mini" /></el-form-item>
      <el-form-item label="默认模型">
        <el-select v-model="form.is_default" style="width: 100%;">
          <el-option :value="0" label="否" />
          <el-option :value="1" label="是" />
        </el-select>
      </el-form-item>
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

  <el-dialog v-model="showTest" title="模型对话测试" width="560px">
    <el-form :model="testForm" label-position="top">
      <el-form-item label="测试输入">
        <el-input v-model="testForm.message" type="textarea" rows="4" placeholder="请输入测试内容" />
      </el-form-item>
      <el-form-item v-if="testReply" label="模型回复">
        <el-input :model-value="testReply" type="textarea" rows="4" readonly />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showTest = false">关闭</el-button>
      <el-button type="primary" @click="runTest">发送</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api'

const models = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')

const showForm = ref(false)
const showTest = ref(false)
const testReply = ref('')
const form = reactive({
  id: null,
  model_name: '',
  model_type: 'text',
  base_url: '',
  api_key: '',
  model_id: '',
  is_default: 0,
  status: 1,
})
const testForm = reactive({ id: null, message: '' })

const formTitle = computed(() => (form.id ? '编辑模型' : '新建模型'))

async function load() {
  const res = await adminApi.models({
    keyword: keyword.value || undefined,
    page: page.value,
    page_size: pageSize.value,
  })
  if (res.code === 0) {
    models.value = res.data.items || []
    total.value = res.data.total || 0
  }
}

function reset() {
  keyword.value = ''
  page.value = 1
  load()
}

function openCreate() {
  Object.assign(form, {
    id: null,
    model_name: '',
    model_type: 'text',
    base_url: '',
    api_key: '',
    model_id: '',
    is_default: 0,
    status: 1,
  })
  showForm.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id,
    model_name: row.model_name,
    model_type: row.model_type,
    base_url: row.base_url,
    api_key: '',
    model_id: row.model_id,
    is_default: row.is_default,
    status: row.status,
  })
  showForm.value = true
}

async function save() {
  const payload = {
    model_name: form.model_name,
    model_type: form.model_type,
    base_url: form.base_url,
    api_key: form.api_key,
    model_id: form.model_id,
    is_default: form.is_default,
    status: form.status,
  }
  if (form.id) {
    await adminApi.updateModel(form.id, payload)
    ElMessage.success('模型已更新')
  } else {
    await adminApi.createModel(payload)
    ElMessage.success('模型已创建')
  }
  showForm.value = false
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除模型 ${row.model_name}？`)
  await adminApi.deleteModel(row.id)
  ElMessage.success('已删除')
  load()
}

async function setDefault(row) {
  await adminApi.setDefaultModel(row.id)
  ElMessage.success('默认模型已更新')
  load()
}

function openTest(row) {
  testForm.id = row.id
  testForm.message = ''
  testReply.value = ''
  showTest.value = true
}

async function runTest() {
  try {
    const res = await adminApi.testModel(testForm.id, { message: testForm.message })
    if (res.code === 0) {
      testReply.value = res.data.reply || ''
    } else {
      ElMessage.error(res.message || '模型测试失败')
    }
  } catch (err) {
    const msg = err?.response?.data?.detail || err?.message || '模型测试失败'
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

onMounted(load)
</script>
