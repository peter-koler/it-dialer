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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { getTaskResults } from '@/api/task'
import SearchBar from './SearchBar.vue'
import StatusTag from './StatusTag.vue'
import TaskDetailModal from './TaskDetailModal.vue'
import ProbeDetailModal from './ProbeDetailModal.vue'
import pinyinToChinese from '@/utils/pinyinToChinese.js'

// 定义变量
const route = useRoute()
const detailModalVisible = ref(false)
const probeDetailVisible = ref(false)
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
    title: '最新状态',
    dataIndex: 'status'
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
      
      // 转换为数组并进行分页处理
      const allResults = Object.values(groupedResults).map(item => ({
        ...item,
        latestStatus: item.status || '',  // 添加latestStatus字段
        count: item.count || 0,  // 确保有执行次数
        avgResponseTime: item.response_time || 0,  // 添加avgResponseTime字段
        latestCreatedAt: formatDate(item.created_at)  // 格式化创建时间
      }))
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
  detailModalVisible.value = true
  
  // 重置地图状态
  mapLevel.value = 'country'
  selectedMapCode.value = ''
  mapData.value = generateMapData(aggregatedResults.value)
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

// 组件挂载时获取数据
onMounted(() => {
  fetchResults()
})
</script>