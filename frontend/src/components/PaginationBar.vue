<template>
  <div v-if="pages > 1" class="pagination">
    <div class="pagination__info">
      共 {{ total }} 条，{{ page }}/{{ pages }} 页
    </div>
    <div class="pagination__pages">
      <button class="page-pill" type="button" :disabled="page <= 1" @click="$emit('change', page - 1)">上一页</button>
      <button
        v-for="item in visiblePages"
        :key="item"
        class="page-pill"
        :class="{ 'is-active': item === page }"
        type="button"
        @click="$emit('change', item)"
      >
        {{ item }}
      </button>
      <button class="page-pill" type="button" :disabled="page >= pages" @click="$emit('change', page + 1)">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, required: true },
  pages: { type: Number, required: true },
  total: { type: Number, required: true },
})

defineEmits(['change'])

const visiblePages = computed(() => {
  const start = Math.max(1, props.page - 2)
  const end = Math.min(props.pages, start + 4)
  const adjustedStart = Math.max(1, end - 4)
  const pages = []
  for (let i = adjustedStart; i <= end; i += 1) {
    pages.push(i)
  }
  return pages
})
</script>

