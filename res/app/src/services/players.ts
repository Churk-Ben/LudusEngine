
export interface LLMProvider {
  id: string;
  name: string;
}

export interface HumanPlayer {
  id: string;
  name: string;
  prefixPrompt: string;
}

export interface OnlinePlayer {
  id: string;
  name: string;
  providerId: string;
  model: string;
  apiKey: string;
}

export interface LocalPlayer {
  id: string;
  name: string;
  modelPath: string;
  parameters: string;
}

export interface AllPlayers {
  human: HumanPlayer[];
  online: OnlinePlayer[];
  local: LocalPlayer[];
}

export async function getProviders(): Promise<LLMProvider[]> {
  const r = await fetch("/api/players/providers");
  if (r.ok) {
    const d = await r.json();
    return d.data;
  }
  return [];
}

export async function getPlayers(): Promise<AllPlayers> {
  const r = await fetch("/api/players");
  if (r.ok) {
    const d = await r.json();
    return d.data;
  }
  return { human: [], online: [], local: [] };
}

export async function savePlayers(players: AllPlayers): Promise<boolean> {
  const r = await fetch("/api/players", {
    method: "POST",
    body: JSON.stringify(players),
  });
  if (!r.ok) {
    console.error("玩家数据保存失败");
  }
  return r.ok;
}
