import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1', timeout: 30000 })

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('admin_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use((res) => res.data)

export const authApi = {
  login: (data) => api.post('/auth/login', data),
}

export const adminApi = {
  users: (params) => api.get('/admin/users', { params }),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  depts: () => api.get('/admin/depts'),
  groups: (params) => api.get('/admin/groups', { params }),
  createGroup: (data) => api.post('/admin/groups', data),
  updateGroup: (id, data) => api.put(`/admin/groups/${id}`, data),
  deleteGroup: (id) => api.delete(`/admin/groups/${id}`),
  sendSystemMessage: (groupId, data) => api.post(`/admin/groups/${groupId}/system-message`, data),
  muteGroup: (id) => api.post(`/admin/groups/${id}/mute`),
  dissolveGroup: (id) => api.post(`/admin/groups/${id}/dissolve`),
  groupMembers: (id) => api.get(`/admin/groups/${id}/members`),
  files: (groupId) => api.get(`/admin/groups/${groupId}/files`),
  messages: (params) => api.get('/admin/messages', { params }),
  recall: (data) => api.post('/admin/messages/recall', data),
  sensitiveWords: () => api.get('/admin/sensitive-words'),
  addSensitiveWord: (data) => api.post('/admin/sensitive-words', data),
  models: (params) => api.get('/admin/models', { params }),
  createModel: (data) => api.post('/admin/models', data),
  updateModel: (id, data) => api.put(`/admin/models/${id}`, data),
  deleteModel: (id) => api.delete(`/admin/models/${id}`),
  setDefaultModel: (id) => api.post(`/admin/models/${id}/set-default`),
  testModel: (id, data) => api.post(`/admin/models/${id}/test`, data),
  skills: (params) => api.get('/admin/skills', { params }),
  createSkill: (data) => api.post('/admin/skills', data),
  updateSkill: (id, data) => api.put(`/admin/skills/${id}`, data),
  deleteSkill: (id) => api.delete(`/admin/skills/${id}`),
  runSkill: (id, data) => api.post(`/admin/skills/${id}/run`, data),
  autoGenerateSkill: (data) => api.post('/admin/skills/auto-generate', data),
  agents: (params) => api.get('/admin/agents', { params }),
  createAgent: (data) => api.post('/admin/agents', data),
  updateAgent: (id, data) => api.put(`/admin/agents/${id}`, data),
  deleteAgent: (id) => api.delete(`/admin/agents/${id}`),
  generateAgentPrompt: (data) => api.post('/admin/agents/generate-prompt', data),
}

export const crawlerApi = {
  tasks: () => api.get('/crawler/tasks'),
  createTask: (data) => api.post('/crawler/tasks', data),
  rules: () => api.get('/crawler/cleaning-rules'),
}
