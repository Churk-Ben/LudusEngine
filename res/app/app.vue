<template>
	<n-config-provider :theme="naiveTheme">
		<div class="app">
			<n-layout
				has-sider
				style="height: 100vh">
				<n-layout-sider
					class="app-sider"
					:width="collapsed ? 64 : 240"
					bordered>
					<div class="grid">
						<div class="flex">
							<span
								class="brand"
								v-if="!collapsed"
								>LudusEngine</span
							>
							<div class="space" />
							<n-button
								class="ctrl"
								quaternary
								size="small"
								@click="toggleCollapsed">
								<fa
									class="fa-ctrl"
									:icon="collapsed ? faAnglesRight : faAnglesLeft" />
							</n-button>
						</div>
						<transition name="slide-fade">
							<div
								v-if="!collapsed"
								class="flex ctrl-group">
								<n-select
									class="compact-select"
									v-model:value="locale"
									:options="localeOptions"
									@update:value="onLocale" />
								<n-button
									class="ctrl"
									tertiary
									size="small"
									@click="toggleTheme">
									<fa
										class="fa-ctrl"
										:icon="themeMode === 'light' ? faMoon : faSun" />
								</n-button>
							</div>
						</transition>
						<n-menu
							class="app-menu"
							:options="menuOptions"
							:value="menuValue"
							:collapsed="collapsed"
							:indent="16"
							:root-indent="16"
							:collapsed-width="64"
							@update:value="onMenu" />
					</div>
				</n-layout-sider>
				<n-layout-content
					class="app-content"
					content-style="min-height: 0;">
					<RouterView />
				</n-layout-content>
			</n-layout>
		</div>
	</n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter, RouterView } from "vue-router";
import {
	NConfigProvider,
	NLayout,
	NLayoutSider,
	NLayoutContent,
	NMenu,
	NSelect,
	NButton,
	NIcon,
	darkTheme,
} from "naive-ui";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
	faUserGroup,
	faGamepad,
	faGlobe,
	faAnglesLeft,
	faAnglesRight,
	faSun,
	faMoon,
	faLanguage,
} from "@fortawesome/free-solid-svg-icons";

const { locale } = useI18n();
const route = useRoute();
const router = useRouter();

const themeMode = ref<"light" | "dark">("light");
const naiveTheme = computed(() => (themeMode.value === "dark" ? darkTheme : null));
const themeLabel = computed(() => (themeMode.value === "light" ? "暗色" : "亮色"));

const collapsed = ref(false);

const localeOptions = [
	{ label: "中文", value: "zh-CN" },
	{ label: "English", value: "en" },
];

function renderIcon(icon: any) {
	return () => h(NIcon, { size: 16 }, { default: () => h(FontAwesomeIcon, { icon }) });
}

const menuOptions = [
	{ label: "角色管理", key: "/roles", icon: renderIcon(faUserGroup) },
	{ label: "本地游戏", key: "/local", icon: renderIcon(faGamepad) },
	{ label: "联机游戏", key: "/online", icon: renderIcon(faGlobe) },
];

const menuValue = ref(route.path);

function toggleTheme() {
	themeMode.value = themeMode.value === "light" ? "dark" : "light";
}

function toggleCollapsed() {
	collapsed.value = !collapsed.value;
}

function onLocale(v: string) {
	locale.value = v;
}

function onMenu(key: string) {
	menuValue.value = key;
	router.push(key);
}

onMounted(() => {
	const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
	themeMode.value = prefersDark ? "dark" : "light";
});
</script>

<style scoped>
.app {
	--motion-duration: 200ms;
	--motion-easing: cubic-bezier(0.2, 0, 0, 1);
	--padding: 12px;
	--gap: 8px;
	--icon-size: 16px;
}
.app-sider {
	transition: width var(--motion-duration) var(--motion-easing);
}
.grid {
	display: flex;
	flex-direction: column;
	gap: var(--gap);
	padding: var(--padding);
}
.flex {
	display: flex;
	align-items: center;
	gap: var(--gap);
}
.space {
	flex: 1;
}
.brand {
	font-size: 14px;
	font-weight: 600;
	letter-spacing: 0.2px;
}
.compact-select {
	width: 120px;
}
.ctrl .fa-ctrl {
	font-size: var(--icon-size);
}
.app-content {
	padding: var(--padding);
}
.slide-fade-enter-active,
.slide-fade-leave-active {
	transition: opacity var(--motion-duration) var(--motion-easing),
		transform var(--motion-duration) var(--motion-easing);
}
.slide-fade-enter-from,
.slide-fade-leave-to {
	opacity: 0;
	transform: translateY(-4px);
}
.app-menu :deep(.n-menu-item-content) {
	transition: background-color var(--motion-duration) var(--motion-easing),
		color var(--motion-duration) var(--motion-easing);
}
</style>
