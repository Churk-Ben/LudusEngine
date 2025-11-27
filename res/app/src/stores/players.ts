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
	modelName: string;
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
			const r = await fetch("/config/providers");
			if (r.ok) this.providers = await r.json();
		},
		addHuman(p: Omit<HumanPlayer, "id">) {
			const id = crypto.randomUUID();
			this.humanPlayers.push({ id, ...p });
		},
		addOnline(p: Omit<OnlinePlayer, "id">) {
			const id = crypto.randomUUID();
			this.onlinePlayers.push({ id, ...p });
		},
		addLocal(p: Omit<LocalPlayer, "id">) {
			const id = crypto.randomUUID();
			this.localPlayers.push({ id, ...p });
		},
		removePlayer(id: string) {
			this.humanPlayers = this.humanPlayers.filter((x) => x.id !== id);
			this.onlinePlayers = this.onlinePlayers.filter((x) => x.id !== id);
			this.localPlayers = this.localPlayers.filter((x) => x.id !== id);
		},
	},
});
