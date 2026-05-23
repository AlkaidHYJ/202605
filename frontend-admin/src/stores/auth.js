import { defineStore } from 'pinia'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: sessionStorage.getItem('admin_token') || '',
    user: JSON.parse(sessionStorage.getItem('admin_user') || 'null'),
  }),
  getters: { isLoggedIn: (s) => !!s.token },
  actions: {
    async login(username, password) {
      const res = await authApi.login({ username, password })
      if (res.code !== 0) throw new Error(res.message)
      if (res.data.is_admin !== 1) throw new Error('需要管理员账号')
      this.token = res.data.access_token
      this.user = res.data
      sessionStorage.setItem('admin_token', this.token)
      sessionStorage.setItem('admin_user', JSON.stringify(res.data))
    },
    logout() {
      this.token = ''
      this.user = null
      sessionStorage.removeItem('admin_token')
      sessionStorage.removeItem('admin_user')
    },
  },
})
