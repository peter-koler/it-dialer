import request from '@/utils/request'

/**
 * 获取告警列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getAlerts(params) {
  return request({
    url: '/alerts',
    method: 'get',
    params
  })
}

/**
 * 获取告警详情
 * @param {string|number} id - 告警ID
 * @returns {Promise}
 */
export function getAlertDetail(id) {
  return request({
    url: `/alerts/${id}`,
    method: 'get'
  })
}

/**
 * 创建告警
 * @param {Object} data - 告警数据
 * @returns {Promise}
 */
export function createAlert(data) {
  return request({
    url: '/alerts',
    method: 'post',
    data
  })
}

/**
 * 更新告警状态
 * @param {string|number|Array} id - 告警ID或ID数组
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export function updateAlertStatus(id, data) {
  const url = Array.isArray(id) ? '/alerts/batch/status' : `/alerts/${id}/status`
  const requestData = Array.isArray(id) ? { alert_ids: id, ...data } : data
  
  return request({
    url,
    method: 'put',
    data: requestData
  })
}

/**
 * 删除告警
 * @param {Array} ids - 告警ID数组
 * @returns {Promise}
 */
export function deleteAlerts(ids) {
  return request({
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