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
          <n-spin :show="loading">
            <div class="container flex-column mb-4">
              <section class="row my-2">
                <div class="col-12 mb-2">
                  <strong>{{ t("role.sections.human") }}</strong>
                </div>
                <div class="col-12">
                  <n-scrollbar style="max-height: 20vh">
                    <div v-if="players.human.length === 0">
                      <n-card size="small" :title="t('role.empty')" />
                    </div>
                    <div v-else v-for="p in players.human" :key="p.uuid">
                      <n-card
                        closable
                        class="mb-1"
                        size="small"
                        :title="p.name"
                        @close="handleRemovePlayer(p.uuid)"
                      >
                        <div class="text-truncate">{{ p.prefixPrompt }}</div>
                      </n-card>
                    </div>
                  </n-scrollbar>
                </div>
              </section>

              <section class="row my-2">
                <div class="col-12 mb-2">
                  <strong>{{ t("role.modal.type.online") }}</strong>
                </div>
                <div class="col-12">
                  <n-scrollbar style="max-height: 20vh">
                    <div v-if="players.online.length === 0">
                      <n-card size="small" :title="t('role.empty')" />
                    </div>
                    <div v-else v-for="p in players.online" :key="p.uuid">
                      <n-card
                        closable
                        class="mb-1"
                        size="small"
                        :title="p.name"
                        @close="handleRemovePlayer(p.uuid)"
                      >
                        {{ providerName(p.providerId) }} - {{ p.model }}
                      </n-card>
                    </div>
                  </n-scrollbar>
                </div>
              </section>

              <section class="row my-2">
                <div class="col-12 mb-2">
                  <strong>{{ t("role.modal.type.local") }}</strong>
                </div>
                <div class="col-12">
                  <n-scrollbar style="max-height: 20vh">
                    <div v-if="players.local.length === 0">
                      <n-card size="small" :title="t('role.empty')" />
                    </div>
                    <div v-else v-for="p in players.local" :key="p.uuid">
                      <n-card
                        closable
                        class="mb-1"
                        size="small"
                        :title="p.name"
                        @close="handleRemovePlayer(p.uuid)"
                      >
                        {{ p.modelPath }}
                      </n-card>
                    </div>
                  </n-scrollbar>
                </div>
              </section>
            </div>
          </n-spin>
        </n-card>

        <n-modal
          v-model:show="showCreate"
          preset="card"
          transform-origin="center"
          :title="t('role.modal.title')"
          :style="{ width: '640px', maxWidth: '80vw', minHeight: '400px' }"
        >
          <div class="container">
            <n-spin :show="providersLoading">
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
                      rows="5"
                    />
                  </div>
                </template>

                <template v-if="createType === 'online'">
                  <div class="col-12">
                    <n-input
                      v-model:value="roleName"
                      :placeholder="t('role.modal.fields.roleName')"
                    />
                  </div>
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
                      :placeholder="t('role.modal.fields.modelName')"
                    />
                  </div>
                  <div class="col-12">
                    <n-input
                      v-model:value="apiKey"
                      :placeholder="t('role.modal.fields.api')"
                      type="password"
                    />
                  </div>
                </template>

                <template v-if="createType === 'local'">
                  <div class="col-12">
                    <n-input
                      v-model:value="roleName"
                      :placeholder="t('role.modal.fields.roleName')"
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
                      type="textarea"
                      :placeholder="t('role.modal.fields.parameters')"
                      rows="3"
                    />
                  </div>
                </template>
              </div>
            </n-spin>
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
import { h, ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import {
  NCard,
  NButton,
  NModal,
  NScrollbar,
  NRadioGroup,
  NRadio,
  NSelect,
  NInput,
  NFlex,
  NSpin,
  NAlert,
  useMessage,
} from "naive-ui";
import * as playerService from "@/services/players";

const { t } = useI18n();

const loading = ref(true);
const players = ref<playerService.AllPlayers>({
  human: [],
  online: [],
  local: [],
});
const providers = ref<playerService.LLMProvider[]>([]);
const providersLoading = ref(false);

// 消息提示
const message = useMessage();
import type { MessageRenderMessage } from "naive-ui";

// 应用消息提示
const renderMessage: MessageRenderMessage = (props) => {
  const { type } = props;
  return h(
    NAlert,
    {
      closable: props.closable,
      onClose: props.onClose,
      type: type === "loading" ? "default" : type,
      title: t("online.lobbyTitle"),
      style: {
        width: "300px",
        maxWidth: "calc(100vw - 32px)",
        backdropFilter: "blur(10px)",
      },
    },
    {
      default: () => props.content,
    }
  );
};

const { info, success, warning, error } = useMessage();

function showInfo(msg: string) {
  info(msg, {
    render: renderMessage,
    closable: true,
  });
}

function showSuccess(msg: string) {
  success(msg, {
    render: renderMessage,
    closable: true,
  });
}

function showWarning(msg: string) {
  warning(msg, {
    render: renderMessage,
    closable: true,
  });
}

function showError(msg: string) {
  error(msg, {
    render: renderMessage,
    closable: true,
  });
}

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

async function openCreate() {
  resetForm();
  showCreate.value = true;

  if (!providers.value.length) {
    providersLoading.value = true;
    try {
      providers.value = await playerService.getProviders();
    } catch (err) {
      showError("Failed to load providers");
    } finally {
      providersLoading.value = false;
    }
  }
}

function closeCreate() {
  showCreate.value = false;
}

function resetForm() {
  createType.value = "human";
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
    return !!roleName.value.trim();
  }
  if (createType.value === "online") {
    return (
      !!roleName.value.trim() &&
      !!providerId.value &&
      !!modelName.value.trim() &&
      !!apiKey.value.trim()
    );
  }
  if (createType.value === "local") {
    const path = modelPath.value.trim();
    const isAbs = /^[a-zA-Z]:[\\/]/.test(path) || path.startsWith("/");
    return !!roleName.value.trim() && isAbs;
  }
  return false;
});

async function doCreate() {
  let newPlayer:
    | Omit<playerService.HumanPlayer, "uuid">
    | Omit<playerService.OnlinePlayer, "uuid">
    | Omit<playerService.LocalPlayer, "uuid">;

  const basePlayer = {
    name: roleName.value.trim(),
  };

  switch (createType.value) {
    case "human":
      newPlayer = {
        ...basePlayer,
        type: "human",
        prefixPrompt: prefixPrompt.value,
      };
      break;
    case "online":
      newPlayer = {
        ...basePlayer,
        type: "online",
        providerId: providerId.value,
        model: modelName.value.trim(),
        apiKey: apiKey.value.trim(),
      };
      break;
    case "local":
      newPlayer = {
        ...basePlayer,
        type: "local",
        modelPath: modelPath.value.trim(),
        parameters: parameters.value.trim(),
      };
      break;
    default:
      showError("Invalid create type");
      return;
  }

  const createdPlayer = await playerService.addPlayer(
    createType.value,
    newPlayer
  );

  if (createdPlayer) {
    // @ts-ignore
    players.value[createType.value].push(createdPlayer);
  }

  closeCreate();
}

async function handleRemovePlayer(pid: string) {
  const success = await playerService.removePlayer(pid);
  if (success) {
    for (const type in players.value) {
      // @ts-ignore
      players.value[type] = players.value[type].filter((p) => p.uuid !== pid);
    }
  }
}

onMounted(async () => {
  try {
    players.value = await playerService.getPlayers();
  } finally {
    loading.value = false;
  }
});
</script>
