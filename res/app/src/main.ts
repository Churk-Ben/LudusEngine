import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import router from '@/router'
import '@/styles/theme.css'
import App from '../app.vue'

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  fallbackLocale: 'en',
  messages: {
    'zh-CN': {},
    en: {}
  }
})

createApp(App).use(createPinia()).use(router).use(i18n).mount('#app')