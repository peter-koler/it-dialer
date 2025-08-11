import request from '@/utils/request'

// 获取任务列表
export function getTasks(params) {
  return request({
    url: '/tasks',
    method: 'get',
    params
  })
}

// 创建任务
export function createTask(data) {
  return request({
    url: '/tasks',
    method: 'post',
    data
  })
}

// 更新任务
export function updateTask(id, data) {
  return request({
    url: `/tasks/${id}`,
    method: 'put',
    data
  })
}

// 删除任务
export function deleteTask(id) {
  return request({
    url: `/tasks/${id}`,
    method: 'delete'
  })
}

// 获取任务详情
export function getTask(id) {
  return request({
    url: `/tasks/${id}`,
    method: 'get'
  })
}

// 获取任务结果
export function getTaskResults(params) {
  return request({
    url: '/results',
    method: 'get',
    params
  })
}

// 获取单个任务结果
export function getTaskResult(id) {
  return request({
    url: `/results/${id}`,
    method: 'get'
  })
}