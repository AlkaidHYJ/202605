import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/workspace' },
      { path: 'workspace', name: 'Workspace', component: () => import('../views/Workspace.vue') },
      { path: 'nl2sql', name: 'Nl2Sql', component: () => import('../views/Nl2Sql.vue') },
      { path: 'im', name: 'IM', component: () => import('../views/IM.vue') },
      { path: 'agents', name: 'Agents', component: () => import('../views/Agents.vue') },
      { path: 'dashboards', name: 'Dashboards', component: () => import('../views/Dashboards.vue') },
    ],
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) return '/login'
  if (to.path === '/login' && auth.isLoggedIn) return '/workspace'
})

export default router
