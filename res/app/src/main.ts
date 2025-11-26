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

const envAny = (import.meta as any).env || {};
const isDev = !!envAny?.DEV;
const socketUrl = envAny?.VITE_SOCKET_URL || (isDev ? "http://127.0.0.1:5000" : window.location.origin || "http://127.0.0.1:5000");
const socket: Socket = io(socketUrl, {
	autoConnect: true,
	transports: ["websocket", "polling"],
	reconnection: true,
	reconnectionAttempts: 10,
	reconnectionDelay: 1000,
	path: "/socket.io",
});

const app = createApp(App).use(createPinia()).use(router).use(i18n).component("fa", FontAwesomeIcon);
app.provide("socket", socket);
app.mount("#app");
