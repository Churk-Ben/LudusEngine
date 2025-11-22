<template>
	<div class="grid cols-2">
		<n-card>
			<div
				class="flex"
				style="margin-bottom: 8px">
				<strong>LLM玩家</strong>
				<div class="space" />
			</div>
			<div class="grid">
				<n-select
					v-model:value="providerId"
					:options="providerOptions"
					placeholder="提供商/API/本地模型" />
				<n-input
					v-model:value="llmName"
					placeholder="名称" />
				<n-input
					v-model:value="model"
					placeholder="模型" />
				<div class="flex">
					<n-button
						type="primary"
						@click="addLLM"
						>添加</n-button
					>
				</div>
			</div>
			<div
				style="margin-top: 12px"
				class="grid">
				<div class="muted">已添加</div>
				<div
					v-for="p in players.llmPlayers"
					:key="p.id"
					class="flex">
					<span>{{ p.name }} · {{ providerName(p.providerId) }} · {{ p.model || "未设定" }}</span>
					<div class="space" />
					<n-button
						quaternary
						@click="players.removePlayer(p.id)"
						>移除</n-button
					>
				</div>
			</div>
		</n-card>

		<n-card>
			<div
				class="flex"
				style="margin-bottom: 8px">
				<strong>本人玩家</strong>
				<div class="space" />
			</div>
			<div class="grid">
				<n-input
					v-model:value="meName"
					placeholder="名称" />
				<div class="flex">
					<n-button
						type="primary"
						@click="addHuman"
						>添加</n-button
					>
				</div>
			</div>
			<div
				style="margin-top: 12px"
				class="grid">
				<div class="muted">已添加</div>
				<div
					v-for="p in players.humanPlayers"
					:key="p.id"
					class="flex">
					<span>{{ p.name }}</span>
					<div class="space" />
					<n-button
						quaternary
						@click="players.removePlayer(p.id)"
						>移除</n-button
					>
				</div>
			</div>
		</n-card>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { NCard, NSelect, NInput, NButton } from "naive-ui";
import { usePlayersStore } from "@/stores/players";

const players = usePlayersStore();
const providerId = ref("");
const llmName = ref("");
const model = ref("");
const meName = ref("");

const providers = computed(() => players.providers);
const providerOptions = computed(() => providers.value.map((p) => ({ label: p.name, value: p.id })));
function providerName(id: string) {
	return providers.value.find((x) => x.id === id)?.name || "";
}

function addLLM() {
	if (!providerId.value || !llmName.value.trim()) return;
	players.addLLM({
		name: llmName.value.trim(),
		providerId: providerId.value,
		model: model.value.trim() || undefined,
	});
	llmName.value = "";
	model.value = "";
}

function addHuman() {
	if (!meName.value.trim()) return;
	players.addHuman({ name: meName.value.trim() });
	meName.value = "";
}

onMounted(() => players.loadProviders());
</script>
