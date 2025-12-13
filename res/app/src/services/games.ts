import type { Socket } from "socket.io-client";

export interface GameInfo {
    name?: string;
    status?: string;
    statusType?: "default" | "success" | "warning" | "error" | "info";
}

export interface Player {
    id: string;
    name: string;
    type: "human" | "online" | "local" | "remote" | "system";
    data?: any;
}

export interface ChatMessage {
    sender: Player;
    content: string;
    time: string;
}

export interface GameNotification {
    type: "success" | "warning" | "error" | "info";
    content: string;
}

// 游戏回调函数接口
export interface GameCallbacks {
    onInfo: (data: GameInfo) => void;
    onPlayers: (data: Player[]) => void;
    onMessage: (data: ChatMessage) => void;
    onNotification: (data: GameNotification) => void;
}

/**
 * @description 获取所有可用的游戏ID
 * @returns {Promise<string[]>}
 */
export async function getGames(): Promise<string[]> {
    const r = await fetch("/api/games");
    if (r.ok) {
        const d = await r.json();
        return d.data || [];
    }
    try {
        const errorData = await r.json();
        console.error("获取游戏列表失败:", errorData.error || r.statusText);
    } catch (e) {
        console.error("获取游戏列表失败:", await r.text());
    }
    return [];
}

export function joinGame(socket: Socket, callbacks: GameCallbacks) {
    console.log("注册游戏事件");
    socket.on("game:info", callbacks.onInfo);
    socket.on("game:players", callbacks.onPlayers);
    socket.on("game:message", callbacks.onMessage);
    socket.on("game:notification", callbacks.onNotification);
}

export function leaveGame(socket: Socket) {
    console.log("取消注册游戏事件");
    socket.off("game:info");
    socket.off("game:players");
    socket.off("game:message");
    socket.off("game:notification");
}

/**
 * @description 发送聊天消息
 * @param {Socket} socket - 游戏Socket连接
 * @param {Player} sender - 发送者玩家对象
 * @param {string} content - 聊天内容
 * @param {string} [sessionId] - 会话ID（可选）
 */
export function sendChatMessage(socket: Socket, sender: Player, content: string, sessionId?: string) {
    socket.emit("game:chat", { "sender": sender, "content": content, "sessionId": sessionId });
}
