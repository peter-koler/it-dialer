import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { getTaskResults } from '@/api/task'
import pinyinToChinese from '@/utils/pinyinToChinese.js'

/**
 * 获取探针数据的组合式函数
 * @param {string} taskId - 任务ID
 * @param {object} timeRange - 时间范围 {start, end}
 * @returns {object} 包含数据和操作方法的对象
 */
export function useProbeData(taskId, timeRange) {
  // 响应式数据
  const loading = ref(false)
  const rawData = ref([])
  const groupedResults = ref({})
  const chartData = ref([])
  const tableData = ref([])

  // 获取探针数据
  const fetchProbeData = async () => {
    // 检查 taskId 和 timeRange 是否有效
    if (!taskId.value || !timeRange.value) return

    loading.value = true
    try {
      // 构造请求参数
      const params = {
        task_id: taskId.value
      }
      
      // 如果有时间范围，添加到参数中
      if (timeRange.value.start && timeRange.value.end) {
        params.start = timeRange.value.start
        params.end = timeRange.value.end
      }

      // 调用API获取数据
      const response = await getTaskResults(params)
      
      if (response.data.code === 0) {
        rawData.value = response.data.list || []
        processData()
      } else {
        message.error(response.message || '获取探针数据失败')
      }
    } catch (error) {
      message.error('获取探针数据失败: ' + error.message)
    } finally {
      loading.value = false
    }
  }

  // 处理数据
  const processData = () => {
    // 按agent_area分组，只保留最新的记录
    const grouped = {}
    rawData.value.forEach(item => {
      const agentArea = item.agent_area
      if (agentArea) {
        if (!grouped[agentArea] || new Date(item.created_at) > new Date(grouped[agentArea].created_at)) {
          // 将 agent_area 字段转换为中文地区名称
          const locationName = pinyinToChinese[agentArea] || agentArea || '未知地区'
          
          grouped[agentArea] = {
            ...item,
            location: locationName
          }
        }
      }
    })
    
    groupedResults.value = grouped
    
    // 转换为表格数据
    const resultsArray = Object.values(grouped).map(item => ({
      ...item,
      latestStatus: item.status || '',
      count: item.count || 0,
      avgResponseTime: item.response_time || 0
    }))
    
    tableData.value = resultsArray
    
    // 生成图表数据
    chartData.value = generateChartData(resultsArray)
  }

  // 生成图表数据
  const generateChartData = (results) => {
    if (!results || !Array.isArray(results)) {
      return []
    }
    
    // 统计各地区的拨测点数量
    const regionCountMap = {}
    
    results.forEach(result => {
      // 使用agent_area字段获取地区信息
      const agentArea = result.agent_area
      
      if (agentArea) {
        // 将拼音地区名转换为中文
        const locationName = pinyinToChinese[agentArea] || agentArea
        
        // 统计数量
        if (regionCountMap[locationName]) {
          regionCountMap[locationName]++
        } else {
          regionCountMap[locationName] = 1
        }
      }
    })
    
    // 转换为地图组件需要的格式
    const mapData = Object.keys(regionCountMap).map(regionName => {
      return {
        name: regionName,
        value: regionCountMap[regionName],
        code: regionName // 使用地区名作为code
      }
    })
    
    return mapData
  }

  return {
    loading,
    rawData,
    groupedResults,
    chartData,
    tableData,
    fetchProbeData,
    processData
  }
}