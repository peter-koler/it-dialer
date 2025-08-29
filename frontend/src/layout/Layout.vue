<template>
  <a-layout has-sider style="min-height: 100vh;">
    <SiderMenu />
    <a-layout>
      <a-layout-header class="layout-header">
        <div class="header-actions">
          <!-- 无租户Alert提示 -->
          <a-alert 
            v-if="userStore.shouldShowNoTenantAlert && !userStore.shouldShowTenantApiError"
            message="未分配租户，请联系管理员"
            type="warning"
            show-icon
            closable
            class="no-tenant-alert"
          />
          
          <!-- 租户API错误提示 -->
          <a-alert 
            v-if="userStore.shouldShowTenantApiError"
            :message="userStore.tenantApiError"
            type="error"
            show-icon
            closable
            class="tenant-api-error-alert"
            @close="userStore.clearTenantApiError"
          >
            <template #action>
              <a-button 
                size="small" 
                type="primary" 
                :loading="userStore.isRetryingTenantApi"
                @click="handleRetryTenantApi"
              >
                重试
              </a-button>
            </template>
          </a-alert>
          
          <!-- 租户选择器 -->
          <a-dropdown v-else-if="userStore.availableTenants.length > 1 || userStore.isSuperAdmin" class="tenant-selector">
            <template #overlay>
              <a-menu @click="handleTenantSwitch">
                <!-- Super Admin的"所有租户"选项 -->
                <a-menu-item 
                  v-if="userStore.isSuperAdmin"
                  key="all_tenants"
                  :class="{ 'ant-menu-item-selected': userStore.currentTenant?.tenant_id === 'all_tenants' }"
                >
                  <GlobalOutlined />
                  所有租户
                  <a-tag size="small" color="purple" style="margin-left: 8px">
                    全局视图
                  </a-tag>
                </a-menu-item>
                
                <!-- 分隔线 -->
                <a-menu-divider v-if="userStore.isSuperAdmin && userStore.availableTenants.length > 0" />
                
                <!-- 普通租户选项 -->
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
                
                <!-- Super Admin管理选项 -->
                <template v-if="userStore.isSuperAdmin">
                  <a-menu-divider />
                  <a-menu-item key="tenant_management" @click="goToTenantManagement">
                    <SettingOutlined />
                    租户管理
                  </a-menu-item>
                </template>
              </a-menu>
            </template>
            <a class="ant-dropdown-link tenant-link" @click.prevent>
              <component :is="getCurrentTenantIcon()" />
              <span class="tenant-name">{{ getCurrentTenantDisplayName() }}</span>
              <DownOutlined />
            </a>
          </a-dropdown>
          
          <!-- 单租户显示 -->
          <div v-else-if="userStore.availableTenants.length === 1" class="single-tenant">
            <TeamOutlined />
            <span class="tenant-name">{{ userStore.currentTenant?.tenant_name }}</span>
            <a-tag v-if="userStore.currentTenant?.role" size="small" :color="getRoleColor(userStore.currentTenant.role)" style="margin-left: 8px">
              {{ getRoleText(userStore.currentTenant.role) }}
            </a-tag>
          </div>
          
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
import { UserOutlined, LogoutOutlined, TeamOutlined, DownOutlined, GlobalOutlined, SettingOutlined } from '@ant-design/icons-vue'
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
  // 处理super_admin的"所有租户"选项
  if (key === 'all_tenants' && userStore.isSuperAdmin) {
    const allTenantOption = {
      tenant_id: 'all_tenants',
      tenant_name: '所有租户',
      role: 'super_admin'
    }
    userStore.switchTenant(allTenantOption)
    message.success('已切换到全局视图')
    // 刷新当前页面以应用新的租户上下文
    window.location.reload()
    return
  }
  
  // 处理普通租户切换
  const tenant = userStore.availableTenants.find(t => t.tenant_id === key)
  if (tenant) {
    userStore.switchTenant(tenant)
    message.success(`已切换到租户: ${tenant.tenant_name}`)
    // 刷新当前页面以应用新的租户上下文
    window.location.reload()
  }
}

// 重试租户API
const handleRetryTenantApi = async () => {
  try {
    await userStore.retryFetchTenants()
    if (!userStore.tenantApiError) {
      message.success('租户列表获取成功')
      // 如果获取成功且有租户，刷新页面以应用新的租户上下文
      if (userStore.availableTenants.length > 0) {
        setTimeout(() => {
          window.location.reload()
        }, 1000)
      }
    }
  } catch (error) {
    message.error('重试失败，请稍后再试')
  }
}

// 获取当前租户显示名称
const getCurrentTenantDisplayName = () => {
  if (userStore.currentTenant?.tenant_id === 'all_tenants') {
    return '所有租户'
  }
  return userStore.currentTenant?.tenant_name || '选择租户'
}

// 获取当前租户图标
const getCurrentTenantIcon = () => {
  if (userStore.currentTenant?.tenant_id === 'all_tenants') {
    return GlobalOutlined
  }
  return TeamOutlined
}

// 跳转到租户管理页面
const goToTenantManagement = () => {
  router.push('/system/tenant-management')
  message.info('跳转到租户管理页面')
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

.no-tenant-alert {
  margin-right: 16px;
  max-width: 300px;
}

.tenant-api-error-alert {
  margin-right: 16px;
  max-width: 350px;
}

.single-tenant {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-right: 1px solid #f0f0f0;
  margin-right: 16px;
  color: rgba(0, 0, 0, 0.85);
}

.single-tenant .tenant-name {
  margin-left: 4px;
  margin-right: 4px;
}

/* 平板设备 */
@media (max-width: 1024px) {
  .header-actions {
    gap: 12px;
  }
  
  .no-tenant-alert {
    max-width: 280px;
  }
  
  .tenant-api-error-alert {
    max-width: 320px;
  }
}

/* 移动设备 */
@media (max-width: 768px) {
  .layout-header {
    padding: 0 16px;
  }
  
  .header-actions {
    gap: 8px;
    flex-wrap: wrap;
  }
  
  .no-tenant-alert {
    max-width: 200px;
    margin-right: 8px;
    font-size: 12px;
  }
  
  .tenant-api-error-alert {
    max-width: 250px;
    margin-right: 8px;
    font-size: 12px;
  }
  
  .tenant-selector {
    border-right: none;
    padding-right: 8px;
  }
  
  .tenant-link {
    padding: 2px 6px;
  }
  
  .tenant-name {
    font-size: 12px;
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .single-tenant {
    padding: 2px 6px;
    margin-right: 8px;
    border-right: none;
  }
  
  .single-tenant .tenant-name {
    font-size: 12px;
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .user-name {
    display: none;
  }
  
  /* 移动端下拉菜单优化 */
  .ant-dropdown-menu {
    max-width: 200px;
  }
  
  .ant-dropdown-menu .ant-menu-item {
    padding: 8px 12px;
    font-size: 12px;
  }
}

/* 小屏幕移动设备 */
@media (max-width: 480px) {
  .layout-header {
    padding: 0 12px;
    height: 56px;
    line-height: 56px;
  }
  
  .header-actions {
    gap: 6px;
  }
  
  .no-tenant-alert {
    max-width: 160px;
    margin-right: 6px;
  }
  
  .tenant-api-error-alert {
    max-width: 180px;
    margin-right: 6px;
  }
  
  .tenant-name {
    max-width: 60px;
  }
  
  .single-tenant .tenant-name {
    max-width: 60px;
  }
  
  /* 隐藏角色标签以节省空间 */
  .ant-tag {
    display: none;
  }
  
  /* 用户头像缩小 */
  .ant-avatar {
    width: 28px !important;
    height: 28px !important;
    font-size: 12px;
  }
}
</style>