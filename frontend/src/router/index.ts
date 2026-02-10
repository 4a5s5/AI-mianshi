import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue')
    },
    {
      path: '/practice/single',
      name: 'SinglePractice',
      component: () => import('@/views/SinglePracticeView.vue')
    },
    {
      path: '/practice/paper',
      name: 'PaperPractice',
      component: () => import('@/views/PaperPracticeView.vue')
    },
    {
      path: '/repository',
      name: 'Repository',
      component: () => import('@/views/RepositoryView.vue')
    },
    {
      path: '/history',
      name: 'History',
      component: () => import('@/views/HistoryView.vue')
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/SettingsView.vue')
    }
  ]
})

export default router
