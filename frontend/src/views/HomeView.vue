<template>
  <div class="page">
    <section class="hero">
      <div class="hero__copy">
        <h1>校园好物，流转新生</h1>
        <p>发现、发布、收藏——让闲置物品在校园里找到新主人。</p>
        <div class="hero__cta">
          <router-link to="/items/new" class="btn btn--primary">发布物品</router-link>
          <router-link to="/" class="btn btn--ghost">浏览全部</router-link>
        </div>
      </div>
    </section>

    <section class="toolbar">
      <form class="filters" @submit.prevent="search">
        <div class="filters-grid">
          <label class="field">
            <span class="field__label">关键词</span>
            <input v-model="filters.q" class="field__input" placeholder="搜索教材、耳机、风扇..." />
          </label>
          <label class="field">
            <span class="field__label">分类</span>
            <select v-model="filters.category_id" class="field__select">
              <option :value="''">全部分类</option>
              <option v-for="category in categories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </label>
          <label class="field">
            <span class="field__label">最低价</span>
            <input v-model="filters.min_price" class="field__input" type="number" min="0" step="0.01" placeholder="0" />
          </label>
          <label class="field">
            <span class="field__label">最高价</span>
            <input v-model="filters.max_price" class="field__input" type="number" min="0" step="0.01" placeholder="999" />
          </label>
          <label class="field">
            <span class="field__label">成色</span>
            <select v-model="filters.condition" class="field__select">
              <option value="">全部</option>
              <option>全新</option>
              <option>九成新</option>
              <option>八成新</option>
              <option>七成新</option>
            </select>
          </label>
          <label class="field">
            <span class="field__label">排序</span>
            <select v-model="filters.sort" class="field__select">
              <option value="newest">最新发布</option>
              <option value="hot">热门推荐</option>
              <option value="views_desc">浏览量</option>
              <option value="price_asc">价格升序</option>
              <option value="price_desc">价格降序</option>
            </select>
          </label>
        </div>

        <div class="filters-actions">
          <button class="btn btn--primary" type="submit">搜索</button>
          <button class="btn btn--ghost" type="button" @click="resetFilters">重置</button>
        </div>
      </form>
    </section>

    <section class="section">
      <div class="section__head">
        <div>
          <h2>全部物品</h2>
          <p>共 {{ total }} 件在售物品</p>
        </div>
      </div>

      <div v-if="loading" class="empty-state surface">正在加载...</div>
      <div v-else-if="items.length" class="card-grid">
        <ItemCard v-for="item in items" :key="item.id" :item="item" @favorite="toggleFavorite" />
      </div>
      <div v-else class="empty-state surface">暂无商品，去发布一件吧。</div>

      <PaginationBar :page="page" :pages="pages" :total="total" @change="loadItems" />
    </section>

    <section class="section">
      <div class="section__head">
        <div>
          <h2>热门推荐</h2>
          <p>近期浏览量最高的校园好物。</p>
        </div>
      </div>
      <div v-if="hotItems.length" class="card-grid card-grid--hot">
        <ItemCard v-for="item in hotItems" :key="item.id" :item="item" @favorite="toggleFavorite" />
      </div>
      <div v-else class="empty-state surface">暂无推荐商品。</div>
    </section>

    <section class="section">
      <div class="section__head">
        <div>
          <h2>价格趋势</h2>
          <p>各分类均价对比、价格区间分布与近 7 天发布趋势。</p>
        </div>
      </div>
      <div class="surface page-panel">
        <PriceChart />
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ItemCard from '../components/ItemCard.vue'
import PaginationBar from '../components/PaginationBar.vue'
import PriceChart from '../components/PriceChart.vue'
import { dashboardStatsApi } from '../api/admin'
import { hotItemsApi, listItemsApi } from '../api/items'
import { listCategoriesApi } from '../api/categories'
import { toggleFavoriteApi } from '../api/favorites'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const categories = ref([])
const items = ref([])
const hotItems = ref([])
const loading = ref(false)
const page = ref(1)
const pages = ref(1)
const total = ref(0)

const filters = reactive({
  q: '',
  category_id: '',
  min_price: '',
  max_price: '',
  condition: '',
  sort: 'newest',
})

const normalizeParams = () => {
  const params = {
    page: page.value,
    page_size: 12,
    sort: filters.sort,
  }
  if (filters.q.trim()) params.q = filters.q.trim()
  if (filters.category_id) params.category_id = filters.category_id
  if (filters.min_price !== '') params.min_price = filters.min_price
  if (filters.max_price !== '') params.max_price = filters.max_price
  if (filters.condition) params.condition = filters.condition
  return params
}

const loadItems = async (targetPage = 1) => {
  loading.value = true
  page.value = targetPage
  try {
    const data = await listItemsApi(normalizeParams())
    items.value = data.items
    total.value = data.total
    pages.value = data.pages
  } finally {
    loading.value = false
  }
}

const loadHome = async () => {
  const [categoryData, , hotData] = await Promise.all([
    listCategoriesApi().catch(() => []),
    dashboardStatsApi().catch(() => ({})),
    hotItemsApi().catch(() => []),
  ])
  categories.value = categoryData
  hotItems.value = Array.isArray(hotData) ? hotData : []
  await loadItems(1)
}

const search = async () => {
  await loadItems(1)
}

const resetFilters = async () => {
  Object.assign(filters, {
    q: '',
    category_id: '',
    min_price: '',
    max_price: '',
    condition: '',
    sort: 'newest',
  })
  await loadItems(1)
}

const toggleFavorite = async (item) => {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  const result = await toggleFavoriteApi(item.id)
  item.is_favorite = result.favorited
  if (!result.favorited && hotItems.value.some((row) => row.id === item.id)) {
    const hot = hotItems.value.find((row) => row.id === item.id)
    if (hot) hot.is_favorite = false
  }
}

onMounted(loadHome)
watch(
  () => filters.sort,
  () => loadItems(1),
)
</script>
