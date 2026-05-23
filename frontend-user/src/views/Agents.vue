<template>
  <div class="soft-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">数字员工广场</div>
          <h1 class="hero-title" style="margin-top: 8px;">挑选适合当前任务的 AI 员工</h1>
        </div>
        <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">{{ agents.length }} 位在岗</div>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">围绕 SQL、文档、运营与创意等场景，为不同任务配置不同的数字员工。点击卡片即可展开对话。</p>
    </section>

    <section class="split-grid">
      <div class="stack-grid">
        <div class="glass-card" style="padding: 20px;">
          <div class="section-heading">
            <h3>员工列表</h3>
            <span class="muted">点击进入会话</span>
          </div>
          <div class="soft-grid two">
            <div
              v-for="a in agents"
              :key="a.id"
              class="agent-card"
              :class="{ active: current?.id === a.id }"
              @click="selectAgent(a)"
            >
              <el-avatar :size="48">{{ a.agent_name?.slice(0, 1) || 'A' }}</el-avatar>
              <div style="min-width: 0;">
                <div class="agent-name">{{ a.agent_name }}</div>
                <div class="muted" style="font-size: 12px; margin-top: 4px; line-height: 1.7;">{{ a.persona }}</div>
                <div class="agent-meta">
                  <span class="meta-pill">模型：{{ a.model_name || '默认模型' }}</span>
                  <span v-for="skill in a.skill_names || []" :key="skill" class="meta-pill">{{ skill }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="glass-card" v-if="current" style="padding: 20px;">
          <div class="section-heading">
            <h3>与 {{ current.agent_name }} 对话</h3>
            <span class="muted">多轮上下文</span>
          </div>
          <div class="chat-history">
            <div v-for="(m, i) in chatLog" :key="i" class="chat-line" :class="m.role">{{ m.text }}</div>
            <div v-if="!chatLog.length" class="muted" style="text-align:center; padding: 24px 0;">发送第一条消息开始会话</div>
          </div>
          <div style="display:flex; gap: 10px; margin-top: 14px;">
            <el-input v-model="input" placeholder="输入问题后回车或点击发送" @keyup.enter="send" />
            <el-button type="primary" @click="send">发送</el-button>
          </div>
        </div>
      </div>

      <aside class="glass-card" style="padding: 20px; min-height: 520px;">
        <div class="section-heading">
          <h3>能力说明</h3>
          <span class="muted">{{ current?.agent_name || '未选择' }}</span>
        </div>
        <div v-if="current" class="agent-detail">
          <el-avatar :size="88">{{ current.agent_name?.slice(0, 1) || 'A' }}</el-avatar>
          <div class="agent-detail-name">{{ current.agent_name }}</div>
          <div class="muted" style="text-align:center; line-height: 1.8;">{{ current.persona }}</div>
          <div class="agent-model">{{ current.model_name || '未绑定模型' }}</div>
          <div class="skill-list">
            <div v-for="skill in current.skill_names || []" :key="skill" class="skill-item">{{ skill }}</div>
            <div v-if="!(current.skill_names || []).length" class="skill-item">暂未绑定技能</div>
          </div>
          <div class="muted" style="text-align:center; font-size: 12px; line-height: 1.6;">可在当前页私聊；群聊中输入 @{{ current.agent_name }} 可唤起它回复。</div>
        </div>
        <el-empty v-else description="请选择一位数字员工" />
      </aside>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { agentApi } from '../api'

const agents = ref([])
const current = ref(null)
const input = ref('')
const chatLog = ref([])

onMounted(async () => {
  const res = await agentApi.list()
  if (res.code === 0) agents.value = res.data || []
})

function selectAgent(a) {
  current.value = a
  chatLog.value = []
}

async function send() {
  if (!current.value || !input.value.trim()) return
  const text = input.value
  chatLog.value.push({ role: 'user', text })
  input.value = ''
  const res = await agentApi.chat({ agent_id: current.value.id, message: text })
  if (res.code === 0) chatLog.value.push({ role: 'bot', text: res.data.reply })
}
</script>

<style scoped>
.agent-card {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 16px;
  border-radius: 18px;
  cursor: pointer;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.agent-card.active {
  border-color: rgba(29, 78, 216, 0.22);
  background: rgba(29, 78, 216, 0.08);
}

.agent-name {
  font-size: 16px;
  font-weight: 800;
}

.agent-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(29, 78, 216, 0.08);
  color: var(--primary-strong);
  font-size: 12px;
  font-weight: 700;
}

.chat-history {
  min-height: 220px;
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-line {
  padding: 12px 14px;
  border-radius: 14px;
  line-height: 1.7;
}

.chat-line.user {
  align-self: flex-end;
  background: rgba(29, 78, 216, 0.08);
  color: var(--primary-strong);
}

.chat-line.bot {
  align-self: flex-start;
  background: rgba(15, 23, 42, 0.04);
}

.agent-detail {
  display: grid;
  place-items: center;
  gap: 12px;
}

.agent-detail-name {
  font-size: 20px;
  font-weight: 900;
}

.agent-model {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  font-weight: 700;
}

.skill-list {
  width: 100%;
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.skill-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(29, 78, 216, 0.06);
  font-weight: 600;
}
</style>
