import { createRouter, createWebHistory } from 'vue-router'

const RoleManager = () => import('@/pages/RoleManager.vue')
const LocalGame = () => import('@/pages/LocalGame.vue')
const OnlineLobby = () => import('@/pages/OnlineLobby.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/roles' },
    { path: '/roles', component: RoleManager },
    { path: '/local', component: LocalGame },
    { path: '/online', component: OnlineLobby }
  ]
})

export default router