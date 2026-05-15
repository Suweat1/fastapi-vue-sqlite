<template>
  <div class="page">
    <section class="surface" style="padding: 24px; border-radius: 28px;">
      <div class="section__head">
        <div>
          <h2>{{ isEdit ? '编辑物品' : '发布物品' }}</h2>
          <p>填写完整信息后即可提交到平台展示</p>
        </div>
        <router-link to="/me/items" class="btn btn--ghost">返回我的发布</router-link>
      </div>

      <form class="auth-card__form" style="margin-top: 18px;" @submit.prevent="save">
        <div class="split-grid">
          <label class="field">
            <span class="field__label">标题</span>
            <input
              v-model="form.title"
              class="field__input"
              maxlength="120"
              required
              placeholder="例如：高数教材九成新"
              @input="clearError"
            />
          </label>
          <label class="field">
            <span class="field__label">分类</span>
            <select v-model.number="form.category_id" class="field__select" required @change="clearError">
              <option :value="0" disabled>请选择分类</option>
              <option v-for="category in categories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </label>
        </div>

        <div class="split-grid">
          <label class="field">
            <span class="field__label">价格</span>
            <input
              v-model="form.price"
              class="field__input"
              type="number"
              min="0"
              max="99999999.99"
              step="0.01"
              required
              @input="clearError"
            />
          </label>
          <label class="field">
            <span class="field__label">成色</span>
            <select v-model="form.condition" class="field__select" @change="clearError">
              <option :value="'\u5168\u65B0'">全新</option>
              <option :value="'\u4E5D\u6210\u65B0'">九成新</option>
              <option :value="'\u516B\u6210\u65B0'">八成新</option>
              <option :value="'\u4E03\u6210\u65B0'">七成新</option>
              <option :value="'\u516D\u6210\u65B0'">六成新</option>
            </select>
          </label>
        </div>

        <div class="split-grid">
          <label class="field">
            <span class="field__label">地点</span>
            <input v-model="form.location" class="field__input" placeholder="例如：南区宿舍楼下" @input="clearError" />
          </label>
          <label class="field">
            <span class="field__label">状态</span>
            <select v-model="form.status" class="field__select" @change="clearError">
              <option value="active">在售</option>
              <option value="sold">已售</option>
              <option value="hidden">隐藏</option>
            </select>
          </label>
        </div>

        <label class="field">
          <span class="field__label">描述</span>
          <textarea
            v-model="form.description"
            class="field__textarea"
            rows="7"
            required
            placeholder="描述物品使用情况、瑕疵、交易方式等"
            @input="clearError"
          ></textarea>
        </label>

        <label class="field">
          <span class="field__label">图片</span>
          <ImageUploader v-model="form.image_urls" />
        </label>

        <p v-if="errorMessage" class="form-alert form-alert--error" role="alert" aria-live="polite">
          {{ errorMessage }}
        </p>

        <div class="filters-actions">
          <button class="btn btn--primary" type="submit" :disabled="saving">
            {{ saving ? '保存中...' : '保存物品' }}
          </button>
          <router-link to="/" class="btn btn--ghost">取消</router-link>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageUploader from '../components/ImageUploader.vue'
import { createItemApi, getItemApi, updateItemApi } from '../api/items'
import { listCategoriesApi } from '../api/categories'
import { getApiErrorMessage } from '../utils/error'

const route = useRoute()
const router = useRouter()
const saving = ref(false)
const categories = ref([])
const errorMessage = ref('')

const form = reactive({
  title: '',
  description: '',
  price: 0,
  condition: '\u4E5D\u6210\u65B0',
  location: '\u6821\u56ED',
  status: 'active',
  category_id: 0,
  image_urls: [],
})

const isEdit = computed(() => Boolean(route.params.id))

const clearError = () => {
  errorMessage.value = ''
}

const loadCategories = async () => {
  categories.value = await listCategoriesApi()
}

const loadItem = async () => {
  if (!isEdit.value) return
  const data = await getItemApi(route.params.id)
  form.title = data.title
  form.description = data.description
  form.price = data.price
  form.condition = data.condition
  form.location = data.location
  form.status = data.status
  form.category_id = data.category.id
  form.image_urls = data.images.map((image) => image.url)
}

const save = async () => {
  errorMessage.value = ''
  if (!Number(form.category_id)) {
    errorMessage.value = '请选择分类后再发布'
    return
  }

  saving.value = true
  try {
    const payload = {
      title: form.title,
      description: form.description,
      price: Number(form.price),
      condition: form.condition,
      location: form.location,
      status: form.status,
      category_id: Number(form.category_id),
      image_urls: form.image_urls,
    }
    if (isEdit.value) {
      await updateItemApi(route.params.id, payload)
    } else {
      await createItemApi(payload)
    }
    router.push({ name: 'my-items' })
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, isEdit.value ? '保存失败，请稍后重试' : '发布失败，请稍后重试')
    window.alert(errorMessage.value)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadCategories()
  await loadItem()
})

watch(
  () => route.params.id,
  async () => {
    if (isEdit.value) {
      await loadItem()
    }
  },
)
</script>
