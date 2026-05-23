import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/users' },
      { path: 'users', component: () => import('../views/Users.vue') },
      { path: 'groups', component: () => import('../views/Groups.vue') },
      { path: 'models', component: () => import('../views/Models.vue') },
      { path: 'skills', component: () => import('../views/Skills.vue') },
      { path: 'agents', component: () => import('../views/Agents.vue') },
      { path: 'messages', component: () => import('../views/Messages.vue') },
      { path: 'sensitive', component: () => import('../views/SensitiveWords.vue') },
      { path: 'crawler', component: () => import('../views/Crawler.vue') },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) return '/login'
  if (to.path === '/login' && auth.isLoggedIn) return '/users'
})

export default router
