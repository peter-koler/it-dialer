// API版本选择功能测试文件
import { getApiVersion, getApiBaseUrl } from './request'
import { useUserStore } from '@/stores/user'

/**
 * 测试API版本选择逻辑
 * 这个函数可以在浏览器控制台中调用来验证API版本选择是否正确
 */
export const testApiVersionSelection = () => {
  console.log('=== API版本选择测试 ===')
  
  try {
    const userStore = useUserStore()
    const currentVersion = getApiVersion()
    const currentBaseUrl = getApiBaseUrl()
    
    console.log('当前用户信息:')
    console.log('- 是否为超级管理员:', userStore.isSuperAdmin)
    console.log('- 租户角色:', userStore.tenantRole)
    console.log('- 租户ID:', userStore.tenantId)
    
    console.log('\nAPI版本选择结果:')
    console.log('- 选择的API版本:', currentVersion)
    console.log('- API基础URL:', currentBaseUrl)
    
    console.log('\n说明:')
    console.log('- 所有用户都使用v2 API以确保租户数据隔离')
    console.log('- v2 API会根据用户权限自动过滤数据')
    
  } catch (error) {
    console.error('测试API版本选择时出错:', error)
  }
}

// 在开发环境下将测试函数暴露到全局
if (process.env.NODE_ENV === 'development') {
  window.testApiVersionSelection = testApiVersionSelection
}