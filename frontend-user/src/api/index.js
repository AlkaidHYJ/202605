import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1', timeout: 30000 })

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res.data,
  (err) => Promise.reject(err.response?.data?.message || err.message)
)

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
}

export const nl2sqlApi = {
  query: (data) => api.post('/nl2sql/query', data),
  history: () => api.get('/nl2sql/history'),
}

export const imApi = {
  send: (data) => api.post('/im/messages', data),
  list: (params) => api.get('/im/messages', { params }),
  groups: () => api.get('/im/groups'),
  createGroup: (data) => api.post('/im/groups', data),
  groupMembers: (groupId) => api.get(`/im/groups/${groupId}/members`),
  addGroupMembers: (groupId, data) => api.post(`/im/groups/${groupId}/members`, data),
  removeGroupMember: (groupId, memberUserId) => api.delete(`/im/groups/${groupId}/members/${memberUserId}`),
  friends: () => api.get('/im/friends'),
  addFriend: (data) => api.post('/im/friends', data),
  friendRequests: () => api.get('/im/friends/requests'),
  acceptFriendRequest: (requesterId) => api.post(`/im/friends/requests/${requesterId}/accept`),
  rejectFriendRequest: (requesterId) => api.post(`/im/friends/requests/${requesterId}/reject`),
  deleteFriend: (friendId) => api.delete(`/im/friends/${friendId}`),
  userProfile: (userId) => api.get(`/im/users/${userId}`),
}

export const dashboardApi = {
  list: () => api.get('/dashboards'),
  get: (id) => api.get(`/dashboards/${id}`),
}

export const crawlerApi = {
  publicTasks: () => api.get('/crawler/public-tasks'),
  publicResults: (taskId) => api.get('/crawler/public-results', { params: taskId ? { task_id: taskId } : {} }),
  publicReport: (taskId) => api.get('/crawler/public-results-report', { params: taskId ? { task_id: taskId } : {} }),
}

export const agentApi = {
  list: () => api.get('/agents'),
  chat: (data) => api.post('/agents/chat', data),
}

export default api
