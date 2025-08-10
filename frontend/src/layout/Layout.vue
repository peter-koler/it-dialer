<template>
  <a-layout has-sider style="min-height: 100vh;">
    <SiderMenu />
    <a-layout>
      <a-layout-header class="layout-header">
        <div class="header-actions">
          <a-dropdown>
            <a class="ant-dropdown-link" @click.prevent>
              <a-avatar :size="32" icon="user" style="background-color: #1890ff;" />
              <span class="user-name">test</span>
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
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons-vue'
import SiderMenu from './SiderMenu.vue'

const router = useRouter()

const goToProfile = () => {
  // 跳转到个人中心页面
  message.info('查看个人中心')
}

const handleLogout = () => {
  // 执行登出操作
  message.success('已退出登录')
  router.push('/login')
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
}

.user-name {
  margin-left: 8px;
  color: rgba(0, 0, 0, 0.85);
}

.ant-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
}
</style>