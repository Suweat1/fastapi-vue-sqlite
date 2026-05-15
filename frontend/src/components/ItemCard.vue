<template>
  <article class="item-card">
    <router-link class="item-card__media" :to="`/items/${item.id}`">
      <img v-if="item.cover_image" :src="item.cover_image" :alt="item.title" />
      <div v-else class="item-card__placeholder">二手好物</div>
      <span class="item-card__status badge badge--primary">{{ statusText }}</span>
    </router-link>

    <div class="item-card__body">
      <div class="item-card__header">
        <div>
          <router-link class="item-card__title" :to="`/items/${item.id}`">{{ item.title }}</router-link>
          <p class="item-card__desc">{{ shortText(item.description, 72) }}</p>
        </div>
        <button
          class="item-card__fav"
          :class="{ 'is-active': item.is_favorite }"
          type="button"
          @click="$emit('favorite', item)"
        >
          ♥
        </button>
      </div>

      <strong class="detail-price">{{ formatCurrency(item.price) }}</strong>

      <div class="item-card__meta">
        <span>分类：{{ item.category?.name }}</span>
        <span>成色：{{ item.condition }}</span>
        <span>浏览：{{ item.views }}</span>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { formatCurrency, shortText } from '../utils/format'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

defineEmits(['favorite'])

const statusText = computed(() => {
  const map = {
    active: '在售',
    sold: '已售',
    hidden: '隐藏',
    pending: '待审',
  }
  return map[props.item.status] || props.item.status || '在售'
})
</script>

