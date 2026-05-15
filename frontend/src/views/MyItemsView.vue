<template>
  <div class="page">
    <section class="surface" style="padding: 24px; border-radius: 28px;">
      <div class="section__head">
        <div>
          <h2>我的发布</h2>
          <p>管理自己发布的物品，可编辑、删除和查看状态</p>
        </div>
        <router-link to="/items/new" class="btn btn--primary">发布新物品</router-link>
      </div>

      <form class="filters" style="margin-top: 18px;" @submit.prevent="loadItems(1)">
        <div class="filters-grid">
          <label class="field">
            <span class="field__label">关键词</span>
            <input v-model="query.q" class="field__input" placeholder="搜索我的物品" />
          </label>
          <label class="field">
            <span class="field__label">状态</span>
            <select v-model="query.status" class="field__select">
              <option value="">全部状态</option>
              <option value="active">在售</option>
              <option value="sold">已售</option>
              <option value="hidden">隐藏</option>
            </select>
          </label>
        </div>
        <div class="filters-actions">
          <button class="btn btn--primary" type="submit">筛选</button>
          <button class="btn btn--ghost" type="button" @click="reset">重置</button>
        </div>
      </form>
    </section>

    <section class="surface" style="padding: 24px; border-radius: 28px;">
      <div v-if="loading" class="empty-state">加载中...</div>
      <div v-else-if="items.length" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>物品</th>
              <th>分类</th>
              <th>价格</th>
              <th>状态</th>
              <th>浏览</th>
              <th>发布时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>
                <strong>{{ item.title }}</strong>
                <div style="color: var(--muted); margin-top: 6px;">{{ item.condition }} · {{ item.location }}</div>
              </td>
              <td>{{ item.category?.name }}</td>
              <td>{{ formatCurrency(item.price) }}</td>
              <td><span :class="statusClass(item.status)">{{ statusText(item.status) }}</span></td>
              <td>{{ item.views }}</td>
              <td>{{ formatDate(item.created_at) }}</td>
              <td>
                <div class="inline-actions">
                  <router-link :to="`/items/${item.id}`" class="btn btn--ghost btn--sm">详情</router-link>
                  <router-link :to="`/items/${item.id}/edit`" class="btn btn--primary btn--sm">编辑</router-link>
                  <button class="btn btn--danger btn--sm" type="button" @click="remove(item.id)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">暂无发布内容。</div>

      <PaginationBar :page="page" :pages="pages" :total="total" @change="loadItems" />
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { deleteItemApi, myItemsApi } from '../api/items'
import { formatCurrency, formatDate } from '../utils/format'
const loading = ref(false)
const items = ref([])
const page = ref(1)
const pages = ref(1)
const total = ref(0)

const query = reactive({
  q: '',
  status: '',
})

const loadItems = async (targetPage = 1) => {
  loading.value = true
  page.value = targetPage
  try {
    const data = await myItemsApi({
      page: page.value,
      page_size: 12,
      q: query.q || undefined,
      status: query.status || undefined,
    })
    items.value = data.items
    pages.value = data.pages
    total.value = data.total
  } finally {
    loading.value = false
  }
}

const reset = async () => {
  query.q = ''
  query.status = ''
  await loadItems(1)
}

const remove = async (id) => {
  if (!window.confirm('确认删除该物品吗？')) return
  await deleteItemApi(id)
  await loadItems(page.value)
}

const statusText = (status) => ({ active: '在售', sold: '已售', hidden: '隐藏', pending: '待审' }[status] || status)
const statusClass = (status) => ({
  active: 'badge badge--green',
  sold: 'badge badge--primary',
  hidden: 'badge badge--slate',
  pending: 'badge badge--blue',
}[status] || 'badge badge--slate')

onMounted(() => loadItems(1))
</script>
