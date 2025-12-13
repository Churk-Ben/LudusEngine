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
        <n-scrollbar
          ref="scrollbarRef"
          id="message-scrollbar"
          @scroll="handleScroll"
        >
          <n-list class="chat-list">
            <n-list-item
              v-for="(msg, index) in messages"
              :key="index"
              class="chat-item"
            >
              <n-thing content-indented>
                <template #avatar>
                  <n-avatar round size="small">
                    <!-- TODO 根据玩家data里的信息设置头像 msg 缺少sender信息 -->
                    {{ msg.sender.name.charAt(0).toUpperCase() }}
                  </n-avatar>
                </template>
                <template #header>
                  {{ msg.sender.name }}
                </template>
                <template #header-extra>
                  <span style="font-size: 12px; opacity: 0.8">
                    {{ msg.time }}
                  </span>
                </template>
                {{ msg.content }}
              </n-thing>
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
        <n-scrollbar>
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
                  {{ player.type }}
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
        </n-scrollbar>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject, onMounted, onUnmounted, h, nextTick } from "vue";
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
import { useRoute, onBeforeRouteLeave } from "vue-router";
const { t } = useI18n();
const route = useRoute();
const socket = inject<Socket>("socket");

// 保存进入页面时的参数快照，防止在 onUnmounted 时 route 已变更导致获取不到
const initialSessionId = route.params.id as string;
const initialGameId = route.query.gameId as string;
const initialPlayerIds = route.query.playerIds as string;

// 游戏信息: 名称和游戏阶段
const gameInfo = ref<GameInfo>({
  name: "游戏标题",
  status: "等待连接",
  statusType: "info",
});
const players = ref<Player[]>([]);
const messages = ref<ChatMessage[]>([]);
const inputValue = ref("");
const scrollbarRef = ref<InstanceType<typeof NScrollbar> | null>(null);
const isAtBottom = ref(true);

const handleScroll = (e: Event) => {
  const target = e.target as HTMLElement;
  isAtBottom.value =
    target.scrollHeight - (target.scrollTop + target.clientHeight) <= 50;
};

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

// 离开页面拦截
const canLeave = ref(false);
let leaveTimer: ReturnType<typeof setTimeout> | null = null;

onBeforeRouteLeave(() => {
  if (canLeave.value) return true;

  showWarning("切换页面将不会为你保存游戏进度, 通知消失前再次点击以切换页面");
  canLeave.value = true;

  if (leaveTimer) clearTimeout(leaveTimer);
  leaveTimer = setTimeout(() => {
    canLeave.value = false;
  }, 3000);

  return false;
});

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
    onMessage: async (data: ChatMessage) => {
      console.log("Received message:", data);
      const shouldScroll = isAtBottom.value;
      messages.value.push(data);
      // 滚动到最底部
      if (shouldScroll) {
        await nextTick();
        if (scrollbarRef.value) {
          scrollbarRef.value.scrollTo({ top: 99999, behavior: "smooth" });
        }
      }
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
  if (initialGameId && initialPlayerIds) {
    try {
      const pIds = JSON.parse(initialPlayerIds);
      socket.emit("app:initGame", {
        gameId: initialGameId,
        playerIds: pIds,
        sessionId: initialSessionId,
      });
    } catch (e) {
      showError("处理玩家ID时出错: " + e);
    }
  }
});

onUnmounted(() => {
  if (leaveTimer) clearTimeout(leaveTimer);
  if (socket) {
    // 离开时通知后端清理
    if (initialGameId && initialPlayerIds) {
      try {
        socket.emit("game:leave", {
          gameId: initialGameId,
          playerIds: JSON.parse(initialPlayerIds),
          sessionId: initialSessionId,
        });
      } catch (e) {
        console.error("Failed to parse playerIds on leave:", e);
      }
    }
    leaveGame(socket);
  }
});

// 发送信息
function sendMessage() {
  if (!inputValue.value.trim()) return;

  if (socket && socket.connected) {
    sendChatMessage(
      socket,
      players.value.find((p) => p.type === "human")!,
      inputValue.value,
      initialSessionId
    );
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
  padding: 1.4em;
}
</style>
