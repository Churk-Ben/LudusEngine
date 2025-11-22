<template>
  <n-config-provider :theme="naiveTheme">
    <div class="app">
      <n-layout style="height: 100vh">
        <n-layout-header bordered>
          <div class="flex" style="padding: 0 12px; height: 56px">
            <span class="brand">LudusEngine</span>
            <span class="muted">语言类桌游平台</span>
            <div class="space" />
            <n-select style="width: 120px" v-model:value="locale" :options="localeOptions" @update:value="onLocale" />
            <n-button tertiary @click="toggleTheme">{{ themeLabel }}</n-button>
          </div>
        </n-layout-header>
        <n-layout has-sider style="height: calc(100vh - 56px)">
          <n-layout-sider width="240" bordered>
            <n-menu :options="menuOptions" :value="menuValue" @update:value="onMenu" />
          </n-layout-sider>
          <n-layout-content content-style="padding: 12px; min-height: 0;">
            <RouterView />
          </n-layout-content>
        </n-layout>
      </n-layout>
    </div>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter, RouterView } from 'vue-router'
import { NConfigProvider, NLayout, NLayoutHeader, NLayoutSider, NLayoutContent, NMenu, NSelect, NButton, darkTheme } from 'naive-ui'

const { locale } = useI18n()
const route = useRoute()
const router = useRouter()

const themeMode = ref<'light' | 'dark'>('light')
const naiveTheme = computed(() => (themeMode.value === 'dark' ? darkTheme : null))
const themeLabel = computed(() => (themeMode.value === 'light' ? '暗色' : '亮色'))


const localeOptions = [
  { label: '中文', value: 'zh-CN' },
  { label: 'English', value: 'en' }
]

const menuOptions = [
  { label: '角色管理', key: '/roles' },
  { label: '本地游戏', key: '/local' },
  { label: '联机游戏', key: '/online' }
]

const menuValue = ref(route.path)

function toggleTheme() {
  themeMode.value = themeMode.value === 'light' ? 'dark' : 'light'
}

function onLocale(v: string) {
  locale.value = v
}

function onMenu(key: string) {
  menuValue.value = key
  router.push(key)
}

onMounted(() => {
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  themeMode.value = prefersDark ? 'dark' : 'light'
})
</script>
