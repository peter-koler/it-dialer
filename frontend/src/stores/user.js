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
  const hasNoTenants = ref(false) // 标记用户是否没有关联租户
  const tenantApiError = ref(null) // 租户API错误信息
  const isRetryingTenantApi = ref(false) // 是否正在重试租户API

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isSuperAdmin = computed(() => {
    // 检查用户在当前租户中的角色是否为super_admin
    return currentTenant.value?.role === 'super_admin' || user.value?.tenant_role === 'super_admin'
  })
  const tenantRole = computed(() => user.value?.tenant_role || 'user')
  const tenantId = computed(() => currentTenant.value?.tenant_id || user.value?.tenant_id)
  const shouldShowNoTenantAlert = computed(() => hasNoTenants.value && isLoggedIn.value && !isSuperAdmin.value)
  const shouldShowTenantApiError = computed(() => !!tenantApiError.value && isLoggedIn.value)

  // 登录
  const login = async (credentials) => {
    try {
      const response = await authRequest.post('/auth/login', credentials)
      const { access_token, user: userData } = response.data
      
      // 存储token和用户信息
      token.value = access_token
      user.value = userData
      
      // 清除之前的错误状态
      tenantApiError.value = null
      
      // 处理租户信息
      if (userData.tenants) {
        availableTenants.value = userData.tenants
        
        // 检查是否有关联租户
        if (userData.tenants.length === 0) {
           hasNoTenants.value = true
           // 如果是super_admin且没有租户，设置为"所有租户"模式
           if (userData.tenant_role === 'super_admin') {
             currentTenant.value = {
               tenant_id: 'all_tenants',
               tenant_name: '所有租户',
               role: 'super_admin'
             }
           } else {
             currentTenant.value = null
           }
         } else {
           hasNoTenants.value = false
           // 设置当前租户（默认使用第一个租户）
           currentTenant.value = userData.tenants[0]
         }
      } else {
        // 如果登录响应中没有租户信息，尝试单独获取
        try {
          const tenantsResponse = await authRequest.get('/tenants')
          const tenants = tenantsResponse.data?.data || []
          userData.tenants = tenants
          availableTenants.value = tenants
          
          if (tenants.length === 0) {
             hasNoTenants.value = true
             // 如果是super_admin且没有租户，设置为"所有租户"模式
             if (userData.tenant_role === 'super_admin') {
               currentTenant.value = {
                 tenant_id: 'all_tenants',
                 tenant_name: '所有租户',
                 role: 'super_admin'
               }
             } else {
               currentTenant.value = null
             }
           } else {
             hasNoTenants.value = false
             currentTenant.value = tenants[0]
           }
        } catch (tenantError) {
          console.error('Failed to fetch tenants during login:', tenantError)
          tenantApiError.value = tenantError.message || '获取租户列表失败'
          availableTenants.value = []
          hasNoTenants.value = true
          currentTenant.value = null
        }
      }
      
      // 存储到localStorage
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('user_info', JSON.stringify(userData))
      if (currentTenant.value) {
        localStorage.setItem('current_tenant', JSON.stringify(currentTenant.value))
      }
      
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
    hasNoTenants.value = false
    tenantApiError.value = null
    isRetryingTenantApi.value = false
    
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
        // 检查是否有关联租户
        hasNoTenants.value = !user.value.tenants || user.value.tenants.length === 0
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

  // 重新获取租户列表
  const retryFetchTenants = async () => {
    if (isRetryingTenantApi.value) return
    
    try {
      isRetryingTenantApi.value = true
      tenantApiError.value = null
      
      const response = await authRequest.get('/tenants')
      const tenants = response.data?.data || []
      
      // 更新用户信息中的租户列表
      if (user.value) {
        user.value.tenants = tenants
        availableTenants.value = tenants
        
        if (tenants.length === 0) {
           hasNoTenants.value = true
           // 如果是super_admin且没有租户，设置为"所有租户"模式
           if (user.value?.tenant_role === 'super_admin') {
             currentTenant.value = {
               tenant_id: 'all_tenants',
               tenant_name: '所有租户',
               role: 'super_admin'
             }
             localStorage.setItem('current_tenant', JSON.stringify(currentTenant.value))
           } else {
             currentTenant.value = null
           }
         } else {
           hasNoTenants.value = false
           currentTenant.value = tenants[0]
           localStorage.setItem('current_tenant', JSON.stringify(tenants[0]))
         }
        
        localStorage.setItem('user_info', JSON.stringify(user.value))
      }
    } catch (error) {
      console.error('Failed to retry fetch tenants:', error)
      tenantApiError.value = error.message || '获取租户列表失败'
    } finally {
      isRetryingTenantApi.value = false
    }
  }

  // 清除租户API错误
  const clearTenantApiError = () => {
    tenantApiError.value = null
  }

  return {
    // 状态
    user,
    token,
    currentTenant,
    availableTenants,
    hasNoTenants,
    tenantApiError,
    isRetryingTenantApi,
    
    // 计算属性
    isLoggedIn,
    isSuperAdmin,
    tenantRole,
    tenantId,
    shouldShowNoTenantAlert,
    shouldShowTenantApiError,
    
    // 方法
    login,
    logout,
    switchTenant,
    initializeUser,
    getResourceQuotas,
    retryFetchTenants,
    clearTenantApiError
  }
})