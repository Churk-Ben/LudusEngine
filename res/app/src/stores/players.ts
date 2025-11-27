import { defineStore } from "pinia";

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

export const usePlayersStore = defineStore("players", {
	state: () => ({
		providers: [] as LLMProvider[],
		humanPlayers: [] as HumanPlayer[],
		onlinePlayers: [] as OnlinePlayer[],
		localPlayers: [] as LocalPlayer[],
	}),
	actions: {
		async loadProviders() {
			const r = await fetch("/api/players/providers");
			if (r.ok) {
				const d = await r.json()
				this.providers = d.data;
			}
		},

		async loadPlayers() {
			const r = await fetch("/api/players");
			if (r.ok) {
				const d = await r.json();
				const players = d.data;
				this.humanPlayers = players.human;
				this.onlinePlayers = players.online;
				this.localPlayers = players.local;
			}
		},

		async savePlayers() {
			const r = await fetch("/api/players", {
				method: "POST",
				body: JSON.stringify({
					human: this.humanPlayers,
					online: this.onlinePlayers,
					local: this.localPlayers,
				}),
			});
			if (r.ok) {
				console.log("玩家数据保存成功");
			} else {
				console.error("玩家数据保存失败");
			}
		},

		async removePlayer(id: string) {
			this.humanPlayers = this.humanPlayers.filter((x) => x.id !== id);
			this.onlinePlayers = this.onlinePlayers.filter((x) => x.id !== id);
			this.localPlayers = this.localPlayers.filter((x) => x.id !== id);
			await this.savePlayers();
		},

		async addHuman(p: Omit<HumanPlayer, "id">) {
			const id = crypto.randomUUID();
			this.humanPlayers.push({ id, ...p });
			await this.savePlayers();
		},
		async addOnline(p: Omit<OnlinePlayer, "id">) {
			const id = crypto.randomUUID();
			this.onlinePlayers.push({ id, ...p });
			await this.savePlayers();
		},
		async addLocal(p: Omit<LocalPlayer, "id">) {
			const id = crypto.randomUUID();
			this.localPlayers.push({ id, ...p });
			await this.savePlayers();
		}
	},
});
