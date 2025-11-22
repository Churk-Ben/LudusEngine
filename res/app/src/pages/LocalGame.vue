<template>
	<div
		class="grid"
		style="min-height: 0">
		<n-card>
            <div class="grid">
                <strong>{{ t('local.selectGameTitle') }}</strong>
                <n-select
                    v-model:value="gameId"
                    :options="gameOptions"
                    :placeholder="t('local.selectPlaceholder')" />
            </div>
		</n-card>

		<n-card>
            <div class="grid">
                <strong>{{ t('local.selectPlayersTitle') }}</strong>
				<div class="grid">
					<div
						class="flex"
						v-for="p in allPlayers"
						:key="p.id">
						<n-checkbox
							:value="p.id"
							v-model:checked="checkedMap[p.id]"
							>{{ p.name }}</n-checkbox
						>
					</div>
				</div>
				<div class="flex">
					<div class="space" />
                    <n-button
                        type="primary"
                        :disabled="!canStart"
                        @click="start"
                        >{{ t('local.startButton') }}</n-button
                    >
				</div>
			</div>
		</n-card>

		<div
			v-if="started"
			class="grid cols-2"
			style="min-height: 0">
			<ChatWindow />
			<div class="grid">
				<GameFlowHint
					:steps="steps"
					:index="flowIndex" />
                <PluginHost>
                    <div class="muted">{{ t('local.pluginPlaceholder') }}</div>
                </PluginHost>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { NCard, NSelect, NCheckbox, NButton } from "naive-ui";
import ChatWindow from "@/components/ChatWindow.vue";
import GameFlowHint from "@/components/GameFlowHint.vue";
import PluginHost from "@/components/PluginHost.vue";
import { usePlayersStore } from "@/stores/players";

const players = usePlayersStore();
const { t } = useI18n();
const games = ref<string[]>([]);
const gameId = ref("");
const started = ref(false);
const steps = computed(() => [
    t("local.steps.prepare"),
    t("local.steps.deal"),
    t("local.steps.play"),
    t("local.steps.result"),
]);
const flowIndex = ref(0);

const allPlayers = computed(() => [...players.humanPlayers, ...players.llmPlayers]);
const checkedMap = ref<Record<string, boolean>>({});
const selectedPlayerIds = computed(() =>
	Object.entries(checkedMap.value)
		.filter(([, v]) => v)
		.map(([k]) => k)
);
const canStart = computed(() => !!gameId.value && selectedPlayerIds.value.length >= 2);

const gameOptions = computed(() => games.value.map((g) => ({ label: g, value: g })));

async function loadGames() {
	const r = await fetch("/api/games");
	if (r.ok) games.value = await r.json();
}

function start() {
	started.value = true;
	flowIndex.value = 0;
}

onMounted(() => loadGames());
</script>
