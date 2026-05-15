import { defineStore } from 'pinia'
import { getMeApi, loginApi, registerApi, updateMeApi } from '../api/auth.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('cm-token') || '',
    user: null,
    ready: false,
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    isAdmin: (state) => state.user?.role === 'admin',
  },
  actions: {
    setToken(token) {
      this.token = token || ''
      if (this.token) {
        localStorage.setItem('cm-token', this.token)
      } else {
        localStorage.removeItem('cm-token')
      }
    },
    async bootstrap() {
      if (this.token && !this.user) {
        try {
          this.user = await getMeApi()
        } catch {
          this.logout()
        }
      }
      this.ready = true
    },
    async login(payload) {
      const { access_token } = await loginApi(payload)
      this.setToken(access_token)
      this.user = await getMeApi()
    },
    async register(payload) {
      const { access_token } = await registerApi(payload)
      this.setToken(access_token)
      this.user = await getMeApi()
    },
    async refreshMe() {
      this.user = await getMeApi()
    },
    async updateProfile(payload) {
      this.user = await updateMeApi(payload)
    },
    logout() {
      this.user = null
      this.setToken('')
    },
  },
})
