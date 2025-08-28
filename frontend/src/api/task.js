import request from '@/utils/request'
import axios from 'axios'

// 创建专门用于v1 API的请求实例（用于任务的增删改查详情操作）
const v1Request = axios.create({
  baseURL: 'http://localhost:5001/api/v1',
  timeout: 5000
})

// 为v1请求实例添加拦截器
v1Request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token
    }
    
    const currentTenant = localStorage.getItem('current_tenant')
    if (currentTenant) {
      try {
        const tenant = JSON.parse(currentTenant)
        if (tenant && tenant.id) {
          config.headers['X-Tenant-ID'] = tenant.id
        }
      } catch (error) {
        console.warn('Failed to parse current tenant:', error)
      }
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

v1Request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      console.error('Response Error:', error.response.data)
      return Promise.reject(error.response.data)
    } else if (error.request) {
      console.error('Response Error: No response from server')
      return Promise.reject(new Error('No response from server'))
    } else {
      console.error('Request Error:', error.message)
      return Promise.reject(error)
    }
  }
)

// 获取任务列表 - 使用v2 API（支持租户隔离）
export function getTasks(params) {
  return request({
    url: '/tasks',
    method: 'get',
    params
  })
}

// 创建任务 - 使用v1 API
export function createTask(data) {
  return v1Request({
    url: '/tasks',
    method: 'post',
    data
  })
}

// 更新任务 - 使用v1 API
export function updateTask(id, data) {
  return v1Request({
    url: `/tasks/${id}`,
    method: 'put',
    data
  })
}

// 删除任务 - 使用v1 API
export function deleteTask(id) {
  return v1Request({
    url: `/tasks/${id}`,
    method: 'delete'
  })
}

// 获取任务详情 - 使用v1 API
export function getTask(id) {
  return v1Request({
    url: `/tasks/${id}`,
    method: 'get'
  })
}

// 获取任务结果列表 - 使用v2 API（支持租户隔离）
export function getTaskResults(params) {
  return request({
    url: '/results',
    method: 'get',
    params
  })
}

// 获取单个任务结果详情 - 使用v1 API
export function getTaskResult(id) {
  return v1Request({
    url: `/results/${id}`,
    method: 'get'
  })
}