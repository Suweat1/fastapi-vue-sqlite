<template>
  <div class="page admin-page">
    <section class="surface page-panel admin-hero">
      <div class="admin-hero__content">
        <span class="eyebrow">管理员仪表盘</span>
        <h2>管理后台</h2>
        <p>管理用户、物品与分类，查看平台数据概览。</p>
        <div class="admin-hero__chips">
          <span class="badge badge--blue">用户 {{ formatCount(stats.users) }}</span>
          <span class="badge badge--green">上架率 {{ formatRate(stats.active_rate) }}</span>
          <span class="badge badge--slate">未读通知 {{ formatCount(stats.unread_notifications) }}</span>
        </div>
      </div>
      <div class="admin-hero__panel">
        <div class="admin-hero__stat">
          <span>商品总数</span>
          <strong>{{ formatCount(stats.items) }}</strong>
          <small>包含上架、已售出与隐藏商品</small>
        </div>
        <div class="admin-hero__stat">
          <span>累计浏览</span>
          <strong>{{ formatCount(stats.views) }}</strong>
          <small>平台整体热度与访问量</small>
        </div>
        <div class="inline-actions admin-hero__actions">
          <button class="btn btn--ghost" type="button" @click="reloadAll">刷新数据</button>
          <button class="btn btn--primary" type="button" @click="downloadDashboardReport" :disabled="downloadingReport">
            {{ downloadingReport ? '正在下载...' : '下载报表' }}
          </button>
        </div>
      </div>
    </section>

    <div v-if="pageError" class="notice notice--error admin-notice">{{ pageError }}</div>

    <section class="surface page-panel admin-section">
      <div class="section__head admin-section__head">
        <div>
          <h3>核心指标</h3>
          <p>最重要的平台数据一屏查看。</p>
        </div>
        <span class="badge badge--slate">共 {{ dashboardMetrics.length }} 项</span>
      </div>
      <div class="dashboard-grid dashboard-grid--core">
        <article
          v-for="metric in coreMetrics"
          :key="metric.key"
          class="dashboard-metric"
          :class="`dashboard-metric--${metric.tone}`"
        >
          <div class="dashboard-metric__icon" v-html="metric.icon"></div>
          <div class="dashboard-metric__body">
            <span class="dashboard-metric__label">{{ metric.label }}</span>
            <strong class="dashboard-metric__value">{{ metric.value }}</strong>
            <p class="dashboard-metric__hint">{{ metric.hint }}</p>
          </div>
        </article>
      </div>
      <div class="dashboard-mini-grid">
        <article
          v-for="metric in supportMetrics"
          :key="metric.key"
          class="dashboard-mini-card"
          :class="`dashboard-mini-card--${metric.tone}`"
        >
          <div class="dashboard-mini-card__icon" v-html="metric.icon"></div>
          <div class="dashboard-mini-card__body">
            <span class="dashboard-mini-card__label">{{ metric.label }}</span>
            <strong class="dashboard-mini-card__value">{{ metric.value }}</strong>
            <p class="dashboard-mini-card__hint">{{ metric.hint }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="surface page-panel admin-section">
      <div class="section__head">
        <div>
          <h3>分类分布</h3>
          <p>按商品数量查看各分类的占比和活跃度。</p>
        </div>
        <span class="badge badge--slate">共 {{ stats.categories }} 个分类</span>
      </div>

      <div v-if="categoryBreakdownRows.length" class="dashboard-breakdown">
        <article v-for="row in categoryBreakdownRows" :key="row.id || row.name" class="dashboard-breakdown__row">
          <div class="dashboard-breakdown__meta">
            <div>
              <strong>{{ row.name }}</strong>
              <span>{{ row.count }} 件</span>
            </div>
            <span>{{ row.share.toFixed(1) }}%</span>
          </div>
          <div class="dashboard-breakdown__bar">
            <span :style="{ width: `${row.barWidth}%` }"></span>
          </div>
        </article>
      </div>
      <div v-else class="empty-state">暂无分类数据。</div>
    </section>

    <section class="surface page-panel admin-section">
      <div class="section__head">
        <div>
          <h3>价格趋势</h3>
          <p>各分类均价对比、价格区间分布与近 7 天发布趋势。</p>
        </div>
      </div>
      <PriceChart ref="priceChartRef" />
    </section>

    <div class="admin-columns">
      <section class="surface page-panel admin-section">
        <div class="section__head">
          <div>
            <h3>用户管理</h3>
            <p>可调整普通用户和管理员角色。</p>
          </div>
        </div>
        <div v-if="usersLoading" class="empty-state">正在加载用户...</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>用户名</th>
                <th>昵称</th>
                <th>邮箱</th>
                <th>角色</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.username }}</td>
                <td>{{ user.nickname }}</td>
                <td>{{ user.email || '-' }}</td>
                <td>
                  <select v-model="user.role" class="field__select admin-select">
                    <option value="user">普通用户</option>
                    <option value="admin">管理员</option>
                  </select>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td>
                  <button class="btn btn--primary btn--sm" type="button" @click="saveRole(user)">保存角色</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="surface page-panel admin-section">
        <div class="section__head">
          <div>
            <h3>物品审核</h3>
            <p>支持查看所有物品并修改状态，可多选批量操作。</p>
          </div>
        </div>
        <div class="filters-grid admin-filters">
          <label class="field">
            <span class="field__label">关键字</span>
            <input v-model="itemsQuery.q" class="field__input" placeholder="搜索物品标题" />
          </label>
          <label class="field">
            <span class="field__label">状态</span>
            <select v-model="itemsQuery.status" class="field__select">
              <option value="">全部</option>
              <option value="active">上架中</option>
              <option value="sold">已售出</option>
              <option value="hidden">已隐藏</option>
            </select>
          </label>
        </div>
        <div class="filters-actions admin-filters__actions">
          <button class="btn btn--primary" type="button" @click="loadAdminItems(1)">筛选</button>
        </div>

        <!-- 批量操作栏 -->
        <div v-if="selectedIds.length" class="batch-bar">
          <span class="batch-bar__info">已选中 <strong>{{ selectedIds.length }}</strong> 件物品</span>
          <div class="inline-actions">
            <button class="btn btn--primary btn--sm" type="button" @click="batchDialogOpen = true">批量修改</button>
            <button class="btn btn--ghost btn--sm" type="button" @click="clearSelection">取消选择</button>
          </div>
        </div>

        <div v-if="itemsLoading" class="empty-state">正在加载物品...</div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th class="col-check">
                  <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
                </th>
                <th>标题</th>
                <th>卖家</th>
                <th>分类</th>
                <th>价格</th>
                <th>状态</th>
                <th>浏览</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in adminItems" :key="item.id" :class="{ 'row-selected': selectedIds.includes(item.id) }">
                <td class="col-check">
                  <input type="checkbox" :value="item.id" v-model="selectedIds" />
                </td>
                <td>{{ item.title }}</td>
                <td>{{ item.seller.nickname || item.seller.username }}</td>
                <td>{{ item.category.name }}</td>
                <td>{{ formatCurrency(item.price) }}</td>
                <td>
                  <select v-model="item.status" class="field__select admin-select">
                    <option value="active">上架中</option>
                    <option value="sold">已售出</option>
                    <option value="hidden">已隐藏</option>
                  </select>
                </td>
                <td>{{ formatCount(item.views) }}</td>
                <td>
                  <button class="btn btn--primary btn--sm" type="button" @click="saveStatus(item)">保存状态</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <PaginationBar :page="itemsPage" :pages="itemsPages" :total="itemsTotal" @change="loadAdminItems" />

        <!-- 批量修改弹窗 -->
        <div v-if="batchDialogOpen" class="modal-overlay" @click.self="batchDialogOpen = false">
          <div class="modal-content surface">
            <div class="modal-header">
              <h3>批量修改 ({{ selectedIds.length }} 件物品)</h3>
              <button class="btn btn--ghost btn--sm" type="button" @click="batchDialogOpen = false">关闭</button>
            </div>
            <form class="modal-body" @submit.prevent="submitBatchUpdate">
              <label class="field">
                <span class="field__label">修改状态</span>
                <select v-model="batchForm.status" class="field__select">
                  <option value="">不修改</option>
                  <option value="active">上架中</option>
                  <option value="sold">已售出</option>
                  <option value="hidden">已隐藏</option>
                </select>
              </label>
              <label class="field">
                <span class="field__label">修改分类</span>
                <select v-model="batchForm.category_id" class="field__select">
                  <option value="">不修改</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                </select>
              </label>
              <label class="field">
                <span class="field__label">修改成色</span>
                <select v-model="batchForm.condition" class="field__select">
                  <option value="">不修改</option>
                  <option value="全新">全新</option>
                  <option value="几乎全新">几乎全新</option>
                  <option value="九成新">九成新</option>
                  <option value="八成新">八成新</option>
                  <option value="七成新">七成新</option>
                  <option value="一般">一般</option>
                </select>
              </label>
              <label class="field">
                <span class="field__label">推荐标记</span>
                <select v-model="batchForm.is_featured" class="field__select">
                  <option value="">不修改</option>
                  <option :value="true">设为推荐</option>
                  <option :value="false">取消推荐</option>
                </select>
              </label>
              <div v-if="batchError" class="notice notice--error">{{ batchError }}</div>
              <div class="filters-actions" style="margin-top: 1rem;">
                <button class="btn btn--primary" type="submit" :disabled="batchSubmitting">
                  {{ batchSubmitting ? '提交中...' : '确认修改' }}
                </button>
                <button class="btn btn--ghost" type="button" @click="batchDialogOpen = false">取消</button>
              </div>
            </form>
          </div>
        </div>
      </section>
    </div>

    <section class="surface page-panel admin-section">
      <div class="section__head">
        <div>
          <h3>分类管理</h3>
          <p>支持新增、编辑与删除分类。</p>
        </div>
      </div>
      <form class="split-grid admin-category-form" @submit.prevent="saveCategory">
        <label class="field">
          <span class="field__label">分类名称</span>
          <input v-model="categoryForm.name" class="field__input" required />
        </label>
        <label class="field">
          <span class="field__label">Slug</span>
          <input v-model="categoryForm.slug" class="field__input" required />
        </label>
        <label class="field">
          <span class="field__label">排序</span>
          <input v-model.number="categoryForm.sort_order" class="field__input" type="number" />
        </label>
        <label class="field">
          <span class="field__label">启用</span>
          <select v-model="categoryForm.is_active" class="field__select">
            <option :value="true">是</option>
            <option :value="false">否</option>
          </select>
        </label>
        <div class="filters-actions admin-category-form__actions">
          <button class="btn btn--primary" type="submit">{{ categoryForm.id ? '保存分类' : '新增分类' }}</button>
          <button class="btn btn--ghost" type="button" @click="resetCategoryForm">清空</button>
        </div>
      </form>

      <div class="table-wrap admin-table-space">
        <table class="data-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>Slug</th>
              <th>排序</th>
              <th>启用</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="category in categories" :key="category.id">
              <td>{{ category.name }}</td>
              <td>{{ category.slug }}</td>
              <td>{{ category.sort_order }}</td>
              <td>{{ category.is_active ? '是' : '否' }}</td>
              <td>{{ formatDate(category.created_at) }}</td>
              <td>
                <div class="inline-actions">
                  <button class="btn btn--ghost btn--sm" type="button" @click="editCategory(category)">编辑</button>
                  <button class="btn btn--danger btn--sm" type="button" @click="removeCategory(category.id)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="surface page-panel admin-section">
      <div class="section__head">
        <div>
          <h3>热门物品</h3>
          <p>浏览量最高的前 6 件物品。</p>
        </div>
      </div>
      <div v-if="stats.top_items?.length" class="card-grid card-grid--hot">
        <ItemCard v-for="item in stats.top_items" :key="item.id" :item="item" @favorite="() => {}" />
      </div>
      <div v-else class="empty-state">暂无热门商品数据。</div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ItemCard from '../components/ItemCard.vue'
import PaginationBar from '../components/PaginationBar.vue'
import PriceChart from '../components/PriceChart.vue'
import {
  batchUpdateItemsApi,
  dashboardStatsApi,
  downloadDashboardReportApi,
  listAdminItemsApi,
  listUsersApi,
  updateItemStatusApi,
  updateUserRoleApi,
} from '../api/admin'
import { createCategoryApi, deleteCategoryApi, listCategoriesApi, updateCategoryApi } from '../api/categories'
import { formatCurrency, formatDate } from '../utils/format'

const numberFormatter = new Intl.NumberFormat('zh-CN')

const defaultStats = {
  users: 0,
  items: 0,
  active_items: 0,
  sold_items: 0,
  hidden_items: 0,
  favorites: 0,
  views: 0,
  categories: 0,
  orders: 0,
  conversations: 0,
  messages: 0,
  notifications: 0,
  unread_notifications: 0,
  active_rate: 0,
  top_items: [],
  category_breakdown: [],
}

const ICONS = {
  users:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M22 21v-2a3 3 0 0 0-2-2.83"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  items:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 7 9-4 9 4-9 4-9-4Z"/><path d="m3 7 9 4 9-4"/><path d="m3 7 9 10 9-10"/><path d="M12 11v10"/></svg>',
  active:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/><circle cx="12" cy="12" r="9"/></svg>',
  sold:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7h18l-2 10H5L3 7Z"/><path d="M8 7V4h8v3"/><path d="M8 11h8"/></svg>',
  favorites:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m12 21-7.5-7.4A4.7 4.7 0 0 1 12 7.2a4.7 4.7 0 0 1 7.5 6.4L12 21Z"/></svg>',
  views:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 12s3.5-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.5 6.5-9.5 6.5S2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/></svg>',
  orders:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2h12v20H6z"/><path d="M9 6h6"/><path d="M9 10h6"/><path d="M9 14h6"/></svg>',
  conversations:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v10H7l-3 3V5Z"/><path d="M8 9h8"/><path d="M8 12h5"/></svg>',
  messages:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 0 1-8 8H7l-4 3V12a8 8 0 1 1 18 0Z"/><path d="M8 12h8"/><path d="M8 8h4"/></svg>',
  notifications:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 17H9a4 4 0 0 1-4-4v-2a7 7 0 0 1 14 0v2a4 4 0 0 1-4 4Z"/><path d="M10 17a2 2 0 0 0 4 0"/><path d="M12 3v2"/></svg>',
  categories:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h6v6H4z"/><path d="M14 4h6v6h-6z"/><path d="M4 14h6v6H4z"/><path d="M14 14h6v6h-6z"/></svg>',
  hidden:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3l18 18"/><path d="M10.58 10.58A3 3 0 1 0 13.42 13.42"/><path d="M9.88 5.08A10.8 10.8 0 0 1 12 4.5c6 0 9.5 7.5 9.5 7.5a18.2 18.2 0 0 1-4.32 5.36"/><path d="M6.6 6.6A18.2 18.2 0 0 0 2.5 12s3.5 7.5 9.5 7.5a11 11 0 0 0 3.18-.48"/></svg>',
}

const stats = ref({ ...defaultStats })
const users = ref([])
const categories = ref([])
const adminItems = ref([])
const usersLoading = ref(false)
const itemsLoading = ref(false)
const downloadingReport = ref(false)
const pageError = ref('')
const itemsPage = ref(1)
const itemsPages = ref(1)
const itemsTotal = ref(0)

const itemsQuery = reactive({
  q: '',
  status: '',
})

const categoryForm = reactive({
  id: null,
  name: '',
  slug: '',
  sort_order: 0,
  is_active: true,
})

const selectedIds = ref([])
const batchDialogOpen = ref(false)
const batchSubmitting = ref(false)
const batchError = ref('')
const batchForm = reactive({
  status: '',
  category_id: '',
  condition: '',
  is_featured: '',
})

const isAllSelected = computed(() => adminItems.value.length > 0 && adminItems.value.every((item) => selectedIds.value.includes(item.id)))

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = adminItems.value.map((item) => item.id)
  }
}

const clearSelection = () => {
  selectedIds.value = []
}

const resetBatchForm = () => {
  batchForm.status = ''
  batchForm.category_id = ''
  batchForm.condition = ''
  batchForm.is_featured = ''
  batchError.value = ''
}

const submitBatchUpdate = async () => {
  const payload = { item_ids: selectedIds.value }
  if (batchForm.status) payload.status = batchForm.status
  if (batchForm.category_id) payload.category_id = Number(batchForm.category_id)
  if (batchForm.condition) payload.condition = batchForm.condition
  if (batchForm.is_featured !== '') payload.is_featured = batchForm.is_featured === true

  if (!payload.status && !payload.category_id && !payload.condition && payload.is_featured === undefined) {
    batchError.value = '请至少选择一项需要修改的内容'
    return
  }

  batchSubmitting.value = true
  batchError.value = ''
  try {
    const result = await batchUpdateItemsApi(payload)
    batchDialogOpen.value = false
    resetBatchForm()
    clearSelection()
    await loadAdminItems(itemsPage.value)
    await loadStats()
    alert(`成功修改 ${result.updated_count} 件物品`)
  } catch (err) {
    batchError.value = err?.response?.data?.detail || err?.message || '批量修改失败，请稍后重试'
  } finally {
    batchSubmitting.value = false
  }
}

const formatCount = (value) => numberFormatter.format(Number(value || 0))
const formatRate = (value) => `${Number(value || 0).toFixed(1)}%`

const dashboardMetrics = computed(() => [
  {
    key: 'users',
    label: '用户总数',
    value: formatCount(stats.value.users),
    hint: '平台注册账号',
    tone: 'blue',
    icon: ICONS.users,
  },
  {
    key: 'items',
    label: '商品总数',
    value: formatCount(stats.value.items),
    hint: '平台内全部商品',
    tone: 'orange',
    icon: ICONS.items,
  },
  {
    key: 'active_items',
    label: '上架中',
    value: formatCount(stats.value.active_items),
    hint: `上架率 ${formatRate(stats.value.active_rate)}`,
    tone: 'green',
    icon: ICONS.active,
  },
  {
    key: 'sold_items',
    label: '已售出',
    value: formatCount(stats.value.sold_items),
    hint: '已完成交易',
    tone: 'amber',
    icon: ICONS.sold,
  },
  {
    key: 'favorites',
    label: '收藏总数',
    value: formatCount(stats.value.favorites),
    hint: '用户收藏行为',
    tone: 'red',
    icon: ICONS.favorites,
  },
  {
    key: 'views',
    label: '累计浏览',
    value: formatCount(stats.value.views),
    hint: '平台流量热度',
    tone: 'cyan',
    icon: ICONS.views,
  },
  {
    key: 'orders',
    label: '订单数量',
    value: formatCount(stats.value.orders),
    hint: '购买闭环记录',
    tone: 'violet',
    icon: ICONS.orders,
  },
  {
    key: 'conversations',
    label: '会话数量',
    value: formatCount(stats.value.conversations),
    hint: '私聊沟通记录',
    tone: 'slate',
    icon: ICONS.conversations,
  },
  {
    key: 'messages',
    label: '消息总数',
    value: formatCount(stats.value.messages),
    hint: '系统消息累计',
    tone: 'orange',
    icon: ICONS.messages,
  },
  {
    key: 'notifications',
    label: '通知总数',
    value: formatCount(stats.value.notifications),
    hint: `未读 ${formatCount(stats.value.unread_notifications)}`,
    tone: 'blue',
    icon: ICONS.notifications,
  },
  {
    key: 'categories',
    label: '分类数量',
    value: formatCount(stats.value.categories),
    hint: '有效分类数量',
    tone: 'green',
    icon: ICONS.categories,
  },
  {
    key: 'hidden_items',
    label: '隐藏商品',
    value: formatCount(stats.value.hidden_items),
    hint: '需要重点关注',
    tone: 'slate',
    icon: ICONS.hidden,
  },
])

const coreMetrics = computed(() => dashboardMetrics.value.slice(0, 6))
const supportMetrics = computed(() => dashboardMetrics.value.slice(6))

const categoryBreakdownRows = computed(() => {
  const rows = stats.value.category_breakdown || []
  const total = rows.reduce((sum, row) => sum + Number(row.count || 0), 0)
  const max = Math.max(1, ...rows.map((row) => Number(row.count || 0)))
  return rows.map((row) => {
    const count = Number(row.count || 0)
    return {
      ...row,
      share: total ? (count / total) * 100 : 0,
      barWidth: total ? Math.max(4, Math.round((count / max) * 100)) : 0,
    }
  })
})

const loadStats = async () => {
  stats.value = await dashboardStatsApi()
}

const loadUsers = async () => {
  usersLoading.value = true
  try {
    users.value = await listUsersApi()
  } finally {
    usersLoading.value = false
  }
}

const loadCategories = async () => {
  categories.value = await listCategoriesApi()
}

const loadAdminItems = async (page = 1) => {
  itemsLoading.value = true
  itemsPage.value = page
  selectedIds.value = []
  try {
    const data = await listAdminItemsApi({
      page,
      page_size: 12,
      q: itemsQuery.q || undefined,
      status: itemsQuery.status || undefined,
    })
    adminItems.value = data.items || []
    itemsPages.value = data.pages || 1
    itemsTotal.value = data.total || 0
  } finally {
    itemsLoading.value = false
  }
}

const saveRole = async (user) => {
  await updateUserRoleApi(user.id, { role: user.role })
  await loadUsers()
  await loadStats()
}

const saveStatus = async (item) => {
  await updateItemStatusApi(item.id, { status: item.status })
  await loadAdminItems(itemsPage.value)
  await loadStats()
}

const resetCategoryForm = () => {
  Object.assign(categoryForm, {
    id: null,
    name: '',
    slug: '',
    sort_order: 0,
    is_active: true,
  })
}

const editCategory = (category) => {
  Object.assign(categoryForm, { ...category })
}

const saveCategory = async () => {
  const payload = {
    name: categoryForm.name,
    slug: categoryForm.slug,
    sort_order: Number(categoryForm.sort_order),
    is_active: Boolean(categoryForm.is_active),
  }
  if (categoryForm.id) {
    await updateCategoryApi(categoryForm.id, payload)
  } else {
    await createCategoryApi(payload)
  }
  resetCategoryForm()
  await loadCategories()
  await loadStats()
}

const removeCategory = async (id) => {
  if (!window.confirm('确认删除这个分类吗？')) return
  await deleteCategoryApi(id)
  await loadCategories()
  await loadStats()
}

const downloadDashboardReport = async () => {
  downloadingReport.value = true
  try {
    const blob = await downloadDashboardReportApi()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `campus-dashboard-report-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.zip`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    pageError.value = error?.message || '报表下载失败，请稍后重试'
  } finally {
    downloadingReport.value = false
  }
}

const reloadAll = async () => {
  pageError.value = ''
  const results = await Promise.allSettled([loadStats(), loadUsers(), loadCategories(), loadAdminItems(1)])
  const failed = results.find((result) => result.status === 'rejected')
  if (failed) {
    pageError.value = '后台部分数据加载失败，请稍后重试'
  }
}

onMounted(reloadAll)
</script>
