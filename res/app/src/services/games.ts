/**
 * @description 获取所有可用的游戏ID
 * @returns {Promise<string[]>}
 */
export async function getGames(): Promise<string[]> {
    const r = await fetch("/api/games");
    if (r.ok) {
        const d = await r.json();
        // 假设后端返回的数据结构是 { data: string[] }
        return d.data || [];
    }
    // 增加错误处理
    try {
        const errorData = await r.json();
        console.error("获取游戏列表失败:", errorData.error || r.statusText);
    } catch (e) {
        console.error("获取游戏列表失败:", await r.text());
    }
    return [];
}

/*
// 未来可以扩展更多与游戏相关的服务函数, 例如:

export interface Game {
  id: string;
  name: string;
  description: string;
}

export async function addGame(game: Omit<Game, 'id'>): Promise<Game | null> {
  const r = await fetch("/api/games/add", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(game),
  });
  if (r.ok) {
    const d = await r.json();
    return d.data;
  }
  // ... error handling
  return null;
}
*/
