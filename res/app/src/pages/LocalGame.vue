<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-12 col-md-8" v-if="!started">
        <n-card embedded :title="t('local.configTitle')">
          <template #header-extra>
            <n-button type="primary" :disabled="!canStart" @click="start">
              {{ t("local.startButton") }}
            </n-button>
          </template>

          <div class="container flex-column mb-4">
            <section class="row my-2">
              <div class="col-12 mb-2">
                <strong>{{ t("local.selectGameTitle") }}</strong>
              </div>
              <div class="col-12">
                <n-select
                  v-model:value="gameId"
                  :options="gameOptions"
                  :placeholder="t('local.selectPlaceholder')"
                />
              </div>
            </section>

            <section class="row my-2">
              <div class="col-12 mb-2">
                <strong>{{ t("local.selectPlayersTitle") }}</strong>
              </div>
              <div class="col-12">
                <n-transfer
                  v-model:value="selectedPlayerIds"
                  :options="transferOptions"
                  :render-source-list="renderSourceList"
                  source-filterable
                  target-filterable
                />
              </div>
            </section>
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
import { ref, computed, onMounted, h } from "vue";
import { useI18n } from "vue-i18n";
import { NCard, NSelect, NCheckbox, NButton, NTransfer, NTree } from "naive-ui";
import type { TransferRenderSourceList, TreeOption } from "naive-ui";
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

const providerMap = computed(() => {
  const m: Record<string, { kind: "api" | "local" }> = {};
  for (const p of players.providers) m[p.id] = { kind: p.kind } as any;
  return m;
});

type Option = { label: string; value: string; children?: Option[] };

const treeData = computed<Option[]>(() => {
  const humans: Option[] = players.humanPlayers.map((p) => ({
    label: p.name,
    value: p.id,
  }));
  const onlines: Option[] = players.llmPlayers
    .filter((p) => providerMap.value[p.providerId]?.kind === "api")
    .map((p) => ({ label: p.name, value: p.id }));
  const locals: Option[] = players.llmPlayers
    .filter((p) => providerMap.value[p.providerId]?.kind === "local")
    .map((p) => ({ label: p.name, value: p.id }));
  return [
    {
      label: t("role.modal.type.human"),
      value: "__group_human",
      children: humans,
    },
    {
      label: t("role.modal.type.online"),
      value: "__group_online",
      children: onlines,
    },
    {
      label: t("role.modal.type.local"),
      value: "__group_local",
      children: locals,
    },
  ];
});

function flattenLeaves(list?: Option[]): { label: string; value: string }[] {
  const result: { label: string; value: string }[] = [];
  function walk(items: Option[] = []) {
    for (const it of items) {
      if (it.children && it.children.length) walk(it.children);
      else result.push({ label: it.label, value: it.value });
    }
  }
  walk(list);
  if (!result.length) return [{ label: t("role.empty"), value: "__empty" }];
  return result;
}

const transferOptions = computed(() => flattenLeaves(treeData.value));

const renderSourceList: TransferRenderSourceList = ({ onCheck, pattern }) => {
  return h(NTree, {
    style: "margin: 0 4px;",
    keyField: "value",
    checkable: true,
    selectable: false,
    blockLine: true,
    checkOnClick: true,
    cascade: true,
    data: treeData.value as unknown as TreeOption[],
    pattern,
    checkedKeys: selectedPlayerIds.value,
    onUpdateCheckedKeys: (keys: Array<string | number>) => {
      const filtered = (keys as string[]).filter(
        (k) => !k.startsWith("__group_")
      );
      onCheck(filtered);
    },
  });
};

const selectedPlayerIds = ref<string[]>([]);

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