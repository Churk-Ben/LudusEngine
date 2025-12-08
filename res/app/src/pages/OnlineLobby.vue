<template>
  <div class="container">
    <div
      class="text-muted"
      style="position: absolute; top: 10px; left: 10px; font-size: 12px"
    >
      {{ socketConnected ? "Socket已连接" : "Socket未连接" }}
    </div>
    <div class="row g-3">
      <div class="col-6">
        <n-card embedded>
          <n-result
            status="info"
            :title="t('online.lobbyTitle')"
            :description="t('online.notOpen')"
          >
            <template #footer>
              <n-space vertical>
                <n-button @click="$router.push('/roles')">
                  {{ t("role.title") }}
                </n-button>
                <n-button @click="$router.push('/local')">
                  {{ t("local.title") }}
                </n-button>
                <n-button @click="test">
                  {{ t("online.testInfo") }}
                </n-button>
              </n-space>
            </template>
          </n-result>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NResult, NCard, NButton, NSpace, NAlert, useMessage } from "naive-ui";
import { ref, onMounted, h, onUnmounted, inject } from "vue";
import { useI18n } from "vue-i18n";
import type { Socket } from "socket.io-client";
const { t } = useI18n();

// socket 组件
const socket = inject<Socket>("socket");
const socketConnected = ref(false);
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

function test() {
  info(t("online.testInfo"), {
    render: renderMessage,
    closable: true,
  });

  success(t("online.testSuccess"), {
    render: renderMessage,
    closable: true,
  });

  warning(t("online.testWarning"), {
    render: renderMessage,
    closable: true,
  });

  error(t("online.testError"), {
    render: renderMessage,
    closable: true,
  });
}

onMounted(() => {
  if (socket) {
    socketConnected.value = socket.connected;
    socket.on("connect", () => {
      socketConnected.value = true;
    });
    socket.on("disconnect", () => {
      socketConnected.value = false;
    });
  }
});

onUnmounted(() => {
  if (socket) {
    socket.off("connect");
    socket.off("disconnect");
  }
});
</script>
