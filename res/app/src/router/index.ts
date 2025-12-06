import { createRouter, createWebHistory } from "vue-router";

const AppHome = () => import("@/pages/AppHome.vue");
const RoleManager = () => import("@/pages/RoleManager.vue");
const LocalGame = () => import("@/pages/LocalGame.vue");
const OnlineLobby = () => import("@/pages/OnlineLobby.vue");
const Gaming = () => import("@/pages/_gaming.vue");

const router = createRouter({
	history: createWebHistory(),
	routes: [
		{ path: "/", component: AppHome },
		{ path: "/roles", component: RoleManager },
		{ path: "/local", component: LocalGame },
		{ path: "/online", component: OnlineLobby },
		{ path: "/gaming/:id", component: Gaming },
	],
});

export default router;
