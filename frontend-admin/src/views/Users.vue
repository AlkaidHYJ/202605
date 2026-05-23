<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">用户与组织</div>
          <h1 class="hero-title" style="margin-top: 8px;">统一管理企业账号与权限结构</h1>
        </div>
        <el-button type="primary" @click="showCreate = true">新建用户</el-button>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">支持查看用户列表、识别管理员账号，并通过弹窗快速创建新的业务账号。</p>

      <div class="metric-grid" style="margin-top: 18px;">
        <div class="metric-card"><div class="metric-label">总用户</div><span class="metric-value">{{ users.length }}</span></div>
        <div class="metric-card"><div class="metric-label">管理员</div><span class="metric-value">{{ adminCount }}</span></div>
        <div class="metric-card"><div class="metric-label">启用状态</div><span class="metric-value">{{ activeCount }}</span></div>
        <div class="metric-card"><div class="metric-label">近期新增</div><span class="metric-value">12</span></div>
      </div>
    </section>

    <div class="glass-card" style="padding: 20px;">
      <div class="section-heading">
        <h3>用户列表</h3>
        <span class="muted">支持分页与条件检索</span>
      </div>
      <div class="toolbar" style="margin-bottom: 12px; flex-wrap: wrap;">
        <el-input v-model="filters.keyword" placeholder="用户名/姓名" style="max-width: 220px;" @keyup.enter="load" />
        <el-input v-model="filters.userId" placeholder="用户 ID" style="max-width: 180px;" @keyup.enter="load" />
        <el-button type="primary" @click="load">搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      <el-table :data="users" border style="width: 100%;">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="real_name" label="姓名" />
        <el-table-column prop="is_admin" label="管理员" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'success' : 'info'" effect="light" round>{{ row.is_admin ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="String(row.status) === '1' ? 'success' : 'warning'" effect="light" round>
              {{ String(row.status) === '1' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
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

    <el-dialog v-model="showCreate" title="新建用户" width="520px">
      <el-form :model="form" label-position="top">
        <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.real_name" /></el-form-item>
        <el-form-item label="管理员">
          <el-select v-model="form.is_admin" style="width: 100%;">
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
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">确定</el-button>
      </template>
    </el-dialog>
  </div>
  <el-dialog v-model="showEdit" title="编辑用户" width="520px">
    <el-form :model="editForm" label-position="top">
      <el-form-item label="用户名"><el-input v-model="editForm.username" /></el-form-item>
      <el-form-item label="密码（可选）"><el-input v-model="editForm.password" type="password" /></el-form-item>
      <el-form-item label="姓名"><el-input v-model="editForm.real_name" /></el-form-item>
      <el-form-item label="管理员">
        <el-select v-model="editForm.is_admin" style="width: 100%;">
          <el-option :value="0" label="否" />
          <el-option :value="1" label="是" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="editForm.status" style="width: 100%;">
          <el-option :value="1" label="启用" />
          <el-option :value="0" label="禁用" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showEdit = false">取消</el-button>
      <el-button type="primary" @click="update">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api'

const users = ref([])
const showCreate = ref(false)
const showEdit = ref(false)
const form = reactive({ username: '', password: '', real_name: '', is_admin: 0, status: 1 })
const editForm = reactive({ id: null, username: '', password: '', real_name: '', is_admin: 0, status: 1 })
const filters = reactive({ keyword: '', userId: '' })
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const adminCount = computed(() => users.value.filter((user) => user.is_admin).length)
const activeCount = computed(() => users.value.filter((user) => String(user.status) === '1').length)

async function load() {
  const res = await adminApi.users({
    page: page.value,
    page_size: pageSize.value,
    keyword: filters.keyword || undefined,
    user_id: filters.userId ? Number(filters.userId) : undefined,
  })
  if (res.code === 0) {
    users.value = res.data.items || []
    total.value = res.data.total || 0
  }
}

async function create() {
  await adminApi.createUser(form)
  ElMessage.success('创建成功')
  showCreate.value = false
  Object.assign(form, { username: '', password: '', real_name: '', is_admin: 0, status: 1 })
  load()
}

function openEdit(row) {
  Object.assign(editForm, {
    id: row.id,
    username: row.username,
    password: '',
    real_name: row.real_name || '',
    is_admin: row.is_admin || 0,
    status: row.status ?? 1,
  })
  showEdit.value = true
}

async function update() {
  await adminApi.updateUser(editForm.id, {
    username: editForm.username,
    password: editForm.password || undefined,
    real_name: editForm.real_name,
    is_admin: editForm.is_admin,
    status: editForm.status,
  })
  ElMessage.success('更新成功')
  showEdit.value = false
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除用户 ${row.username}？`)
  await adminApi.deleteUser(row.id)
  ElMessage.success('已删除')
  load()
}

function resetFilters() {
  filters.keyword = ''
  filters.userId = ''
  page.value = 1
  load()
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
