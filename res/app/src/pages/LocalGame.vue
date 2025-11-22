<template>
  <div class="grid" style="min-height: 0;">
    <n-card>
      <div class="grid">
        <strong>选择本地游戏</strong>
        <n-select v-model:value="gameId" :options="gameOptions" placeholder="请选择" />
      </div>
    </n-card>

    <n-card>
      <div class="grid">
        <strong>选择参与玩家</strong>
        <div class="grid">
          <div class="flex" v-for="p in allPlayers" :key="p.id">
            <n-checkbox :value="p.id" v-model:checked="checkedMap[p.id]">{{ p.name }}</n-checkbox>
          </div>
        </div>
        <div class="flex">
          <div class="space" />
          <n-button type="primary" :disabled="!canStart" @click="start">进入游戏界面</n-button>
        </div>
      </div>
    </n-card>

    <div v-if="started" class="grid cols-2" style="min-height: 0;">
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
import { NCard, NSelect, NCheckbox, NButton } from 'naive-ui'
import ChatWindow from '@/components/ChatWindow.vue'
import GameFlowHint from '@/components/GameFlowHint.vue'
import PluginHost from '@/components/PluginHost.vue'
import { usePlayersStore } from '@/stores/players'

const players = usePlayersStore()
const games = ref<string[]>([])
const gameId = ref('')
const started = ref(false)
const steps = ['准备', '发牌/分配角色', '游戏进行', '结算']
const flowIndex = ref(0)

const allPlayers = computed(() => [...players.humanPlayers, ...players.llmPlayers])
const checkedMap = ref<Record<string, boolean>>({})
const selectedPlayerIds = computed(() => Object.entries(checkedMap.value).filter(([, v]) => v).map(([k]) => k))
const canStart = computed(() => !!gameId.value && selectedPlayerIds.value.length >= 2)

const gameOptions = computed(() => games.value.map(g => ({ label: g, value: g })))

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