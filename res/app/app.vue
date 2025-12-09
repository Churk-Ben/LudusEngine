<template>
  <n-config-provider
    :date-locale="naiveDateLocale"
    :inline-theme-disabled="true"
    :locale="naiveLocale"
    :theme="naiveTheme"
  >
    <div class="app">
      <n-layout has-sider style="height: 100vh">
        <n-layout-sider
          :width="collapsed ? 64 : 240"
          bordered
          class="app-sider"
        >
          <div
            :style="{ opacity: siderContentVisible ? 1 : 0 }"
            class="sider-content d-flex flex-column justify-content-between h-100"
          >
            <n-menu
              :collapsed="collapsed"
              :collapsed-width="64"
              :indent="16"
              :options="menuOptions"
              :root-indent="16"
              :value="menuValue"
              class="app-menu"
              @update:value="onMenu"
            />
            <n-menu
              :collapsed="collapsed"
              :collapsed-width="64"
              :indent="16"
              :options="ctrlOptions"
              :root-indent="16"
              :value="ctrlValue"
              class="app-ctrl"
              @update:value="onCtrl"
            />
          </div>
        </n-layout-sider>
        <n-layout-content class="app-content" content-style="min-height: 0;">
          <n-dialog-provider>
            <n-message-provider placement="bottom-right">
              <RouterView />
            </n-message-provider>
          </n-dialog-provider>
        </n-layout-content>
      </n-layout>
    </div>
  </n-config-provider>
</template>

<script lang="ts" setup>
import { computed, h, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { RouterView, useRoute, useRouter } from "vue-router";
import {
  darkTheme,
  dateEnUS,
  dateJaJP,
  dateZhCN,
  enUS,
  jaJP,
  NConfigProvider,
  NIcon,
  NLayout,
  NLayoutContent,
  NLayoutSider,
  NMenu,
  NMessageProvider,
  NDialogProvider,
  zhCN,
} from "naive-ui";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import {
  faBars,
  faGamepad,
  faGlobe,
  faHome,
  faLanguage,
  faMoon,
  faSun,
  faUserGroup,
} from "@fortawesome/free-solid-svg-icons";

const { locale, t } = useI18n();
const route = useRoute();
const router = useRouter();

function renderIcon(icon: any) {
  return () =>
    h(NIcon, { size: 16 }, { default: () => h(FontAwesomeIcon, { icon }) });
}

// 应用侧边栏折叠状态
const collapsed = ref(localStorage.getItem("collapsed") === "true");
const siderContentVisible = ref(true);
const siderAnimating = ref(false);

function toggleCollapsed() {
  const duration = 200;
  if (collapsed.value) {
    if (siderAnimating.value) return;
    siderAnimating.value = true;
    siderContentVisible.value = false;
    window.setTimeout(() => {
      collapsed.value = false;
      localStorage.setItem("collapsed", "false");
      window.setTimeout(() => {
        siderContentVisible.value = true;
        siderAnimating.value = false;
      }, duration);
    }, duration);
  } else {
    collapsed.value = true;
    localStorage.setItem("collapsed", "true");
  }
}

// 应用菜单选项
const menuValue = ref(route.path);
const menuOptions = computed(() => [
  { label: t("sider.menu.home"), key: "/", icon: renderIcon(faHome) },
  {
    label: t("sider.menu.roles"),
    key: "/roles",
    icon: renderIcon(faUserGroup),
  },
  { label: t("sider.menu.local"), key: "/local", icon: renderIcon(faGamepad) },
  { label: t("sider.menu.online"), key: "/online", icon: renderIcon(faGlobe) },
]);

function onMenu(key: string) {
  menuValue.value = key;
  router.push(key);
}

// 应用控制选项
const ctrlValue = ref<string | null>(null);
const ctrlOptions = computed(() => [
  {
    label: collapsed.value ? t("sider.ctrl.expand") : t("sider.ctrl.collapse"),
    key: "toggleCollapsed",
    icon: renderIcon(faBars),
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

// 应用主题模式
const prefersDark = () => {
  if (localStorage.getItem("themeMode")) {
    return localStorage.getItem("themeMode") === "dark";
  }
  return (
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
};
const themeMode = ref<"light" | "dark">(prefersDark() ? "dark" : "light");
const naiveTheme = computed(() =>
  themeMode.value === "dark" ? darkTheme : null
);

const themeLabel = computed(() =>
  themeMode.value === "light"
    ? t("sider.ctrl.theme.dark")
    : t("sider.ctrl.theme.light")
);

function toggleTheme() {
  themeMode.value = themeMode.value === "light" ? "dark" : "light";
  localStorage.setItem("themeMode", themeMode.value);
}

// 应用语言选项
const localeLabel = computed(() => t("sider.ctrl.locale"));
const localeOptions = [
  { label: "中文", value: "zh-CN" },
  { label: "English", value: "en" },
  { label: "日本語", value: "jp" },
];

const naiveLocale = computed(() => {
  if (locale.value === "zh-CN") return zhCN;
  if (locale.value === "en") return enUS;
  if (locale.value === "jp") return jaJP;
  return null;
});

const naiveDateLocale = computed(() => {
  if (locale.value === "zh-CN") return dateZhCN;
  if (locale.value === "en") return dateEnUS;
  if (locale.value === "jp") return dateJaJP;
  return null;
});

function onLocale(v: string) {
  locale.value = v;
  localStorage.setItem("locale", v);
  document.documentElement.lang = v;
}

// 应用初始化
onMounted(() => {
  document.documentElement.lang = locale.value;
  collapsed.value = localStorage.getItem("collapsed") === "true";
});

watch(
  () => route.path,
  (p) => {
    menuValue.value = p;
  }
);
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
  transition: width var(--motion-duration) var(--motion-easing),
    max-width var(--motion-duration) var(--motion-easing),
    min-width var(--motion-duration) var(--motion-easing),
    color var(--motion-duration) var(--motion-easing),
    background-color var(--motion-duration) var(--motion-easing),
    border-color var(--motion-duration) var(--motion-easing),
    flex-basis var(--motion-duration) var(--motion-easing);
}

.sider-content {
  transition: opacity var(--motion-duration) var(--motion-easing);
}

.app-menu :deep(.n-menu-item-content),
.app-ctrl:deep(.n-menu-item-content) {
  transition: color var(--motion-duration) var(--motion-easing),
    background-color var(--motion-duration) var(--motion-easing),
    border-color var(--motion-duration) var(--motion-easing),
    padding var(--motion-duration) var(--motion-easing),
    margin var(--motion-duration) var(--motion-easing),
    transform var(--motion-duration) var(--motion-easing);
  will-change: padding, margin, transform;
}

.app-menu :deep(.n-menu-item-content__icon),
.app-ctrl :deep(.n-menu-item-content__icon) {
  font-size: var(--icon-size);
}

.app-content {
  padding: var(--padding);
}
</style>
