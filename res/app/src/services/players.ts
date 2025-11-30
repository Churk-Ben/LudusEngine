// 玩家服务接口
export interface LLMProvider {
  uuid: string;
  name: string;
}

export interface HumanPlayer {
  uuid: string;
  name: string;
  prefixPrompt: string;
}

export interface OnlinePlayer {
  uuid: string;
  name: string;
  providerId: string;
  model: string;
  apiKey: string;
}

export interface LocalPlayer {
  uuid: string;
  name: string;
  modelPath: string;
  parameters: string;
}

export interface AllPlayers {
  human: HumanPlayer[];
  online: OnlinePlayer[];
  local: LocalPlayer[];
}

// 前端接口
export async function getPlayers(): Promise<AllPlayers> {
  const r = await fetch("/api/players");
  if (r.ok) {
    const d = await r.json();
    return d.data;
  }
  return { human: [], online: [], local: [] };
}

export async function getProviders(): Promise<LLMProvider[]> {
  const r = await fetch("/api/players/providers");
  if (r.ok) {
    const d = await r.json();
    return d.data;
  }
  return [];
}

export async function addPlayer(
  type: "human" | "online" | "local",
  player: HumanPlayer | OnlinePlayer | LocalPlayer
): Promise<boolean> {
  const r = await fetch("/api/players/add", {
    method: "POST",
    body: JSON.stringify({ type, player }),
  });
  if (r.ok) {
    return true;
  } else {
    const data = await r.json();
    const msg = data.get("error") || "玩家数据保存失败";
    console.error(msg);
    return false;
  }
}

export async function removePlayer(uuid: string): Promise<boolean> {
  const r = await fetch(`/api/players/${uuid}`, {
    method: "DELETE",
  });
  if (r.ok) {
    return true;
  } else {
    const data = await r.json();
    const msg = data.get("error") || "玩家数据删除失败";
    console.error(msg);
    return false;
  }
}