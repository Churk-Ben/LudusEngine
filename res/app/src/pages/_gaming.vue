<template>
  <div class="gaming-page">
    <!-- Left Column: Game Header & Messages -->
    <div class="gaming-left-column" style="">
      <!-- Top Header: Game Name & Status -->
      <n-card size="small">
        <n-page-header>
          <template #title>
            {{ gameInfo.name }}
          </template>
          <template #extra>
            <n-tag :type="gameInfo.statusType || 'default'">
              {{ gameInfo.status }}
            </n-tag>
          </template>
        </n-page-header>
      </n-card>

      <!-- Message Container -->
      <div class="message-container">
        <n-scrollbar style="height: 100%" content-style="padding: 16px;">
          <n-list :bordered="false">
            <n-list-item v-for="(msg, index) in messages" :key="index">
              <div class="message-item">
                <n-thing :title="msg.sender">
                  <template #description>
                    <span style="font-size: 12px; opacity: 0.8">
                      {{ msg.time }}
                    </span>
                  </template>
                  {{ msg.content }}
                </n-thing>
              </div>
            </n-list-item>
          </n-list>
        </n-scrollbar>
      </div>

      <!-- Bottom: Input Area -->
      <div class="input-container gap-2 mb-1">
        <n-input
          v-model:value="inputValue"
          size="large"
          type="text"
          placeholder="输入消息..."
          @keyup.enter="sendMessage"
        />
        <n-button
          type="primary"
          size="large"
          @click="sendMessage"
          :disabled="!inputValue.trim()"
        >
          {{ $t("发送") }}
        </n-button>
      </div>
    </div>

    <!-- Right Column: Player List -->
    <div class="gaming-right-column">
      <n-card
        title="玩家列表"
        style="height: 100%"
        content-style="padding: 0; overflow-y: auto;"
        header-style="padding: 16px; border-bottom: 1px solid var(--n-border-color);"
      >
        <n-list hoverable clickable>
          <n-list-item v-for="player in players" :key="player.id">
            <n-thing>
              <template #avatar>
                <n-avatar round size="small">{{
                  player.name.charAt(0).toUpperCase()
                }}</n-avatar>
              </template>
              <template #header>
                {{ player.name }}
              </template>
              <template #description>
                {{ player.status }}
              </template>
            </n-thing>
          </n-list-item>
          <!-- Default Card if no players -->
          <div v-if="players.length === 0" style="padding: 16px">
            <n-card embedded>
              <n-result
                status="info"
                title="等待玩家"
                description="暂无玩家加入"
                size="small"
              />
            </n-card>
          </div>
        </n-list>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted, h } from "vue";
import {
  NCard,
  NPageHeader,
  NTag,
  NList,
  NListItem,
  NThing,
  NAvatar,
  NInput,
  NInputGroup,
  NButton,
  NScrollbar,
  NResult,
  NAlert,
  useMessage,
} from "naive-ui";
import type { MessageRenderMessage } from "naive-ui";
import type { Socket } from "socket.io-client";

// Types
interface GameInfo {
  name: string;
  status: string;
  statusType?: "default" | "success" | "warning" | "error" | "info";
}

interface Player {
  id: string;
  name: string;
  status: string;
}

interface ChatMessage {
  sender: string;
  content: string;
  time: string;
}

// State
const gameInfo = ref<GameInfo>({
  name: "未连接游戏",
  status: "等待连接",
  statusType: "default",
});
const players = ref<Player[]>([]);
const messages = ref<ChatMessage[]>([]);
const inputValue = ref("");

// Socket
const socket = inject<Socket>("socket");

// Message Provider Configuration (Reference from OnlineLobby.vue)
const renderMessage: MessageRenderMessage = (props) => {
  const { type } = props;
  return h(
    NAlert,
    {
      closable: props.closable,
      onClose: props.onClose,
      type: type === "loading" ? "default" : type,
      title: "你看你手上拿的是什么啊", // Keep consistent with OnlineLobby.vue
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

const message = useMessage();

// Custom message methods
const showInfo = (content: string) =>
  message.info(content, { render: renderMessage, closable: true });
const showSuccess = (content: string) =>
  message.success(content, { render: renderMessage, closable: true });
const showWarning = (content: string) =>
  message.warning(content, { render: renderMessage, closable: true });
const showError = (content: string) =>
  message.error(content, { render: renderMessage, closable: true });

// Socket Event Handlers
onMounted(() => {
  if (!socket) {
    showError("Socket未连接");
    return;
  }

  // 1. Game Info Update
  socket.on("game:info", (data: GameInfo) => {
    gameInfo.value = data;
  });

  // 2. Player List Update
  socket.on("game:players", (data: Player[]) => {
    players.value = data;
  });

  // 3. Incoming Message
  socket.on("game:message", (data: ChatMessage) => {
    messages.value.push(data);
    // TODO: Scroll to bottom logic if needed
  });

  // 4. Error/Notification from server
  socket.on("game:notification", (data: { type: string; content: string }) => {
    switch (data.type) {
      case "success":
        showSuccess(data.content);
        break;
      case "warning":
        showWarning(data.content);
        break;
      case "error":
        showError(data.content);
        break;
      default:
        showInfo(data.content);
    }
  });
});

onUnmounted(() => {
  if (socket) {
    socket.off("game:info");
    socket.off("game:players");
    socket.off("game:message");
    socket.off("game:notification");
  }
});

// Send Message
function sendMessage() {
  if (!inputValue.value.trim()) return;

  if (socket && socket.connected) {
    socket.emit("game:chat", { content: inputValue.value });
    inputValue.value = "";
  } else {
    showError("无法发送消息：Socket未连接");
  }
}
</script>

<style scoped>
.gaming-page {
  height: 100%;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.gaming-left-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-right: 12px;
}

.gaming-right-column {
  width: 300px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.message-container {
  flex: 1;
  min-height: 0;
}

.input-container {
  display: flex;
  flex-direction: row;
  align-items: center;
}
</style>
