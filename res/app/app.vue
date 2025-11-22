<template>
  <n-config-provider :theme="naiveTheme">
    <div class="app">
      <n-layout has-sider style="height: 100vh">
        <n-layout-sider
          class="app-sider"
          :width="collapsed ? 64 : 240"
          bordered
        >
          <div class="d-flex flex-column justify-content-between h-100">
            <n-menu
              class="app-menu"
              :options="menuOptions"
              :value="menuValue"
              :collapsed="collapsed"
              :indent="16"
              :root-indent="16"
              :collapsed-width="64"
              @update:value="onMenu"
            />
            <n-menu
              class="app-ctrl"
              :options="ctrlOptions"
              :value="ctrlValue"
              :collapsed="collapsed"
              :indent="16"
              :root-indent="16"
              :collapsed-width="64"
              @update:value="onCtrl"
            />
          </div>
        </n-layout-sider>
        <n-layout-content class="app-content" content-style="min-height: 0;">
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
const naiveTheme = computed(() =>
  themeMode.value === "dark" ? darkTheme : null
);
const themeLabel = computed(() =>
  themeMode.value === "light" ? "暗色" : "亮色"
);

const collapsed = ref(false);

const localeOptions = [
  { label: "中文", value: "zh-CN" },
  { label: "English", value: "en" },
];

const localeLabel = computed(() =>
  locale.value === "zh-CN" ? "语言" : "Language"
);

function renderIcon(icon: any) {
  return () =>
    h(NIcon, { size: 16 }, { default: () => h(FontAwesomeIcon, { icon }) });
}

const menuOptions = computed(() => [
  { label: t("menu.roles"), key: "/roles", icon: renderIcon(faUserGroup) },
  { label: t("menu.local"), key: "/local", icon: renderIcon(faGamepad) },
  { label: t("menu.online"), key: "/online", icon: renderIcon(faGlobe) },
]);

const menuValue = ref(route.path);

const ctrlValue = ref<string | null>(null);

const ctrlOptions = computed(() => [
  {
    label: collapsed.value ? "展开" : "收起",
    key: "toggleCollapsed",
    icon: renderIcon(collapsed.value ? faAnglesRight : faAnglesLeft),
  },
  {
    label: themeLabel.value,
    key: "toggleTheme",
    icon: renderIcon(themeMode.value === "light" ? faMoon : faSun),
  },
  {
    label: localeLabel.value,
    key: "locale",
    icon: renderIcon(faLanguage),
    children: localeOptions.map((o) => ({
      label: o.label,
      key: `locale:${o.value}`,
    })),
  },
]);

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

function onCtrl(key: string | null) {
  if (!key) return;
  if (key === "toggleCollapsed") {
    toggleCollapsed();
  } else if (key === "toggleTheme") {
    toggleTheme();
  } else if (key.startsWith("locale:")) {
    onLocale(key.split(":")[1]);
  }
  ctrlValue.value = null;
}

onMounted(() => {
  const prefersDark =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
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

.app-ctrl :deep(.n-menu-item-content__icon) {
  font-size: var(--icon-size);
}
</style>
