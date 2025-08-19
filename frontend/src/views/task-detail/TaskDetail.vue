<template>
  <div>
    <a-card title="任务结果列表">
      <!-- 搜索栏 -->
      <SearchBar 
        :search-params="searchParams"
        @search="handleSearch"
        @status-change="handleStatusChange"
      />
      
      <a-table
        :dataSource="aggregatedResults"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        :rowKey="(record) => record.task.id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'status'">
            <!-- 显示任务的最新状态 -->
            <StatusTag :status="record.latestStatus" />
          </template>
          
          <template v-else-if="column.dataIndex === 'latestResult'">
            <!-- 显示最新执行结果 -->
            <StatusTag :status="record.latestStatus" />
          </template>
          
          <template v-else-if="column.dataIndex === 'response_time'">
            <!-- 显示平均响应时间 -->
            <span v-if="record.avgResponseTime">{{ record.avgResponseTime.toFixed(2) }} ms</span>
            <span v-else>-</span>
          </template>
          
          <template v-else-if="column.dataIndex === 'count'">
            {{ record.count }}
          </template>
          
          <!-- 在TaskDetailModal中添加ProbeList组件的引用 -->
          <template v-else-if="column.dataIndex === 'details'">
            <a-button type="link" size="small" @click="showDetails(record)">查看详情</a-button>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 详情模态框 -->
    <TaskDetailModal 
      v-model:open="detailModalVisible"
      :selected-task="selectedTask"
      :map-data="mapData"
      :map-level="mapLevel"
      :selected-map-code="selectedMapCode"
      @cancel="handleDetailModalCancel"
      @region-click="handleRegionClick"
      @level-change="handleLevelChange"
      @show-probe-detail="showProbeDetail"
    />
    
    <!-- 拨测点详情弹窗 -->
    <ProbeDetailModal
      v-model:open="probeDetailVisible"
      :selected-probe="selectedProbe"
      :probe-details="probeDetails"
      @cancel="handleProbeDetailCancel"
    />
    
    <!-- API拨测任务结果弹窗已移除，现在直接跳转到新页面 -->
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getTaskResults } from '@/api/task'
import SearchBar from './SearchBar.vue'
import StatusTag from './StatusTag.vue'
import TaskDetailModal from './TaskDetailModal.vue'
import ProbeDetailModal from './ProbeDetailModal.vue'
// 已移除对旧ApiTaskResultModal的引用
import pinyinToChinese from '@/utils/pinyinToChinese.js'

// 定义变量
const route = useRoute()
const router = useRouter()
const detailModalVisible = ref(false)
const probeDetailVisible = ref(false)
// 已移除apiResultModalVisible引用
const selectedTask = ref(null)
const selectedProbe = ref(null)
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
const probeDetails = ref({}) // 存储每个拨测点的详细数据

// 地图相关数据
const mapData = ref([])
const mapLevel = ref('country')
const selectedMapCode = ref('')

// 表格列定义
const columns = [
  {
    title: '任务ID',
    dataIndex: ['task', 'id'],
    width: 80
  },
  {
    title: '任务名称',
    dataIndex: ['task', 'name']
  },
  {
    title: '任务目标',
    dataIndex: ['task', 'target']
  },
  {
    title: '任务类型',
    dataIndex: ['task', 'type']
  },
  {
    title: '执行状态',
    dataIndex: 'status'
  },
  {
    title: '最新执行结果',
    dataIndex: 'latestResult'
  },
  {
    title: '平均响应时间',
    dataIndex: 'response_time'
  },
  {
    title: '执行次数',
    dataIndex: 'count'
  },
  {
    title: '创建时间',
    dataIndex: 'latestCreatedAt'
  },
  {
    title: '操作',
    dataIndex: 'details',
    width: 100
  }
]

// 格式化时间
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
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
    
    const data = await getTaskResults(params)
    
    if (data.code === 0) {
      // 只显示每个拨测点的最新记录
      const groupedResults = {}
      data.data.list.forEach(item => {
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
      
      // 获取该任务的所有结果数据用于统计
      const allTaskResults = data.data.list
      
      // 转换为数组并进行分页处理
      const allResults = Object.values(groupedResults).map(item => {
        // 计算该地区的执行统计
        const regionResults = allTaskResults.filter(r => r.agent_area === item.agent_area)
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) // 按时间降序排序
        const latestResult = regionResults.length > 0 ? regionResults[0] : item
        
        // 计算该地区的实际执行次数
        const count = regionResults.length
        
        // 获取正确的最新状态 - 从details.status获取
        let correctLatestStatus = '未知';
        if (latestResult && latestResult.details && latestResult.details.status) {
          correctLatestStatus = latestResult.details.status;
        } else if (latestResult && latestResult.status) {
          correctLatestStatus = latestResult.status;
        }
        
        // 计算最近10次拨测结果的平均响应时间
        const recentResults = regionResults.slice(0, 10) // 取最近10次结果
        const responseTimes = recentResults
          .map(r => {
            // 从多层嵌套结构中提取response_time
            let responseTime = r.response_time;
            if (r.details && r.details.response_time !== undefined) {
              responseTime = r.details.response_time;
            }
            if (r.details && r.details.details && r.details.details.response_time !== undefined) {
              responseTime = r.details.details.response_time;
            }
            return responseTime;
          })
          .filter(time => time !== undefined && time !== null && time > 0)
        const avgResponseTime = responseTimes.length > 0 
          ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length 
          : 0
        
        // 获取最新执行结果的详细信息
        let latestResultDetails = null
        if (latestResult && latestResult.details) {
          latestResultDetails = {
            status: correctLatestStatus,
            message: latestResult.details.message || latestResult.message || '',
            responseTime: latestResult.response_time,
            createdAt: formatDate(latestResult.created_at)
          }
        }
        
        return {
          ...item,
          latestStatus: correctLatestStatus,  // 使用正确的最新状态
          count: count,  // 使用实际执行次数
          avgResponseTime: avgResponseTime,  // 使用最近10次平均响应时间
          latestCreatedAt: formatDate(item.created_at),  // 格式化创建时间
          latestResultDetails: latestResultDetails  // 最新执行结果详情
        }
      })
      pagination.value.total = allResults.length
      
      // 手动分页
      const start = (pagination.value.current - 1) * pagination.value.pageSize
      const end = start + pagination.value.pageSize
      aggregatedResults.value = allResults.slice(start, end)
      
      // 如果是查看详情，也需要更新 selectedTask 的 results 数据
      if (selectedTask.value) {
        selectedTask.value.results = allResults
      }
    } else {
      message.error(data.message || '获取结果列表失败')
    }
  } catch (error) {
    message.error('获取结果列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 显示详情
const showDetails = (record) => {
  // 确保使用聚合后的数据
  const detailRecord = {
    ...record,
    results: aggregatedResults.value || []
  }
  selectedTask.value = detailRecord
  
  // 根据任务类型选择不同的详情展示模式
  if (record.task && record.task.type === 'api') {
    // API拨测任务跳转到新的结果展示页面
    router.push(`/api-monitoring/result/${record.task.id}`)
  } else {
    // 其他类型任务使用常规详情展示
    detailModalVisible.value = true
    
    // 重置地图状态
    mapLevel.value = 'country'
    selectedMapCode.value = ''
    mapData.value = generateMapData(aggregatedResults.value)
  }
}

// 生成地图数据
const generateMapData = (results) => {
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

// 处理地图区域点击
const handleRegionClick = (regionInfo) => {
  console.log('点击了区域:', regionInfo)
  // 可以根据点击的区域筛选右侧表格数据
}

// 处理地图层级变化
const handleLevelChange = (levelInfo) => {
  mapLevel.value = levelInfo.level
  selectedMapCode.value = levelInfo.code
  console.log('地图层级变化:', levelInfo)
}

// 确保showProbeDetail函数被正确调用
const showProbeDetail = async (record) => {
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

// 处理详情模态框取消
const handleDetailModalCancel = () => {
  detailModalVisible.value = false
  selectedTask.value = null
  mapLevel.value = 'country'
  selectedMapCode.value = ''
}

// 处理拨测点详情弹窗关闭
const handleProbeDetailCancel = () => {
  probeDetailVisible.value = false
  selectedProbe.value = null
}

// 已移除handleApiResultModalCancel函数

// 组件挂载时获取数据
onMounted(() => {
  fetchResults()
})
</script>