<template>
  <div class="gaming-page">
    <!-- 左列: 游戏标题和消息收发容器 -->
    <div class="gaming-left-column">
      <!-- 顶部标题: 游戏名称和状态 -->
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

      <!-- 消息容器 -->
      <div class="message-container">
        <n-scrollbar>
          <n-list class="chat-list">
            <n-list-item
              v-for="(msg, index) in messages"
              :key="index"
              class="chat-item"
            >
              <div class="bubble">{{ msg.sender }}: {{ msg.content }}</div>
              <!-- <n-thing class="my-1 px-2 py-1 rounded-md" :title="msg.sender">
                <template #description>
                  <span style="font-size: 12px; opacity: 0.8">
                    {{ msg.time }}
                  </span>
                </template>
                {{ msg.content }}
              </n-thing> -->
            </n-list-item>
          </n-list>
        </n-scrollbar>
      </div>

      <!-- 底部: 输入区域 -->
      <div class="input-container gap-2 mb-1">
        <n-input
          v-model:value="inputValue"
          size="large"
          type="text"
          :placeholder="t('game.chat.inputPlaceholder')"
          @keyup.enter="sendMessage"
        />
        <n-button
          type="primary"
          size="large"
          @click="sendMessage"
          :disabled="!inputValue.trim()"
        >
          {{ t("game.chat.send") }}
        </n-button>
      </div>
    </div>

    <!-- 右列: 玩家列表 -->
    <div class="gaming-right-column">
      <n-card
        :title="t('game.players')"
        style="height: 100%"
        content-style="padding: 0; overflow-y: auto;"
        header-style="padding: 16px; border-bottom: 1px solid var(--n-border-color);"
      >
        <n-list hoverable clickable>
          <n-list-item
            v-for="player in players"
            :key="player.id"
            @click="toggleDetail(player)"
          >
            <n-thing>
              <template #avatar>
                <n-avatar round size="small">
                  <!-- TODO 根据玩家data里的信息设置头像 -->
                  {{ player.name.charAt(0).toUpperCase() }}
                </n-avatar>
              </template>
              <template #header>
                {{ player.name }}
              </template>
              <template #header-extra>
                {{ player.status }}
              </template>
              <template #description>
                <div v-if="expandedPlayerIds.includes(player.id)">
                  {{ JSON.stringify(player.data || {}, null, 2) }}
                </div>
                <template v-else>
                  <span>点按查看玩家数据</span>
                </template>
              </template>
            </n-thing>
          </n-list-item>
          <!-- 默认玩家卡片 -->
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
  NButton,
  NScrollbar,
  NResult,
  NAlert,
  useMessage,
} from "naive-ui";
import type { MessageRenderMessage } from "naive-ui";
import type { Socket } from "socket.io-client";
import {
  type GameInfo,
  type Player,
  type ChatMessage,
  type GameNotification,
  joinGame,
  leaveGame,
  sendChatMessage,
} from "@/services/games";
import { useI18n } from "vue-i18n";
import { useRoute } from "vue-router";
const { t } = useI18n();
const route = useRoute();
const socket = inject<Socket>("socket");

// 游戏信息: 名称和游戏阶段
const gameInfo = ref<GameInfo>({
  name: "游戏标题",
  status: "等待连接",
  statusType: "info",
});
const players = ref<Player[]>([]);
const messages = ref<ChatMessage[]>([]);
const inputValue = ref("");

// 应用消息通知
const renderMessage: MessageRenderMessage = (props) => {
  const { type } = props;
  return h(
    NAlert,
    {
      closable: props.closable,
      onClose: props.onClose,
      type: type === "loading" ? "default" : type,
      title: "游戏通知",
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

const message = useMessage();

const showInfo = (content: string) =>
  message.info(content, { render: renderMessage, closable: true });
const showSuccess = (content: string) =>
  message.success(content, { render: renderMessage, closable: true });
const showWarning = (content: string) =>
  message.warning(content, { render: renderMessage, closable: true });
const showError = (content: string) =>
  message.error(content, { render: renderMessage, closable: true });

const expandedPlayerIds = ref<string[]>([]);

// 切换展示玩家详情(玩家的data对象)
function toggleDetail(player: Player) {
  const index = expandedPlayerIds.value.indexOf(player.id);
  if (index > -1) {
    expandedPlayerIds.value.splice(index, 1);
  } else {
    expandedPlayerIds.value.push(player.id);
  }
}

// Socket 事件
onMounted(() => {
  if (!socket) {
    showError("Socket未连接");
    return;
  }

  joinGame(socket, {
    onInfo: (data: GameInfo) => {
      // 定向更新: 仅更新存在的字段
      if (data.name !== undefined) gameInfo.value.name = data.name;
      if (data.status !== undefined) gameInfo.value.status = data.status;
      if (data.statusType !== undefined)
        gameInfo.value.statusType = data.statusType;
    },
    onPlayers: (data: Player[]) => {
      players.value = data;
    },
    onMessage: (data: ChatMessage) => {
      messages.value.push(data);
      // TODO: Scroll to bottom logic if needed
    },
    onNotification: (data: GameNotification) => {
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
    },
  });

  // 尝试初始化游戏（如果携带了参数）
  const sessionId = route.params.id as string;
  const qGameId = route.query.gameId as string;
  const qPlayerIds = route.query.playerIds as string;

  if (qGameId && qPlayerIds) {
    try {
      const pIds = JSON.parse(qPlayerIds);
      socket.emit("app:initGame", {
        gameId: qGameId,
        playerIds: pIds,
        sessionId: sessionId,
      });
    } catch (e) {
      showError("处理玩家ID时出错: " + e);
    }
  }
});

onUnmounted(() => {
  if (socket) {
    leaveGame(socket);
  }
});

// Send Message
function sendMessage() {
  if (!inputValue.value.trim()) return;

  if (socket && socket.connected) {
    sendChatMessage(socket, "ME", inputValue.value);
    inputValue.value = "";
  } else {
    showError("无法发送消息: Socket未连接");
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
  word-break: break-word;
  line-height: 1.5;
}

.input-container {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.chat-list {
  margin: 8px 0;
  padding: 0 12px;
  background-color: transparent;
  border-bottom: 0;
}

.chat-item {
  background-color: var(--n-color);
  border-radius: var(--n-border-radius);
  border: 1px solid var(--n-border-color);
  margin: 12px 0;
  padding: 2em;
}
</style>
