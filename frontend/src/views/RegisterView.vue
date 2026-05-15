<template>
  <div class="auth-page">
    <section class="auth-card glass">
      <div class="auth-card__hero">
        <div>
          <h1>加入校园集市</h1>
          <p>注册账号后即可发布闲置物品、收藏好物并与卖家沟通。</p>
        </div>
      </div>

      <div class="auth-card__panel">
        <h2>注册</h2>
        <p style="color: var(--muted); margin-top: 0;">填写基础信息即可创建账号。</p>
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
            <span class="field__label">邮箱</span>
            <input v-model="form.email" class="field__input" type="email" autocomplete="email" @input="errorMessage = ''" />
          </label>
          <label class="field">
            <span class="field__label">昵称</span>
            <input v-model="form.nickname" class="field__input" @input="errorMessage = ''" />
          </label>
          <label class="field">
            <span class="field__label">密码</span>
            <input
              v-model="form.password"
              class="field__input"
              type="password"
              autocomplete="new-password"
              required
              @input="errorMessage = ''"
            />
          </label>
          <button class="btn btn--primary" type="submit" :disabled="busy">{{ busy ? '注册中...' : '注册' }}</button>
          <router-link to="/login" class="btn btn--ghost">已有账号，去登录</router-link>
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
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getApiErrorMessage } from '../utils/error'

const auth = useAuthStore()
const router = useRouter()
const busy = ref(false)
const errorMessage = ref('')

const form = reactive({
  username: '',
  email: '',
  nickname: '',
  password: '',
})

const submit = async () => {
  busy.value = true
  errorMessage.value = ''
  try {
    await auth.register(form)
    router.push('/')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '注册失败，请检查输入信息')
  } finally {
    busy.value = false
  }
}
</script>
