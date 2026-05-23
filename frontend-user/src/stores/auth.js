import { defineStore } from 'pinia'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: sessionStorage.getItem('token') || '',
    user: JSON.parse(sessionStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
  },
  actions: {
    async login(username, password) {
      const res = await authApi.login({ username, password })
      if (res.code !== 0) throw new Error(res.message)
      this.token = res.data.access_token
      this.user = res.data
      sessionStorage.setItem('token', this.token)
      sessionStorage.setItem('user', JSON.stringify(res.data))
    },
    async register(payload) {
      const res = await authApi.register(payload)
      if (res.code !== 0) throw new Error(res.message)
      return res.data
    },
    logout() {
      this.token = ''
      this.user = null
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')
    },
  },
})
