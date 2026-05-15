<template>
  <div class="page">
    <section class="surface page-panel">
      <div class="section__head">
        <div>
          <h2>私聊消息</h2>
          <p>可以从商品详情页或订单页发起会话，也可以在这里继续沟通。</p>
        </div>
        <button class="btn btn--ghost" type="button" @click="refreshWorkspace" :disabled="loadingConversations || loadingMessages">
          刷新会话
        </button>
      </div>
    </section>

    <section v-if="pageError" class="empty-state surface">{{ pageError }}</section>

    <section v-else class="messages-layout">
      <aside class="conversation-list surface">
        <div class="conversation-list__head">
          <h3>会话列表</h3>
          <span class="badge badge--blue">{{ conversations.length }} 个会话</span>
        </div>

        <div v-if="loadingConversations" class="empty-state" style="padding: 24px 0;">正在加载会话...</div>
        <div v-else-if="conversations.length" class="conversation-stack">
          <button
            v-for="conversation in conversations"
            :key="conversation.id"
            type="button"
            class="conversation-item"
            :class="{ 'is-active': selectedConversationId === conversation.id }"
            @click="openConversation(conversation.id)"
          >
            <div class="conversation-item__header">
              <strong>{{ conversation.other_user.nickname || conversation.other_user.username }}</strong>
              <span v-if="conversation.unread_count > 0" class="conversation-item__badge">{{ conversation.unread_count }}</span>
            </div>
            <div class="conversation-item__meta">
              <span>{{ conversation.item.title }}</span>
              <span>{{ formatRelativeTime(conversation.last_message_at || conversation.updated_at) }}</span>
            </div>
            <p class="conversation-item__preview">{{ conversation.last_message_preview || '暂无消息，点击即可开始聊天' }}</p>
          </button>
        </div>
        <div v-else class="empty-state" style="padding: 24px 0;">暂无私聊记录，先去商品详情页发起对话吧。</div>
      </aside>

      <section v-if="selectedConversation" class="chat-pane surface">
        <div class="chat-pane__header">
          <div>
            <h3>{{ selectedConversation.other_user.nickname || selectedConversation.other_user.username }}</h3>
            <p>
              商品：
              <router-link :to="`/items/${selectedConversation.item.id}`" class="chat-pane__link">
                {{ selectedConversation.item.title }}
              </router-link>
            </p>
          </div>
          <div class="chat-pane__actions">
            <router-link :to="`/items/${selectedConversation.item.id}`" class="btn btn--ghost btn--sm">查看商品</router-link>
          </div>
        </div>

        <div class="chat-pane__summary">
          <span class="badge badge--slate">会话编号 {{ selectedConversation.id }}</span>
          <span class="badge badge--green">未读 {{ selectedConversation.unread_count }}</span>
        </div>

        <div ref="threadRef" class="message-thread">
          <div v-if="loadingMessages" class="empty-state" style="padding: 24px 0;">正在加载消息...</div>
          <div v-else-if="messages.length" class="message-stack">
            <article
              v-for="message in messages"
              :key="message.id"
              class="message-bubble"
              :class="{ 'message-bubble--mine': message.sender.id === auth.user?.id }"
            >
              <div class="message-bubble__meta">
                <strong>{{ message.sender.id === auth.user?.id ? '我' : (message.sender.nickname || message.sender.username) }}</strong>
                <span>{{ formatDate(message.created_at) }}</span>
              </div>
              <p>{{ message.content }}</p>
            </article>
          </div>
          <div v-else class="empty-state" style="padding: 24px 0;">暂无消息，先发送一条内容吧。</div>
        </div>

        <form class="message-form" @submit.prevent="sendMessage">
          <label class="field">
            <span class="field__label">发送消息</span>
            <textarea
              v-model="draft"
              class="field__textarea"
              placeholder="输入你想说的话..."
            ></textarea>
          </label>
          <div class="filters-actions">
            <button class="btn btn--primary" type="submit" :disabled="sending || !draft.trim()">发送消息</button>
            <button class="btn btn--ghost" type="button" @click="refreshCurrentConversation" :disabled="loadingMessages || sending">
              刷新当前会话
            </button>
          </div>
          <p v-if="sendError" class="form-alert form-alert--error">{{ sendError }}</p>
        </form>
      </section>

      <section v-else class="empty-state surface">
        选择一个会话开始聊天，或者先从商品详情页发起私聊。
      </section>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listConversationsApi, getConversationMessagesApi, markConversationReadApi, sendMessageApi } from '../api/chats'
import { formatDate, formatRelativeTime } from '../utils/format'
import { getApiErrorMessage } from '../utils/error'
import { emitNotificationChange, REALTIME_CONVERSATION_EVENT, REALTIME_MESSAGE_EVENT } from '../utils/events'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const conversations = ref([])
const selectedConversationId = ref(null)
const selectedConversation = ref(null)
const messages = ref([])
const draft = ref('')
const loadingConversations = ref(false)
const loadingMessages = ref(false)
const sending = ref(false)
const pageError = ref('')
const sendError = ref('')
const threadRef = ref(null)
const initialized = ref(false)
const realtimeHandlers = []

const conversationIdFromRoute = computed(() => {
  const raw = route.query.conversationId
  const value = Array.isArray(raw) ? raw[0] : raw
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null
})

const scrollToBottom = async () => {
  await nextTick()
  if (threadRef.value) {
    threadRef.value.scrollTop = threadRef.value.scrollHeight
  }
}

const loadConversations = async (preserveSelection = false) => {
  loadingConversations.value = true
  pageError.value = ''
  try {
    const data = await listConversationsApi()
    conversations.value = data.items || []

    if (preserveSelection && selectedConversationId.value) {
      const existing = conversations.value.find((conversation) => conversation.id === selectedConversationId.value)
      if (existing) {
        selectedConversation.value = existing
      }
    }
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '会话列表加载失败，请稍后重试')
  } finally {
    loadingConversations.value = false
  }
}

const loadConversation = async (conversationId, syncRoute = true) => {
  if (!conversationId) return
  loadingMessages.value = true
  sendError.value = ''
  pageError.value = ''
  try {
    const data = await getConversationMessagesApi(conversationId)
    selectedConversationId.value = conversationId
    selectedConversation.value = data.conversation
    messages.value = data.items || []
    draft.value = ''
    await markConversationReadApi(conversationId)
    emitNotificationChange()
    await loadConversations(true)
    await scrollToBottom()
    if (syncRoute && conversationIdFromRoute.value !== conversationId) {
      await router.replace({ name: 'messages', query: { conversationId } })
    }
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '会话加载失败，请稍后重试')
  } finally {
    loadingMessages.value = false
  }
}

const openConversation = async (conversationId) => {
  if (conversationId !== conversationIdFromRoute.value) {
    await router.push({ name: 'messages', query: { conversationId } })
  }
}

const refreshWorkspace = async () => {
  await loadConversations(false)
  if (!selectedConversationId.value) {
    const fallbackId = conversationIdFromRoute.value || conversations.value[0]?.id || null
    if (fallbackId) {
      await loadConversation(fallbackId, true)
    }
  } else {
    await loadConversation(selectedConversationId.value, false)
  }
}

const refreshCurrentConversation = async () => {
  if (!selectedConversationId.value) return
  await loadConversation(selectedConversationId.value, false)
}

const registerRealtimeListeners = () => {
  if (typeof window === 'undefined' || realtimeHandlers.length > 0) {
    return
  }
  const messageHandler = (event) => {
    void syncConversationFromRealtime(event)
  }
  const conversationHandler = (event) => {
    void syncConversationFromRealtime(event)
  }
  realtimeHandlers.push([REALTIME_MESSAGE_EVENT, messageHandler])
  realtimeHandlers.push([REALTIME_CONVERSATION_EVENT, conversationHandler])
  window.addEventListener(REALTIME_MESSAGE_EVENT, messageHandler)
  window.addEventListener(REALTIME_CONVERSATION_EVENT, conversationHandler)
}

const unregisterRealtimeListeners = () => {
  if (typeof window === 'undefined') return
  realtimeHandlers.forEach(([eventName, handler]) => {
    window.removeEventListener(eventName, handler)
  })
  realtimeHandlers.length = 0
}

const syncConversationFromRealtime = async (event) => {
  const payload = event?.detail || {}
  const targetId = payload.conversation?.id || payload.conversation_id
  if (payload.type === 'conversation.updated') {
    await loadConversations(true)
    return
  }
  if (!targetId) return
  if (selectedConversationId.value && targetId === selectedConversationId.value) {
    await loadConversation(targetId, false)
    return
  }
  await loadConversations(true)
}

const sendMessage = async () => {
  if (!selectedConversationId.value || !draft.value.trim()) return
  sending.value = true
  sendError.value = ''
  try {
    await sendMessageApi(selectedConversationId.value, { content: draft.value.trim() })
    emitNotificationChange()
    await loadConversation(selectedConversationId.value, false)
  } catch (error) {
    sendError.value = getApiErrorMessage(error, '发送消息失败，请稍后重试')
  } finally {
    sending.value = false
  }
}

watch(conversationIdFromRoute, async (conversationId) => {
  if (!initialized.value) return
  if (!conversationId) return
  if (conversationId !== selectedConversationId.value) {
    await loadConversation(conversationId, false)
  }
})

onMounted(async () => {
  if (!auth.ready) {
    await auth.bootstrap()
  }
  registerRealtimeListeners()
  await loadConversations(false)
  const initialId = conversationIdFromRoute.value || conversations.value[0]?.id || null
  if (initialId) {
    await loadConversation(initialId, false)
    if (!conversationIdFromRoute.value) {
      await router.replace({ name: 'messages', query: { conversationId: initialId } })
    }
  }
  initialized.value = true
})

onBeforeUnmount(() => {
  unregisterRealtimeListeners()
})
</script>
