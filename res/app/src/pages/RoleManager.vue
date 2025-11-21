<template>
  <div class="grid cols-2">
    <div class="card">
      <div class="flex" style="margin-bottom:8px"><strong>LLM玩家</strong><div class="space" /></div>
      <div class="grid">
        <select class="select" v-model="providerId">
          <option disabled value="">提供商/API/本地模型</option>
          <option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <input class="input" v-model="llmName" placeholder="名称" />
        <input class="input" v-model="model" placeholder="模型" />
        <div class="flex">
          <button class="button" @click="addLLM">添加</button>
        </div>
      </div>
      <div style="margin-top:12px" class="grid">
        <div class="muted">已添加</div>
        <div v-for="p in players.llmPlayers" :key="p.id" class="flex">
          <span>{{ p.name }} · {{ providerName(p.providerId) }} · {{ p.model || '未设定' }}</span>
          <div class="space" />
          <button class="button" @click="players.removePlayer(p.id)">移除</button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="flex" style="margin-bottom:8px"><strong>本人玩家</strong><div class="space" /></div>
      <div class="grid">
        <input class="input" v-model="meName" placeholder="名称" />
        <div class="flex">
          <button class="button" @click="addHuman">添加</button>
        </div>
      </div>
      <div style="margin-top:12px" class="grid">
        <div class="muted">已添加</div>
        <div v-for="p in players.humanPlayers" :key="p.id" class="flex">
          <span>{{ p.name }}</span>
          <div class="space" />
          <button class="button" @click="players.removePlayer(p.id)">移除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePlayersStore } from '@/stores/players'

const players = usePlayersStore()
const providerId = ref('')
const llmName = ref('')
const model = ref('')
const meName = ref('')

const providers = computed(() => players.providers)
function providerName(id: string) { return providers.value.find(x => x.id === id)?.name || '' }

function addLLM() {
  if (!providerId.value || !llmName.value.trim()) return
  players.addLLM({ name: llmName.value.trim(), providerId: providerId.value, model: model.value.trim() || undefined })
  llmName.value = ''
  model.value = ''
}

function addHuman() {
  if (!meName.value.trim()) return
  players.addHuman({ name: meName.value.trim() })
  meName.value = ''
}

onMounted(() => players.loadProviders())
</script>