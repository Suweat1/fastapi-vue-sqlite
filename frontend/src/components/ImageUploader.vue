<template>
  <div class="uploader">
    <div class="uploader__grid">
      <div v-for="(url, index) in modelValue" :key="`${url}-${index}`" class="uploader__item">
        <img :src="url" :alt="`图片${index + 1}`" />
        <button class="uploader__remove" type="button" @click="remove(index)">×</button>
      </div>

      <label class="uploader__trigger">
        <input type="file" hidden multiple accept="image/*" @change="handleFiles" />
        <span v-if="busy">上传中...</span>
        <span v-else>点击或选择图片上传</span>
      </label>
    </div>
    <div class="notice">支持多图上传，第一张图将作为封面图展示。</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadImagesApi } from '../api/upload'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue'])
const busy = ref(false)

const remove = (index) => {
  const next = [...props.modelValue]
  next.splice(index, 1)
  emit('update:modelValue', next)
}

const handleFiles = async (event) => {
  const files = Array.from(event.target.files || [])
  if (!files.length) return
  busy.value = true
  try {
    const uploaded = await uploadImagesApi(files)
    const next = [...props.modelValue, ...uploaded.map((file) => file.url)]
    emit('update:modelValue', next)
  } finally {
    busy.value = false
    event.target.value = ''
  }
}
</script>

