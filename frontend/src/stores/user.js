import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'
import axios from 'axios'

// 创建专门用于认证的v1 API请求实例
const authRequest = axios.create({
  baseURL: 'http://localhost:5001/api/v1',
  timeout: 5000
})

// 认证请求拦截器
authRequest.interceptors.request.use(
  config => {
    // 认证请求不需要token，但可能需要其他headers
    return config
  },
  error => {
    console.log(error)
    return Promise.reject(error)
  }
)

// 认证响应拦截器
authRequest.interceptors.response.use(
  response => {
    const res = response.data
    if (response.status >= 200 && response.status < 300) {
      return res
    } else {
      const errorMessage = res.message || res.error || 'Request failed'
      console.error('Auth API Error:', errorMessage)
      return Promise.reject(new Error(errorMessage))
    }
  },
  error => {
    let errorMessage = 'Network Error'
    if (error.response) {
      const res = error.response.data
      errorMessage = res.message || res.error || `HTTP ${error.response.status} Error`
    } else if (error.request) {
      errorMessage = 'No response from server'
    } else {
      errorMessage = error.message
    }
    console.error('Auth Response Error:', errorMessage)
    return Promise.reject(new Error(errorMessage))
  }
)

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || '')
  const currentTenant = ref(null)
  const availableTenants = ref([])

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isSuperAdmin = computed(() => {
    // 检查用户在当前租户中的角色是否为super_admin
    return currentTenant.value?.role === 'super_admin' || user.value?.tenant_role === 'super_admin'
  })
  const tenantRole = computed(() => user.value?.tenant_role || 'user')
  const tenantId = computed(() => currentTenant.value?.tenant_id || user.value?.tenant_id)

  // 登录
  const login = async (credentials) => {
    try {
      const response = await authRequest.post('/auth/login', credentials)
      const { access_token, user: userData } = response.data
      
      // 存储token和用户信息
      token.value = access_token
      user.value = userData
      availableTenants.value = userData.tenants || []
      
      // 设置当前租户（默认使用第一个租户）
      if (userData.tenants && userData.tenants.length > 0) {
        currentTenant.value = userData.tenants[0]
      } else {
        currentTenant.value = {
          tenant_id: userData.tenant_id,
          tenant_name: '默认租户',
          role: userData.tenant_role
        }
      }
      
      // 存储到localStorage
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('user_info', JSON.stringify(userData))
      localStorage.setItem('current_tenant', JSON.stringify(currentTenant.value))
      
      return response
    } catch (error) {
      throw error
    }
  }

  // 登出
  const logout = () => {
    token.value = ''
    user.value = null
    currentTenant.value = null
    availableTenants.value = []
    
    // 清除localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('current_tenant')
  }

  // 切换租户
  const switchTenant = (tenant) => {
    currentTenant.value = tenant
    localStorage.setItem('current_tenant', JSON.stringify(tenant))
  }

  // 初始化用户状态（从localStorage恢复）
  const initializeUser = () => {
    const storedUser = localStorage.getItem('user_info')
    const storedTenant = localStorage.getItem('current_tenant')
    
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
        availableTenants.value = user.value.tenants || []
      } catch (error) {
        console.error('Failed to parse stored user info:', error)
        logout()
      }
    }
    
    if (storedTenant) {
      try {
        currentTenant.value = JSON.parse(storedTenant)
      } catch (error) {
        console.error('Failed to parse stored tenant info:', error)
      }
    }
  }

  // 获取用户资源限额信息
  const getResourceQuotas = async () => {
    try {
      const response = await request.get('/users/quotas')
      return response.data
    } catch (error) {
      console.error('Failed to get resource quotas:', error)
      return null
    }
  }

  return {
    // 状态
    user,
    token,
    currentTenant,
    availableTenants,
    
    // 计算属性
    isLoggedIn,
    isSuperAdmin,
    tenantRole,
    tenantId,
    
    // 方法
    login,
    logout,
    switchTenant,
    initializeUser,
    getResourceQuotas
  }
})