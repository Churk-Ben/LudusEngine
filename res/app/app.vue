<template>
  <div class="app" :data-theme="theme">
    <header class="header">
      <div class="flex">
        <span class="brand">LudusEngine</span>
        <span class="muted">语言类桌游平台</span>
      </div>
      <div class="toolbar">
        <select class="select" v-model="locale" @change="onLocale">
          <option value="zh-CN">中文</option>
          <option value="en">English</option>
        </select>
        <button class="button" @click="toggleTheme">{{ themeLabel }}</button>
      </div>
    </header>
    <div class="container">
      <aside class="sidebar">
        <nav class="nav">
          <RouterLink to="/roles" active-class="active">角色管理</RouterLink>
          <RouterLink to="/local" active-class="active">本地游戏</RouterLink>
          <RouterLink to="/online" active-class="active">联机游戏</RouterLink>
        </nav>
      </aside>
      <main class="main">
        <RouterView v-slot="{ Component }">
          <transition name="fade"><component :is="Component" /></transition>
        </RouterView>
      </main>
    </div>
  </div>
  
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, RouterView } from 'vue-router'

const theme = ref<'light' | 'dark'>('light')
const themeLabel = computed(() => (theme.value === 'light' ? '暗色' : '亮色'))
const { locale } = useI18n()

function applyTheme() {
  document.documentElement.setAttribute('data-theme', theme.value === 'light' ? '' : 'dark')
}

function toggleTheme() {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
  applyTheme()
}

function onLocale() {}

onMounted(() => {
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  theme.value = prefersDark ? 'dark' : 'light'
  applyTheme()
})
</script>