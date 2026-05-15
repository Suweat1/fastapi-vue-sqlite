<template>
  <div class="page">
    <section class="surface" style="padding: 24px; border-radius: 28px;">
      <div class="section__head">
        <div>
          <h2>我的收藏</h2>
          <p>收藏的物品可再次查看、取消收藏或跳转详情页</p>
        </div>
      </div>
    </section>

    <section class="section">
      <div v-if="loading" class="empty-state surface">正在加载收藏列表...</div>
      <div v-else-if="items.length" class="card-grid">
        <ItemCard v-for="item in items" :key="item.id" :item="item" @favorite="toggleFavorite" />
      </div>
      <div v-else class="empty-state surface">暂无收藏，去首页看看热门商品吧。</div>
      <PaginationBar :page="page" :pages="pages" :total="total" @change="loadItems" />
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import ItemCard from '../components/ItemCard.vue'
import PaginationBar from '../components/PaginationBar.vue'
import { listFavoritesApi, toggleFavoriteApi } from '../api/favorites'

const loading = ref(false)
const items = ref([])
const page = ref(1)
const pages = ref(1)
const total = ref(0)

const loadItems = async (targetPage = 1) => {
  loading.value = true
  page.value = targetPage
  try {
    const data = await listFavoritesApi({
      page: page.value,
      page_size: 12,
    })
    items.value = data.items
    pages.value = data.pages
    total.value = data.total
  } finally {
    loading.value = false
  }
}

const toggleFavorite = async (item) => {
  const result = await toggleFavoriteApi(item.id)
  if (!result.favorited) {
    items.value = items.value.filter((row) => row.id !== item.id)
    total.value -= 1
    return
  }
  item.is_favorite = result.favorited
}

onMounted(() => loadItems(1))
</script>

