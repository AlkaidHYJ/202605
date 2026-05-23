<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">沟通与协作</div>
          <h1 class="hero-title" style="margin-top: 8px;">统一好友与群聊的智能会话中心</h1>
        </div>
        <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">我的 ID：{{ currentUserId }}</div>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">支持好友列表、群列表、单聊/群聊消息、语音/视频通话、Emoji、文件和图片发送。消息通过 WebSocket 实时推送。</p>
    </section>

    <section class="chat-shell">
      <aside class="glass-card" style="padding: 16px; min-height: 680px;">
        <div class="section-heading">
          <h3>会话列表</h3>
          <span class="muted">{{ totalSessions }} 个</span>
        </div>

        <el-input v-model="keyword" placeholder="搜索好友或群组" size="large" style="margin-bottom: 12px;" />

        <div class="session-tabs">
          <button :class="['tab-btn', activeTab === 'friends' ? 'active' : '']" @click="activeTab = 'friends'">好友</button>
          <button :class="['tab-btn', activeTab === 'groups' ? 'active' : '']" @click="activeTab = 'groups'">群组</button>
        </div>

        <div v-if="activeTab === 'friends'" class="session-list">
          <div class="session-actions">
            <el-button size="default" type="primary" class="action-btn" @click="showAddFriend = true">通过 ID 添加好友</el-button>
          </div>
          <div
            v-for="friend in filteredFriends"
            :key="friend.friend_id"
            class="session-item"
            :class="{ active: selectedChat.type === 'friend' && selectedChat.id === friend.friend_id }"
            @click="selectFriend(friend.friend_id)"
          >
            <el-avatar :size="40">{{ friendDisplayName(friend).slice(0, 1) }}</el-avatar>
            <div style="min-width: 0;">
              <div class="session-title">{{ friendDisplayName(friend) }}</div>
              <div class="muted" style="font-size: 12px; margin-top: 4px;">ID：{{ friend.friend_id }}</div>
            </div>
            <span v-if="getUnreadCount('friend', friend.friend_id)" class="session-badge">{{ getUnreadCount('friend', friend.friend_id) }}</span>
          </div>
          <el-empty v-if="!filteredFriends.length" description="暂无好友" />
        </div>

        <div v-else class="session-list">
          <div class="session-actions">
            <el-button size="default" type="primary" class="action-btn" @click="showCreateGroup = true">创建群</el-button>
          </div>
          <div
            v-for="group in filteredGroups"
            :key="group.id"
            class="session-item"
            :class="{ active: selectedChat.type === 'group' && selectedChat.id === group.id }"
            @click="selectGroup(group.id)"
          >
            <el-avatar :size="40">{{ group.group_name.slice(0, 1) }}</el-avatar>
            <div style="min-width: 0;">
              <div class="session-title">{{ group.group_name }}</div>
              <div class="muted" style="font-size: 12px; margin-top: 4px;">群 ID：{{ group.id }}</div>
            </div>
            <span v-if="getUnreadCount('group', group.id)" class="session-badge">{{ getUnreadCount('group', group.id) }}</span>
          </div>
          <el-empty v-if="!filteredGroups.length" description="暂无群组" />
        </div>
      </aside>

      <div class="glass-card chat-window">
        <div class="chat-header">
          <div>
            <div class="card-title">{{ activeTitle }}</div>
            <div class="muted" style="font-size: 12px; margin-top: 4px;">{{ activeSubtitle }}</div>
          </div>
          <div class="chat-actions">
            <el-button v-if="selectedChat.type === 'friend'" size="small" @click="openCall('voice')">语音</el-button>
            <el-button v-if="selectedChat.type === 'friend'" size="small" @click="openCall('video')">视频</el-button>
            <div class="pill">{{ activeMessages.length }} 条消息</div>
          </div>
        </div>

        <div class="chat-messages" ref="msgBox">
          <div v-if="!activeMessages.length" class="muted" style="height: 100%; display: grid; place-items: center;">暂无消息，先发送第一条内容吧。</div>
          <div v-for="message in activeMessages" :key="message.id">
            <div v-if="isSystemMessage(message)" class="system-message">
              {{ parsedMessage(message).content }}
            </div>
            <div v-else class="bubble" :class="message.sender_id === currentUserId ? 'user' : 'bot'">
              <div class="bubble-meta">{{ senderName(message) }} · {{ formatTime(message.created_at) }}</div>
              <div v-if="parsedMessage(message).type === 'text'" class="bubble-text">{{ parsedMessage(message).content }}</div>
              <div v-else-if="parsedMessage(message).type === 'emoji'" class="bubble-text" style="font-size: 22px;">{{ parsedMessage(message).content }}</div>
              <div v-else-if="parsedMessage(message).type === 'image'" class="bubble-media">
                <img :src="parsedMessage(message).url" :alt="parsedMessage(message).fileName" />
                <div class="muted" style="font-size: 12px; margin-top: 6px;">{{ parsedMessage(message).fileName }}</div>
              </div>
              <div v-else-if="parsedMessage(message).type === 'file'" class="bubble-file">
                <div class="file-title">{{ parsedMessage(message).fileName }}</div>
                <div class="muted" style="font-size: 12px;">{{ parsedMessage(message).fileSize }}</div>
                <a v-if="parsedMessage(message).url" :href="parsedMessage(message).url" :download="parsedMessage(message).fileName" class="file-link">下载文件</a>
              </div>
              <div v-else-if="parsedMessage(message).type === 'call'" class="bubble-call">
                {{ parsedMessage(message).content }}
              </div>
            </div>
          </div>
        </div>

        <div class="composer">
          <div class="composer-tools">
            <el-popover placement="top-start" :width="260" trigger="click">
              <div class="emoji-grid">
                <button v-for="emoji in emojis" :key="emoji" class="emoji-btn" @click="sendEmoji(emoji)">{{ emoji }}</button>
              </div>
              <template #reference>
                <el-button size="small">表情</el-button>
              </template>
            </el-popover>
            <el-button size="small" @click="triggerUpload('image')">图片</el-button>
            <el-button size="small" @click="triggerUpload('file')">文件</el-button>
          </div>
          <el-input v-model="content" placeholder="输入消息内容" size="large" @keyup.enter="sendText" />
          <el-button type="primary" size="large" @click="sendText">发送</el-button>
          <div v-if="selectedChat.type === 'group' && activeGroupMembers.some((member) => member.member_type === 'agent')" class="member-hint" style="grid-column: 1 / -1;">
            群聊里输入 @员工名 可唤起数字员工回复，例如 @{{ activeGroupMembers.find((member) => member.member_type === 'agent')?.agent_name }}。
          </div>
        </div>
      </div>

      <aside class="glass-card" style="padding: 16px; min-height: 680px;">
        <div class="section-heading">
          <h3>{{ sideTitle }}</h3>
          <span class="muted">{{ sideSubtitle }}</span>
        </div>
        <div v-if="selectedChat.type === 'friend'" class="detail-card">
          <el-avatar :size="72">{{ activeFriendName.slice(0, 1) || 'F' }}</el-avatar>
          <div class="detail-name">{{ activeFriendName }}</div>
          <div class="muted" style="text-align: center; line-height: 1.8;">好友 ID：{{ selectedChat.id }}</div>
          <div class="detail-meta">
            <div><span>账号</span><strong>{{ activeFriend?.username || '-' }}</strong></div>
            <div><span>状态</span><strong>{{ activeFriend?.status === 1 ? '在线' : '离线' }}</strong></div>
          </div>
        </div>

        <div v-else class="detail-card">
          <el-avatar :size="72">{{ activeGroup?.group_name?.slice(0, 1) || 'G' }}</el-avatar>
          <div class="detail-name">{{ activeGroup?.group_name || '未选择群组' }}</div>
          <div class="muted" style="text-align: center; line-height: 1.8;">群聊成员管理与权限设置</div>
          <el-button size="small" type="primary" style="margin-top: 12px;" @click="showAddMembers = true">添加成员</el-button>
          <div class="member-list">
            <div v-for="member in activeGroupMembers" :key="member.user_id" class="member-item">
              <el-avatar :size="32">{{ memberAvatar(member) }}</el-avatar>
              <span>{{ memberDisplayName(member) }}</span>
            </div>
          </div>
        </div>
      </aside>
    </section>
  </div>

  <input ref="imageInput" type="file" accept="image/*" class="hidden-input" @change="onImageUpload" />
  <input ref="fileInput" type="file" class="hidden-input" @change="onFileUpload" />

  <el-dialog v-model="showAddFriend" title="通过 ID 添加好友" width="420px">
    <el-form label-position="top" :model="addFriendForm">
      <el-form-item label="好友 ID"><el-input v-model="addFriendForm.friendId" placeholder="输入好友的唯一 ID" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddFriend = false">取消</el-button>
      <el-button type="primary" @click="addFriendById">确认添加</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showCreateGroup" title="创建群组" width="520px">
    <el-form label-position="top" :model="newGroup">
      <el-form-item label="群名称"><el-input v-model="newGroup.name" placeholder="例如：Q2 策略会议群" /></el-form-item>
      <el-form-item label="选择成员">
        <el-select v-model="newGroup.members" multiple placeholder="选择成员" style="width: 100%;">
          <el-option v-for="friend in friends" :key="friend.friend_id" :label="friendDisplayName(friend)" :value="friend.friend_id" />
        </el-select>
      </el-form-item>
      <el-form-item label="绑定数字员工">
        <el-select v-model="newGroup.agentIds" multiple placeholder="选择数字员工" style="width: 100%;">
          <el-option v-for="agent in agents" :key="agent.id" :label="agent.agent_name" :value="agent.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showCreateGroup = false">取消</el-button>
      <el-button type="primary" @click="createGroup">确认创建</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showAddMembers" title="添加群成员" width="520px">
    <el-form label-position="top">
      <el-form-item label="选择成员">
        <el-select v-model="selectedMembers" multiple placeholder="选择成员" style="width: 100%;">
          <el-option v-for="friend in friends" :key="friend.friend_id" :label="friendDisplayName(friend)" :value="friend.friend_id" />
        </el-select>
      </el-form-item>
      <el-form-item label="添加数字员工">
        <el-select v-model="selectedAgentIds" multiple placeholder="选择数字员工" style="width: 100%;">
          <el-option v-for="agent in agents" :key="agent.id" :label="agent.agent_name" :value="agent.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddMembers = false">取消</el-button>
      <el-button type="primary" @click="addMembers">确认添加</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="callState.visible" :title="callState.type === 'voice' ? '语音通话' : '视频通话'" width="420px">
    <div class="call-box">
      <div class="call-avatar">{{ activeFriendName.slice(0, 1) || 'A' }}</div>
      <div class="call-title">{{ callState.type === 'voice' ? '正在呼叫语音' : '正在呼叫视频' }}</div>
      <div class="muted" style="margin-top: 8px;">等待对方接听...</div>
      <div class="call-actions">
        <el-button @click="callState.visible = false">取消</el-button>
        <el-button type="primary" @click="finishCall">结束</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { agentApi, imApi } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const currentUserId = computed(() => auth.user?.user_id || auth.user?.id || 0)
const currentUserName = computed(() => auth.user?.real_name || auth.user?.username || '我')

const activeTab = ref('friends')
const keyword = ref('')
const content = ref('')
const msgBox = ref(null)
const ws = ref(null)
const reconnectTimer = ref(null)

const friends = ref([])
const groups = ref([])
const agents = ref([])
const groupMembers = ref({})
const messageCache = ref({})
const unreadCounts = ref({})

const selectedChat = ref({ type: 'friend', id: null })

const emojis = ['😀', '😄', '😉', '🤝', '📌', '🚀', '📈', '✅', '🎯', '💡', '🧠']

const showAddFriend = ref(false)
const showCreateGroup = ref(false)
const showAddMembers = ref(false)
const addFriendForm = ref({ friendId: '' })
const newGroup = ref({ name: '', members: [], agentIds: [] })
const selectedMembers = ref([])
const selectedAgentIds = ref([])

const imageInput = ref(null)
const fileInput = ref(null)

const callState = ref({ visible: false, type: 'voice' })

const filteredFriends = computed(() => {
  const key = keyword.value.trim()
  if (!key) return friends.value
  return friends.value.filter((friend) => friendDisplayName(friend).includes(key))
})

const filteredGroups = computed(() => {
  const key = keyword.value.trim()
  if (!key) return groups.value
  return groups.value.filter((group) => group.group_name.includes(key))
})

const totalSessions = computed(() => friends.value.length + groups.value.length)

const activeFriend = computed(() => friends.value.find((friend) => friend.friend_id === selectedChat.value.id) || null)
const activeGroup = computed(() => groups.value.find((group) => group.id === selectedChat.value.id) || null)
const activeGroupMembers = computed(() => groupMembers.value[selectedChat.value.id] || [])

const activeTitle = computed(() => {
  if (selectedChat.value.type === 'friend') return activeFriendName.value || '请选择好友'
  return activeGroup.value?.group_name || '请选择群组'
})

const activeSubtitle = computed(() => {
  if (selectedChat.value.type === 'friend') return activeFriend?.username || '单人会话'
  return `${activeGroupMembers.value.length} 位成员 · 群聊会话`
})

const sideTitle = computed(() => (selectedChat.value.type === 'friend' ? '好友资料' : '群组详情'))
const sideSubtitle = computed(() => (selectedChat.value.type === 'friend' ? '单人沟通' : '成员管理'))

const activeMessages = computed(() => {
  if (!selectedChat.value.id) return []
  const key = `${selectedChat.value.type}:${selectedChat.value.id}`
  return messageCache.value[key] || []
})

const activeFriendName = computed(() => friendDisplayName(activeFriend.value || {}))

async function loadFriends() {
  const res = await imApi.friends()
  if (res.code === 0) friends.value = res.data || []
}

async function loadGroups() {
  const res = await imApi.groups()
  if (res.code === 0) groups.value = res.data || []
}

async function loadAgents() {
  const res = await agentApi.list()
  if (res.code === 0) agents.value = res.data || []
}

async function loadMessages() {
  if (!selectedChat.value.id) return
  const params = selectedChat.value.type === 'friend'
    ? { chat_type: 1, receiver_id: selectedChat.value.id }
    : { chat_type: 2, group_id: selectedChat.value.id }
  const res = await imApi.list(params)
  if (res.code === 0) {
    const key = `${selectedChat.value.type}:${selectedChat.value.id}`
    messageCache.value[key] = res.data?.items || []
    unreadCounts.value = { ...unreadCounts.value, [key]: 0 }
  }
  await scrollToBottom()
}

async function loadGroupMembers(groupId) {
  if (!groupId) return
  const res = await imApi.groupMembers(groupId)
  if (res.code === 0) {
    groupMembers.value = { ...groupMembers.value, [groupId]: res.data || [] }
  }
}

function selectFriend(id) {
  selectedChat.value = { type: 'friend', id }
  activeTab.value = 'friends'
  loadMessages()
}

function selectGroup(id) {
  selectedChat.value = { type: 'group', id }
  activeTab.value = 'groups'
  loadMessages()
  loadGroupMembers(id)
}

async function sendText() {
  if (!selectedChat.value.id || !content.value.trim()) return
  await sendMessage({ type: 'text', content: content.value.trim() })
  content.value = ''
}

async function sendEmoji(emoji) {
  await sendMessage({ type: 'emoji', content: emoji })
}

async function sendMessage(payload) {
  if (!selectedChat.value.id) return
  const message = buildContent(payload)
  const data = {
    chat_type: selectedChat.value.type === 'friend' ? 1 : 2,
    receiver_id: selectedChat.value.type === 'friend' ? selectedChat.value.id : undefined,
    group_id: selectedChat.value.type === 'group' ? selectedChat.value.id : undefined,
    content: message.content,
    msg_type: message.msg_type,
  }
  try {
    const res = await imApi.send(data)
    if (res.code === 0 && res.data) {
      const saved = { ...res.data, sender_name: currentUserName.value }
      insertMessage(saved)
    }
  } catch (e) {
    ElMessage.error(String(e))
  }
}

function buildContent(payload) {
  if (payload.type === 'text' || payload.type === 'emoji') {
    return { content: payload.content, msg_type: 1 }
  }
  return { content: JSON.stringify(payload), msg_type: 2 }
}

function triggerUpload(type) {
  if (type === 'image') imageInput.value?.click()
  if (type === 'file') fileInput.value?.click()
}

function onImageUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning('图片大小需小于 2MB')
    event.target.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    const result = String(reader.result || '')
    const payload = {
      type: 'image',
      fileName: file.name,
      fileSize: formatSize(file.size),
      url: result,
    }
    sendMessage(payload)
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function onFileUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (file.size > 1024 * 1024) {
    ElMessage.warning('文件大小需小于 1MB')
    event.target.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    const result = String(reader.result || '')
    const payload = {
      type: 'file',
      fileName: file.name,
      fileSize: formatSize(file.size),
      url: result,
    }
    sendMessage(payload)
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function openCall(type) {
  callState.value = { visible: true, type }
  sendMessage({ type: 'call', content: type === 'voice' ? '发起语音通话' : '发起视频通话' })
}

function finishCall() {
  callState.value.visible = false
  sendMessage({ type: 'call', content: '通话已结束' })
}

async function addFriendById() {
  const id = Number(addFriendForm.value.friendId)
  if (!id) {
    ElMessage.warning('请输入有效的好友 ID')
    return
  }
  try {
    await imApi.addFriend({ friend_id: id })
    showAddFriend.value = false
    addFriendForm.value.friendId = ''
    await loadFriends()
  } catch (e) {
    ElMessage.error(String(e))
  }
}

async function createGroup() {
  if (!newGroup.value.name.trim()) {
    ElMessage.warning('请输入群名称')
    return
  }
  const res = await imApi.createGroup({
    group_name: newGroup.value.name,
    member_ids: newGroup.value.members,
    agent_ids: newGroup.value.agentIds,
    invite_bot: false,
  })
  if (res.code === 0) {
    newGroup.value = { name: '', members: [], agentIds: [] }
    showCreateGroup.value = false
    await loadGroups()
  }
}

async function addMembers() {
  if (!activeGroup.value) return
  const payload = { member_ids: selectedMembers.value, agent_ids: selectedAgentIds.value }
  await imApi.addGroupMembers(activeGroup.value.id, payload)
  selectedMembers.value = []
  selectedAgentIds.value = []
  showAddMembers.value = false
  await loadGroupMembers(activeGroup.value.id)
}

function friendDisplayName(friend) {
  if (!friend) return ''
  return friend.real_name || friend.username || ''
}

function memberDisplayName(member) {
  if (!member) return ''
  if (member.member_type === 'agent') return member.agent_name || '数字员工'
  return member.real_name || member.username || `用户${member.user_id}`
}

function memberAvatar(member) {
  const name = memberDisplayName(member)
  return name ? name.slice(0, 1) : 'A'
}

function senderName(message) {
  if (message.sender_name) return message.sender_name
  if (message.sender_id === 0) return '系统消息'
  if (message.sender_id === currentUserId.value) return currentUserName.value
  const friend = friends.value.find((f) => f.friend_id === message.sender_id)
  if (friend) return friendDisplayName(friend)
  const members = groupMembers.value[message.group_id] || []
  const match = members.find((m) => m.user_id === message.sender_id)
  return match ? memberDisplayName(match) : `用户${message.sender_id}`
}

function isSystemMessage(message) {
  return message.system === true || (message.sender_id === 0 && message.chat_type === 2)
}

function parsedMessage(message) {
  if (message.msg_type === 1) return { type: 'text', content: message.content }
  try {
    const payload = JSON.parse(message.content)
    return payload.type ? payload : { type: 'text', content: message.content }
  } catch {
    return { type: 'text', content: message.content }
  }
}

function formatTime(value) {
  if (!value) return '刚刚'
  try {
    const date = new Date(value)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return String(value)
  }
}

function formatSize(size) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function connectWs() {
  const token = auth.token || sessionStorage.getItem('token')
  if (!token) return
  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const wsUrl = `${wsProtocol}://${window.location.hostname}:8000/ws?token=${token}`
  ws.value = new WebSocket(wsUrl)
  ws.value.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload.type === 'message') handleIncoming(payload.data)
    } catch {
      // ignore
    }
  }
  ws.value.onclose = () => scheduleReconnect()
  ws.value.onerror = () => ws.value?.close()
}

function handleIncoming(message) {
  const key = resolveChatKey(message)
  insertMessage(message)
  if (`${selectedChat.value.type}:${selectedChat.value.id}` === key) {
    scrollToBottom()
  } else {
    const next = (unreadCounts.value[key] || 0) + 1
    unreadCounts.value = { ...unreadCounts.value, [key]: next }
  }
}

function resolveChatKey(message) {
  return message.chat_type === 1
    ? `friend:${message.sender_id === currentUserId.value ? message.receiver_id : message.sender_id}`
    : `group:${message.group_id}`
}

function insertMessage(message) {
  const key = resolveChatKey(message)
  const list = messageCache.value[key] || []
  if (message.id && list.some((item) => item.id === message.id)) return
  messageCache.value[key] = [...list, message]
  unreadCounts.value = { ...unreadCounts.value, [key]: unreadCounts.value[key] || 0 }
}

function getUnreadCount(type, id) {
  if (!id) return 0
  return unreadCounts.value[`${type}:${id}`] || 0
}

function scheduleReconnect() {
  if (reconnectTimer.value) return
  reconnectTimer.value = setTimeout(() => {
    reconnectTimer.value = null
    connectWs()
  }, 2000)
}

async function scrollToBottom() {
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

onMounted(async () => {
  await loadFriends()
  await loadGroups()
  await loadAgents()
  if (friends.value.length) selectFriend(friends.value[0].friend_id)
  connectWs()
})

onBeforeUnmount(() => {
  if (ws.value) ws.value.close()
  if (reconnectTimer.value) clearTimeout(reconnectTimer.value)
})
</script>

<style scoped>
.session-tabs {
  display: flex;
  gap: 8px;
  padding: 6px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.04);
  margin-bottom: 12px;
}

.tab-btn {
  flex: 1;
  border: none;
  padding: 8px 0;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  background: transparent;
  color: var(--muted);
}

.tab-btn.active {
  background: #fff;
  color: var(--primary);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08);
}

.session-list {
  display: grid;
  gap: 10px;
}

.session-actions {
  display: flex;
  justify-content: flex-end;
}

.action-btn {
  font-weight: 700;
  border-radius: 12px;
  padding: 8px 14px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 16px;
  cursor: pointer;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.session-badge {
  margin-left: auto;
  min-width: 22px;
  height: 22px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #ef4444;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  padding: 0 6px;
}

.session-item.active {
  border-color: rgba(29, 78, 216, 0.22);
  background: rgba(29, 78, 216, 0.08);
}

.session-title {
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-header {
  padding: 18px 20px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.chat-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.bubble-text {
  white-space: pre-wrap;
}

.bubble-media img {
  max-width: 220px;
  border-radius: 14px;
}

.bubble-file {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.06);
  line-height: 1.7;
}

.system-message {
  margin: 10px auto;
  max-width: 80%;
  text-align: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  font-weight: 700;
  font-size: 13px;
}

.file-link {
  display: inline-flex;
  margin-top: 6px;
  color: var(--primary);
  font-weight: 700;
}

.file-title {
  font-weight: 700;
}

.bubble-call {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(29, 78, 216, 0.1);
  font-weight: 700;
}

.composer {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  padding: 16px 20px 20px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
}

.composer-tools {
  display: flex;
  gap: 6px;
  align-items: center;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 6px;
}

.emoji-btn {
  border: none;
  background: rgba(15, 23, 42, 0.04);
  border-radius: 10px;
  padding: 6px 0;
  cursor: pointer;
  font-size: 18px;
}

.detail-card {
  display: grid;
  place-items: center;
  gap: 12px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.03);
}

.detail-name {
  font-size: 18px;
  font-weight: 800;
}

.detail-meta {
  width: 100%;
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.detail-meta div {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--muted);
}

.detail-meta strong {
  color: var(--text);
}

.member-list {
  width: 100%;
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.04);
}

.hidden-input { display: none; }

.call-box {
  display: grid;
  place-items: center;
  gap: 10px;
  padding: 12px 0;
}

.call-avatar {
  width: 72px;
  height: 72px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: rgba(29, 78, 216, 0.16);
  font-weight: 800;
  font-size: 22px;
}

.call-title {
  font-weight: 800;
}

.call-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.member-hint {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 1200px) {
  .composer {
    grid-template-columns: 1fr;
  }
}
</style>
