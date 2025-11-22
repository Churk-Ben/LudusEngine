<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-12">
        <n-card>
          <div class="row g-2">
            <div class="col-12">
              <strong>{{ t("local.selectGameTitle") }}</strong>
            </div>
            <div class="col-12">
              <n-select
                v-model:value="gameId"
                :options="gameOptions"
                :placeholder="t('local.selectPlaceholder')"
              />
            </div>
          </div>
        </n-card>
      </div>

      <div class="col-12">
        <n-card>
          <div class="row g-2">
            <div class="col-12">
              <strong>{{ t("local.selectPlayersTitle") }}</strong>
            </div>
            <div class="col-12">
              <div class="row g-2">
                <div
                  class="col-12 d-flex align-items-center"
                  v-for="p in allPlayers"
                  :key="p.id"
                >
                  <n-checkbox
                    :value="p.id"
                    v-model:checked="checkedMap[p.id]"
                    >{{ p.name }}</n-checkbox
                  >
                </div>
              </div>
            </div>
            <div class="col-12 d-flex">
              <div class="ms-auto">
                <n-button type="primary" :disabled="!canStart" @click="start">{{
                  t("local.startButton")
                }}</n-button>
              </div>
            </div>
          </div>
        </n-card>
      </div>

      <div class="col-12" v-if="started">
        <div class="row g-3">
          <div class="col-12 col-md-6">
            <ChatWindow />
          </div>
          <div class="col-12 col-md-6">
            <div class="row g-3">
              <div class="col-12">
                <GameFlowHint :steps="steps" :index="flowIndex" />
              </div>
              <div class="col-12">
                <PluginHost>
                  <div class="text-muted">
                    {{ t("local.pluginPlaceholder") }}
                  </div>
                </PluginHost>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { NCard, NSelect, NCheckbox, NButton } from "naive-ui";
import ChatWindow from "@/components/ChatWindow.vue";
import GameFlowHint from "@/components/GameFlowHint.vue";
import PluginHost from "@/components/PluginHost.vue";
import { usePlayersStore } from "@/stores/players";

const players = usePlayersStore();
const { t } = useI18n();
const games = ref<string[]>([]);
const gameId = ref("");
const started = ref(false);
const steps = computed(() => [
  t("local.steps.prepare"),
  t("local.steps.deal"),
  t("local.steps.play"),
  t("local.steps.result"),
]);
const flowIndex = ref(0);

const allPlayers = computed(() => [
  ...players.humanPlayers,
  ...players.llmPlayers,
]);
const checkedMap = ref<Record<string, boolean>>({});
const selectedPlayerIds = computed(() =>
  Object.entries(checkedMap.value)
    .filter(([, v]) => v)
    .map(([k]) => k)
);
const canStart = computed(
  () => !!gameId.value && selectedPlayerIds.value.length >= 2
);

const gameOptions = computed(() =>
  games.value.map((g) => ({ label: g, value: g }))
);

async function loadGames() {
  const r = await fetch("/api/games");
  if (r.ok) games.value = await r.json();
}

function start() {
  started.value = true;
  flowIndex.value = 0;
}

onMounted(() => loadGames());
</script>
