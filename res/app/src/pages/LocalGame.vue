<template>
  <div class="grid">
    <div class="card grid">
      <strong>选择本地游戏</strong>
      <select class="select" v-model="gameId">
        <option disabled value="">请选择</option>
        <option v-for="g in games" :key="g" :value="g">{{ g }}</option>
      </select>
    </div>

    <div class="card grid">
      <strong>选择参与玩家</strong>
      <div class="grid">
        <div class="flex" v-for="p in allPlayers" :key="p.id">
          <label class="flex" style="gap:6px">
            <input type="checkbox" :value="p.id" v-model="selectedPlayerIds" />
            <span>{{ p.name }}</span>
          </label>
        </div>
      </div>
      <div class="flex">
        <div class="space" />
        <button class="button" :disabled="!canStart" @click="start">进入游戏界面</button>
      </div>
    </div>

    <div v-if="started" class="grid cols-2">
      <ChatWindow />
      <div class="grid">
        <GameFlowHint :steps="steps" :index="flowIndex" />
        <PluginHost>
          <div class="muted">游戏插件预留空间，供自定义风格与交互</div>
        </PluginHost>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ChatWindow from '@/components/ChatWindow.vue'
import GameFlowHint from '@/components/GameFlowHint.vue'
import PluginHost from '@/components/PluginHost.vue'
import { usePlayersStore } from '@/stores/players'

const players = usePlayersStore()
const games = ref<string[]>([])
const gameId = ref('')
const selectedPlayerIds = ref<string[]>([])
const started = ref(false)
const steps = ['准备', '发牌/分配角色', '游戏进行', '结算']
const flowIndex = ref(0)

const allPlayers = computed(() => [...players.humanPlayers, ...players.llmPlayers])
const canStart = computed(() => !!gameId.value && selectedPlayerIds.value.length >= 2)

async function loadGames() {
  const r = await fetch('/api/games')
  if (r.ok) games.value = await r.json()
}

function start() {
  started.value = true
  flowIndex.value = 0
}

onMounted(() => loadGames())
</script>