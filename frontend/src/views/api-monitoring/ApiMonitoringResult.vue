<template>
  <div class="api-monitoring-result-page">
    <a-card :bordered="false" class="page-header-card">
      <a-page-header :title="task.name || 'API 拨测'" @back="() => $router.back()">
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
    <ApiResultDetailModal
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
            <a-button type="link" @click="showDetails(record)">查看API详情</a-button>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- 快照查看弹窗 -->
    <a-modal
      v-model:open="snapshotModalVisible"
      title="API执行快照"
      width="80%"
      :footer="null"
    >
      <AlertSnapshot 
        v-if="currentSnapshot" 
        :snapshot="currentSnapshot"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, defineEmits, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getTask } from '@/api/task'
import { getAggregatedResults } from '@/api/result'
import TaskInfoPanel from './components/TaskInfoPanel.vue'
import MapListPanel from './components/MapListPanel.vue'
import ChartPanel from './components/ChartPanel.vue'
import AlertPanel from './components/AlertPanel.vue'
import ApiResultDetailModal from './components/ApiResultDetailModal.vue'
import AlertSnapshot from '../alert-management/components/AlertSnapshot.vue'
import * as echarts from 'echarts'
import pinyinToChinese from '@/utils/pinyinToChinese'
import { statisticsByProvince, statisticsByCity, getProvinceByPinyin } from '@/utils/regionStatistics'

const emit = defineEmits(['update:level', 'update:selectedCode'])

const route = useRoute()
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

// 快照查看弹窗相关状态
const snapshotModalVisible = ref(false)
const currentSnapshot = ref(null)

// 组件引用
const alertPanelRef = ref(null)

// 时间筛选相关状态
const timeRange = ref([])
const originalResults = ref([]) // 保存原始数据
const currentQuickTime = ref(null) // 当前选中的快捷时间 { value: 1, unit: 'hour' }

// 时间选择器快捷选项
const timeRangePresets = [
  {
    label: '最近1小时',
    value: () => [dayjs().subtract(1, 'hour'), dayjs()]
  },
  {
    label: '最近24小时',
    value: () => [dayjs().subtract(24, 'hour'), dayjs()]
  }
]

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
      agentCount: agentIds.size || probes.length, // 如果没有agent_id，则使用探针数量
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
   // console.log('mapData: aggregatedResults为空')
    return []
  }
  
  //console.log('mapData: aggregatedResults数据:', aggregatedResults.value.slice(0, 3))
 // console.log('mapData: 广州数据样本:', aggregatedResults.value.filter(item => item.agent_area === 'guangzhou').slice(0, 2))
  
  // 使用地域统计工具按省份统计
  const provinceStats = statisticsByProvince(aggregatedResults.value)
  //console.log('mapData: provinceStats结果:', provinceStats)
  
  // 转换为地图组件需要的格式
  const result = Object.values(provinceStats).map(province => {
    // 转换城市数据，将count字段转换为value字段
    const cities = {}
    Object.keys(province.cities).forEach(cityName => {
      const cityData = province.cities[cityName]
      cities[cityName] = {
        name: cityData.name,
        value: cityData.count, // 将count转换为value
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
  
  //console.log('mapData: 最终地图数据:', result)
  //console.log('mapData: 广东省数据:', result.find(item => item.name === '广东省'))
  //console.log('mapData: 广东省城市数据:', result.find(item => item.name === '广东省').cities)
  return result
})

// 告警数据状态
const alertData = ref([])
const alertsByRegion = computed(() => {
  const regionAlerts = {}
  
  alertData.value.forEach(alert => {
    const province = getProvinceByPinyin(alert.probeName || alert.agent_area)
    const cityName = pinyinToChinese[alert.probeName || alert.agent_area] || alert.probeName || alert.agent_area
    
    // 按省份统计告警
    if (!regionAlerts[province]) {
      regionAlerts[province] = {
        critical: 0,
        warning: 0,
        info: 0
      }
    }
    
    // 按城市统计告警
    if (!regionAlerts[cityName]) {
      regionAlerts[cityName] = {
        critical: 0,
        warning: 0,
        info: 0
      }
    }
    
    if (alert.alertLevel) {
      regionAlerts[province][alert.alertLevel]++
      regionAlerts[cityName][alert.alertLevel]++
    }
  })
  
  return regionAlerts
})

// 获取区域告警级别（最高级别）
const getRegionAlertLevel = (regionName) => {
  const alerts = alertsByRegion.value[regionName]
  if (!alerts) return null
  
  if (alerts.critical > 0) return 'critical'
  if (alerts.warning > 0) return 'warning'
  if (alerts.info > 0) return 'info'
  return null
}

// 拨测点表格列定义
const probeColumns = [
  { title: '位置', dataIndex: 'location', key: 'location',
    customRender: ({ text }) => {
      const chineseName = pinyinToChinese[text] || text;
      return chineseName;
    }
  },
  { title: '时间', dataIndex: 'created_at', key: 'created_at',
    customRender: ({ text }) => formatDate(text) },
  { title: '响应时间', dataIndex: 'response_time', key: 'response_time',
    customRender: ({ text }) => text ? `${text} ms` : '-' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', dataIndex: 'action', key: 'action' }
]

const fetchTaskDetails = async () => {
  try {
    const response = await getTask(taskId)
  //  console.log('任务详情响应:', response)
    
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

// 获取告警数据
const fetchAlerts = async (startTime = null, endTime = null) => {
  try {
    const params = {
      task_id: taskId,
      page: 1,
      size: 1000 // 获取足够多的告警数据
    }
    
    if (startTime && endTime) {
      params.start = startTime
      params.end = endTime
    }
    
    // 使用真实的告警API接口调用
     const { getAlerts } = await import('@/api/alerts')
     const response = await getAlerts(params)
    if (response && response.code === 0) {
      // 过滤当前任务的告警
      const allAlerts = response.alerts || response.list || []
      const taskAlerts = allAlerts.filter(alert => alert.task_id == taskId)
      
      alertData.value = taskAlerts.map(alert => ({
        id: alert.id,
        taskName: alert.taskName || alert.task_name,
        probeName: alert.agent_area || alert.probeName || alert.agent_id,
        agent_area: alert.agent_area || alert.probeName || alert.agent_id,
        alertLevel: alert.alertLevel || alert.alert_level,
        content: alert.content,
        created_at: alert.created_at || alert.triggerTime,
        snapshot: alert.snapshot_data || alert.snapshot
      }))
      
     // console.log('fetchAlerts: 获取到告警数据:', alertData.value)
    } else {
      console.warn('获取告警数据失败:', response?.message)
      alertData.value = []
    }
  } catch (error) {
    console.error('获取告警数据失败:', error)
    alertData.value = []
  }
}

const fetchResults = async (startTime = null, endTime = null) => {
  loading.value = true
  try {
    const params = {
      type: 'api',
      page: 1,
      size: 100 // 获取足够多的数据以便聚合
    }
    
    // 如果有时间筛选条件，添加到参数中
     if (startTime && endTime) {
       params.start = startTime
       params.end = endTime
     }
    
    // 同时获取拨测结果和告警数据
    const [response] = await Promise.all([
      getAggregatedResults(taskId, params),
      fetchAlerts(startTime, endTime)
    ])
    
    // 处理响应数据
    if (response && response.data && Array.isArray(response.data.list)) {
   //   console.log('fetchResults: API响应数据:', response.data)
   //   console.log('fetchResults: 原始数据条数:', response.data.list.length)
    //  console.log('fetchResults: 广州原始数据:', response.data.list.filter(item => item.agent_area === 'guangzhou').length)
      
      // 提取list数组作为拨测结果
      const results = response.data.list.map(item => {
        // 获取原始的agent_area（拼音格式）
        const agentArea = item.agent_area || item.location || '默认位置'
        // 将拼音地区名转换为中文
        const locationName = pinyinToChinese[agentArea] || agentArea
        
        // 确保每个结果都有必要的字段
        return {
          id: item.id,
          probe_id: item.id, // 使用结果ID作为探针ID
          task_id: item.task_id || taskId,
          agent_id: item.agent_id || (item.task && item.task.agent_ids ? item.task.agent_ids[0] : '未知'),
          location: locationName, // 使用转换后的中文地区名
          agent_area: agentArea, // 保留原始的拼音格式用于统计
          status: item.status || 'unknown',
          response_time: item.details && item.details.response_time ? item.details.response_time : (item.response_time || 0),
          created_at: item.created_at || new Date().toISOString(),
          details: item.details || {}
        }
      })
      
    //  console.log('fetchResults: 处理后数据条数:', results.length)
     // console.log('fetchResults: 处理后广州数据:', results.filter(item => item.agent_area === 'guangzhou').length)
     // console.log('fetchResults: 广州数据样本:', results.filter(item => item.agent_area === 'guangzhou').slice(0, 2))
      
      // 如果没有时间筛选，保存为原始数据
      if (!startTime && !endTime) {
        originalResults.value = results
      }
      
      aggregatedResults.value = results
    } else {
      aggregatedResults.value = []
    }
    
    if (aggregatedResults.value.length === 0) {
      message.warning('未找到拨测结果数据')
    }
  } catch (error) {
    console.error('Failed to fetch results:', error)
    message.error('获取拨测结果失败: ' + (error.response?.data?.message || error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const showDetails = async (record) => {
  try {
    // 使用API方法获取单个探针的详细信息
    const { getResultDetail } = await import('@/api/result')
    const response = await getResultDetail(record.id)
    
    let enriched = { ...record }
    
    if (response && response.data) {
      const resultData = response.data
      
      // 处理API详情数据
      const detailsData = resultData.details || {}
      
      enriched = {
        ...record,
        details: {
          total_time: detailsData.response_time || record.response_time || 0,
          message: detailsData.message || '',
          status: detailsData.status || resultData.status || 'unknown',
          steps: [],
          variables: [],
          assertions: {
            total: 0,
            passed: detailsData.status === 'success' ? 1 : 0,
            failed: detailsData.status === 'success' ? 0 : 1
          }
        }
      }
      
      // 如果details中有details嵌套字段，处理其中的步骤数据
      if (detailsData.details && detailsData.details.steps) {
        enriched.details.steps = detailsData.details.steps
      } else {
        // 构建一个基本步骤
        enriched.details.steps = [
          {
            id: '1',
            name: 'API请求',
            method: 'GET',
            url: resultData.task?.config?.url || '',
            status: detailsData.status || resultData.status || 'unknown',
            status_code: detailsData.status === 'success' ? 200 : 0,
            response_time: detailsData.response_time || 0,
            request: {
              headers: {},
              body: '{}'
            },
            response: {
              headers: {},
              body: '{}',
              size: 0
            },
            assertions: [],
            variables: []
          }
        ]
      }
    } else {
      // 如果API没有返回详情数据，使用记录中的基本信息
      console.warn('API未返回详情数据，使用基本信息')
      
      if (!enriched.details || !enriched.details.steps) {
        enriched.details = {
          total_time: record.response_time || 0,
          steps: [
            {
              id: '1',
              name: 'API请求',
              method: 'GET',
              url: '',
              status: record.status || 'unknown',
              status_code: record.status === 'success' ? 200 : 0,
              response_time: record.response_time || 0,
              request: { headers: {}, body: '{}' },
              response: { headers: {}, body: '{}', size: 0 },
              assertions: [],
              variables: []
            }
          ],
          variables: [],
          assertions: {
            total: 0,
            passed: 0,
            failed: 0
          }
        }
      }
    }
    
    selectedProbeData.value = enriched;
    isModalOpen.value = true;
  } catch (error) {
    console.error('获取API详情失败:', error)
    message.error('获取API详情失败: ' + (error.response?.data?.message || error.message || '未知错误'))
    
    // 出错时仍然显示基本信息
    const enriched = {
      ...record,
      details: {
        total_time: record.response_time || 0,
        steps: [
          {
            id: '1',
            name: 'API请求',
            method: 'GET',
            url: '',
            status: record.status || 'unknown',
            status_code: record.status === 'success' ? 200 : 0,
            response_time: record.response_time || 0,
            request: { headers: {}, body: '{}' },
            response: { headers: {}, body: '{}', size: 0 },
            assertions: [],
            variables: []
          }
        ],
        variables: [],
        assertions: {
          total: 0,
          passed: 0,
          failed: 0
        }
      }
    }
    
    selectedProbeData.value = enriched;
    isModalOpen.value = true;
  }
}

// 显示聚合拨测点详情
const showAggregatedProbeDetail = (record) => {
  // 根据位置筛选出该区域的所有拨测点
  selectedProbeGroup.value = aggregatedResults.value.filter(item => item.location === record.location)
  aggregatedProbeModalVisible.value = true
}

// 关闭聚合拨测点详情弹窗
const handleAggregatedModalCancel = () => {
  aggregatedProbeModalVisible.value = false
}



// 时间筛选处理
 const handleTimeRangeChange = (dates) => {
   // 清除快捷时间选择状态（因为用户手动选择了时间）
   currentQuickTime.value = null
   
   if (dates && dates.length === 2) {
     const startTime = dates[0].format('YYYY-MM-DDTHH:mm:ss')
     const endTime = dates[1].format('YYYY-MM-DDTHH:mm:ss')
     
     // 更新时间范围
     timeRange.value = dates
     
     // 获取筛选后的数据
     fetchResults(startTime, endTime)
     
     // 通知AlertPanel更新数据
     if (alertPanelRef.value) {
       alertPanelRef.value.fetchAlerts(startTime, endTime)
     }
   } else {
     // 如果清空时间选择，恢复原始数据
     timeRange.value = []
     aggregatedResults.value = originalResults.value
     
     // 通知AlertPanel重置数据
     if (alertPanelRef.value) {
       alertPanelRef.value.fetchAlerts()
     }
   }
 }

// 重置时间筛选
const resetTimeFilter = () => {
  timeRange.value = []
  currentQuickTime.value = null // 清除快捷时间选择状态
  aggregatedResults.value = originalResults.value
  message.success('时间筛选已重置')
}

// 处理探针点击事件
const handleProbeClick = (probeData) => {
  // 处理探针点击逻辑
}

// 显示探针详情
const showProbeDetail = (record) => {
  showAggregatedProbeDetail(record)
}

onMounted(() => {
  // 设置默认时间范围为最近1小时
  const defaultStartTime = dayjs().subtract(1, 'hour')
  const defaultEndTime = dayjs()
  timeRange.value = [defaultStartTime, defaultEndTime]
  
  fetchTaskDetails()
  // 使用默认时间范围获取数据
  fetchResults(defaultStartTime.format('YYYY-MM-DDTHH:mm:ss'), defaultEndTime.format('YYYY-MM-DDTHH:mm:ss'))
})
</script>

<style scoped>
.api-monitoring-result-page {
  background-color: #f0f2f5;
}
.page-header-card {
  margin-bottom: 16px;
}
.page-content {
  padding: 0 24px 24px;
}
</style>