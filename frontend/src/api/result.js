import request from '@/utils/request'
import axios from 'axios'

// 创建专门用于v1 API的请求实例
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

// 获取聚合结果 - 强制使用v1 API
export function getAggregatedResults(taskId, params) {
  return v1Request({
    url: `/tasks/${taskId}/results/aggregated`,
    method: 'get',
    params: params || {}
  })
}

// 获取拨测点详细结果
export function getProbeResult(probeId, params) {
  return request({
    url: `/probes/${probeId}/results`,
    method: 'get',
    params
  })
}

// 获取单次拨测结果
export function getSingleResult(resultId) {
  return request({
    url: `/results/${resultId}`,
    method: 'get'
  })
}

// 获取任务结果列表
export function getTaskResults(params) {
  return request({
    url: '/results',
    method: 'get',
    params
  })
}

// 获取结果详情
export function getResultDetail(resultId) {
  return request({
    url: `/results/${resultId}`,
    method: 'get'
  })
}

// 获取Ping拨测点详细信息
export function getPingProbeDetail(taskId, location, agentArea, params) {
  return v1Request({
    url: `/tasks/${taskId}/ping/probes/${encodeURIComponent(location)}/${encodeURIComponent(agentArea)}/detail`,
    method: 'get',
    params: params || {}
  })
}

// 获取Ping拨测点历史数据趋势
export function getPingProbeHistoryTrend(taskId, location, agentArea, params) {
  return v1Request({
    url: `/tasks/${taskId}/ping/probes/${encodeURIComponent(location)}/${encodeURIComponent(agentArea)}/trend`,
    method: 'get',
    params: params || {}
  })
}

// 获取Ping拨测点详细记录
export function getPingProbeRecords(taskId, location, agentArea, params) {
  return v1Request({
    url: `/tasks/${taskId}/ping/probes/${encodeURIComponent(location)}/${encodeURIComponent(agentArea)}/records`,
    method: 'get',
    params: params || {}
  })
}

// 获取Ping单次记录详情
export function getPingRecordDetail(recordId) {
  return v1Request({
    url: `/ping/records/${recordId}`,
    method: 'get'
  })
}