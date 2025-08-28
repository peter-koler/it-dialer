<template>
  <a-layout has-sider style="min-height: 100vh;">
    <SiderMenu />
    <a-layout>
      <a-layout-header class="layout-header">
        <div class="header-actions">
          <!-- 租户选择器 -->
          <a-dropdown v-if="userStore.availableTenants.length > 1" class="tenant-selector">
            <template #overlay>
              <a-menu @click="handleTenantSwitch">
                <a-menu-item 
                  v-for="tenant in userStore.availableTenants" 
                  :key="tenant.tenant_id"
                  :class="{ 'ant-menu-item-selected': tenant.tenant_id === userStore.currentTenant?.tenant_id }"
                >
                  <TeamOutlined />
                  {{ tenant.tenant_name }}
                  <a-tag v-if="tenant.role" size="small" :color="getRoleColor(tenant.role)" style="margin-left: 8px">
                    {{ getRoleText(tenant.role) }}
                  </a-tag>
                </a-menu-item>
              </a-menu>
            </template>
            <a class="ant-dropdown-link tenant-link" @click.prevent>
              <TeamOutlined />
              <span class="tenant-name">{{ userStore.currentTenant?.tenant_name || '选择租户' }}</span>
              <DownOutlined />
            </a>
          </a-dropdown>
          
          <!-- 用户菜单 -->
          <a-dropdown>
            <a class="ant-dropdown-link" @click.prevent>
              <a-avatar :size="32" icon="user" style="background-color: #1890ff;" />
              <span class="user-name">
                {{ userStore.user?.username || '用户' }}
                <a-tag v-if="userStore.tenantRole" size="small" :color="getRoleColor(userStore.tenantRole)" style="margin-left: 4px">
                  {{ getRoleText(userStore.tenantRole) }}
                </a-tag>
              </span>
            </a>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile" @click="goToProfile">
                  <UserOutlined />
                  个人中心
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout">
                  <LogoutOutlined />
                  退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content style="padding: 24px; background: #f0f2f5;">
        <div style="background: #fff; padding: 24px; min-height: calc(100vh - 160px);">
          <router-view />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LogoutOutlined, TeamOutlined, DownOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import SiderMenu from './SiderMenu.vue'

const router = useRouter()
const userStore = useUserStore()

// 初始化用户状态
onMounted(() => {
  userStore.initializeUser()
})

const goToProfile = () => {
  // 跳转到个人中心页面
  message.info('查看个人中心')
}

const handleLogout = () => {
  // 执行登出操作
  userStore.logout()
  message.success('已退出登录')
  router.push('/login')
}

// 租户切换处理
const handleTenantSwitch = ({ key }) => {
  const tenant = userStore.availableTenants.find(t => t.tenant_id === key)
  if (tenant) {
    userStore.switchTenant(tenant)
    message.success(`已切换到租户: ${tenant.tenant_name}`)
    // 刷新当前页面以应用新的租户上下文
    window.location.reload()
  }
}

// 角色颜色映射
const getRoleColor = (role) => {
  const colorMap = {
    'admin': 'red',
    'operator': 'orange', 
    'viewer': 'blue',
    'super_admin': 'purple'
  }
  return colorMap[role] || 'default'
}

// 角色文本映射
const getRoleText = (role) => {
  const textMap = {
    'admin': '管理员',
    'operator': '操作员',
    'viewer': '查看者',
    'super_admin': '超级管理员'
  }
  return textMap[role] || role
}
</script>

<style scoped>
.layout-header {
  background: #fff;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: flex-end;
  align-items: center;
  height: 64px;
  line-height: 64px;
  position: relative;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-name {
  margin-left: 8px;
  color: rgba(0, 0, 0, 0.85);
}

.tenant-name {
  margin-left: 4px;
  margin-right: 4px;
  color: rgba(0, 0, 0, 0.85);
}

.ant-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.tenant-link {
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.tenant-link:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.tenant-selector {
  border-right: 1px solid #f0f0f0;
  padding-right: 16px;
}
</style>