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
                    <div class="d-flex flex-column justify-content-between h-100">
						<n-menu
							class="app-menu"
							:options="menuOptions"
							:value="menuValue"
							:collapsed="collapsed"
							:indent="16"
							:root-indent="16"
							:collapsed-width="64"
							@update:value="onMenu" />
                        <div class="app-ctrl d-flex flex-column align-items-start gap-2">
							<n-button
								class="toggle-collapse"
								quaternary
								size="small"
								@click="toggleCollapsed">
								<fa
									class="fa-ctrl"
									:icon="collapsed ? faAnglesRight : faAnglesLeft" />
							</n-button>
							<n-button
								class="toggle-theme"
								quaternary
								size="small"
								@click="toggleTheme">
								<fa
									class="fa-ctrl"
									:icon="themeMode === 'light' ? faMoon : faSun" />
							</n-button>
							<n-select
								class="ctrl"
								quaternary
								size="small"
								:options="localeOptions"
								@update:value="onLocale" />
						</div>
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
	NGrid,
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

const { locale, t } = useI18n();
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

const menuOptions = computed(() => [
	{ label: t("menu.roles"), key: "/roles", icon: renderIcon(faUserGroup) },
	{ label: t("menu.local"), key: "/local", icon: renderIcon(faGamepad) },
	{ label: t("menu.online"), key: "/online", icon: renderIcon(faGlobe) },
]);

const menuValue = ref(route.path);

function toggleTheme() {
	themeMode.value = themeMode.value === "light" ? "dark" : "light";
}

function toggleCollapsed() {
	collapsed.value = !collapsed.value;
}

function onLocale(v: string) {
	locale.value = v;
	localStorage.setItem("locale", v);
	document.documentElement.lang = v;
}

function onMenu(key: string) {
	menuValue.value = key;
	router.push(key);
}

onMounted(() => {
	const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
	themeMode.value = prefersDark ? "dark" : "light";
	document.documentElement.lang = locale.value;
});
</script>

<style scoped>
.app {
	--motion-duration: 200ms;
	--motion-easing: ease;
	--padding: 12px;
	--gap: 8px;
	--icon-size: 16px;
}

.app-sider {
	transition: all var(--motion-duration) var(--motion-easing);
}

.app-menu :deep(.n-menu-item-content) {
	transition: all var(--motion-duration) var(--motion-easing);
}

.app-ctrl {
	transition: all var(--motion-duration) var(--motion-easing);
}

.app-content {
	padding: var(--padding);
}

.ctrl .fa-ctrl {
	font-size: var(--icon-size);
}
</style>
