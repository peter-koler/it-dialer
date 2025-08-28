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

/**
 * 获取TCP任务列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getTcpTasks(params) {
  return request({
    url: '/tasks',
    method: 'get',
    params: {
      ...params,
      type: 'tcp'
    }
  })
}

/**
 * 创建TCP任务
 * @param {Object} data - 任务数据
 * @returns {Promise}
 */
export function createTcpTask(data) {
  return request({
    url: '/tasks',
    method: 'post',
    data: {
      ...data,
      type: 'tcp'
    }
  })
}

/**
 * 更新TCP任务
 * @param {string|number} id - 任务ID
 * @param {Object} data - 任务数据
 * @returns {Promise}
 */
export function updateTcpTask(id, data) {
  return request({
    url: `/tasks/${id}`,
    method: 'put',
    data
  })
}

/**
 * 获取TCP任务详情
 * @param {string|number} id - 任务ID
 * @returns {Promise}
 */
export function getTcpTask(id) {
  return request({
    url: `/tasks/${id}`,
    method: 'get'
  })
}

/**
 * 获取TCP任务结果
 * @param {string|number} taskId - 任务ID
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getTcpTaskResults(taskId, params) {
  return request({
    url: `/tasks/${taskId}/results`,
    method: 'get',
    params
  })
}

/**
 * 获取TCP任务聚合结果
 * @param {string|number} taskId - 任务ID
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getTcpAggregatedResults(taskId, params) {
  return v1Request({
    url: `/tasks/${taskId}/results/aggregated`,
    method: 'get',
    params: params || {}
  })
}

/**
 * 获取TCP任务告警配置
 * @param {string|number} taskId - 任务ID
 * @returns {Promise}
 */
export function getTcpAlertConfig(taskId) {
  return request({
    url: `/tasks/${taskId}/alert-config`,
    method: 'get'
  })
}

/**
 * 更新TCP任务告警配置
 * @param {string|number} taskId - 任务ID
 * @param {Object} data - 配置数据
 * @returns {Promise}
 */
export function updateTcpAlertConfig(taskId, data) {
  return request({
    url: `/tasks/${taskId}/alert-config`,
    method: 'put',
    data
  })
}

/**
 * 获取TCP任务告警列表
 * @param {string|number} taskId - 任务ID
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getTcpAlerts(taskId, params) {
  return request({
    url: '/alerts',
    method: 'get',
    params: {
      ...params,
      task_id: taskId,
      task_type: 'tcp'
    }
  })
}

/**
 * 获取TCP拨测点结果
 * @param {string|number} taskId - 任务ID
 * @param {string} probeId - 拨测点ID
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getTcpProbeResults(taskId, probeId, params) {
  return request({
    url: `/tasks/${taskId}/probes/${probeId}/results`,
    method: 'get',
    params
  })
}

/**
 * 获取TCP单次拨测结果详情
 * @param {string|number} resultId - 结果ID
 * @returns {Promise}
 */
export function getTcpResultDetail(resultId) {
  return request({
    url: `/results/${resultId}`,
    method: 'get'
  })
}

/**
 * 测试TCP连接
 * @param {Object} data - 测试数据 { host, port, timeout }
 * @returns {Promise}
 */
export function testTcpConnection(data) {
  return request({
    url: '/tcp/test',
    method: 'post',
    data
  })
}

/**
 * 获取TCP任务统计信息
 * @param {string|number} taskId - 任务ID
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getTcpTaskStats(taskId, params) {
  return request({
    url: `/tasks/${taskId}/stats`,
    method: 'get',
    params
  })
}