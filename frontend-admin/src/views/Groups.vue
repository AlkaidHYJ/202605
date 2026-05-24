<template>
  <div class="split-grid">
    <section class="stack-grid">
      <div class="hero-block">
        <div class="section-heading" style="margin-bottom: 8px;">
          <div>
            <div class="hero-subtitle">群组管理中心</div>
            <h1 class="hero-title" style="margin-top: 8px;">监控并干预全企业聊天群组</h1>
          </div>
          <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">{{ groups.length }} 个群组</div>
        </div>
        <p class="hero-subtitle" style="max-width: 740px; line-height: 1.8;">可快速检索群名、查看状态，并执行禁言或解散操作。</p>
      </div>

      <div class="metric-grid">
        <div class="metric-card"><div class="metric-label">活跃群组</div><span class="metric-value">{{ groups.length }}</span></div>
        <div class="metric-card"><div class="metric-label">正常</div><span class="metric-value">{{ normalCount }}</span></div>
        <div class="metric-card"><div class="metric-label">禁言</div><span class="metric-value">{{ muteCount }}</span></div>
        <div class="metric-card"><div class="metric-label">已解散</div><span class="metric-value">{{ dissolveCount }}</span></div>
      </div>
    </section>

    <div class="glass-card" style="padding: 20px;">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索群名" style="max-width: 220px;" @keyup.enter="load" />
        <el-input v-model="groupId" placeholder="群 ID" style="max-width: 180px;" @keyup.enter="load" />
        <el-button type="primary" @click="load">搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
        <el-button type="primary" @click="showCreate = true">新建群组</el-button>
      </div>
      <el-table :data="groups" border style="width: 100%;">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="group_name" label="群名" />
        <el-table-column prop="owner_id" label="群主ID" width="100" />
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" effect="light" round>{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="420">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row, 'members')">成员</el-button>
            <el-button size="small" @click="openDetail(row, 'files')">文件管理</el-button>
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" @click="openSystem(row)">系统消息</el-button>
            <el-button size="small" @click="mute(row.id)">禁言</el-button>
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

  <el-dialog v-model="showCreate" title="新建群组" width="520px">
    <el-form :model="createForm" label-position="top">
      <el-form-item label="群名称"><el-input v-model="createForm.group_name" /></el-form-item>
      <el-form-item label="群主 ID"><el-input v-model="createForm.owner_id" /></el-form-item>
      <el-form-item label="机器人">
        <el-select v-model="createForm.is_bot_enabled" style="width: 100%;">
          <el-option :value="1" label="启用" />
          <el-option :value="0" label="关闭" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="createForm.status" style="width: 100%;">
          <el-option :value="1" label="正常" />
          <el-option :value="2" label="禁言" />
          <el-option :value="3" label="解散" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showCreate = false">取消</el-button>
      <el-button type="primary" @click="create">确定</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showEdit" title="编辑群组" width="520px">
    <el-form :model="editForm" label-position="top">
      <el-form-item label="群名称"><el-input v-model="editForm.group_name" /></el-form-item>
      <el-form-item label="群主 ID"><el-input v-model="editForm.owner_id" /></el-form-item>
      <el-form-item label="机器人">
        <el-select v-model="editForm.is_bot_enabled" style="width: 100%;">
          <el-option :value="1" label="启用" />
          <el-option :value="0" label="关闭" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="editForm.status" style="width: 100%;">
          <el-option :value="1" label="正常" />
          <el-option :value="2" label="禁言" />
          <el-option :value="3" label="解散" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showEdit = false">取消</el-button>
      <el-button type="primary" @click="update">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showSystem" title="发送系统消息" width="520px">
    <el-form :model="systemForm" label-position="top">
      <el-form-item label="内容">
        <el-input v-model="systemForm.content" type="textarea" rows="4" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showSystem = false">取消</el-button>
      <el-button type="primary" @click="sendSystem">发送</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showDetail" :title="detailGroup?.group_name ? `群组详情 - ${detailGroup.group_name}` : '群组详情'" width="960px">
    <el-tabs v-model="detailTab">
      <el-tab-pane label="群成员" name="members">
        <div v-loading="detailLoading">
          <el-table :data="detailMembers" border style="width: 100%;">
            <el-table-column label="成员" min-width="180">
              <template #default="{ row }">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <el-avatar :size="32">{{ memberAvatar(row) }}</el-avatar>
                  <div>
                    <div style="font-weight: 700;">{{ memberName(row) }}</div>
                    <div class="muted" style="font-size: 12px;">{{ row.member_type === 'agent' ? '数字员工' : '企业用户' }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="user_id" label="成员 ID" width="120" />
            <el-table-column label="角色" width="120">
              <template #default="{ row }">
                <el-tag :type="memberRoleTag(row.role)" effect="light" round>{{ memberRoleText(row.role) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="join_time" label="加入时间" width="180" />
          </el-table>
          <el-empty v-if="!detailMembers.length" description="暂无群成员" />
        </div>
      </el-tab-pane>
      <el-tab-pane label="文件管理" name="files">
        <div v-loading="detailLoading">
          <div class="metric-grid" style="margin-bottom: 16px;">
            <div class="metric-card"><div class="metric-label">去重后文件</div><span class="metric-value">{{ detailFiles.length }}</span></div>
            <div class="metric-card"><div class="metric-label">引用总次数</div><span class="metric-value">{{ fileReferenceCount }}</span></div>
          </div>
          <el-table :data="detailFiles" border style="width: 100%;">
            <el-table-column prop="file_name" label="文件名" min-width="220" />
            <el-table-column prop="file_type" label="类型" width="100" />
            <el-table-column prop="file_size" label="大小" width="120" />
            <el-table-column prop="reference_count" label="引用次数" width="100" />
            <el-table-column prop="latest_created_at" label="最后出现时间" width="180" />
          </el-table>
          <el-empty v-if="!detailFiles.length" description="暂无文件" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api'

const groups = ref([])
const keyword = ref('')
const groupId = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const showCreate = ref(false)
const showEdit = ref(false)
const showSystem = ref(false)
const showDetail = ref(false)
const createForm = reactive({ group_name: '', owner_id: '', is_bot_enabled: 1, status: 1 })
const editForm = reactive({ id: null, group_name: '', owner_id: '', is_bot_enabled: 1, status: 1 })
const systemForm = reactive({ group_id: null, content: '' })
const detailGroup = ref(null)
const detailTab = ref('members')
const detailLoading = ref(false)
const detailMembers = ref([])
const detailFiles = ref([])

const normalCount = computed(() => groups.value.filter((group) => group.status === 1).length)
const muteCount = computed(() => groups.value.filter((group) => group.status === 2).length)
const dissolveCount = computed(() => groups.value.filter((group) => group.status === 3).length)
const fileReferenceCount = computed(() => detailFiles.value.reduce((total, file) => total + (file.reference_count || 0), 0))

async function load() {
  const res = await adminApi.groups({
    keyword: keyword.value || undefined,
    group_id: groupId.value ? Number(groupId.value) : undefined,
    page: page.value,
    page_size: pageSize.value,
  })
  if (res.code === 0) {
    groups.value = res.data.items || []
    total.value = res.data.total || 0
  }
}

function resetFilters() {
  keyword.value = ''
  groupId.value = ''
  page.value = 1
  load()
}

async function create() {
  await adminApi.createGroup({
    group_name: createForm.group_name,
    owner_id: Number(createForm.owner_id),
    member_ids: [],
    is_bot_enabled: createForm.is_bot_enabled,
    status: createForm.status,
  })
  ElMessage.success('创建成功')
  showCreate.value = false
  Object.assign(createForm, { group_name: '', owner_id: '', is_bot_enabled: 1, status: 1 })
  load()
}

function openEdit(row) {
  Object.assign(editForm, {
    id: row.id,
    group_name: row.group_name,
    owner_id: row.owner_id,
    is_bot_enabled: row.is_bot_enabled,
    status: row.status,
  })
  showEdit.value = true
}

async function update() {
  await adminApi.updateGroup(editForm.id, {
    group_name: editForm.group_name,
    owner_id: Number(editForm.owner_id),
    is_bot_enabled: editForm.is_bot_enabled,
    status: editForm.status,
  })
  ElMessage.success('更新成功')
  showEdit.value = false
  load()
}

async function remove(row) {
  await ElMessageBox.confirm('确认删除该群组？')
  await adminApi.deleteGroup(row.id)
  ElMessage.success('已删除')
  load()
}

async function mute(id) {
  await adminApi.muteGroup(id)
  ElMessage.success('已禁言')
  load()
}

function openSystem(row) {
  systemForm.group_id = row.id
  systemForm.content = ''
  showSystem.value = true
}

async function openDetail(row, tab = 'members') {
  detailGroup.value = row
  detailTab.value = tab
  showDetail.value = true
  detailLoading.value = true
  try {
    const [membersRes, filesRes] = await Promise.all([
      adminApi.groupMembers(row.id),
      adminApi.files(row.id),
    ])
    if (membersRes.code === 0) detailMembers.value = membersRes.data || []
    if (filesRes.code === 0) detailFiles.value = filesRes.data?.items || []
  } catch (error) {
    ElMessage.error(String(error))
  } finally {
    detailLoading.value = false
  }
}

async function sendSystem() {
  await adminApi.sendSystemMessage(systemForm.group_id, { content: systemForm.content })
  ElMessage.success('系统消息已发送')
  showSystem.value = false
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

function statusText(status) {
  return { 1: '正常', 2: '禁言', 3: '解散' }[status] || '未知'
}

function statusTag(status) {
  return { 1: 'success', 2: 'warning', 3: 'danger' }[status] || 'info'
}

function memberName(member) {
  if (!member) return ''
  if (member.member_type === 'agent') return member.agent_name || '数字员工'
  return member.real_name || member.username || `用户${member.user_id}`
}

function memberAvatar(member) {
  const name = memberName(member)
  return name ? name.slice(0, 1) : 'A'
}

function memberRoleText(role) {
  return { 1: '群主', 2: '管理员', 3: '成员', 4: '数字员工' }[role] || '未知'
}

function memberRoleTag(role) {
  return { 1: 'danger', 2: 'warning', 3: 'success', 4: 'info' }[role] || 'info'
}

onMounted(load)
</script>
