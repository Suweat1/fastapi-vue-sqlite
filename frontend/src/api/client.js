import axios from 'axios'

const VIEW_SESSION_KEY = 'cm-view-session'

const getViewSession = () => {
  if (typeof sessionStorage === 'undefined') {
    return typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`
  }
  const existing = sessionStorage.getItem(VIEW_SESSION_KEY)
  if (existing) return existing

  const next = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`

  sessionStorage.setItem(VIEW_SESSION_KEY, next)
  return next
}

const client = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('cm-token')
  const viewSession = getViewSession()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  config.headers = config.headers || {}
  config.headers['X-View-Session'] = viewSession
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
)

export default client
