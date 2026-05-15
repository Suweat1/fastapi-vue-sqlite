<template>
  <div class="app-shell">
    <header class="topbar">
      <router-link to="/" class="brand">
        <span class="brand__text">
          <strong>校园集市</strong>
        </span>
      </router-link>

      <nav class="nav-links">
        <router-link to="/" class="nav-link">浏览</router-link>
        <template v-if="auth.isLoggedIn">
          <span class="nav-separator"></span>
          <router-link to="/items/new" class="nav-link">发布</router-link>
          <span class="nav-separator"></span>
          <router-link to="/me/items" class="nav-link">我的发布</router-link>
          <router-link to="/me/favorites" class="nav-link">我的收藏</router-link>
          <router-link to="/me/orders" class="nav-link">我的订单</router-link>
          <span class="nav-separator"></span>
          <router-link to="/me/messages" class="nav-link nav-link--badge">
            私聊
            <span v-if="unreadCount > 0" class="nav-link__badge">{{ badgeLabel }}</span>
          </router-link>
          <router-link to="/me/notifications" class="nav-link nav-link--badge">
            提醒
            <span v-if="unreadCount > 0" class="nav-link__badge nav-link__badge--accent">{{ badgeLabel }}</span>
          </router-link>
          <template v-if="auth.isAdmin">
            <span class="nav-separator"></span>
            <router-link to="/admin" class="nav-link">管理</router-link>
          </template>
        </template>
      </nav>

      <div class="topbar__actions">
        <button class="theme-toggle" type="button" :title="isDark ? '切换亮色' : '切换暗色'" @click="toggleTheme">
          <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
        <template v-if="auth.isLoggedIn">
          <div class="user-chip">
            <span class="user-chip__name">{{ auth.user?.nickname || auth.user?.username }}</span>
          </div>
          <button class="btn btn--ghost btn--sm" type="button" @click="logout">退出</button>
        </template>
        <template v-else>
          <router-link class="btn btn--ghost btn--sm" to="/login">登录</router-link>
          <router-link class="btn btn--primary btn--sm" to="/register">注册</router-link>
        </template>
      </div>

      <button class="hamburger" :class="{ 'is-open': mobileMenuOpen }" type="button" @click="mobileMenuOpen = !mobileMenuOpen">
        <span></span>
        <span></span>
        <span></span>
      </button>
    </header>

    <div class="mobile-menu" :class="{ 'is-open': mobileMenuOpen }" @click="mobileMenuOpen = false">
      <router-link to="/" class="nav-link">浏览</router-link>
      <template v-if="auth.isLoggedIn">
        <router-link to="/items/new" class="nav-link">发布物品</router-link>
        <router-link to="/me/items" class="nav-link">我的发布</router-link>
        <router-link to="/me/favorites" class="nav-link">我的收藏</router-link>
        <router-link to="/me/orders" class="nav-link">我的订单</router-link>
        <router-link to="/me/messages" class="nav-link">私聊消息</router-link>
        <router-link to="/me/notifications" class="nav-link">消息提醒</router-link>
        <router-link v-if="auth.isAdmin" to="/admin" class="nav-link">管理后台</router-link>
      </template>
      <template v-else>
        <router-link to="/login" class="nav-link">登录</router-link>
        <router-link to="/register" class="nav-link">注册</router-link>
      </template>
    </div>

    <div v-if="toasts.length" class="realtime-toast-stack" aria-live="polite" aria-atomic="true">
      <article
        v-for="toast in toasts"
        :key="toast.id"
        class="realtime-toast"
        :class="`realtime-toast--${toast.kind}`"
      >
        <div class="realtime-toast__head">
          <strong>{{ toast.title }}</strong>
          <button class="realtime-toast__close" type="button" @click="removeToast(toast.id)">×</button>
        </div>
        <p>{{ toast.message }}</p>
      </article>
    </div>

    <main class="page-wrap">
      <router-view />
    </main>

    <footer class="footer">&copy; 2026 校园集市</footer>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getUnreadNotificationCountApi } from './api/notifications'
import { useAuthStore } from './stores/auth'
import {
  NOTIFICATION_CHANGE_EVENT,
  REALTIME_CONVERSATION_EVENT,
  REALTIME_MESSAGE_EVENT,
  REALTIME_NOTIFICATION_EVENT,
  emitRealtimeConversation,
  emitRealtimeMessage,
  emitRealtimeNotification,
} from './utils/events'
import { RealtimeClient } from './utils/realtime'

const auth = useAuthStore()
const router = useRouter()
const unreadCount = ref(0)
const toasts = ref([])
const mobileMenuOpen = ref(false)
const isDark = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const initTheme = () => {
  const saved = localStorage.getItem('theme')
  if (saved === 'dark') {
    isDark.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  } else {
    isDark.value = false
    document.documentElement.setAttribute('data-theme', 'light')
  }
}
let timerId = null
let toastSeed = 0
let realtimeClient = null
const toastTimers = new Map()

const badgeLabel = computed(() => (unreadCount.value > 99 ? '99+' : `${unreadCount.value}`))

// 路由切换时关闭移动端菜单
router.afterEach(() => {
  mobileMenuOpen.value = false
})

const refreshUnreadCount = async () => {
  if (!auth.isLoggedIn) {
    unreadCount.value = 0
    return
  }
  try {
    const data = await getUnreadNotificationCountApi()
    unreadCount.value = data.unread_count || 0
  } catch {
    unreadCount.value = 0
  }
}

const handleNotificationChange = () => {
  void refreshUnreadCount()
}

const removeToast = (toastId) => {
  toasts.value = toasts.value.filter((toast) => toast.id !== toastId)
  const timerId = toastTimers.get(toastId)
  if (timerId) {
    window.clearTimeout(timerId)
    toastTimers.delete(toastId)
  }
}

const pushToast = (kind, title, message) => {
  if (typeof window === 'undefined') return
  const id = ++toastSeed
  toasts.value = [...toasts.value, { id, kind, title, message }]
  const timerId = window.setTimeout(() => {
    removeToast(id)
  }, 4800)
  toastTimers.set(id, timerId)
}

const clearToasts = () => {
  toastTimers.forEach((timerId) => window.clearTimeout(timerId))
  toastTimers.clear()
  toasts.value = []
}

const handleRealtimePayload = (payload) => {
  if (!payload || typeof payload !== 'object') return

  if (payload.type === 'message.new') {
    emitRealtimeMessage(payload)
    void refreshUnreadCount()
    if (payload.sender_id !== auth.user?.id && router.currentRoute.value.name !== 'messages') {
      const sender = payload.message?.sender || {}
      pushToast(
        'message',
        `来自 ${sender.nickname || sender.username || '新消息'} 的消息`,
        payload.message?.content || '你收到了一条新消息',
      )
    }
    return
  }

  if (payload.type === 'notification.new') {
    emitRealtimeNotification(payload)
    void refreshUnreadCount()
    const notification = payload.notification || {}
    if (notification.kind !== 'message') {
      pushToast('notification', notification.title || '消息提醒', notification.content || '你有一条新的系统提醒')
    }
    return
  }

  if (payload.type === 'conversation.updated') {
    emitRealtimeConversation(payload)
    void refreshUnreadCount()
    return
  }

  if (payload.type === 'notification.updated') {
    emitRealtimeNotification(payload)
    void refreshUnreadCount()
  }
}

const connectRealtime = (token) => {
  if (realtimeClient) {
    realtimeClient.disconnect()
    realtimeClient = null
  }
  if (!token) return
  realtimeClient = new RealtimeClient({
    onMessage: handleRealtimePayload,
  })
  realtimeClient.connect(token)
}

const logout = () => {
  auth.logout()
  unreadCount.value = 0
  if (realtimeClient) {
    realtimeClient.disconnect()
    realtimeClient = null
  }
  clearToasts()
  mobileMenuOpen.value = false
  router.push('/')
}

watch(
  () => [auth.ready, auth.token],
  ([ready, token]) => {
    if (!ready) {
      return
    }
    if (!token) {
      unreadCount.value = 0
      if (realtimeClient) {
        realtimeClient.disconnect()
        realtimeClient = null
      }
      clearToasts()
      return
    }
    connectRealtime(token)
    void refreshUnreadCount()
  },
  { immediate: true },
)

onMounted(async () => {
  initTheme()
  if (!auth.ready) {
    await auth.bootstrap()
  }
  await refreshUnreadCount()
  timerId = window.setInterval(refreshUnreadCount, 30000)
  window.addEventListener(NOTIFICATION_CHANGE_EVENT, handleNotificationChange)
})

onBeforeUnmount(() => {
  if (timerId) {
    window.clearInterval(timerId)
  }
  window.removeEventListener(NOTIFICATION_CHANGE_EVENT, handleNotificationChange)
  if (realtimeClient) {
    realtimeClient.disconnect()
    realtimeClient = null
  }
  clearToasts()
})
</script>
