import { ref, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { getTaskResults } from '@/api/task'
import pinyinToChinese from '@/utils/pinyinToChinese.js'

/**
 * 模态框管理 composable
 */
export function useModals() {
  const route = useRoute()
  const detailModalVisible = ref(false)
  const probeDetailVisible = ref(false)
  const selectedTask = ref(null)
  const selectedProbe = ref(null)
  const probeDetails = ref({}) // 存储每个拨测点的详细数据

  // 显示详情
  const showDetails = async (record, { generateMapData, resetMapState, renderLatencyChart, renderTcpCharts, chinaMapRef, mapData }) => {
    selectedTask.value = record
    detailModalVisible.value = true
    
    // 重置地图状态
    resetMapState()
    
    // 生成地图数据
    const newMapData = generateMapData(record.results)
    mapData.value = newMapData
    console.log('Map data set:', newMapData) // 调试用
    
    // 等待DOM更新后渲染图表和地图
    await nextTick()
    console.log('DOM updated, mapData:', mapData.value) // 调试用
    
    // 重新初始化地图
    if (chinaMapRef.value) {
      await chinaMapRef.value.initMap()
    }
    
    if (record.task.type === 'ping') {
      renderLatencyChart(record.results)
    } else if (record.task.type === 'tcp') {
      renderTcpCharts(record.results)
    }
  }

  // 显示拨测点详情
  const showProbeDetail = async (record, { renderProbeDetailChart }) => {
    selectedProbe.value = record
    probeDetailVisible.value = true
    
    // 获取该拨测点的所有记录
    try {
      const taskId = route.params.id
      const params = {
        task_id: taskId,
        agent_area: record.agent_area,
        page: 1,
        size: 1000,
        sort: 'created_at',
        order: 'desc'
      }
      
      const result = await getTaskResults(params)
      
      if (result.code === 0) {
        probeDetails.value[record.agent_area] = result.data.list.map(item => {
          // 获取地区中文名称
          const locationName = pinyinToChinese[item.agent_area] || item.agent_area || '未知地区'
          
          return {
            ...item,
            location: locationName
          }
        })
      }
    } catch (error) {
      console.error('获取拨测点详细数据失败:', error)
    }
    
    // 等待DOM更新后渲染图表
    nextTick(() => {
      renderProbeDetailChart(record, selectedTask.value)
    })
  }

  // 处理详情模态框取消
  const handleDetailModalCancel = ({ resetMapState }) => {
    detailModalVisible.value = false
    selectedTask.value = null
    resetMapState()
  }

  // 处理拨测点详情弹窗关闭
  const handleProbeDetailCancel = () => {
    probeDetailVisible.value = false
    selectedProbe.value = null
  }

  return {
    detailModalVisible,
    probeDetailVisible,
    selectedTask,
    selectedProbe,
    probeDetails,
    showDetails,
    showProbeDetail,
    handleDetailModalCancel,
    handleProbeDetailCancel
  }
}