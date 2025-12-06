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
                <n-button @click="testErr">
                  {{ t("online.testErr") }}
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
      title: "你看你手上拿的是什么啊",
      style: {
        boxShadow: "var(--n-box-shadow)",
        maxWidth: "calc(100vw - 32px)",
        width: "480px",
      },
    },
    {
      default: () => props.content,
    }
  );
};

const { info, success, warning, error } = useMessage();

function testErr() {
  info("这是一个信息提示", {
    render: renderMessage,
    closable: true,
  });

  success("这是一个成功提示", {
    render: renderMessage,
    closable: true,
  });

  warning("这是一个警告提示", {
    render: renderMessage,
    closable: true,
  });

  error("这是一个错误提示", {
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
