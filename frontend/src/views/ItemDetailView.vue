<template>
  <div v-if="loading" class="empty-state surface">正在加载物品详情...</div>

  <div v-else-if="pageError" class="empty-state surface">
    <div>{{ pageError }}</div>
    <router-link to="/" class="btn btn--primary" style="margin-top: 16px;">返回首页</router-link>
  </div>

  <div v-else-if="item" class="detail-grid">
    <article class="detail-card">
      <p v-if="actionMessage" class="notice detail-notice">{{ actionMessage }}</p>
      <p v-if="actionError" class="form-alert form-alert--error">{{ actionError }}</p>

      <div class="mini-gallery">
        <div class="mini-gallery__main">
          <img v-if="activeImage" :src="activeImage" :alt="item.title" />
          <div v-else class="item-card__placeholder">暂无图片</div>
        </div>
        <div v-if="item.images.length" class="mini-gallery__thumbs">
          <img
            v-for="image in item.images"
            :key="image.id"
            class="thumb"
            :class="{ 'is-active': activeImage === image.url }"
            :src="image.url"
            :alt="item.title"
            @click="activeImage = image.url"
          />
        </div>
      </div>

      <div class="detail-meta">
        <span class="badge badge--primary">{{ item.category?.name }}</span>
        <span class="badge badge--blue">{{ item.condition }}</span>
        <span class="badge badge--slate">{{ item.location }}</span>
        <span class="badge badge--green">浏览 {{ item.views }}</span>
        <span class="badge" :class="statusBadgeClass">{{ statusText }}</span>
      </div>

      <h1 class="detail-title">{{ item.title }}</h1>
      <div class="detail-price">{{ formatCurrency(item.price) }}</div>

      <p class="detail-text">{{ item.description }}</p>

      <div class="inline-actions">
        <button
          v-if="canBuy"
          class="btn btn--success"
          type="button"
          :disabled="actionBusy === 'purchase'"
          @click="buyItem"
        >
          {{ purchaseLabel }}
        </button>
        <button v-else class="btn btn--ghost" type="button" disabled>{{ purchaseLabel }}</button>

        <button
          v-if="canChat"
          class="btn btn--primary"
          type="button"
          :disabled="actionBusy === 'chat'"
          @click="openChat"
        >
          {{ chatLabel }}
        </button>
        <button
          v-else-if="!canEdit && !auth.isLoggedIn"
          class="btn btn--ghost"
          type="button"
          @click="goLogin"
        >
          登录后私聊
        </button>

        <button class="btn btn--primary" type="button" @click="toggleFavorite">
          {{ item.is_favorite ? '取消收藏' : '收藏物品' }}
        </button>
        <router-link v-if="canEdit" :to="`/items/${item.id}/edit`" class="btn btn--ghost">编辑物品</router-link>
        <router-link to="/" class="btn btn--ghost">返回首页</router-link>
      </div>
    </article>

    <aside class="detail-side">
      <section class="sidebar-card">
        <h3>卖家信息</h3>
        <p>昵称：{{ item.seller.nickname || item.seller.username }}</p>
        <p>账号：{{ item.seller.username }}</p>
        <p>发布时间：{{ formatDate(item.created_at) }}</p>
        <p>更新时间：{{ formatDate(item.updated_at) }}</p>
      </section>

      <section class="sidebar-card">
        <h3>交易提示</h3>
        <p>
          支持收藏、私聊卖家、立即购买和校园当面交易。请在交易前再次确认物品成色、价格与交付方式。
        </p>
      </section>

      <section class="sidebar-card">
        <div class="section__head" style="margin-bottom: 12px;">
          <div>
            <h3>热门推荐</h3>
            <p>浏览量较高的校园好物</p>
          </div>
        </div>
        <div v-if="recommendations.length" class="recommendation-list">
          <router-link
            v-for="recommend in recommendations"
            :key="recommend.id"
            :to="`/items/${recommend.id}`"
            class="recommendation-item"
          >
            <div class="recommendation-item__title">{{ recommend.title }}</div>
            <div class="recommendation-item__meta">
              <span>{{ recommend.category?.name }}</span>
              <strong>{{ formatCurrency(recommend.price) }}</strong>
            </div>
          </router-link>
        </div>
        <div v-else class="empty-state" style="padding: 18px 0;">暂无推荐数据</div>
      </section>
    </aside>
  </div>

  <div v-else class="empty-state surface">物品不存在或已下架。</div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItemApi, hotItemsApi } from '../api/items'
import { purchaseItemApi } from '../api/orders'
import { toggleFavoriteApi } from '../api/favorites'
import { startConversationFromItemApi } from '../api/chats'
import { useAuthStore } from '../stores/auth'
import { formatCurrency, formatDate } from '../utils/format'
import { getApiErrorMessage } from '../utils/error'
import { emitNotificationChange } from '../utils/events'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const item = ref(null)
const loading = ref(false)
const pageError = ref('')
const recommendations = ref([])
const activeImage = ref('')
const actionMessage = ref('')
const actionError = ref('')
const actionBusy = ref('')

const canEdit = computed(() => {
  if (!item.value || !auth.user) return false
  return auth.isAdmin || auth.user.id === item.value.seller.id
})

const canBuy = computed(() => Boolean(item.value && item.value.status === 'active' && !canEdit.value))
const canChat = computed(() => Boolean(item.value && item.value.status === 'active' && !canEdit.value))

const statusText = computed(() => {
  if (!item.value) return ''
  return {
    active: '在售',
    sold: '已售出',
    hidden: '已隐藏',
    pending: '审核中',
  }[item.value.status] || item.value.status
})

const statusBadgeClass = computed(() => {
  if (!item.value) return 'badge--slate'
  return {
    active: 'badge--green',
    sold: 'badge--primary',
    hidden: 'badge--slate',
    pending: 'badge--blue',
  }[item.value.status] || 'badge--slate'
})

const purchaseLabel = computed(() => {
  if (!auth.isLoggedIn) return '登录后购买'
  if (!item.value || item.value.status !== 'active') return '已售出'
  if (canEdit.value) return '不可购买'
  return '立即购买'
})

const chatLabel = computed(() => {
  if (!auth.isLoggedIn) return '登录后私聊'
  return '私聊卖家'
})

const goLogin = () => {
  router.push({ name: 'login', query: { redirect: route.fullPath } })
}

const loadDetail = async (keepFeedback = false) => {
  loading.value = true
  pageError.value = ''
  if (!keepFeedback) {
    actionError.value = ''
    actionMessage.value = ''
  }
  try {
    const [detail, hot] = await Promise.all([
      getItemApi(route.params.id),
      hotItemsApi().catch(() => []),
    ])
    item.value = detail
    recommendations.value = Array.isArray(hot) ? hot.filter((row) => row.id !== detail.id).slice(0, 4) : []
    activeImage.value = detail.cover_image || detail.images?.[0]?.url || ''
  } catch (error) {
    item.value = null
    recommendations.value = []
    activeImage.value = ''
    pageError.value = getApiErrorMessage(error, '物品加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const toggleFavorite = async () => {
  if (!auth.isLoggedIn) {
    goLogin()
    return
  }
  try {
    const result = await toggleFavoriteApi(item.value.id)
    item.value.is_favorite = result.favorited
    actionMessage.value = result.favorited ? '已加入收藏。' : '已取消收藏。'
    actionError.value = ''
    emitNotificationChange()
  } catch (error) {
    actionError.value = getApiErrorMessage(error, '收藏操作失败')
    actionMessage.value = ''
  }
}

const buyItem = async () => {
  if (!auth.isLoggedIn) {
    goLogin()
    return
  }
  if (!canBuy.value) {
    actionError.value = '该商品当前不可购买。'
    return
  }
  actionBusy.value = 'purchase'
  actionError.value = ''
  actionMessage.value = ''
  try {
    await purchaseItemApi(item.value.id)
    actionMessage.value = '购买成功，系统已生成订单并发送消息提醒。'
    emitNotificationChange()
    await loadDetail(true)
  } catch (error) {
    actionError.value = getApiErrorMessage(error, '购买失败，请稍后重试')
  } finally {
    actionBusy.value = ''
  }
}

const openChat = async () => {
  if (!auth.isLoggedIn) {
    goLogin()
    return
  }
  if (!canChat.value) {
    actionError.value = '当前商品不可发起私聊。'
    return
  }
  actionBusy.value = 'chat'
  actionError.value = ''
  actionMessage.value = ''
  try {
    const conversation = await startConversationFromItemApi(item.value.id)
    emitNotificationChange()
    router.push({ name: 'messages', query: { conversationId: conversation.id } })
  } catch (error) {
    actionError.value = getApiErrorMessage(error, '发起私聊失败，请稍后重试')
  } finally {
    actionBusy.value = ''
  }
}

watch(
  () => route.params.id,
  () => loadDetail(),
  { immediate: true },
)

onMounted(() => {
  if (!auth.ready) {
    void auth.bootstrap()
  }
})
</script>
