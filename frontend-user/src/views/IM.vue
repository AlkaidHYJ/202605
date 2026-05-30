<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">沟通与协作</div>
          <h1 class="hero-title" style="margin-top: 8px;">统一好友、群组与数字员工会话中心</h1>
        </div>
        <div class="pill" style="background: rgba(255,255,255,0.16); color: #fff;">我的 ID：{{ currentUserId }}</div>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">支持好友申请、群聊@成员、数字员工私聊、文件图片发送与音视频通话信令。</p>
    </section>

    <section class="chat-shell">
      <aside class="glass-card" style="padding: 16px; min-height: 680px;">
        <div class="section-heading">
          <h3>会话列表</h3>
          <span class="muted">{{ totalSessions }} 个</span>
        </div>

        <el-input v-model="keyword" placeholder="搜索好友、群组或数字员工" size="large" style="margin-bottom: 12px;" />

        <div class="session-tabs">
          <button :class="['tab-btn', activeTab === 'friends' ? 'active' : '']" @click="activeTab = 'friends'">好友</button>
          <button :class="['tab-btn', activeTab === 'groups' ? 'active' : '']" @click="activeTab = 'groups'">群组</button>
          <button :class="['tab-btn', activeTab === 'agents' ? 'active' : '']" @click="activeTab = 'agents'">数字员工</button>
        </div>

        <div v-if="activeTab === 'friends'" class="session-list">
          <div class="session-actions">
            <el-button size="default" type="primary" class="action-btn" @click="showAddFriend = true">添加好友</el-button>
            <el-badge :value="friendRequests.length" :hidden="!friendRequests.length" class="friend-req-badge">
              <el-button size="default" class="action-btn" @click="showFriendRequests = true">好友申请</el-button>
            </el-badge>
          </div>
          <div
            v-for="friend in filteredFriends"
            :key="friend.friend_id"
            class="session-item"
            :class="{ active: selectedChat.type === 'friend' && selectedChat.id === friend.friend_id }"
            @click="selectFriend(friend.friend_id)"
          >
            <el-avatar :size="40">{{ friendDisplayName(friend).slice(0, 1) || 'F' }}</el-avatar>
            <div style="min-width: 0;">
              <div class="session-title">{{ friendDisplayName(friend) }}</div>
              <div class="muted" style="font-size: 12px; margin-top: 4px;">ID：{{ friend.friend_id }}</div>
            </div>
            <span v-if="getUnreadCount('friend', friend.friend_id)" class="session-badge">{{ getUnreadCount('friend', friend.friend_id) }}</span>
          </div>
          <el-empty v-if="!filteredFriends.length" description="暂无好友" />
        </div>

        <div v-else-if="activeTab === 'groups'" class="session-list">
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

        <div v-else class="session-list">
          <div
            v-for="agent in filteredAgents"
            :key="agent.id"
            class="session-item"
            :class="{ active: selectedChat.type === 'agent' && selectedChat.id === agent.id }"
            @click="selectAgent(agent.id)"
          >
            <el-avatar :size="40">{{ (agent.agent_name || 'A').slice(0, 1) }}</el-avatar>
            <div style="min-width: 0;">
              <div class="session-title">{{ agent.agent_name }}</div>
              <div class="muted" style="font-size: 12px; margin-top: 4px;">私聊数字员工</div>
            </div>
            <span v-if="getUnreadCount('agent', agent.id)" class="session-badge">{{ getUnreadCount('agent', agent.id) }}</span>
          </div>
          <el-empty v-if="!filteredAgents.length" description="暂无数字员工" />
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
              <div v-else-if="parsedMessage(message).type === 'html'" class="bubble-html" v-html="parsedMessage(message).content"></div>
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

        <div class="composer" style="position: relative;">
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
          <el-input
            v-model="content"
            placeholder="输入消息内容"
            size="large"
            @input="onContentInput"
            @keydown.enter.prevent="onEnterPress"
            @keydown.down.prevent="onMentionArrow('down')"
            @keydown.up.prevent="onMentionArrow('up')"
          />
          <el-button type="primary" size="large" @click="sendText">发送</el-button>
          <div
            v-if="showMentionPanel"
            class="mention-panel"
          >
            <div
              v-for="member in mentionCandidates"
              :key="member.user_id"
              class="mention-item"
              :class="{ active: mentionCandidates[mentionIndex]?.user_id === member.user_id }"
              @click="chooseMention(member)"
            >
              <el-avatar :size="24">{{ memberAvatar(member) }}</el-avatar>
              <span>{{ memberDisplayName(member) }}</span>
            </div>
            <div v-if="!mentionCandidates.length" class="mention-empty">没有匹配成员</div>
          </div>
          <div v-if="selectedChat.type === 'group' && activeGroupMembers.some((member) => member.member_type === 'agent')" class="member-hint" style="grid-column: 1 / -1;">
            输入 @ 可选择群成员，@数字员工会自动触发回复。
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
          <el-button type="danger" plain size="small" @click="removeFriend">删除好友</el-button>
        </div>

        <div v-else-if="selectedChat.type === 'group'" class="detail-card">
          <el-avatar :size="72">{{ activeGroup?.group_name?.slice(0, 1) || 'G' }}</el-avatar>
          <div class="detail-name">{{ activeGroup?.group_name || '未选择群组' }}</div>
          <div class="muted" style="text-align: center; line-height: 1.8;">点击成员查看资料并可进入私聊</div>
          <el-button size="small" type="primary" style="margin-top: 12px;" @click="showAddMembers = true">添加成员</el-button>
          <div class="member-list">
            <div v-for="member in activeGroupMembers" :key="member.user_id" class="member-item" @click="openMemberProfile(member)">
              <el-avatar :size="32">{{ memberAvatar(member) }}</el-avatar>
              <span>{{ memberDisplayName(member) }}</span>
              <el-button
                v-if="canKickMember(member)"
                size="small"
                type="danger"
                text
                style="margin-left: auto;"
                @click.stop="kickMember(member)"
              >移出群聊</el-button>
            </div>
          </div>
        </div>

        <div v-else class="detail-card">
          <el-avatar :size="72">{{ activeAgent?.agent_name?.slice(0, 1) || 'A' }}</el-avatar>
          <div class="detail-name">{{ activeAgent?.agent_name || '未选择数字员工' }}</div>
        </div>
      </aside>
    </section>
  </div>

  <input ref="imageInput" type="file" accept="image/*" class="hidden-input" @change="onImageUpload" />
  <input ref="fileInput" type="file" class="hidden-input" @change="onFileUpload" />

  <el-dialog v-model="showAddFriend" title="添加好友" width="420px">
    <el-form label-position="top" :model="addFriendForm">
      <el-form-item label="好友 ID"><el-input v-model="addFriendForm.friendId" placeholder="输入对方用户 ID" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddFriend = false">取消</el-button>
      <el-button type="primary" @click="addFriendById">发送申请</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showFriendRequests" title="好友申请" width="520px">
    <div class="request-list">
      <div v-for="request in friendRequests" :key="request.requester_id" class="request-item">
        <div>
          <div style="font-weight: 700;">{{ request.real_name || request.username }}</div>
          <div class="muted" style="font-size: 12px;">ID：{{ request.requester_id }}</div>
        </div>
        <div style="display: flex; gap: 8px;">
          <el-button size="small" type="primary" @click="acceptFriendRequest(request.requester_id)">同意</el-button>
          <el-button size="small" @click="rejectFriendRequest(request.requester_id)">拒绝</el-button>
        </div>
      </div>
      <el-empty v-if="!friendRequests.length" description="暂无好友申请" />
    </div>
  </el-dialog>

  <el-dialog v-model="showCreateGroup" title="创建群组" width="520px" :close-on-click-modal="false">
    <el-form label-position="top" :model="newGroup">
      <el-form-item label="群名称"><el-input v-model="newGroup.name" placeholder="例如：Q2 策略会议群" /></el-form-item>
      <el-form-item label="选择成员">
        <el-select v-model="newGroup.members" multiple filterable placeholder="选择成员" style="width: 100%;">
          <el-option v-for="friend in friends" :key="friend.friend_id" :label="friendDisplayName(friend)" :value="friend.friend_id" />
        </el-select>
      </el-form-item>
      <el-form-item label="绑定数字员工">
        <el-select v-model="newGroup.agentIds" multiple filterable placeholder="选择数字员工" style="width: 100%;">
          <el-option v-for="agent in agents" :key="agent.id" :label="agent.agent_name" :value="agent.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showCreateGroup = false">取消</el-button>
      <el-button type="primary" @click="createGroup">确认创建</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showAddMembers" title="添加群成员" width="520px" :close-on-click-modal="false">
    <el-form label-position="top">
      <el-form-item label="选择成员">
        <el-select v-model="selectedMembers" multiple filterable placeholder="选择成员" style="width: 100%;">
          <el-option v-for="friend in friends" :key="friend.friend_id" :label="friendDisplayName(friend)" :value="friend.friend_id" />
        </el-select>
      </el-form-item>
      <el-form-item label="添加数字员工">
        <el-select v-model="selectedAgentIds" multiple filterable placeholder="选择数字员工" style="width: 100%;">
          <el-option v-for="agent in agents" :key="agent.id" :label="agent.agent_name" :value="agent.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddMembers = false">取消</el-button>
      <el-button type="primary" @click="addMembers">确认添加</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="showMemberProfile" title="成员资料" width="460px">
    <div v-if="memberProfile" class="detail-card" style="padding: 8px; background: transparent;">
      <el-avatar :size="64">{{ (memberProfile.real_name || memberProfile.username || memberProfile.agent_name || 'U').slice(0, 1) }}</el-avatar>
      <div class="detail-name">{{ memberProfile.real_name || memberProfile.username || memberProfile.agent_name }}</div>
      <div class="muted">{{ memberProfile.member_type === 'agent' ? '数字员工' : `用户 ID：${memberProfile.user_id}` }}</div>
      <div style="display: flex; gap: 10px; margin-top: 10px;">
        <el-button v-if="memberProfile.member_type === 'user'" type="primary" @click="startPrivateChatFromProfile">发起私聊</el-button>
        <el-button v-if="memberProfile.member_type === 'agent'" type="primary" @click="startAgentChatFromProfile">私聊</el-button>
      </div>
    </div>
  </el-dialog>

  <el-dialog v-model="callState.visible" :title="callDialogTitle" width="560px" :close-on-click-modal="false">
    <div class="call-box">
      <div class="call-title">{{ callState.tip }}</div>
      <div class="call-video-wrap">
        <video ref="localVideoRef" autoplay playsinline muted class="call-video"></video>
        <video ref="remoteVideoRef" autoplay playsinline class="call-video"></video>
      </div>
      <div class="call-actions">
        <el-button v-if="callState.incoming" type="primary" @click="acceptIncomingCall">接听</el-button>
        <el-button v-if="callState.incoming" @click="rejectIncomingCall">拒绝</el-button>
        <el-button v-if="!callState.incoming && localStream" @click="toggleMute">{{ callMuted ? '取消静音' : '静音' }}</el-button>
        <el-button v-if="!callState.incoming && localStream" @click="toggleCamera">{{ cameraEnabled ? '关闭摄像头' : '开启摄像头' }}</el-button>
        <el-button v-if="!callState.incoming" @click="hangupCall">挂断</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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
const tempContacts = ref({})

const selectedChat = ref({ type: 'friend', id: null })
const emojis = ['😀', '😄', '😉', '🤝', '📌', '🚀', '📈', '✅', '🎯', '💡', '🧠']

const showAddFriend = ref(false)
const showFriendRequests = ref(false)
const showCreateGroup = ref(false)
const showAddMembers = ref(false)
const showMemberProfile = ref(false)

const addFriendForm = ref({ friendId: '' })
const friendRequests = ref([])
const newGroup = ref({ name: '', members: [], agentIds: [] })
const selectedMembers = ref([])
const selectedAgentIds = ref([])
const memberProfile = ref(null)

const imageInput = ref(null)
const fileInput = ref(null)

const mentionKeyword = ref('')
const mentionStart = ref(-1)
const mentionIndex = ref(0)
const callTimeoutTimer = ref(null)

const callState = ref({
  visible: false,
  type: 'voice',
  incoming: false,
  tip: '',
  fromUserId: null,
  offer: null,
})
const callMuted = ref(false)
const cameraEnabled = ref(true)
const localVideoRef = ref(null)
const remoteVideoRef = ref(null)
const localStream = ref(null)
const remoteStream = ref(null)
const peerConnection = ref(null)

const mergedFriends = computed(() => {
  const map = new Map()
  for (const friend of friends.value) map.set(friend.friend_id, friend)
  for (const [id, contact] of Object.entries(tempContacts.value)) {
    const numId = Number(id)
    if (!map.has(numId)) map.set(numId, contact)
  }
  return Array.from(map.values())
})

const filteredFriends = computed(() => {
  const key = keyword.value.trim()
  if (!key) return mergedFriends.value
  return mergedFriends.value.filter((friend) => friendDisplayName(friend).includes(key))
})

const filteredGroups = computed(() => {
  const key = keyword.value.trim()
  if (!key) return groups.value
  return groups.value.filter((group) => group.group_name.includes(key))
})

const filteredAgents = computed(() => {
  const key = keyword.value.trim()
  if (!key) return agents.value
  return agents.value.filter((agent) => (agent.agent_name || '').includes(key))
})

const totalSessions = computed(() => mergedFriends.value.length + groups.value.length + agents.value.length)

const activeFriend = computed(() => mergedFriends.value.find((friend) => friend.friend_id === selectedChat.value.id) || null)
const activeGroup = computed(() => groups.value.find((group) => group.id === selectedChat.value.id) || null)
const activeAgent = computed(() => agents.value.find((agent) => agent.id === selectedChat.value.id) || null)
const activeGroupMembers = computed(() => groupMembers.value[selectedChat.value.id] || [])
const isGroupOwner = computed(() => activeGroup.value?.owner_id === currentUserId.value)

const activeTitle = computed(() => {
  if (selectedChat.value.type === 'friend') return activeFriendName.value || '请选择好友'
  if (selectedChat.value.type === 'group') return activeGroup.value?.group_name || '请选择群组'
  return activeAgent.value?.agent_name || '请选择数字员工'
})

const activeSubtitle = computed(() => {
  if (selectedChat.value.type === 'friend') return activeFriend.value?.username || '单人会话'
  if (selectedChat.value.type === 'group') return `${activeGroupMembers.value.length} 位成员 · 群聊会话`
  return '数字员工私聊'
})

const sideTitle = computed(() => {
  if (selectedChat.value.type === 'friend') return '好友资料'
  if (selectedChat.value.type === 'group') return '群组详情'
  return '数字员工详情'
})

const sideSubtitle = computed(() => {
  if (selectedChat.value.type === 'friend') return '单人沟通'
  if (selectedChat.value.type === 'group') return '成员管理'
  return 'AI 协作'
})

const activeMessages = computed(() => {
  if (!selectedChat.value.id) return []
  const key = `${selectedChat.value.type}:${selectedChat.value.id}`
  return messageCache.value[key] || []
})

const activeFriendName = computed(() => friendDisplayName(activeFriend.value || {}))

const mentionCandidates = computed(() => {
  if (selectedChat.value.type !== 'group') return []
  const key = mentionKeyword.value.trim().toLowerCase()
  return activeGroupMembers.value.filter((member) => {
    const name = memberDisplayName(member)
    return key ? name.toLowerCase().includes(key) : true
  })
})

const showMentionPanel = computed(() => selectedChat.value.type === 'group' && mentionStart.value >= 0)

const callDialogTitle = computed(() => (callState.value.type === 'voice' ? '语音通话' : '视频通话'))

async function loadFriends() {
  const res = await imApi.friends()
  if (res.code === 0) friends.value = res.data || []
}

async function loadFriendRequests() {
  const res = await imApi.friendRequests()
  if (res.code === 0) friendRequests.value = res.data || []
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
  if (selectedChat.value.type === 'agent') {
    const key = `agent:${selectedChat.value.id}`
    unreadCounts.value = { ...unreadCounts.value, [key]: 0 }
    await scrollToBottom()
    return
  }
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
  hideMentionPanel()
  loadMessages()
}

function selectGroup(id) {
  selectedChat.value = { type: 'group', id }
  activeTab.value = 'groups'
  hideMentionPanel()
  loadMessages()
  loadGroupMembers(id)
}

function selectAgent(id) {
  selectedChat.value = { type: 'agent', id }
  activeTab.value = 'agents'
  hideMentionPanel()
  loadMessages()
}

function onContentInput(value) {
  if (selectedChat.value.type !== 'group') {
    hideMentionPanel()
    return
  }
  const text = String(value || '')
  const marker = text.match(/@([^\s@]*)$/)
  if (!marker || marker.index == null) {
    hideMentionPanel()
    return
  }
  mentionStart.value = marker.index
  mentionKeyword.value = marker[1] || ''
}

function chooseMention(member) {
  const text = content.value || ''
  if (mentionStart.value < 0) return
  const prefix = text.slice(0, mentionStart.value)
  const suffix = text.slice((text.match(/@([^\s@]*)$/) || [''])[0].length + mentionStart.value)
  const replaced = `${prefix}@${memberDisplayName(member)} ${suffix}`.replace(/\s+/g, ' ').trimStart()
  content.value = replaced
  hideMentionPanel()
}

function hideMentionPanel() {
  mentionStart.value = -1
  mentionKeyword.value = ''
  mentionIndex.value = 0
}

function onEnterPress() {
  if (showMentionPanel.value && mentionCandidates.value.length) {
    chooseMention(mentionCandidates.value[Math.min(mentionIndex.value, mentionCandidates.value.length - 1)])
    return
  }
  sendText()
}

function onMentionArrow(direction) {
  if (!showMentionPanel.value || !mentionCandidates.value.length) return
  const max = mentionCandidates.value.length - 1
  if (direction === 'down') mentionIndex.value = mentionIndex.value >= max ? 0 : mentionIndex.value + 1
  if (direction === 'up') mentionIndex.value = mentionIndex.value <= 0 ? max : mentionIndex.value - 1
}

async function sendText() {
  if (!selectedChat.value.id || !content.value.trim()) return
  const text = content.value.trim()
  content.value = ''
  hideMentionPanel()
  try {
    await sendMessage({ type: 'text', content: text })
  } catch {
    content.value = text
  }
}

async function sendEmoji(emoji) {
  await sendMessage({ type: 'emoji', content: emoji })
}

async function sendMessage(payload) {
  if (!selectedChat.value.id) return
  const message = buildContent(payload)

  if (selectedChat.value.type === 'agent') {
    const key = `agent:${selectedChat.value.id}`
    const now = new Date().toISOString()
    const userMessage = {
      id: `local-user-${Date.now()}`,
      chat_type: 1,
      sender_id: currentUserId.value,
      receiver_id: selectedChat.value.id,
      group_id: null,
      content: message.content,
      msg_type: 1,
      created_at: now,
      sender_name: currentUserName.value,
    }
    messageCache.value[key] = [...(messageCache.value[key] || []), userMessage]
    await scrollToBottom()
    try {
      const res = await agentApi.chat({ agent_id: selectedChat.value.id, message: payload.content || '' })
      if (res.code === 0) {
        const replyPayload = res.data?.reply_html
          ? { type: 'html', content: res.data.reply_html }
          : { type: 'text', content: res.data?.reply || '' }
        const replyContent = buildContent(replyPayload)
        const replyMessage = {
          id: `local-agent-${Date.now()}`,
          chat_type: 1,
          sender_id: -selectedChat.value.id,
          receiver_id: currentUserId.value,
          group_id: null,
          content: replyContent.content,
          msg_type: replyContent.msg_type,
          created_at: new Date().toISOString(),
          sender_name: activeAgent.value?.agent_name || '数字员工',
        }
        messageCache.value[key] = [...(messageCache.value[key] || []), replyMessage]
        await scrollToBottom()
      }
    } catch (e) {
      ElMessage.error(String(e))
    }
    return
  }

  const data = {
    chat_type: selectedChat.value.type === 'friend' ? 1 : 2,
    receiver_id: selectedChat.value.type === 'friend' ? selectedChat.value.id : undefined,
    group_id: selectedChat.value.type === 'group' ? selectedChat.value.id : undefined,
    content: message.content,
    msg_type: message.msg_type,
  }

  const res = await imApi.send(data)
  if (res.code === 0 && res.data) {
    const saved = { ...res.data, sender_name: currentUserName.value }
    insertMessage(saved)
    await scrollToBottom()
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
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小需小于 10MB')
    event.target.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = async () => {
    const payload = {
      type: 'image',
      fileName: file.name,
      fileSize: formatSize(file.size),
      url: String(reader.result || ''),
    }
    await sendMessage(payload)
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function onFileUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.warning('文件大小需小于 20MB')
    event.target.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = async () => {
    const payload = {
      type: 'file',
      fileName: file.name,
      fileSize: formatSize(file.size),
      url: String(reader.result || ''),
    }
    await sendMessage(payload)
  }
  reader.readAsDataURL(file)
  event.target.value = ''
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
    ElMessage.success('好友申请已发送')
  } catch (e) {
    ElMessage.error(String(e))
  }
}

async function acceptFriendRequest(requesterId) {
  await imApi.acceptFriendRequest(requesterId)
  ElMessage.success('已同意好友申请')
  await Promise.all([loadFriendRequests(), loadFriends()])
}

async function rejectFriendRequest(requesterId) {
  await imApi.rejectFriendRequest(requesterId)
  ElMessage.success('已拒绝好友申请')
  await loadFriendRequests()
}

async function removeFriend() {
  if (selectedChat.value.type !== 'friend' || !selectedChat.value.id) return
  await ElMessageBox.confirm('确认删除该好友？', '提示', { type: 'warning' })
  await imApi.deleteFriend(selectedChat.value.id)
  ElMessage.success('已删除好友')
  await loadFriends()
  selectedChat.value = { type: 'friend', id: null }
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
  await imApi.addGroupMembers(activeGroup.value.id, {
    member_ids: selectedMembers.value,
    agent_ids: selectedAgentIds.value,
  })
  selectedMembers.value = []
  selectedAgentIds.value = []
  showAddMembers.value = false
  await loadGroupMembers(activeGroup.value.id)
}

function openMemberProfile(member) {
  if (member.member_type === 'agent') {
    memberProfile.value = {
      user_id: member.user_id,
      agent_id: member.agent_id,
      member_type: 'agent',
      agent_name: member.agent_name,
    }
    showMemberProfile.value = true
    return
  }
  imApi.userProfile(member.user_id).then((res) => {
    if (res.code === 0) {
      memberProfile.value = {
        ...res.data,
        member_type: 'user',
      }
      showMemberProfile.value = true
    }
  })
}

function startPrivateChatFromProfile() {
  if (!memberProfile.value || memberProfile.value.member_type !== 'user') return
  const id = memberProfile.value.user_id
  tempContacts.value = {
    ...tempContacts.value,
    [id]: {
      friend_id: id,
      username: memberProfile.value.username,
      real_name: memberProfile.value.real_name,
      status: memberProfile.value.status,
    },
  }
  showMemberProfile.value = false
  selectFriend(id)
}

function startAgentChatFromProfile() {
  if (!memberProfile.value || memberProfile.value.member_type !== 'agent') return
  const aid = Number(memberProfile.value.agent_id)
  if (!aid) return
  showMemberProfile.value = false
  selectAgent(aid)
}

function canKickMember(member) {
  return selectedChat.value.type === 'group' && isGroupOwner.value && member.user_id !== currentUserId.value
}

async function kickMember(member) {
  if (!activeGroup.value) return
  await ElMessageBox.confirm(`确认将 ${memberDisplayName(member)} 移出群聊？`, '提示', { type: 'warning' })
  await imApi.removeGroupMember(activeGroup.value.id, member.user_id)
  ElMessage.success('已移出群聊')
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
  const friend = mergedFriends.value.find((f) => f.friend_id === message.sender_id)
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
    return new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
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
      if (payload.type?.startsWith('call_')) handleCallSignal(payload)
      if (payload.type === 'friend_request') handleFriendRequestNotify(payload.data)
      if (payload.type === 'friend_added') handleFriendAdded(payload.data)
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

function sendCallSignal(type, toUserId, payload = null) {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    ElMessage.warning('通话信令未连接，请稍后重试')
    return
  }
  ws.value.send(JSON.stringify({ type, to_user_id: toUserId, payload }))
}

function playNotifyTone() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = ctx.createOscillator()
    const gain = ctx.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.setValueAtTime(880, ctx.currentTime)
    gain.gain.setValueAtTime(0.06, ctx.currentTime)
    oscillator.connect(gain)
    gain.connect(ctx.destination)
    oscillator.start()
    oscillator.stop(ctx.currentTime + 0.12)
  } catch {
    // ignore audio init failures
  }
}

function handleFriendRequestNotify(data) {
  if (!data?.requester_id) return
  const exists = friendRequests.value.some((item) => item.requester_id === data.requester_id)
  if (exists) return
  friendRequests.value = [
    {
      requester_id: data.requester_id,
      username: data.username,
      real_name: data.real_name,
      created_at: new Date().toISOString(),
    },
    ...friendRequests.value,
  ]
  playNotifyTone()
  ElMessage.info(`${data.real_name || data.username || '有新用户'} 发送了好友申请`)
}

function upsertFriend(friend) {
  if (!friend?.friend_id) return
  const next = friends.value.filter((item) => item.friend_id !== friend.friend_id)
  next.unshift(friend)
  friends.value = next
}

function handleFriendAdded(data) {
  if (!data?.friend_id) return
  upsertFriend({
    friend_id: data.friend_id,
    username: data.username,
    real_name: data.real_name,
    status: data.status,
  })
  playNotifyTone()
  ElMessage.success(`${data.real_name || data.username || '新好友'} 已添加到好友列表`)
}

function startRingingTimer() {
  stopRingingTimer()
  callTimeoutTimer.value = setTimeout(() => {
    if (!callState.value.visible || !callState.value.fromUserId) return
    ElMessage.warning('响铃超时，通话已自动挂断')
    sendCallSignal('call_reject', callState.value.fromUserId, { reason: 'timeout' })
    hangupCall(false)
  }, 30000)
}

function stopRingingTimer() {
  if (callTimeoutTimer.value) {
    clearTimeout(callTimeoutTimer.value)
    callTimeoutTimer.value = null
  }
}

function syncTrackStates() {
  if (!localStream.value) return
  const audioTrack = localStream.value.getAudioTracks()[0]
  const videoTrack = localStream.value.getVideoTracks()[0]
  if (audioTrack) audioTrack.enabled = !callMuted.value
  if (videoTrack) videoTrack.enabled = cameraEnabled.value
}

function toggleMute() {
  callMuted.value = !callMuted.value
  syncTrackStates()
}

function toggleCamera() {
  cameraEnabled.value = !cameraEnabled.value
  syncTrackStates()
}

async function openCall(type) {
  if (selectedChat.value.type !== 'friend' || !selectedChat.value.id) return
  callMuted.value = false
  cameraEnabled.value = type === 'video'
  callState.value = {
    visible: true,
    type,
    incoming: false,
    tip: `正在呼叫${type === 'voice' ? '语音' : '视频'}...`,
    fromUserId: selectedChat.value.id,
    offer: null,
  }
  await setupPeerConnection(selectedChat.value.id, type)
  const offer = await peerConnection.value.createOffer()
  await peerConnection.value.setLocalDescription(offer)
  sendCallSignal('call_offer', selectedChat.value.id, {
    sdp: offer,
    call_type: type,
  })
  startRingingTimer()
  sendMessage({ type: 'call', content: `发起${type === 'voice' ? '语音' : '视频'}通话` })
}

async function setupPeerConnection(targetUserId, type) {
  await closeMedia()
  const media = await navigator.mediaDevices.getUserMedia({
    audio: true,
    video: type === 'video',
  })
  localStream.value = media
  remoteStream.value = new MediaStream()
  if (localVideoRef.value) localVideoRef.value.srcObject = localStream.value
  if (remoteVideoRef.value) remoteVideoRef.value.srcObject = remoteStream.value
  syncTrackStates()

  const pc = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
  })
  peerConnection.value = pc

  localStream.value.getTracks().forEach((track) => pc.addTrack(track, localStream.value))
  pc.ontrack = (event) => {
    for (const track of event.streams[0].getTracks()) remoteStream.value.addTrack(track)
  }
  pc.onicecandidate = (event) => {
    if (event.candidate) {
      sendCallSignal('call_ice', targetUserId, { candidate: event.candidate })
    }
  }
  pc.onconnectionstatechange = () => {
    if (['failed', 'disconnected', 'closed'].includes(pc.connectionState)) {
      hangupCall(false)
    }
  }
}

async function handleCallSignal(payload) {
  const fromUserId = payload.from_user_id
  if (!fromUserId) return

  if (payload.type === 'call_offer') {
    callMuted.value = false
    cameraEnabled.value = payload.payload?.call_type === 'video'
    callState.value = {
      visible: true,
      type: payload.payload?.call_type || 'voice',
      incoming: true,
      tip: `${resolveUserName(fromUserId)} 邀请你${payload.payload?.call_type === 'video' ? '视频' : '语音'}通话`,
      fromUserId,
      offer: payload.payload?.sdp || null,
    }
    playNotifyTone()
    startRingingTimer()
    return
  }

  if (payload.type === 'call_answer' && peerConnection.value) {
    stopRingingTimer()
    await peerConnection.value.setRemoteDescription(new RTCSessionDescription(payload.payload?.sdp))
    callState.value.tip = '通话中'
    return
  }

  if (payload.type === 'call_ice' && peerConnection.value && payload.payload?.candidate) {
    try {
      await peerConnection.value.addIceCandidate(new RTCIceCandidate(payload.payload.candidate))
    } catch {
      // ignore invalid candidate
    }
    return
  }

  if (payload.type === 'call_reject') {
    stopRingingTimer()
    ElMessage.warning(`${resolveUserName(fromUserId)} 拒绝了通话`)
    hangupCall(false)
    return
  }

  if (payload.type === 'call_hangup') {
    stopRingingTimer()
    ElMessage.info(`${resolveUserName(fromUserId)} 已结束通话`)
    hangupCall(false)
  }
}

async function acceptIncomingCall() {
  if (!callState.value.fromUserId || !callState.value.offer) return
  stopRingingTimer()
  await setupPeerConnection(callState.value.fromUserId, callState.value.type)
  await peerConnection.value.setRemoteDescription(new RTCSessionDescription(callState.value.offer))
  const answer = await peerConnection.value.createAnswer()
  await peerConnection.value.setLocalDescription(answer)
  sendCallSignal('call_answer', callState.value.fromUserId, { sdp: answer })
  callState.value.incoming = false
  callState.value.tip = '通话中'
}

function rejectIncomingCall() {
  if (callState.value.fromUserId) {
    sendCallSignal('call_reject', callState.value.fromUserId)
  }
  stopRingingTimer()
  hangupCall(false)
}

function hangupCall(notify = true) {
  stopRingingTimer()
  if (notify && callState.value.fromUserId) {
    sendCallSignal('call_hangup', callState.value.fromUserId)
  }
  closeMedia()
  callState.value = {
    visible: false,
    type: 'voice',
    incoming: false,
    tip: '',
    fromUserId: null,
    offer: null,
  }
}

async function closeMedia() {
  if (peerConnection.value) {
    peerConnection.value.ontrack = null
    peerConnection.value.onicecandidate = null
    peerConnection.value.close()
    peerConnection.value = null
  }
  if (localStream.value) {
    localStream.value.getTracks().forEach((track) => track.stop())
    localStream.value = null
  }
  if (remoteStream.value) {
    remoteStream.value.getTracks().forEach((track) => track.stop())
    remoteStream.value = null
  }
  if (localVideoRef.value) localVideoRef.value.srcObject = null
  if (remoteVideoRef.value) remoteVideoRef.value.srcObject = null
  callMuted.value = false
  cameraEnabled.value = true
}

function resolveUserName(userId) {
  const friend = mergedFriends.value.find((f) => f.friend_id === userId)
  return friend ? friendDisplayName(friend) : `用户${userId}`
}

onMounted(async () => {
  await Promise.all([loadFriends(), loadFriendRequests(), loadGroups(), loadAgents()])
  if (mergedFriends.value.length) selectFriend(mergedFriends.value[0].friend_id)
  else if (groups.value.length) selectGroup(groups.value[0].id)
  else if (agents.value.length) selectAgent(agents.value[0].id)
  connectWs()
})

onBeforeUnmount(() => {
  if (ws.value) ws.value.close()
  if (reconnectTimer.value) clearTimeout(reconnectTimer.value)
  stopRingingTimer()
  closeMedia()
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
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.friend-req-badge :deep(.el-badge__content) {
  right: 6px;
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

.bubble-html {
  display: grid;
  gap: 10px;
}

:deep(.skill-card) {
  border-radius: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: #fff;
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

:deep(.skill-title) {
  font-weight: 800;
  font-size: 15px;
}

:deep(.skill-subtitle) {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

:deep(.skill-subtitle.success) {
  color: #16a34a;
}

:deep(.skill-subtitle.failure) {
  color: #ef4444;
}

:deep(.skill-body) {
  margin: 10px 0 0;
  background: rgba(15, 23, 42, 0.04);
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(.skill-meta) {
  margin-top: 10px;
  font-size: 11px;
  color: var(--muted);
}

:deep(.weather-card) {
  position: relative;
  overflow: hidden;
  color: #0f172a;
}

:deep(.weather-card .weather-backdrop) {
  position: absolute;
  inset: 0;
  opacity: 0.9;
  background: radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.8), transparent 55%);
  animation: weatherGlow 6s ease-in-out infinite;
}

:deep(.weather-card .weather-content) {
  position: relative;
  display: grid;
  gap: 8px;
}

:deep(.weather-city) {
  font-size: 18px;
  font-weight: 800;
}

:deep(.weather-condition) {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

:deep(.weather-detail) {
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
}

:deep(.weather-meta) {
  font-size: 11px;
  color: var(--muted);
}

:deep(.theme-sunny) {
  background: linear-gradient(135deg, #fef9c3, #fde68a);
}

:deep(.theme-cloudy) {
  background: linear-gradient(135deg, #e2e8f0, #cbd5f5);
}

:deep(.theme-rainy) {
  background: linear-gradient(135deg, #bfdbfe, #93c5fd);
}

:deep(.theme-storm) {
  background: linear-gradient(135deg, #c7d2fe, #818cf8);
}

:deep(.theme-snowy) {
  background: linear-gradient(135deg, #f8fafc, #e2e8f0);
}

:deep(.theme-foggy) {
  background: linear-gradient(135deg, #e5e7eb, #cbd5e1);
}

:deep(.theme-clear) {
  background: linear-gradient(135deg, #dbeafe, #e0f2fe);
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

@keyframes weatherGlow {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.12); opacity: 0.9; }
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

.mention-panel {
  position: absolute;
  bottom: 74px;
  left: 110px;
  right: 90px;
  max-height: 220px;
  overflow-y: auto;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: #fff;
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.16);
  z-index: 20;
}

.mention-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
}

.mention-item:hover {
  background: rgba(29, 78, 216, 0.08);
}

.mention-item.active {
  background: rgba(29, 78, 216, 0.12);
}

.mention-empty {
  padding: 12px;
  color: var(--muted);
  font-size: 13px;
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
  cursor: pointer;
}

.request-list {
  display: grid;
  gap: 12px;
}

.request-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 10px 12px;
}

.hidden-input {
  display: none;
}

.call-box {
  display: grid;
  gap: 12px;
}

.call-title {
  font-weight: 800;
  text-align: center;
}

.call-video-wrap {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.call-video {
  width: 100%;
  height: 180px;
  border-radius: 12px;
  object-fit: cover;
  background: #000;
}

.call-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
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

  .mention-panel {
    left: 20px;
    right: 20px;
    bottom: 120px;
  }

  .call-video-wrap {
    grid-template-columns: 1fr;
  }
}
</style>
