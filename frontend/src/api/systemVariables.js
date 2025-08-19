import request from '@/utils/request'

// 获取系统变量列表
export function getSystemVariables(params) {
  return request({
    url: '/system-variables',
    method: 'get',
    params
  })
}

// 创建系统变量
export function createSystemVariable(data) {
  return request({
    url: '/system-variables',
    method: 'post',
    data
  })
}

// 更新系统变量
export function updateSystemVariable(id, data) {
  return request({
    url: `/system-variables/${id}`,
    method: 'put',
    data
  })
}

// 删除系统变量
export function deleteSystemVariable(id) {
  return request({
    url: `/system-variables/${id}`,
    method: 'delete'
  })
}