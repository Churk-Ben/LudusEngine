<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-12 col-md-6">
        <n-card>
          <div class="d-flex align-items-center mb-2">
            <strong>{{ t("role.llm.title") }}</strong>
          </div>
          <div class="row g-2">
            <div class="col-12">
              <n-select
                v-model:value="providerId"
                :options="providerOptions"
                :placeholder="t('role.llm.providerPlaceholder')"
              />
            </div>
            <div class="col-12">
              <n-input
                v-model:value="llmName"
                :placeholder="t('role.common.namePlaceholder')"
              />
            </div>
            <div class="col-12">
              <n-input
                v-model:value="model"
                :placeholder="t('role.llm.modelPlaceholder')"
              />
            </div>
            <div class="col-12 d-flex">
              <div class="ms-auto">
                <n-button type="primary" @click="addLLM">{{
                  t("role.common.add")
                }}</n-button>
              </div>
            </div>
          </div>
          <div class="row g-2 mt-3">
            <div class="col-12 text-muted">{{ t("role.common.added") }}</div>
            <div
              class="col-12 d-flex"
              v-for="p in players.llmPlayers"
              :key="p.id"
            >
              <span
                >{{ p.name }} · {{ providerName(p.providerId) }} ·
                {{ p.model || t("role.common.notSet") }}</span
              >
              <div class="ms-auto">
                <n-button quaternary @click="players.removePlayer(p.id)">{{
                  t("role.common.remove")
                }}</n-button>
              </div>
            </div>
          </div>
        </n-card>
      </div>
      <div class="col-12 col-md-6">
        <n-card>
          <div class="d-flex align-items-center mb-2">
            <strong>{{ t("role.me.title") }}</strong>
          </div>
          <div class="row g-2">
            <div class="col-12">
              <n-input
                v-model:value="meName"
                :placeholder="t('role.common.namePlaceholder')"
              />
            </div>
            <div class="col-12 d-flex">
              <div class="ms-auto">
                <n-button type="primary" @click="addHuman">{{
                  t("role.common.add")
                }}</n-button>
              </div>
            </div>
          </div>
          <div class="row g-2 mt-3">
            <div class="col-12 text-muted">{{ t("role.common.added") }}</div>
            <div
              class="col-12 d-flex"
              v-for="p in players.humanPlayers"
              :key="p.id"
            >
              <span>{{ p.name }}</span>
              <div class="ms-auto">
                <n-button quaternary @click="players.removePlayer(p.id)">{{
                  t("role.common.remove")
                }}</n-button>
              </div>
            </div>
          </div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { NCard, NSelect, NInput, NButton } from "naive-ui";
import { usePlayersStore } from "@/stores/players";

const players = usePlayersStore();
const { t } = useI18n();
const providerId = ref("");
const llmName = ref("");
const model = ref("");
const meName = ref("");

const providers = computed(() => players.providers);
const providerOptions = computed(() =>
  providers.value.map((p) => ({ label: p.name, value: p.id }))
);
function providerName(id: string) {
  return providers.value.find((x) => x.id === id)?.name || "";
}

function addLLM() {
  if (!providerId.value || !llmName.value.trim()) return;
  players.addLLM({
    name: llmName.value.trim(),
    providerId: providerId.value,
    model: model.value.trim() || undefined,
  });
  llmName.value = "";
  model.value = "";
}

function addHuman() {
  if (!meName.value.trim()) return;
  players.addHuman({ name: meName.value.trim() });
  meName.value = "";
}

onMounted(() => players.loadProviders());
</script>
