import { defineStore } from "pinia";

export type ProviderKind = "api" | "local";

export interface LLMProvider {
	id: string;
	name: string;
	kind: ProviderKind;
	endpoint?: string;
}

export interface LLMPlayer {
	id: string;
	name: string;
	providerId: string;
	model?: string;
	api?: string;
}

export interface HumanPlayer {
	id: string;
	name: string;
}

export const usePlayersStore = defineStore("players", {
	state: () => ({
		providers: [] as LLMProvider[],
		llmPlayers: [] as LLMPlayer[],
		humanPlayers: [] as HumanPlayer[],
	}),
	actions: {
		async loadProviders() {
			const r = await fetch("/api/providers");
			if (r.ok) this.providers = await r.json();
		},
		addLLM(p: Omit<LLMPlayer, "id">) {
			const id = crypto.randomUUID();
			this.llmPlayers.push({ id, ...p });
		},
		addHuman(p: Omit<HumanPlayer, "id">) {
			const id = crypto.randomUUID();
			this.humanPlayers.push({ id, ...p });
		},
		removePlayer(id: string) {
			this.llmPlayers = this.llmPlayers.filter((x) => x.id !== id);
			this.humanPlayers = this.humanPlayers.filter((x) => x.id !== id);
		},
	},
});
