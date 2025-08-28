import request from '@/utils/request'
import axios from 'axios'

// 创建专门用于v1 API的请求实例（用于告警的增删改查详情操作）
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

/**
 * 获取告警列表 - 使用v2 API（支持租户隔离）
 * @param {Object} params - 查询参数
 * @param {string} customUrl - 自定义API端点
 * @returns {Promise}
 */
export function getAlerts(params, customUrl = '/alerts') {
  return request({
    url: customUrl,
    method: 'get',
    params
  })
}

/**
 * 获取告警详情 - 使用v1 API
 * @param {string|number} id - 告警ID
 * @returns {Promise}
 */
export function getAlertDetail(id) {
  return v1Request({
    url: `/alerts/${id}`,
    method: 'get'
  })
}

/**
 * 创建告警 - 使用v1 API
 * @param {Object} data - 告警数据
 * @returns {Promise}
 */
export function createAlert(data) {
  return v1Request({
    url: '/alerts',
    method: 'post',
    data
  })
}

/**
 * 更新告警状态 - 使用v1 API
 * @param {string|number|Array} id - 告警ID或ID数组
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export function updateAlertStatus(id, data) {
  const url = Array.isArray(id) ? '/alerts/batch/status' : `/alerts/${id}/status`
  const requestData = Array.isArray(id) ? { alert_ids: id, ...data } : data
  
  return v1Request({
    url,
    method: 'put',
    data: requestData
  })
}

/**
 * 删除告警 - 使用v1 API
 * @param {Array} ids - 告警ID数组
 * @returns {Promise}
 */
export function deleteAlerts(ids) {
  return v1Request({
    url: '/alerts/batch',
    method: 'delete',
    data: { alert_ids: ids }
  })
}

/**
 * 获取告警统计信息
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getAlertStats(params) {
  return request({
    url: '/alerts/stats',
    method: 'get',
    params
  })
}

/**
 * 获取告警配置
 * @param {string|number} taskId - 任务ID
 * @returns {Promise}
 */
export function getAlertConfig(taskId) {
  return request({
    url: `/tasks/${taskId}/alert-config`,
    method: 'get'
  })
}

/**
 * 更新告警配置
 * @param {string|number} taskId - 任务ID
 * @param {Object} data - 配置数据
 * @returns {Promise}
 */
export function updateAlertConfig(taskId, data) {
  return request({
    url: `/tasks/${taskId}/alert-config`,
    method: 'put',
    data
  })
}