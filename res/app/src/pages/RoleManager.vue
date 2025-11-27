<template>
  <div class="container">
    <div class="row g-3">
      <div class="col-6">
        <n-card embedded :title="t('role.manager.title')">
          <template #header-extra>
            <n-button type="primary" @click="openCreate">
              {{ t("role.addRole") }}
            </n-button>
          </template>
          <div class="container flex-column mb-4">
            <section class="row my-2">
              <div class="col-12 mb-2">
                <strong>{{ t("role.sections.human") }}</strong>
              </div>
              <div class="col-12">
                <div v-if="players.human.length === 0">
                  <n-card size="small" :title="t('role.empty')" />
                </div>
                <div v-else v-for="p in players.human" :key="p.id">
                  <n-card
                    closable
                    class="mb-1"
                    size="small"
                    :title="p.name"
                    @close="removePlayer(p.id)"
                  >
                    <div class="text-truncate">{{ p.prefixPrompt }}</div>
                  </n-card>
                </div>
              </div>
            </section>

            <section class="row my-2">
              <div class="col-12 mb-2">
                <strong>{{ t("role.modal.type.online") }}</strong>
              </div>
              <div class="col-12">
                <div v-if="players.online.length === 0">
                  <n-card size="small" :title="t('role.empty')" />
                </div>
                <div v-else v-for="p in players.online" :key="p.id">
                  <n-card
                    closable
                    class="mb-1"
                    size="small"
                    :title="p.name"
                    @close="removePlayer(p.id)"
                  >
                    {{ providerName(p.providerId) }} - {{ p.model }}
                  </n-card>
                </div>
              </div>
            </section>

            <section class="row my-2">
              <div class="col-12 mb-2">
                <strong>{{ t("role.modal.type.local") }}</strong>
              </div>
              <div class="col-12">
                <div v-if="players.local.length === 0">
                  <n-card size="small" :title="t('role.empty')" />
                </div>
                <div v-else v-for="p in players.local" :key="p.id">
                  <n-card
                    closable
                    class="mb-1"
                    size="small"
                    :title="p.name"
                    @close="removePlayer(p.id)"
                  >
                    {{ p.modelPath }}
                  </n-card>
                </div>
              </div>
            </section>
          </div>
        </n-card>

        <n-modal
          v-model:show="showCreate"
          preset="card"
          transform-origin="center"
          :title="t('role.modal.title')"
          :style="{ width: '640px', maxWidth: '80vw', minHeight: '400px' }"
        >
          <div class="container">
            <div class="row g-2">
              <div class="col-12">
                <n-flex justify="space-between">
                  <label class="me-2 my-3" style="font-weight: bold">
                    {{ t("role.modal.type.label") }}
                  </label>

                  <n-radio-group class="mx-2 my-3" v-model:value="createType">
                    <n-radio value="human">
                      {{ t("role.modal.type.human") }}
                    </n-radio>
                    <n-radio value="online">
                      {{ t("role.modal.type.online") }}
                    </n-radio>
                    <n-radio value="local">
                      {{ t("role.modal.type.local") }}
                    </n-radio>
                  </n-radio-group>
                </n-flex>
              </div>

              <template v-if="createType === 'human'">
                <div class="col-12">
                  <n-input
                    v-model:value="roleName"
                    :placeholder="t('role.modal.fields.roleName')"
                  />
                </div>
                <div class="col-12">
                  <n-input
                    v-model:value="prefixPrompt"
                    type="textarea"
                    :placeholder="t('role.modal.fields.prefixPrompt')"
                    rows="6"
                  />
                </div>
              </template>

              <template v-if="createType === 'online'">
                <div class="col-12">
                  <n-select
                    v-model:value="providerId"
                    :options="providerOptions"
                    :placeholder="t('role.modal.fields.provider')"
                  />
                </div>
                <div class="col-12">
                  <n-input
                    v-model:value="modelName"
                    :placeholder="t('role.modal.fields.roleName')"
                  />
                </div>
                <div class="col-12">
                  <n-input
                    v-model:value="apiKey"
                    :placeholder="t('role.modal.fields.api')"
                    type="password"
                  />
                </div>
                <div class="col-12">
                  <n-input
                    v-model:value="roleName"
                    :placeholder="t('role.modal.fields.roleName')"
                  />
                </div>
              </template>

              <template v-if="createType === 'local'">
                <div class="col-12">
                  <n-input
                    v-model:value="roleName"
                    :placeholder="t('role.modal.fields.name')"
                  />
                </div>
                <div class="col-12">
                  <n-input
                    v-model:value="modelPath"
                    :placeholder="t('role.modal.fields.localPath')"
                  />
                </div>
                <div class="col-12">
                  <n-input
                    v-model:value="parameters"
                    :placeholder="t('role.modal.fields.parameters')"
                  />
                </div>
              </template>
            </div>
          </div>
          <template #footer>
            <n-flex justify="end">
              <n-button quaternary @click="closeCreate">
                {{ t("role.modal.actions.cancel") }}
              </n-button>
              <n-button type="primary" :disabled="!canCreate" @click="doCreate">
                {{ t("role.modal.actions.create") }}
              </n-button>
            </n-flex>
          </template>
        </n-modal>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import {
  NCard,
  NButton,
  NModal,
  NRadioGroup,
  NRadio,
  NSelect,
  NInput,
  NFlex,
} from "naive-ui";
import * as playerService from "@/services/players";

const { t } = useI18n();
const debugMode = true;

const players = ref<playerService.AllPlayers>({
  human: [],
  online: [],
  local: [],
});
const providers = ref<playerService.LLMProvider[]>([]);

// 模态框
const showCreate = ref(false);
const createType = ref<"human" | "online" | "local">("human");
const roleName = ref("");
const providerId = ref("");
const modelName = ref("");
const apiKey = ref("");
const modelPath = ref("");
const prefixPrompt = ref("");
const parameters = ref("");

const providerOptions = computed(() =>
  providers.value.map((p) => ({ label: p.name, value: p.id }))
);
function providerName(id: string) {
  return providers.value.find((x) => x.id === id)?.name || id;
}

function openCreate() {
  resetForm();
  showCreate.value = true;
}

function closeCreate() {
  showCreate.value = false;
}

function resetForm() {
  if (players.value.human.length === 0) {
    createType.value = "human";
  } else {
    createType.value = "online";
  }
  roleName.value = "";
  providerId.value = "";
  modelName.value = "";
  apiKey.value = "";
  modelPath.value = "";
  prefixPrompt.value = "";
  parameters.value = "";
}

const canCreate = computed(() => {
  if (createType.value === "human") {
    return !!roleName.value.trim() || debugMode === true;
  }
  if (createType.value === "online") {
    return (
      (!!roleName.value.trim() &&
        !!providerId.value &&
        !!modelName.value.trim() &&
        !!apiKey.value.trim()) ||
      debugMode === true
    );
  }
  if (createType.value === "local") {
    const path = modelPath.value.trim();
    const isAbs = /^[a-zA-Z]:[\\/]/.test(path) || path.startsWith("/");
    return (!!roleName.value.trim() && isAbs) || debugMode === true;
  }
  return false;
});

async function removePlayer(id: string) {
  players.value.human = players.value.human.filter((p) => p.id !== id);
  players.value.online = players.value.online.filter((p) => p.id !== id);
  players.value.local = players.value.local.filter((p) => p.id !== id);
  await playerService.savePlayers(players.value);
}

async function doCreate() {
  const newPlayer = {
    id: crypto.randomUUID(),
    name: roleName.value.trim(),
  };

  if (createType.value === "human") {
    players.value.human.push({
      ...newPlayer,
      prefixPrompt: prefixPrompt.value,
    });
  } else if (createType.value === "online") {
    players.value.online.push({
      ...newPlayer,
      providerId: providerId.value,
      model: modelName.value.trim(),
      apiKey: apiKey.value.trim(),
    });
  } else if (createType.value === "local") {
    players.value.local.push({
      ...newPlayer,
      modelPath: modelPath.value.trim(),
      parameters: parameters.value.trim(),
    });
  }

  await playerService.savePlayers(players.value);
  closeCreate();
}

onMounted(async () => {
  players.value = await playerService.getPlayers();
  providers.value = await playerService.getProviders();
});
</script>
