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
              </n-space>
            </template>
          </n-result>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NResult, NCard, NButton, NSpace } from "naive-ui";
import { ref, onMounted, onUnmounted, inject } from "vue";
import { useI18n } from "vue-i18n";
import type { Socket } from "socket.io-client";
const { t } = useI18n();

// socket 组件
const socket = inject<Socket>("socket");
const socketConnected = ref(false);
const lastPong = ref<any>(null);

onMounted(() => {
  if (socket) {
    socketConnected.value = socket.connected;
    socket.on("connect", () => {
      socketConnected.value = true;
    });
    socket.on("disconnect", () => {
      socketConnected.value = false;
    });
    socket.on("server:ready", () => {
      socketConnected.value = true;
    });
    socket.on("server:pong", (data: any) => {
      lastPong.value = data;
    });
  }
});

onUnmounted(() => {
  if (socket) {
    socket.off("connect");
    socket.off("disconnect");
    socket.off("server:ready");
    socket.off("server:pong");
  }
});
</script>
