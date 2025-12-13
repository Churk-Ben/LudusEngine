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

          <n-spin :show="loading">
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
          </n-spin>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h, inject } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  NCard,
  NSelect,
  NButton,
  NTransfer,
  NTree,
  NSpin,
  useMessage,
} from "naive-ui";
import type { TransferRenderSourceList, TreeOption } from "naive-ui";
import * as playerService from "@/services/players";
import * as gameService from "@/services/games";
import type { Socket } from "socket.io-client";

const { t } = useI18n();
const router = useRouter();
const socket = inject<Socket>("socket");
const connected = ref(false);
const started = ref(false);
const gameId = ref("");
const loading = ref(true);

const games = ref<string[]>([]);
const selectedPlayerIds = ref<string[]>([]);
const players = ref<playerService.AllPlayers>({
  human: [],
  online: [],
  local: [],
});

// 配置穿梭框部分
type Option = { label: string; value: string; children?: Option[] };
const treeData = computed<Option[]>(() => {
  const humans: Option[] = players.value.human.map((p) => ({
    label: p.name,
    value: p.uuid,
  }));
  const onlines: Option[] = players.value.online.map((p) => ({
    label: p.name,
    value: p.uuid,
  }));
  const locals: Option[] = players.value.local.map((p) => ({
    label: p.name,
    value: p.uuid,
  }));
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
      if (it.children && it.children.length) {
        walk(it.children);
      } else {
        result.push({ label: it.label, value: it.value });
      }
    }
  }
  walk(list);
  if (!result.length) {
    return [{ label: t("role.empty"), value: "__empty" }];
  }
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

const canStart = computed(
  () => !!gameId.value && selectedPlayerIds.value.length >= 2
);

const gameOptions = computed(() =>
  games.value.map((g) => ({ label: g, value: g }))
);

function start() {
  if (socket) {
    connected.value = true;
    const sessionId = Math.random().toString(36).substring(2, 6);

    // 跳转到游戏页面
    router.push({
      path: `/gaming/${sessionId}`,
      query: {
        gameId: gameId.value,
        playerIds: JSON.stringify(selectedPlayerIds.value),
      },
    });
    started.value = true;
  } else {
    console.error("socket 未连接");
  }
}

// 载入游戏
onMounted(async () => {
  try {
    const [loadedGames, loadedPlayers] = await Promise.all([
      gameService.getGames(),
      playerService.getPlayers(),
    ]);
    games.value = loadedGames;
    players.value = loadedPlayers;
  } finally {
    loading.value = false;
  }
});
</script>
