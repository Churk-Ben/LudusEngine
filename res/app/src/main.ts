import { createApp } from "vue";
import { createPinia } from "pinia";
import { createI18n } from "vue-i18n";
import { messages } from "@/i18n";
import router from "@/router";
import "bootstrap/dist/css/bootstrap.min.css";
import "@/styles/theme.css";
import "bootstrap";
import App from "../app.vue";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

function resolveInitialLocale(): string {
	const saved = localStorage.getItem("locale");
	if (saved) return saved;
	const nav = (navigator.language || "zh-CN").toLowerCase();
	if (nav.startsWith("zh")) return "zh-CN";
	return "en";
}

const i18n = createI18n({
	legacy: false,
	locale: resolveInitialLocale(),
	fallbackLocale: "en",
	messages,
});

createApp(App).use(createPinia()).use(router).use(i18n).component("fa", FontAwesomeIcon).mount("#app");
