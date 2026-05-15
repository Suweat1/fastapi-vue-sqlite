<template>
  <div class="page">
    <section class="surface page-panel">
      <div class="section__head">
        <div>
          <h2>我的订单</h2>
          <p>购买成功后会在这里生成订单记录，可继续查看商品或联系对方。</p>
        </div>
        <router-link to="/" class="btn btn--ghost">返回首页</router-link>
      </div>

      <form class="filters" style="margin-top: 18px;" @submit.prevent="loadOrders(1)">
        <div class="filters-grid filters-grid--orders">
          <label class="field">
            <span class="field__label">查看范围</span>
            <select v-model="query.scope" class="field__select">
              <option value="all">全部订单</option>
              <option value="buyer">我买到的</option>
              <option value="seller">我卖出的</option>
            </select>
          </label>
        </div>
        <div class="filters-actions">
          <button class="btn btn--primary" type="submit">刷新订单</button>
        </div>
      </form>
    </section>

    <section class="section">
      <div v-if="pageError" class="empty-state surface">{{ pageError }}</div>
      <div v-else-if="loading" class="empty-state surface">正在加载订单...</div>
      <div v-else-if="orders.length" class="order-grid">
        <article v-for="order in orders" :key="order.id" class="order-card surface">
          <router-link :to="`/items/${order.item.id}`" class="order-card__media">
            <img v-if="order.item.cover_image" :src="order.item.cover_image" :alt="order.item.title" />
            <div v-else class="item-card__placeholder">订单商品</div>
          </router-link>

          <div class="order-card__body">
            <div class="order-card__head">
              <div>
                <router-link :to="`/items/${order.item.id}`" class="order-card__title">
                  {{ order.item.title }}
                </router-link>
                <p class="order-card__subtitle">
                  {{ order.item.category?.name }} · {{ order.item.condition }} · {{ order.item.location }}
                </p>
              </div>
              <span class="badge badge--green">已成交</span>
            </div>

            <div class="order-card__info">
              <div>
                <span class="order-card__label">成交金额</span>
                <strong class="detail-price">{{ formatCurrency(order.amount) }}</strong>
              </div>
              <div>
                <span class="order-card__label">我的角色</span>
                <strong>{{ order.buyer.id === auth.user?.id ? '买家' : '卖家' }}</strong>
              </div>
              <div>
                <span class="order-card__label">交易对象</span>
                <strong>{{ order.buyer.id === auth.user?.id ? order.seller.nickname || order.seller.username : order.buyer.nickname || order.buyer.username }}</strong>
              </div>
              <div>
                <span class="order-card__label">下单时间</span>
                <strong>{{ formatRelativeTime(order.created_at) }}</strong>
              </div>
            </div>

            <p class="order-card__desc">
              订单状态：{{ statusText(order.status) }} · 商品发布时间：{{ formatDate(order.item.created_at) }}
            </p>

            <div class="order-card__actions">
              <router-link :to="`/items/${order.item.id}`" class="btn btn--ghost btn--sm">查看商品</router-link>
              <button class="btn btn--primary btn--sm" type="button" :disabled="busyOrderId === order.id" @click="openConversation(order)">
                联系对方
              </button>
            </div>
          </div>
        </article>
      </div>
      <div v-else class="empty-state surface">暂无订单记录，先去首页购买一个心仪的商品吧。</div>

      <PaginationBar :page="page" :pages="pages" :total="total" @change="loadOrders" />
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import PaginationBar from '../components/PaginationBar.vue'
import { listMyOrdersApi } from '../api/orders'
import { startConversationFromOrderApi } from '../api/chats'
import { formatCurrency, formatDate, formatRelativeTime } from '../utils/format'
import { getApiErrorMessage } from '../utils/error'
import { emitNotificationChange } from '../utils/events'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const pageError = ref('')
const orders = ref([])
const page = ref(1)
const pages = ref(1)
const total = ref(0)
const busyOrderId = ref(0)

const query = reactive({
  scope: 'all',
})

const statusText = (status) => ({
  completed: '交易完成',
  pending: '待处理',
  cancelled: '已取消',
}[status] || status || '交易完成')

const loadOrders = async (targetPage = 1) => {
  loading.value = true
  page.value = targetPage
  pageError.value = ''
  try {
    const data = await listMyOrdersApi({
      page: page.value,
      page_size: 12,
      scope: query.scope,
    })
    orders.value = data.items || []
    pages.value = data.pages || 1
    total.value = data.total || 0
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '订单加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const openConversation = async (order) => {
  busyOrderId.value = order.id
  try {
    const conversation = await startConversationFromOrderApi(order.id)
    emitNotificationChange()
    router.push({ name: 'messages', query: { conversationId: conversation.id } })
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '打开聊天失败，请稍后重试')
  } finally {
    busyOrderId.value = 0
  }
}

watch(
  () => query.scope,
  () => {
    void loadOrders(1)
  },
)

onMounted(async () => {
  if (!auth.ready) {
    await auth.bootstrap()
  }
  await loadOrders(1)
})
</script>
