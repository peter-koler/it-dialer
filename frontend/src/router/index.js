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
    redirect: '/probe-config/node',
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
        path: '/tasks/api/new',
        name: 'ApiTaskNew',
        component: () => import('../views/api-task/ApiTaskNew.vue')
      },
      {
        path: '/tasks/api/edit/:id',
        name: 'ApiTaskEdit',
        component: () => import('../views/api-task/ApiTaskEdit.vue'),
        props: true
      },
      {
        path: '/task-management/list',
        name: 'TaskList',
        component: () => import('../views/task-detail/TaskDetail.vue')
      },
      {
        path: '/task-management/detail/:id',
        name: 'TaskDetail',
        component: () => import('../views/task-detail/TaskDetail.vue'),
        props: true
      },
      {
        path: '/task-management/api-result/:id',
        name: 'ApiMonitoringResult',
        component: () => import('../views/api-monitoring/ApiMonitoringResult.vue'),
        props: true
      },
      {
        path: '/task-management/http-result/:id',
        name: 'HttpMonitoringResult',
        component: () => import('../views/http-monitoring/HttpMonitoringResult.vue'),
        props: true
      },
      {
        path: '/task-management/http-probe-detail/:taskId/:probeName/:agentArea',
        name: 'HttpProbeDetail',
        component: () => import('../views/http-monitoring/HttpProbeDetail.vue'),
        meta: { title: 'HTTP拨测点详情' },
        props: true
      },
      {
        path: '/api-monitoring/result/:taskId',
        name: 'ApiMonitoringResultPage',
        component: () => import('../views/api-monitoring/ApiMonitoringResult.vue'),
        props: true
      },
      {
        path: '/api-monitoring/task-result/:id',
        name: 'ApiTaskResult',
        component: () => import('../views/api-monitoring/ApiTaskResult.vue'),
        props: true
      },
      {
        path: '/system/user',
        name: 'UserManagement',
        component: () => import('../views/UserManagement.vue')
      },
      {
        path: '/system/variables',
        name: 'SystemVariables',
        component: () => import('../views/system/SystemVariableManager.vue')
      },
      {
        path: '/task-management/api-alerts',
        name: 'ApiAlertManagement',
        component: () => import('../views/alert-management/ApiAlertManagement.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 添加路由守卫
const whiteList = ['/login']

router.beforeEach((to, from, next) => {
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