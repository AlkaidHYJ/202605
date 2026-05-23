<template>
  <div class="split-grid">
    <section class="stack-grid">
      <div class="hero-block">
        <div class="section-heading" style="margin-bottom: 8px;">
          <div>
            <div class="hero-subtitle">消息合规审计</div>
            <h1 class="hero-title" style="margin-top: 8px;">审计、筛查与撤回聊天消息</h1>
          </div>
          <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">{{ messages.length }} 条记录</div>
        </div>
        <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">结合关键词与群 ID 检索历史消息，定位后可直接执行强制撤回。</p>
      </div>

      <div class="glass-card" style="padding: 20px;">
        <div class="toolbar" style="flex-wrap: wrap;">
          <el-input v-model="keyword" placeholder="关键词" style="max-width: 220px;" />
          <el-input v-model="groupId" placeholder="群 ID" style="max-width: 220px;" />
          <el-button type="primary" @click="load">检索</el-button>
        </div>

        <div class="metric-grid" style="margin-bottom: 18px;">
          <div class="metric-card"><div class="metric-label">总消息</div><span class="metric-value">{{ messages.length }}</span></div>
          <div class="metric-card"><div class="metric-label">已审计</div><span class="metric-value">{{ auditedCount }}</span></div>
          <div class="metric-card"><div class="metric-label">待处理</div><span class="metric-value">{{ pendingCount }}</span></div>
          <div class="metric-card"><div class="metric-label">违规命中</div><span class="metric-value">{{ flaggedCount }}</span></div>
        </div>

        <el-table :data="messages" border style="width: 100%;">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="sender_id" label="发送人" width="90" />
          <el-table-column prop="content" label="内容" show-overflow-tooltip />
          <el-table-column prop="audit_status" label="审计" width="110">
            <template #default="{ row }">
              <el-tag :type="row.audit_status === 1 ? 'warning' : 'info'" effect="light" round>
                {{ row.audit_status === 1 ? '已审计' : '正常' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="recall(row.id)">强制撤回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <aside class="glass-card" style="padding: 20px; min-height: 520px;">
      <div class="section-heading">
        <h3>审计说明</h3>
        <span class="muted">审计工作流</span>
      </div>
      <div class="instruction-box" style="margin-bottom: 14px;">
        <div class="metric-label">规则命中</div>
        <div style="margin-top: 8px; line-height: 1.8;">敏感词会被拦截或标记，管理端可对单条消息发起撤回。</div>
      </div>
      <div class="instruction-box" style="margin-bottom: 14px;">
        <div class="metric-label">审核范围</div>
        <div style="margin-top: 8px; line-height: 1.8;">支持按群 ID、关键词和消息状态快速聚焦目标记录。</div>
      </div>
      <div class="instruction-box">
        <div class="metric-label">建议动作</div>
        <div style="margin-top: 8px; line-height: 1.8;">对高风险消息优先执行撤回，然后同步排查敏感词来源。</div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '../api'

const messages = ref([])
const keyword = ref('')
const groupId = ref('')

const auditedCount = computed(() => messages.value.filter((message) => message.audit_status === 1).length)
const pendingCount = computed(() => messages.value.filter((message) => !message.audit_status).length)
const flaggedCount = computed(() => messages.value.filter((message) => String(message.content || '').includes('vault_keys')).length)

async function load() {
  const res = await adminApi.messages({
    keyword: keyword.value || undefined,
    group_id: groupId.value ? Number(groupId.value) : undefined,
  })
  if (res.code === 0) messages.value = res.data.items || []
}

async function recall(id) {
  await adminApi.recall({ message_id: id })
  ElMessage.success('撤回指令已下发')
  load()
}
</script>
