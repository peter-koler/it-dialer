import request from '@/utils/request'

// 获取报表列表
export function getReportList(params) {
  return request({
    url: '/reports',
    method: 'get',
    params
  })
}

// 报表总览（v2）
export function getReportOverview(params) {
  return request({
    url: '/reports/overview',
    method: 'get',
    params
  })
}

// 创建报表
export function createReport(data) {
  return request({
    url: '/reports',
    method: 'post',
    data
  })
}

// 获取报表详情
export function getReportDetail(reportId) {
  return request({
    url: `/reports/${reportId}`,
    method: 'get'
  })
}

// 更新报表
export function updateReport(reportId, data) {
  return request({
    url: `/reports/${reportId}`,
    method: 'put',
    data
  })
}

// 删除报表
export function deleteReport(reportId) {
  return request({
    url: `/reports/${reportId}`,
    method: 'delete'
  })
}

// 生成报表数据
export function generateReport(reportId, data) {
  return request({
    url: `/reports/${reportId}/generate`,
    method: 'post',
    data
  })
}

// 导出报表
export function exportReport(reportId, data) {
  return request({
    url: `/reports/${reportId}/export`,
    method: 'post',
    data,
    responseType: 'blob' // 重要：设置响应类型为blob以处理文件下载
  })
}

// 获取报表类型列表
export function getReportTypes() {
  return request({
    url: '/reports/types',
    method: 'get'
  })
}

// 获取订阅列表
export function getSubscriptionList(params) {
  return request({
    url: '/subscriptions',
    method: 'get',
    params
  })
}

// 创建订阅
export function createSubscription(data) {
  return request({
    url: '/subscriptions',
    method: 'post',
    data
  })
}

// 更新订阅
export function updateSubscription(subscriptionId, data) {
  return request({
    url: `/subscriptions/${subscriptionId}`,
    method: 'put',
    data
  })
}

// 删除订阅
export function deleteSubscription(subscriptionId) {
  return request({
    url: `/subscriptions/${subscriptionId}`,
    method: 'delete'
  })
}

// 切换订阅状态
export function toggleSubscriptionStatus(subscriptionId) {
  return request({
    url: `/subscriptions/${subscriptionId}/toggle`,
    method: 'post'
  })
}

// 获取TCP专项报表数据
export function getTcpReport(params) {
  return request({
    url: '/reports/tcp',
    method: 'get',
    params
  })
}

// 获取HTTP专项报表数据
export function getHttpReport(params) {
  return request({
    url: '/reports/http',
    method: 'get',
    params
  })
}

// 获取API专项报表数据
export function getApiReport(params) {
  return request({
    url: '/reports/api',
    method: 'get',
    params
  })
}

// 获取Ping专项报表数据
export function getPingReport(params) {
  return request({
    url: '/reports/ping',
    method: 'get',
    params
  })
}