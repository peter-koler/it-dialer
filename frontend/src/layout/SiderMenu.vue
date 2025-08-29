<template>
  <a-layout-sider 
    width="256" 
    :collapsed="collapsed"
    collapsible
    :trigger="null"
    breakpoint="lg"
    @collapse="onCollapse"
  >
    <div class="logo">
      <h2 v-if="!collapsed" style="color: white">IT 拨测系统</h2>
      <span v-else style="color: white; font-size: 18px">IT</span>
    </div>
    <a-menu
      v-model:selectedKeys="selectedKeys"
      v-model:openKeys="openKeys"
      mode="inline"
      theme="dark"
      :collapsed="collapsed"
      @click="handleMenuClick"
    >
      <template v-for="item in filteredMenuItems" :key="item.key">
        <a-sub-menu v-if="item.children" :key="`sub-${item.key}`">
          <template #title>
            <span>
              <component v-if="item.icon" :is="item.icon" />
              <span>{{ t(item.label) }}</span>
            </span>
          </template>
          <template v-for="child in item.children" :key="child.key">
            <a-sub-menu v-if="child.children" :key="`sub-${child.key}`">
              <template #title>
                <span>
                  <component v-if="child.icon" :is="child.icon" />
                  <span>{{ t(child.label) }}</span>
                </span>
              </template>
              <a-menu-item v-for="grandChild in child.children" :key="grandChild.key">
                <component v-if="grandChild.icon" :is="grandChild.icon" />
                <span>{{ t(grandChild.label) }}</span>
              </a-menu-item>
            </a-sub-menu>
            <a-menu-item v-else :key="child.key">
              <component v-if="child.icon" :is="child.icon" />
              <span>{{ t(child.label) }}</span>
            </a-menu-item>
          </template>
        </a-sub-menu>
        <a-menu-item v-else :key="item.key">
          <component v-if="item.icon" :is="item.icon" />
          <span>{{ t(item.label) }}</span>
        </a-menu-item>
      </template>
    </a-menu>
  </a-layout-sider>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import {
  DeploymentUnitOutlined,
  ClusterOutlined,
  SettingOutlined,
  UserOutlined,
  ToolOutlined,
  AlertOutlined,
  BarChartOutlined,
  LineChartOutlined,
  TeamOutlined,
  DashboardOutlined
} from '@ant-design/icons-vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 菜单数据
const menuItems = [
  {
    key: '/dashboard',
    label: 'menu.dashboard',
    icon: DashboardOutlined
  },
  {
    key: 'probe-config',
    label: 'menu.probeConfig',
    icon: DeploymentUnitOutlined,
    children: [
      {
        key: '/probe-config/node',
        label: 'menu.probeConfig.node',
        icon: ClusterOutlined
      },
      {
        key: '/probe-config/task',
        label: 'menu.probeConfig.task',
        icon: ToolOutlined
      }
    ]
  },
  {
    key: 'task-management',
    label: 'menu.taskManagement',
    icon: DeploymentUnitOutlined,
    children: [
      {
        key: '/task-management/list',
        label: 'menu.taskManagement.list',
        icon: ToolOutlined
      }
    ]
  },
  {
    key: 'alarm-management',
    label: 'menu.alarmManagement',
    icon: AlertOutlined,
    children: [
      {
        key: '/alarm-management',
        label: 'menu.alarmManagement.probe',
        icon: AlertOutlined
      },
      {
        key: '/task-management/api-alerts',
        label: 'menu.alarmManagement.api',
        icon: ToolOutlined
      }
    ]
  },
  {
    key: 'reports',
    label: 'menu.reports',
    icon: BarChartOutlined,
    children: [
      {
        key: '/reports/overview',
        label: 'menu.reports.overview',
        icon: LineChartOutlined
      },
      {
        key: 'reports-detailed',
        label: 'menu.reports.detailed',
        icon: BarChartOutlined,
        children: [
          {
            key: '/reports/tcp',
            label: 'menu.reports.tcp',
            icon: ToolOutlined
          },
          {
            key: '/reports/ping',
            label: 'menu.reports.ping',
            icon: ToolOutlined
          },
          {
            key: '/reports/http',
            label: 'menu.reports.http',
            icon: ToolOutlined
          },
          {
            key: '/reports/api',
            label: 'menu.reports.api',
            icon: ToolOutlined
          }
        ]
      }
    ]
  },
  {
    key: 'system',
    label: 'menu.system',
    icon: SettingOutlined,
    children: [
      {
        key: '/system/user',
        label: 'menu.system.user',
        icon: UserOutlined,
        permission: 'sys:user'
      },
      {
        key: '/system/variables',
        label: 'menu.system.variables',
        icon: ToolOutlined
      },
      {
        key: '/system/tenant',
        label: 'menu.system.tenant',
        icon: TeamOutlined,
        permission: 'sys:tenant'
      },
      {
        key: '/system/user-tenant-management',
        label: 'menu.system.userTenantManagement',
        icon: TeamOutlined,
        permission: 'sys:tenant'
      }
    ]
  }
]

// 根据权限过滤菜单
const filteredMenuItems = computed(() => {
  const userRole = userStore.tenantRole
  const isSuperAdmin = userStore.isSuperAdmin
  
  return menuItems.map(item => {
    if (item.children) {
      // 过滤子菜单
      const filteredChildren = item.children.filter(child => {
        // 用户管理权限检查
        if (child.permission === 'sys:user') {
          return userRole === 'admin' || isSuperAdmin
        }
        // 租户管理权限检查（仅超级管理员可见）
        if (child.permission === 'sys:tenant') {
          return isSuperAdmin
        }
        // 其他菜单项的权限检查
        if (userRole === 'viewer') {
          // viewer角色只能查看，不能操作
          return !child.key.includes('/new') && !child.key.includes('/edit')
        }
        return true
      })
      
      // 如果还有子菜单则保留父菜单
      if (filteredChildren.length > 0) {
        return { ...item, children: filteredChildren }
      }
      return null
    }
    return item
  }).filter(Boolean)
})

const collapsed = ref(false)
const selectedKeys = ref([route.path])
const openKeys = ref(['probe-config'])

// 监听路由变化
watch(
  () => route.path,
  (newPath) => {
    selectedKeys.value = [newPath]
    
    // 根据当前路径确定展开的菜单
    if (newPath === '/dashboard') {
      openKeys.value = []
    } else if (newPath.startsWith('/probe-config')) {
      openKeys.value = ['probe-config']
    } else if (newPath.startsWith('/system')) {
      openKeys.value = ['system']
    } else if (newPath.startsWith('/task-management')) {
      if (newPath.includes('api-alerts')) {
        openKeys.value = ['alarm-management']
      } else {
        openKeys.value = ['task-management']
      }
    } else if (newPath.startsWith('/alarm-management')) {
      openKeys.value = ['alarm-management']
    } else if (newPath.startsWith('/reports')) {
      openKeys.value = ['reports', 'reports-detailed']
    }
  }
)

const onCollapse = (collapsedState) => {
  collapsed.value = collapsedState
}

const handleMenuClick = ({ key }) => {
  router.push(key)
}
</script>

<style scoped>
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  margin-bottom: 16px;
}
</style>