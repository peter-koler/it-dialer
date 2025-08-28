import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { getTaskResults } from '@/api/task'
import pinyinToChinese from '@/utils/pinyinToChinese.js'

/**
 * 任务数据管理 composable
 */
export function useTaskData() {
  const route = useRoute()
  const aggregatedResults = ref([])
  const loading = ref(false)
  const pagination = ref({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const searchParams = ref({
    keyword: '',
    status: ''
  })

  // 格式化时间
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN')
  }

  // 格式化详情信息
  const formatDetails = (details) => {
    if (typeof details === 'string') {
      try {
        return JSON.stringify(JSON.parse(details), null, 2)
      } catch (e) {
        return details
      }
    } else {
      return JSON.stringify(details, null, 2)
    }
  }

  // 获取行类名
  const getRowClassName = (record, index) => {
    if (record.status === 'failed') {
      return 'table-row-error'
    } else if (record.status === 'timeout') {
      return 'table-row-warning'
    }
    return ''
  }

  // 获取结果列表并聚合
  const fetchResults = async () => {
    loading.value = true
    try {
      // 使用 useRoute() 获取当前任务的ID
      const taskId = route.params.id
      
      // 通过 /api/v1/results?task_id=${taskId} 接口获取真实的拨测结果数据
      const params = {
        task_id: taskId,
        page: pagination.value.current,
        size: pagination.value.pageSize
      }
      
      const response = await getTaskResults(params)
      
      if (response.data.code === 0) {
        // 只显示每个拨测点的最新记录
        const groupedResults = {}
        response.data.list.forEach(item => {
          // 优先使用item.agent_area，如果没有则尝试使用item.task.agent_ids的第一个元素
          const agentArea = item.agent_area || (item.task && item.task.agent_ids && item.task.agent_ids.length > 0 ? item.task.agent_ids[0] : null)
          if (agentArea) {
            if (!groupedResults[agentArea] || new Date(item.created_at) > new Date(groupedResults[agentArea].created_at)) {
              // 将 agent_area 字段（如 "guangzhou"）转换为中文地区名称（如 "广州市"）
              const locationName = pinyinToChinese[agentArea] || agentArea || '未知地区'
              
              groupedResults[agentArea] = {
                ...item,
                location: locationName
              }
            }
          }
        })
        
        // 转换为数组并进行分页处理
        const allResults = Object.values(groupedResults).map(item => ({
          ...item,
          // 添加聚合字段
          task: item.task || { id: 0, name: '', target: '', type: '' },
          status: item.status || '',
          count: 1, // 每个agent_area只有一条记录
          avgResponseTime: item.response_time || 0,
          latestCreatedAt: formatDate(item.created_at)
        }))
        
        pagination.value.total = allResults.length
        
        // 手动分页
        const start = (pagination.value.current - 1) * pagination.value.pageSize
        const end = start + pagination.value.pageSize
        aggregatedResults.value = allResults.slice(start, end)
      } else {
        message.error(response.data.message || '获取结果列表失败')
      }
    } catch (error) {
      console.error('获取结果列表失败:', error)
      if (error instanceof SyntaxError) {
        message.error('获取结果列表失败: 服务器响应格式错误')
      } else {
        message.error('获取结果列表失败: ' + (error.message || '网络错误'))
      }
    } finally {
      loading.value = false
    }
  }

  // 按任务聚合结果
  const aggregateResults = (results) => {
    const taskMap = new Map()
    
    results.forEach(result => {
      const taskId = result.task.id
      if (!taskMap.has(taskId)) {
        taskMap.set(taskId, {
          task: result.task,
          results: [],
          count: 0,
          avgResponseTime: 0,
          latestStatus: '',
          latestCreatedAt: ''
        })
      }
      
      const taskGroup = taskMap.get(taskId)
      taskGroup.results.push(result)
      taskGroup.count++
      
      // 更新最新状态和时间
      if (!taskGroup.latestCreatedAt || result.created_at > taskGroup.latestCreatedAt) {
        taskGroup.latestStatus = result.status
        taskGroup.latestCreatedAt = result.created_at
      }
    })
    
    // 计算平均响应时间
    taskMap.forEach(taskGroup => {
      const totalResponseTime = taskGroup.results.reduce((sum, result) => {
        // 对于TCP任务，使用execution_time作为响应时间
        if (taskGroup.task.type === 'tcp') {
          try {
            const details = typeof result.details === 'string' 
              ? JSON.parse(result.details) 
              : result.details;
            return sum + (details.execution_time * 1000 || 0); // 转换为毫秒
          } catch (e) {
            return sum + (result.response_time || 0);
          }
        } else {
          return sum + (result.response_time || 0);
        }
      }, 0)
      
      taskGroup.avgResponseTime = taskGroup.count > 0 ? totalResponseTime / taskGroup.count : 0
    })
    
    // 转换为数组并按最新创建时间排序
    return Array.from(taskMap.values()).sort((a, b) => {
      return new Date(b.latestCreatedAt) - new Date(a.latestCreatedAt)
    })
  }

  // 处理搜索
  const handleSearch = () => {
    pagination.value.current = 1
    fetchResults()
  }

  // 处理状态筛选
  const handleStatusChange = () => {
    pagination.value.current = 1
    fetchResults()
  }

  // 处理表格变化
  const handleTableChange = (pager) => {
    pagination.value.current = pager.current
    pagination.value.pageSize = pager.pageSize
    fetchResults()
  }

  return {
    aggregatedResults,
    loading,
    pagination,
    searchParams,
    formatDate,
    formatDetails,
    getRowClassName,
    fetchResults,
    aggregateResults,
    handleSearch,
    handleStatusChange,
    handleTableChange
  }
}