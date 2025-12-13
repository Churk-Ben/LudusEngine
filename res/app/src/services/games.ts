import type { Socket } from "socket.io-client";

export interface GameInfo {
    name?: string;
    status?: string;
    statusType?: "default" | "success" | "warning" | "error" | "info";
}

export interface Player {
    id: string;
    name: string;
    type: "human" | "online" | "local" | "system";
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
    console.log("Registering game socket events");
    socket.on("game:info", callbacks.onInfo);
    socket.on("game:players", callbacks.onPlayers);
    socket.on("game:message", callbacks.onMessage);
    socket.on("game:notification", callbacks.onNotification);
}

export function leaveGame(socket: Socket) {
    socket.off("game:info");
    socket.off("game:players");
    socket.off("game:message");
    socket.off("game:notification");
}

export function sendChatMessage(socket: Socket, sender: Player, content: string, sessionId?: string) {
    socket.emit("game:chat", { "sender": sender, "content": content, "sessionId": sessionId });
}
