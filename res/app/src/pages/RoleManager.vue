<template>
	<div class="grid cols-2">
		<n-card>
            <div
                class="flex"
                style="margin-bottom: 8px">
                <strong>{{ t("role.llm.title") }}</strong>
                <div class="space" />
            </div>
			<div class="grid">
                <n-select
                    v-model:value="providerId"
                    :options="providerOptions"
                    :placeholder="t('role.llm.providerPlaceholder')" />
                <n-input
                    v-model:value="llmName"
                    :placeholder="t('role.common.namePlaceholder')" />
                <n-input
                    v-model:value="model"
                    :placeholder="t('role.llm.modelPlaceholder')" />
				<div class="flex">
                    <n-button
                        type="primary"
                        @click="addLLM"
                        >{{ t('role.common.add') }}</n-button
                    >
				</div>
			</div>
			<div
				style="margin-top: 12px"
				class="grid">
                <div class="muted">{{ t('role.common.added') }}</div>
				<div
					v-for="p in players.llmPlayers"
					:key="p.id"
					class="flex">
                    <span>{{ p.name }} · {{ providerName(p.providerId) }} · {{ p.model || t('role.common.notSet') }}</span>
					<div class="space" />
                    <n-button
                        quaternary
                        @click="players.removePlayer(p.id)"
                        >{{ t('role.common.remove') }}</n-button
                    >
				</div>
			</div>
		</n-card>

		<n-card>
            <div
                class="flex"
                style="margin-bottom: 8px">
                <strong>{{ t("role.me.title") }}</strong>
                <div class="space" />
            </div>
			<div class="grid">
                <n-input
                    v-model:value="meName"
                    :placeholder="t('role.common.namePlaceholder')" />
				<div class="flex">
                    <n-button
                        type="primary"
                        @click="addHuman"
                        >{{ t('role.common.add') }}</n-button
                    >
				</div>
			</div>
			<div
				style="margin-top: 12px"
				class="grid">
				<div class="muted">{{ t('role.common.added') }}</div>
				<div
					v-for="p in players.humanPlayers"
					:key="p.id"
					class="flex">
					<span>{{ p.name }}</span>
					<div class="space" />
					<n-button
						quaternary
						@click="players.removePlayer(p.id)"
						>{{ t('role.common.remove') }}</n-button
					>
				</div>
			</div>
		</n-card>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { NCard, NSelect, NInput, NButton } from "naive-ui";
import { usePlayersStore } from "@/stores/players";

const players = usePlayersStore();
const { t } = useI18n();
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
