import axios from 'axios'

// 需要使用v2 API的路径列表（支持租户隔离的功能）
const V2_API_PATHS = [
  '/tasks'            // 拨测任务列表查询
]

// API版本选择函数
export const getApiVersion = (url = '') => {
  // 监测点相关的路径应该使用v1 API
  const probePatterns = [
    '/tasks/\\d+/ping/probes',
    '/tasks/\\d+/tcp/probes',
    '/tasks/\\d+/http/probes',
    '/tasks/\\d+/api/probes'
  ]
  
  // 检查是否是监测点相关路径
  const isProbeUrl = probePatterns.some(pattern => {
    const regex = new RegExp(pattern)
    return regex.test(url)
  })
  
  // 如果是监测点相关路径，强制使用v1
  if (isProbeUrl) {
    return 'v1'
  }
  
  // 检查URL是否需要使用v2 API
  const needsV2 = V2_API_PATHS.some(path => {
    // 精确匹配或以该路径开头的URL
    return url === path || url.startsWith(path + '/') || url.startsWith(path + '?')
  })
  
  return needsV2 ? 'v2' : 'v1'
}

// 获取API基础URL
export const getApiBaseUrl = (url = '') => {
  const version = getApiVersion(url)
  return `http://localhost:5001/api/${version}`
}

// 创建axios实例
const service = axios.create({
  baseURL: 'http://localhost:5001', // 基础URL，具体API版本在拦截器中动态设置
  timeout: 5000 // 请求超时时间
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 动态更新baseURL以确保使用正确的API版本
    config.baseURL = getApiBaseUrl(config.url)
    
    // 在发送请求之前做些什么
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token
    }
    
    // 添加租户ID到请求头
    const currentTenant = localStorage.getItem('current_tenant')
    if (currentTenant) {
      try {
        const tenant = JSON.parse(currentTenant)
        if (tenant.tenant_id) {
          config.headers['X-Tenant-ID'] = tenant.tenant_id
        }
      } catch (error) {
        console.error('Failed to parse tenant info:', error)
      }
    }
    
    return config
  },
  error => {
    // 对请求错误做些什么
    console.log(error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    const res = response.data
    
    // 如果是blob类型响应（文件下载），直接返回response对象
    if (response.config.responseType === 'blob') {
      return response
    }
    
    // 检查HTTP状态码，2xx范围内的状态码都表示成功
    if (response.status >= 200 && response.status < 300) {
      // 返回response.data而不是整个response对象，这样前端代码可以直接使用
      return res
    } else {
      const errorMessage = res.message || res.error || 'Request failed'
      console.error('API Error:', errorMessage)
      return Promise.reject(new Error(errorMessage))
    }
  },
  error => {
    // 对响应错误做点什么
    let errorMessage = 'Network Error'
    
    if (error.response) {
      // 服务器返回了错误状态码
      const res = error.response.data
      errorMessage = res.message || res.error || `HTTP ${error.response.status} Error`
      
      // 处理401未授权错误
      if (error.response.status === 401) {
        console.log('检测到401未授权错误，开始清理认证信息并跳转到登录页面')
        
        // 清除本地存储的认证信息
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_info')
        localStorage.removeItem('current_tenant')
        
        console.log('认证信息已清除，准备跳转到登录页面')
        
        // 跳转到登录页面
        if (window.location.pathname !== '/login') {
          console.log('当前页面不是登录页面，执行跳转')
          window.location.href = '/login'
        } else {
          console.log('当前已在登录页面，无需跳转')
        }
        
        return Promise.reject(new Error('登录已过期，请重新登录'))
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      errorMessage = 'No response from server'
    } else {
      // 其他错误
      errorMessage = error.message || 'Request failed'
    }
    
    console.error('Response Error:', errorMessage)
    return Promise.reject(new Error(errorMessage))
  }
)

export default service