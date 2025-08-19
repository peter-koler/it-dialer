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
        <a-sub-menu v-if="item.children" :key="item.key">
          <template #title>
            <span>
              <component v-if="item.icon" :is="item.icon" />
              <span>{{ t(item.label) }}</span>
            </span>
          </template>
          <a-menu-item v-for="child in item.children" :key="child.key">
            <component v-if="child.icon" :is="child.icon" />
            <span>{{ t(child.label) }}</span>
          </a-menu-item>
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
import {
  DeploymentUnitOutlined,
  ClusterOutlined,
  SettingOutlined,
  UserOutlined,
  ToolOutlined
} from '@ant-design/icons-vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

// 菜单数据
const menuItems = [
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
      },
      {
        key: '/task-management/api-alerts',
        label: 'menu.taskManagement.apiAlerts',
        icon: ToolOutlined
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
      }
    ]
  }
]

// 模拟用户角色 (实际应该从store获取)
const currentUserRole = 'admin'

// 根据权限过滤菜单
const filteredMenuItems = computed(() => {
  // 简化权限检查逻辑
  if (currentUserRole === 'admin') {
    return menuItems
  }
  
  // viewer角色只显示部分菜单
  return menuItems.filter(item => {
    if (item.children) {
      // 过滤子菜单
      const filteredChildren = item.children.filter(child => {
        if (child.permission === 'sys:user') {
          return currentUserRole === 'admin'
        }
        return true
      })
      
      // 如果还有子菜单则保留父菜单
      return filteredChildren.length > 0
    }
    return true
  })
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
    if (newPath.startsWith('/probe-config')) {
      openKeys.value = ['probe-config']
    } else if (newPath.startsWith('/system')) {
      openKeys.value = ['system']
    } else if (newPath.startsWith('/task-management')) {
      openKeys.value = ['task-management']
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