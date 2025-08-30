<template>
  <div class="tcp-monitoring-result-page">
    <!-- 页面头部 -->
    <a-card :bordered="false" class="page-header-card">
      <a-page-header :title="task.name || 'TCP 拨测'" @back="() => $router.back()">
        <template #extra>
          <a-tag :color="task.status === 'active' ? 'green' : 'red'">
            {{ task.status === 'active' ? '运行中' : '已停止' }}
          </a-tag>
        </template>
        <template #footer>
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="overview" tab="总览"></a-tab-pane>
          </a-tabs>
        </template>
      </a-page-header>
    </a-card>
    
    <!-- 任务基本信息面板 -->
    <TaskInfoPanel
      :task="task"
      :total-executions="totalExecutions"
      :avg-response-time="avgResponseTime"
      :latest-status="latestStatus"
      v-model:time-range="timeRange"
      v-model:current-quick-time="currentQuickTime"
      @time-range-change="handleTimeRangeChange"
      @reset-time-filter="resetTimeFilter"
    />

    <div class="page-content">
      <!-- 地图和列表面板 -->
      <MapListPanel
        :data="agentAggregatedResults"
        :mapData="mapData"
        :alertsByRegion="alertsByRegion"
        :getRegionAlertLevel="getRegionAlertLevel"
        :level="level"
        :selectedCode="selectedCode"
        @update:level="level = $event"
        @update:selectedCode="selectedCode = $event"
        @probe-click="handleProbeClick"
        @show-probe-detail="showProbeDetail"
        @showDetails="showDetails"
        @goToProbeDetail="goToProbeDetail"
      />
      
      <!-- 图表面板 -->
      <ChartPanel
        :agent-aggregated-results="agentAggregatedResults"
      />
      
      <!-- 告警面板 -->
      <AlertPanel
        :task-id="taskId"
        :time-range="timeRange"
        ref="alertPanelRef"
      />
    </div>
    
    <!-- 单次拨测结果弹窗 -->
    <TcpResultDetailModal
      v-model:open="isModalOpen"
      :probe-data="selectedProbeData"
    />
    
    <!-- 聚合拨测点详情弹窗 -->
    <a-modal
      v-model:open="aggregatedProbeModalVisible"
      title="拨测点详情"
      width="70%"
      :footer="null"
      @cancel="handleAggregatedModalCancel"
    >
      <a-table
        :dataSource="selectedProbeGroup"
        :columns="probeColumns"
        :pagination="{ pageSize: 5 }"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'status'">
            <a-tag :color="record.status === 'success' ? 'green' : 'red'">
              {{ record.status === 'success' ? '成功' : '失败' }}
            </a-tag>
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <a-space>
              <a-button type="link" @click="showDetails(record)">查看TCP详情</a-button>
              <a-button type="link" @click="goToProbeDetail(record)">查看拨测点详情</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-modal>
    
    <!-- 快照查看弹窗 -->
    <a-modal
      v-model:open="snapshotModalVisible"
      title="TCP拨测快照详情"
      width="1000px"
      :footer="null"
    >
      <div v-if="currentSnapshot">
        <!-- 基本信息 -->
        <a-card size="small" title="基本信息" class="mb-16">
          <a-descriptions :column="3" size="small">
            <a-descriptions-item label="任务名称">
              {{ currentSnapshot.task_name }}
            </a-descriptions-item>
            <a-descriptions-item label="任务类型">
              <a-tag color="blue">TCP</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="告警级别">
              <a-tag :color="getAlertLevelColor(currentSnapshot.alertLevel)">
                {{ getAlertLevelText(currentSnapshot.alertLevel) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="拨测点">
              {{ currentSnapshot.probeName || 'N/A' }}
            </a-descriptions-item>
            <a-descriptions-item label="触发时间">
              {{ formatDate(currentSnapshot.created_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="告警状态">
              <a-tag color="orange">待处理</a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
        
        <!-- 快照详情 -->
        <SnapshotViewer 
          task-type="tcp" 
          :snapshot-data="getSnapshotData(currentSnapshot)"
        />
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, defineEmits, nextTick, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getTask } from '@/api/task'
import { getAggregatedResults } from '@/api/result'

import MapListPanel from './components/MapListPanel.vue'
import TcpResultDetailModal from './components/TcpResultDetailModal.vue'
import TaskInfoPanel from './components/TaskInfoPanel.vue'
import ChartPanel from './components/ChartPanel.vue'
import AlertPanel from './components/AlertPanel.vue'
import SnapshotViewer from '@/components/SnapshotViewer.vue'

import pinyinToChinese from '@/utils/pinyinToChinese'
import { statisticsByProvince, statisticsByCity, getProvinceByPinyin } from '@/utils/regionStatistics'

const components = {
  MapListPanel,
  TcpResultDetailModal,
  TaskInfoPanel,
  ChartPanel,
  AlertPanel,
  SnapshotViewer
}

const emit = defineEmits(['update:level', 'update:selectedCode'])

const route = useRoute()
const router = useRouter()
const taskId = route.params.id || route.params.taskId

const task = ref({})
const aggregatedResults = ref([])
const loading = ref(false)
const activeTab = ref('overview')
const isModalOpen = ref(false)
const selectedProbeData = ref({})

// 聚合拨测点详情弹窗相关状态
const aggregatedProbeModalVisible = ref(false)
const selectedProbeGroup = ref([])



// 时间筛选相关状态
const timeRange = ref([])
const originalResults = ref([]) // 保存原始数据
const currentQuickTime = ref(null) // 当前选中的快捷时间 { value: 1, unit: 'hour' }

// 地图相关状态
const level = ref('province')
const selectedCode = ref('')



// 计算属性：总执行次数
const totalExecutions = computed(() => aggregatedResults.value.length)

// 计算属性：平均响应时间
const avgResponseTime = computed(() => {
  const validTimes = aggregatedResults.value
    .map(item => item.response_time)
    .filter(time => time !== undefined && time !== null && time > 0)
  
  if (validTimes.length === 0) return 0
  return validTimes.reduce((sum, time) => sum + time, 0) / validTimes.length
})

// 计算属性：最新状态
const latestStatus = computed(() => {
  if (aggregatedResults.value.length === 0) return 'unknown'
  return aggregatedResults.value[0].status || 'unknown'
})

// 按Agent ID聚合数据
const agentAggregatedResults = computed(() => {
  const groupedByLocation = aggregatedResults.value.reduce((acc, probe) => {
    if (!acc[probe.location]) {
      acc[probe.location] = []
    }
    acc[probe.location].push(probe)
    return acc
  }, {})

  const result = Object.keys(groupedByLocation).map(location => {
    const probes = groupedByLocation[location]
    const successCount = probes.filter(p => p.status === 'success').length
    const latestProbe = probes.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
    const agentIds = new Set(probes.map(p => p.agent_id).filter(id => id))
    
    // 计算平均响应时间
    const validTimes = probes
      .map(item => item.response_time)
      .filter(time => time !== undefined && time !== null && time > 0)
    const avgTime = validTimes.length > 0 
      ? validTimes.reduce((sum, time) => sum + time, 0) / validTimes.length 
      : 0

    return {
      location,
      agentCount: agentIds.size || probes.length,
      successRate: probes.length > 0 ? successCount / probes.length : 0,
      status: latestProbe.status,
      avgResponseTime: avgTime,
      probes,
    }
  })
  
  return result
})

// 地图数据 - 按省份统计拨测点
const mapData = computed(() => {
  if (!aggregatedResults.value.length) {
    return []
  }
  
  // 使用地域统计工具按省份统计
  const provinceStats = statisticsByProvince(aggregatedResults.value)
  
  // 转换为地图组件需要的格式
  const result = Object.values(provinceStats).map(province => {
    // 转换城市数据，将count字段转换为value字段
    const cities = {}
    Object.keys(province.cities).forEach(cityName => {
      const cityData = province.cities[cityName]
      cities[cityName] = {
        name: cityData.name,
        value: cityData.count,
        count: cityData.count,
        probes: cityData.probes
      }
    })
    
    return {
      name: province.name,
      value: province.count,
      probes: province.probes,
      cities: cities
    }
  })
  
  return result
})



const alertsByRegion = computed(() => {
  // 告警数据现在由AlertPanel组件处理
  return {}
})

// 获取区域告警级别
const getRegionAlertLevel = (regionName) => {
  // 告警级别现在由AlertPanel组件处理
  return 'none'
}



// 拨测点表格列定义
const probeColumns = [
  {
    title: '拨测点',
    dataIndex: 'location',
    key: 'location'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status'
  },
  {
    title: '响应时间',
    dataIndex: 'response_time',
    key: 'response_time',
    customRender: ({ text }) => text ? `${text} ms` : '-'
  },
  {
    title: '执行时间',
    dataIndex: 'created_at',
    key: 'created_at',
    customRender: ({ text }) => formatDate(text)
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'action'
  }
]

// 时间筛选相关方法
const setQuickTime = (value, unit) => {
  const now = dayjs()
  let startTime
  
  if (unit === 'hour') {
    startTime = now.subtract(value, 'hour')
  } else if (unit === 'day') {
    startTime = now.subtract(value, 'day')
  }
  
  timeRange.value = [startTime, now]
  currentQuickTime.value = { value, unit }
  handleTimeRangeChange([startTime, now])
}

const isQuickTimeActive = (value, unit) => {
  return currentQuickTime.value && 
         currentQuickTime.value.value === value && 
         currentQuickTime.value.unit === unit
}

const handleTimeRangeChange = (dates) => {
  if (!dates || dates.length === 0) {
    // 重置为原始数据
    aggregatedResults.value = [...originalResults.value]
    return
  }
  
  const [startTime, endTime] = dates
  const startTimestamp = startTime.valueOf()
  const endTimestamp = endTime.valueOf()
  
  // 筛选数据
  aggregatedResults.value = originalResults.value.filter(item => {
    const itemTime = dayjs(item.created_at).valueOf()
    return itemTime >= startTimestamp && itemTime <= endTimestamp
  })
  
  // 重新获取告警数据
  fetchAlerts(startTime.format('YYYY-MM-DD HH:mm:ss'), endTime.format('YYYY-MM-DD HH:mm:ss'))
  
  // 更新图表
  updateChart()
}

const resetTimeFilter = () => {
  timeRange.value = []
  currentQuickTime.value = null
  aggregatedResults.value = [...originalResults.value]
}



// 获取任务详情
const fetchTaskDetails = async () => {
  try {
    const response = await getTask(taskId)
    
    if (response && response.code === 0) {
      task.value = response.data
    } else {
      console.warn('未获取到任务详情数据')
      message.warning('未获取到任务详情数据')
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    message.error('获取任务详情失败: ' + (error.response?.data?.message || error.message || '未知错误'))
  }
}

// 获取拨测结果
const fetchResults = async (startTime = null, endTime = null) => {
  loading.value = true
  try {
    const params = {
      type: 'tcp',
      page: 1,
      size: 100
    }
    
    // 如果有时间筛选条件，添加到参数中
    if (startTime && endTime) {
      params.start = startTime
      params.end = endTime
    }
    
    // 获取拨测结果
    const response = await getAggregatedResults(taskId, params)
    
    // 处理响应数据
    if (response && response.data && Array.isArray(response.data.list)) {
      // 提取list数组作为拨测结果
      const results = response.data.list.map(item => {
        return {
          ...item,
          id: item.id || Math.random().toString(36).substr(2, 9),
          location: item.agent_area || item.location || 'Unknown',
          status: item.status || 'unknown',
          response_time: item.response_time || item.execution_time || 0,
          created_at: item.created_at || new Date().toISOString()
        }
      })
      
      aggregatedResults.value = results
      originalResults.value = [...results] // 保存原始数据
      

    } else {
      console.warn('未获取到拨测结果数据')
      aggregatedResults.value = []
      originalResults.value = []
    }
  } catch (error) {
    console.error('获取拨测结果失败:', error)
    message.error('获取拨测结果失败: ' + (error.response?.data?.message || error.message || '未知错误'))
    aggregatedResults.value = []
    originalResults.value = []
  } finally {
    loading.value = false
  }
}



// 事件处理方法
const handleProbeClick = (probe) => {
  selectedProbeData.value = probe
  isModalOpen.value = true
}

const showProbeDetail = (probeGroup) => {
  selectedProbeGroup.value = probeGroup
  aggregatedProbeModalVisible.value = true
}

const showDetails = (record) => {
  selectedProbeData.value = record
  isModalOpen.value = true
}

const goToProbeDetail = (record) => {
  // 跳转到拨测点详情页面
  const agentArea = record.agent_area || record.location || 'unknown'
  const probeName = pinyinToChinese[agentArea] || agentArea
  
  // 确保所有必需参数都有值
  if (!probeName || !agentArea || !taskId) {
    message.error('缺少必要的路由参数，无法跳转到详情页面')
    return
  }
  
  router.push({
    name: 'TcpProbeDetail',
    params: {
      taskId: taskId,
      probeName: probeName,
      agentArea: agentArea
    }
  })
}

const handleAggregatedModalCancel = () => {
  aggregatedProbeModalVisible.value = false
  selectedProbeGroup.value = []
}





// 组件挂载时获取数据
onMounted(async () => {
  if (taskId) {
    await fetchTaskDetails()
    await fetchResults()
  }
})


</script>

<style scoped>
.tcp-monitoring-result-page {
  padding: 0;
  background-color: #f5f5f5;
}

.page-header-card {
  margin-bottom: 16px;
}

.header-extra {
  display: flex;
  align-items: center;
  gap: 16px;
}

.time-filter-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-time-buttons {
  display: flex;
  gap: 4px;
}

.time-range-picker {
  width: 300px;
}

.task-info-card {
  margin-bottom: 16px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chart-card {
  min-height: 400px;
}

.tcp-chart {
  width: 100%;
  height: 350px;
}

.alert-card {
  min-height: 300px;
}

.mb-16 {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .header-extra {
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
  }
  
  .time-filter-wrapper {
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
  }
  
  .time-range-picker {
    width: 250px;
  }
}
</style>