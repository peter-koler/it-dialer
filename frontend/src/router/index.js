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
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/Dashboard.vue'),
        meta: { title: '仪表板' }
      },
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
        path: '/task-management/ping-result/:id',
        name: 'PingMonitoringResult',
        component: () => import('../views/ping-monitoring/PingMonitoringResult.vue'),
        props: true
      },
      {
        path: '/task-management/tcp-result/:id',
        name: 'TcpMonitoringResult',
        component: () => import('../views/tcp-monitoring/TcpMonitoringResult.vue'),
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
        path: '/task-management/ping-probe-detail/:taskId/:location/:agentArea',
        name: 'PingProbeDetail',
        component: () => import('../views/ping-monitoring/PingProbeDetail.vue'),
        meta: { title: 'Ping拨测点详情' },
        props: true
      },
      {
        path: '/task-management/tcp-probe-detail/:taskId/:probeName/:agentArea',
        name: 'TcpProbeDetail',
        component: () => import('../views/tcp-monitoring/TcpProbeDetail.vue'),
        meta: { title: 'TCP拨测点详情' },
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
      },
      {
          path: '/alarm-management',
          name: 'AlarmManagement',
          component: () => import('../views/alarm/AlarmManagement.vue'),
          meta: { title: '告警管理', icon: 'alert' }
        },
      {
        path: '/reports/overview',
        name: 'ReportOverview',
        component: () => import('../views/reports/ReportOverview.vue'),
        meta: { title: '报表总览' }
      },
      {
        path: '/reports/tcp',
        name: 'TcpReport',
        component: () => import('../views/reports/TcpReport.vue'),
        meta: { title: 'TCP报表' }
      },
      {
        path: '/reports/ping',
        name: 'PingReport',
        component: () => import('../views/reports/PingReport.vue'),
        meta: { title: 'Ping报表' }
      },
      {
        path: '/reports/http',
        name: 'HttpReport',
        component: () => import('../views/reports/HttpReport.vue'),
        meta: { title: 'HTTP报表' }
      },
      {
        path: '/reports/api',
        name: 'ApiReport',
        component: () => import('../views/reports/ApiReport.vue'),
        meta: { title: 'API报表' }
      },
      {
        path: '/system/tenant',
        name: 'TenantManagement',
        component: () => import('../views/tenant-management/TenantManagement.vue'),
        meta: { title: '租户管理', requiresSuperAdmin: true }
      },
      {
        path: '/system/user-tenant-management',
        name: 'UserTenantManagement',
        component: () => import('../views/system/UserTenantManagement.vue'),
        meta: { title: '用户租户关联管理', requiresSuperAdmin: true }
      },
      {
        path: '/tenant/user-management',
        name: 'TenantUserManagement',
        component: () => import('../views/tenant-management/TenantUserManagement.vue'),
        meta: { title: '租户用户管理', requiresTenantAdmin: true }
      },
      {
        path: '/system/audit-logs',
        name: 'AuditLogs',
        component: () => import('../views/system/AuditLogs.vue'),
        meta: { title: '审计日志查询', requiresTenantAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
const whiteList = ['/login']

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  
  if (token) {
    if (to.path === '/login') {
      next('/')
    } else {
      // 检查超级管理员权限
      if (to.meta?.requiresSuperAdmin) {
        const userInfo = localStorage.getItem('user_info')
        if (userInfo) {
          try {
            const user = JSON.parse(userInfo)
            // 检查用户的租户角色是否为超级管理员
            if (user.tenant_role !== 'super_admin') {
              // 非超级管理员，跳转到首页
              next('/')
              return
            }
          } catch (error) {
            console.error('Failed to parse user info:', error)
            next('/login')
            return
          }
        } else {
          next('/login')
          return
        }
      }
      
      // 检查租户管理员权限
      if (to.meta?.requiresTenantAdmin) {
        const userInfo = localStorage.getItem('user_info')
        const currentTenant = localStorage.getItem('current_tenant')
        if (userInfo && currentTenant) {
          try {
            const user = JSON.parse(userInfo)
            const tenant = JSON.parse(currentTenant)
            // 检查用户是否为租户管理员或超级管理员
            if (tenant.role !== 'tenant_admin' && user.tenant_role !== 'super_admin') {
              // 非租户管理员，跳转到首页
              next('/')
              return
            }
          } catch (error) {
            console.error('Failed to parse user or tenant info:', error)
            next('/login')
            return
          }
        } else {
          next('/login')
          return
        }
      }
      next()
    }
  } else {
    if (whiteList.includes(to.path)) {
      next()
    } else {
      next('/login')
    }
  }
})

export default router