<template>
  <div class="auth-page">
    <section class="auth-card glass">
      <div class="auth-card__hero">
        <div>
          <h1>欢迎回来</h1>
          <p>登录后即可浏览、发布和收藏校园二手物品。</p>
        </div>
      </div>

      <div class="auth-card__panel">
        <h2>登录</h2>
        <p style="color: var(--muted); margin-top: 0;">输入用户名和密码后即可进入系统。</p>
        <form class="auth-card__form" @submit.prevent="submit">
          <label class="field">
            <span class="field__label">用户名</span>
            <input
              v-model="form.username"
              class="field__input"
              autocomplete="username"
              required
              @input="errorMessage = ''"
            />
          </label>
          <label class="field">
            <span class="field__label">密码</span>
            <input
              v-model="form.password"
              class="field__input"
              type="password"
              autocomplete="current-password"
              required
              @input="errorMessage = ''"
            />
          </label>
          <button class="btn btn--primary" type="submit" :disabled="busy">{{ busy ? '登录中...' : '登录' }}</button>
          <router-link to="/register" class="btn btn--ghost">没有账号，去注册</router-link>
          <p v-if="errorMessage" class="form-alert form-alert--error" role="alert" aria-live="polite">
            {{ errorMessage }}
          </p>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getApiErrorMessage } from '../utils/error'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const busy = ref(false)
const errorMessage = ref('')

const form = reactive({
  username: '',
  password: '',
})

const submit = async () => {
  busy.value = true
  errorMessage.value = ''
  try {
    await auth.login(form)
    router.push(route.query.redirect || '/')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '用户名或密码错误')
  } finally {
    busy.value = false
  }
}
</script>
