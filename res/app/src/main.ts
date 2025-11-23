import { createApp } from "vue";
import { createPinia } from "pinia";
import { createI18n } from "vue-i18n";
import { messages } from "@/locales/.index";
import router from "@/router";
import "bootstrap/dist/css/bootstrap.min.css";
import "@/styles/root.css";
import "bootstrap";
import App from "../app.vue";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { io, Socket } from "socket.io-client";

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

const socketUrl = (import.meta as any).env?.VITE_SOCKET_URL || "http://127.0.0.1:5000";
const socket: Socket = io(socketUrl, { transports: ["websocket"], autoConnect: true });

const app = createApp(App).use(createPinia()).use(router).use(i18n).component("fa", FontAwesomeIcon);
app.provide("socket", socket);
app.mount("#app");
