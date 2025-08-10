import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layout/Layout.vue'
import Login from '../views/Login.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: Layout,
    redirect: '/probe-config/node', // 添加默认重定向
    children: [
      {
        path: '/probe-config/node',
        name: 'NodeManagement',
        component: () => import('../views/NodeManagement.vue')
      },
      {
        path: '/probe-config/task',
        name: 'ProbeTask',
        component: () => import('../views/probe-task/index.vue')
      },
      {
        path: '/task-management/list',
        name: 'TaskList',
        component: () => import('../views/TaskList.vue')
      },
      {
        path: '/system/user',
        name: 'UserManagement',
        component: () => import('../views/UserManagement.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 添加路由守卫
const whiteList = ['/login'] // 不重定向白名单

router.beforeEach((to, from, next) => {
  // 检查是否已登录
  const token = localStorage.getItem('access_token')
  
  if (whiteList.indexOf(to.path) !== -1) {
    next()
    return
  }
  
  if (!token) {
    next('/login')
  } else {
    next()
  }
})

export default router