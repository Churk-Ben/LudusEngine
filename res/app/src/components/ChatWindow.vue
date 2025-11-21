<template>
  <div class="card" style="height: 420px; display: grid; grid-template-rows: 1fr auto;">
    <div style="overflow: auto; display: grid; gap: 8px;">
      <div v-for="m in messages" :key="m.id" class="flex">
        <strong>{{ m.author }}</strong>
        <span class="muted">{{ m.time }}</span>
        <div class="space" />
        <span>{{ m.text }}</span>
      </div>
    </div>
    <div class="flex">
      <input class="input" v-model="draft" placeholder="输入消息" @keydown.enter="send" />
      <button class="button" @click="send">发送</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Msg { id: string; author: string; text: string; time: string }

const messages = ref<Msg[]>([])
const draft = ref('')

function send() {
  if (!draft.value.trim()) return
  messages.value.push({ id: crypto.randomUUID(), author: '我', text: draft.value.trim(), time: new Date().toLocaleTimeString() })
  draft.value = ''
}
</script>