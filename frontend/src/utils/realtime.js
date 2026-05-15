const DEFAULT_WS_PATH = '/api/ws/updates'

const getWsBaseUrl = () => {
  if (typeof window === 'undefined') {
    return 'http://localhost'
  }
  return import.meta.env?.VITE_WS_BASE_URL || window.location.origin
}

export const buildRealtimeUrl = (token) => {
  const url = new URL(DEFAULT_WS_PATH, getWsBaseUrl())
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.searchParams.set('token', token)
  return url.toString()
}

export class RealtimeClient {
  constructor({ onMessage, onOpen, onClose, onError } = {}) {
    this.onMessage = onMessage
    this.onOpen = onOpen
    this.onClose = onClose
    this.onError = onError
    this.socket = null
    this.token = ''
    this.shouldReconnect = false
    this.reconnectDelay = 1000
    this.reconnectTimer = null
  }

  connect(token) {
    this.token = token || ''
    this.shouldReconnect = Boolean(this.token)
    this.reconnectDelay = 1000
    this._clearReconnectTimer()
    this._open()
  }

  disconnect() {
    this.shouldReconnect = false
    this._clearReconnectTimer()
    if (this.socket) {
      const socket = this.socket
      this.socket = null
      socket.close(1000, 'client disconnect')
    }
  }

  _clearReconnectTimer() {
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  _open() {
    if (!this.token || typeof WebSocket === 'undefined') {
      return
    }

    try {
      const socket = new WebSocket(buildRealtimeUrl(this.token))
      this.socket = socket

      socket.onopen = (event) => {
        this.reconnectDelay = 1000
        this.onOpen?.(event)
      }

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data)
          this.onMessage?.(payload)
        } catch {
          // Ignore malformed payloads so one bad frame does not break the stream.
        }
      }

      socket.onerror = (event) => {
        this.onError?.(event)
      }

      socket.onclose = (event) => {
        if (this.socket === socket) {
          this.socket = null
        }
        this.onClose?.(event)
        if (!this.shouldReconnect || event.code === 1008 || event.code === 4401) {
          return
        }
        this._scheduleReconnect()
      }
    } catch (error) {
      this.onError?.(error)
      this._scheduleReconnect()
    }
  }

  _scheduleReconnect() {
    if (!this.shouldReconnect) {
      return
    }
    this._clearReconnectTimer()
    const delay = this.reconnectDelay
    this.reconnectDelay = Math.min(Math.round(this.reconnectDelay * 1.5), 10000)
    this.reconnectTimer = window.setTimeout(() => {
      this._open()
    }, delay)
  }
}

