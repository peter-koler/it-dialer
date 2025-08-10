import request from '@/utils/request'

// 获取节点列表
export function getNodeList(params) {
  return request({
    url: '/nodes',
    method: 'get',
    params
  })
}

// 获取节点详情
export function getNodeDetail(id) {
  return request({
    url: `/nodes/${id}`,
    method: 'get'
  })
}

// 更新节点状态
export function updateNodeStatus(data) {
  return request({
    url: '/nodes/status',
    method: 'put',
    data
  })
}

// 删除节点
export function deleteNode(id) {
  return request({
    url: `/nodes/${id}`,
    method: 'delete'
  })
}

// 更新节点信息
export function updateNode(id, data) {
  return request({
    url: `/nodes/${id}`,
    method: 'put',
    data
  })
}