<template>
  <div class="page">
    <section class="surface page-panel">
      <div class="section__head">
        <div>
          <h2>消息提醒</h2>
          <p>这里会汇总购买提醒、私聊消息和与订单相关的通知。</p>
        </div>
        <div class="inline-actions">
          <button class="btn btn--ghost" type="button" @click="refreshNotifications" :disabled="loading">
            刷新
          </button>
          <button class="btn btn--primary" type="button" @click="markAllRead" :disabled="loading || unreadCount === 0">
            全部标为已读
          </button>
        </div>
      </div>
    </section>

    <section class="section">
      <div v-if="pageError" class="empty-state surface">{{ pageError }}</div>
      <div v-else-if="loading" class="empty-state surface">正在加载消息提醒...</div>
      <div v-else-if="notifications.length" class="notification-list">
        <article
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-card surface"
          :class="{ 'is-read': notification.is_read }"
        >
          <div class="notification-card__main">
            <div class="notification-card__header">
              <div>
                <div class="notification-card__title-row">
                  <h3>{{ notification.title }}</h3>
                  <span v-if="!notification.is_read" class="notification-card__dot"></span>
                </div>
                <p class="notification-card__time">{{ formatRelativeTime(notification.created_at) }}</p>
              </div>
              <span class="badge" :class="kindBadgeClass(notification.kind)">{{ kindLabel(notification.kind) }}</span>
            </div>

            <p class="notification-card__content">{{ notification.content }}</p>

            <div v-if="notification.item_title" class="notification-card__item">
              <img
                v-if="notification.item_cover_image"
                :src="notification.item_cover_image"
                :alt="notification.item_title"
              />
              <div class="notification-card__item-body">
                <span>关联商品</span>
                <strong>{{ notification.item_title }}</strong>
              </div>
            </div>

            <div class="notification-card__actions">
              <button
                v-if="notification.item_id"
                class="btn btn--ghost btn--sm"
                type="button"
                :disabled="busyId === notification.id"
                @click="openItem(notification)"
              >
                查看商品
              </button>
              <button
                v-if="notification.conversation_id"
                class="btn btn--primary btn--sm"
                type="button"
                :disabled="busyId === notification.id"
                @click="openConversation(notification)"
              >
                去私聊
              </button>
              <button
                v-if="notification.order_id && !notification.conversation_id"
                class="btn btn--primary btn--sm"
                type="button"
                :disabled="busyId === notification.id"
                @click="openOrderConversation(notification)"
              >
                联系对方
              </button>
              <button
                v-if="!notification.is_read"
                class="btn btn--ghost btn--sm"
                type="button"
                :disabled="busyId === notification.id"
                @click="markRead(notification)"
              >
                标为已读
              </button>
            </div>
          </div>
        </article>

        <PaginationBar :page="page" :pages="pages" :total="total" @change="loadNotifications" />
      </div>
      <div v-else class="empty-state surface">暂无消息提醒，系统会在购买成功和收到私聊时自动提醒你。</div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PaginationBar from '../components/PaginationBar.vue'
import {
  listNotificationsApi,
  markNotificationReadApi,
  markAllNotificationsReadApi,
} from '../api/notifications'
import { startConversationFromOrderApi } from '../api/chats'
import { formatRelativeTime } from '../utils/format'
import { getApiErrorMessage } from '../utils/error'
import { emitNotificationChange, REALTIME_NOTIFICATION_EVENT } from '../utils/events'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const notifications = ref([])
const loading = ref(false)
const pageError = ref('')
const page = ref(1)
const pages = ref(1)
const total = ref(0)
const busyId = ref(0)
const realtimeHandlers = []

const unreadCount = computed(() => notifications.value.filter((notification) => !notification.is_read).length)

const kindLabel = (kind) => ({
  message: '私聊消息',
  order: '订单提醒',
  system: '系统通知',
}[kind] || '通知')

const kindBadgeClass = (kind) => ({
  message: 'badge--blue',
  order: 'badge--primary',
  system: 'badge--slate',
}[kind] || 'badge--slate')

const registerRealtimeListeners = () => {
  if (typeof window === 'undefined' || realtimeHandlers.length > 0) {
    return
  }
  const notificationHandler = () => {
    void loadNotifications(page.value)
  }
  realtimeHandlers.push([REALTIME_NOTIFICATION_EVENT, notificationHandler])
  window.addEventListener(REALTIME_NOTIFICATION_EVENT, notificationHandler)
}

const unregisterRealtimeListeners = () => {
  if (typeof window === 'undefined') return
  realtimeHandlers.forEach(([eventName, handler]) => {
    window.removeEventListener(eventName, handler)
  })
  realtimeHandlers.length = 0
}

const loadNotifications = async (targetPage = 1) => {
  loading.value = true
  page.value = targetPage
  pageError.value = ''
  try {
    const data = await listNotificationsApi({
      page: page.value,
      page_size: 12,
    })
    notifications.value = data.items || []
    pages.value = data.pages || 1
    total.value = data.total || 0
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '消息提醒加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const refreshNotifications = async () => {
  await loadNotifications(page.value)
}

const markRead = async (notification) => {
  busyId.value = notification.id
  try {
    await markNotificationReadApi(notification.id)
    notification.is_read = true
    emitNotificationChange()
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '标记已读失败，请稍后重试')
  } finally {
    busyId.value = 0
  }
}

const markAllRead = async () => {
  busyId.value = -1
  try {
    await markAllNotificationsReadApi()
    notifications.value.forEach((notification) => {
      notification.is_read = true
    })
    emitNotificationChange()
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '全部已读失败，请稍后重试')
  } finally {
    busyId.value = 0
  }
}

const openItem = async (notification) => {
  await markRead(notification)
  router.push(`/items/${notification.item_id}`)
}

const openConversation = async (notification) => {
  await markRead(notification)
  router.push({ name: 'messages', query: { conversationId: notification.conversation_id } })
}

const openOrderConversation = async (notification) => {
  busyId.value = notification.id
  try {
    const conversation = await startConversationFromOrderApi(notification.order_id)
    await markRead(notification)
    emitNotificationChange()
    router.push({ name: 'messages', query: { conversationId: conversation.id } })
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '打开订单聊天失败，请稍后重试')
  } finally {
    busyId.value = 0
  }
}

onMounted(async () => {
  if (!auth.ready) {
    await auth.bootstrap()
  }
  registerRealtimeListeners()
  await loadNotifications(1)
})

onBeforeUnmount(() => {
  unregisterRealtimeListeners()
})
</script>
