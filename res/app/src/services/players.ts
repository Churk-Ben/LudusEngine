// 玩家服务接口
export interface LLMProvider {
  id: string;
  name: string;
}

export interface HumanPlayer {
  uuid: string;
  name: string;
  type: "human";
  prefixPrompt: string;
}

export interface OnlinePlayer {
  uuid: string;
  name: string;
  type: "online";
  providerId: string;
  model: string;
  apiKey: string;
}

export interface LocalPlayer {
  uuid: string;
  name: string;
  type: "local";
  modelPath: string;
  parameters: string;
}

export interface RemotePlayer {
  uuid: string;
  name: string;
  type: "remote";
}

export interface AllPlayers {
  human: HumanPlayer[];
  online: OnlinePlayer[];
  local: LocalPlayer[];
}

// 前端接口
/**
 * @description 获取所有玩家(后端可查)
 * @returns {Promise<AllPlayers>}
 */
export async function getPlayers(): Promise<AllPlayers> {
  const r = await fetch("/api/players");
  if (r.ok) {
    const d = await r.json();
    return d.data;
  }
  return { human: [], online: [], local: [] };
}

/**
 * @description 获取所有LLM提供方
 * @returns {Promise<LLMProvider[]>}
 */
export async function getProviders(): Promise<LLMProvider[]> {
  const r = await fetch("/api/players/providers");
  if (r.ok) {
    const d = await r.json();
    return d.data;
  }
  return [];
}

/**
 * @description 添加新玩家
 * @param {string} type - 玩家类型
 * @param {Omit<HumanPlayer | OnlinePlayer | LocalPlayer, "uuid">} player - 玩家数据
 * @returns {Promise<HumanPlayer | OnlinePlayer | LocalPlayer | null>}
 */
export async function addPlayer(
  type: "human" | "online" | "local",
  player: Omit<HumanPlayer | OnlinePlayer | LocalPlayer, "uuid">
): Promise<HumanPlayer | OnlinePlayer | LocalPlayer | null> {
  const r = await fetch("/api/players/add", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ type, player }),
  });
  if (r.ok) {
    const d = await r.json();
    return d.data;
  } else {
    try {
      const data = await r.json();
      const msg = data.error || "玩家数据保存失败";
      console.error(msg);
    } catch (e) {
      console.error("玩家数据保存失败", await r.text());
    }
    return null;
  }
}

export async function removePlayer(uuid: string): Promise<boolean> {
  const r = await fetch(`/api/players/${uuid}`, {
    method: "DELETE",
  });
  if (!r.ok) {
    try {
      const data = await r.json();
      const msg = data.error || "玩家数据删除失败";
      console.error(msg);
    } catch (e) {
      console.error("玩家数据删除失败", await r.text());
    }
  }
  return r.ok;
}