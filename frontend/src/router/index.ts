import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/board/HomeView.vue'),
    meta: { title: '校园论坛 - 首页' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '登录/注册', requiresGuest: true },
  },
  {
    path: '/boards/:slug',
    name: 'BoardPosts',
    component: () => import('@/views/board/BoardPostsView.vue'),
    meta: { title: '板块帖子' },
  },
  {
    path: '/posts/:id',
    name: 'PostDetail',
    component: () => import('@/views/post/PostDetailView.vue'),
    meta: { title: '帖子详情' },
  },
  {
    path: '/posts/new',
    name: 'PostCreate',
    component: () => import('@/views/post/PostEditView.vue'),
    meta: { title: '发布帖子', requiresAuth: true },
  },
  {
    path: '/posts/:id/edit',
    name: 'PostEdit',
    component: () => import('@/views/post/PostEditView.vue'),
    meta: { title: '编辑帖子', requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/user/ProfileView.vue'),
    meta: { title: '个人中心', requiresAuth: true },
  },
  {
    path: '/profile/posts',
    name: 'UserPosts',
    component: () => import('@/views/user/UserPostsView.vue'),
    meta: { title: '我的帖子', requiresAuth: true },
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/views/notification/NotificationListView.vue'),
    meta: { title: '通知', requiresAuth: true },
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: () => import('@/views/auth/VerifyEmailView.vue'),
    meta: { title: '验证邮箱', requiresGuest: true },
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/auth/ResetPasswordView.vue'),
    meta: { title: '修改密码', requiresAuth: true },
  },
  {
    path: '/admin',
    component: () => import('@/components/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/AdminDashboardView.vue'),
        meta: { title: '管理后台 - 统计' },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/AdminUsersView.vue'),
        meta: { title: '管理后台 - 用户管理' },
      },
      {
        path: 'boards',
        name: 'AdminBoards',
        component: () => import('@/views/admin/AdminBoardsView.vue'),
        meta: { title: '管理后台 - 板块管理' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '404 - 页面未找到' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  document.title = (to.meta.title as string) || '校园论坛'

  const authStore = useAuthStore()

  if (authStore.token && !authStore.currentUser) {
    await authStore.restoreSession()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    return { name: 'Home' }
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: 'Home' }
  }
})

export default router
