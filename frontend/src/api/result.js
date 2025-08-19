import request from '@/utils/request'

// 获取聚合结果
export function getAggregatedResults(taskId, params) {
  return request({
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