// API 模块统一导出
import * as alerts from './alerts'
import * as node from './node'
import * as reports from './reports'
import * as result from './result'
import * as systemVariables from './systemVariables'
import * as task from './task'
import * as tcp from './tcp'
import request from '@/utils/request'

// 审计日志相关 API
export const auditLogs = {
  // 获取审计日志列表
  getAuditLogs(params) {
    return request({
      url: '/v2/audit-logs',
      method: 'get',
      params
    })
  },
  
  // 获取操作类型选项
  getActionOptions() {
    return request({
      url: '/v2/audit-logs/actions',
      method: 'get'
    })
  },
  
  // 获取资源类型选项
  getResourceTypeOptions() {
    return request({
      url: '/v2/audit-logs/resource-types',
      method: 'get'
    })
  },
  
  // 获取用户选项
  getUserOptions() {
    return request({
      url: '/v2/audit-logs/users',
      method: 'get'
    })
  },
  
  // 获取租户选项
  getTenantOptions() {
    return request({
      url: '/v2/audit-logs/tenants',
      method: 'get'
    })
  }
}

// 导出所有 API 模块
export default {
  alerts,
  node,
  reports,
  result,
  systemVariables,
  task,
  tcp,
  auditLogs
}