<template>
  <div class="login-container">
    <div class="login-form-container">
      <div class="login-header">
        <div class="logo">
          <span class="logo-text">IT 拨测系统</span>
        </div>
        <div class="login-title">登录</div>
      </div>
      
      <a-form
        :model="formState"
        @submit.prevent="handleLogin"
        class="login-form"
      >
        <a-form-item
          name="username"
          :rules="[{ required: true, message: '请输入用户名!' }]"
        >
          <a-input 
            v-model:value="formState.username" 
            size="large"
            placeholder="用户名"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>
        
        <a-form-item
          name="password"
          :rules="[{ required: true, message: '请输入密码!' }]"
        >
          <a-input-password
            v-model:value="formState.password"
            size="large"
            placeholder="密码"
            @pressEnter="handleLogin"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
        
        <a-form-item>
          <a-button 
            type="primary" 
            html-type="submit" 
            :loading="loading"
            size="large"
            block
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>
      
      <div class="login-footer">
        <div class="default-credentials">
          <p>默认账户: test / 123456</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const formState = reactive({
  username: 'test',
  password: '123456'
})

const handleLogin = async () => {
  loading.value = true
  
  try {
    await userStore.login({
      username: formState.username,
      password: formState.password
    })
    
    message.success('登录成功')
    // 跳转到首页
    router.push('/probe-config/node')
  } catch (error) {
    message.error('登录失败: ' + error.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.login-form-container {
  width: 400px;
  padding: 40px 30px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  text-align: center;
}

.login-header {
  margin-bottom: 30px;
}

.logo {
  margin-bottom: 20px;
}

.logo-text {
  font-size: 24px;
  font-weight: 600;
  color: #1890ff;
}

.login-title {
  font-size: 20px;
  font-weight: 500;
  color: #333;
  margin-bottom: 10px;
}

.login-form {
  margin-bottom: 20px;
}

.login-footer {
  margin-top: 20px;
}

.default-credentials {
  font-size: 12px;
  color: #999;
}

.default-credentials p {
  margin: 0;
}
</style>