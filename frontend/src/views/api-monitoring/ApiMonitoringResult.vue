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
    
    <!-- 任务基本信息 -->
    <a-card :bordered="false" class="task-info-card">
      <template #title>
        <div class="task-info-header">
          <span>任务基本信息</span>
          <div class="time-filter-wrapper">
            <div class="quick-time-buttons">
              <a-button 
                size="small" 
                @click="setQuickTime(1, 'hour')"
                :type="isQuickTimeActive(1, 'hour') ? 'primary' : 'default'"
              >
                最近1小时
              </a-button>
              <a-button 
                size="small" 
                @click="setQuickTime(8, 'hour')"
                :type="isQuickTimeActive(8, 'hour') ? 'primary' : 'default'"
              >
                最近8小时
              </a-button>
              <a-button 
                size="small" 
                @click="setQuickTime(1, 'day')"
                :type="isQuickTimeActive(1, 'day') ? 'primary' : 'default'"
              >
                最近1天
              </a-button>
              <a-button 
                size="small" 
                @click="setQuickTime(7, 'day')"
                :type="isQuickTimeActive(7, 'day') ? 'primary' : 'default'"
              >
                最近7天
              </a-button>
            </div>
            <a-range-picker
              v-model:value="timeRange"
              :placeholder="['开始时间', '结束时间']"
              format="YYYY-MM-DD HH:mm:ss"
              show-time
              @change="handleTimeRangeChange"
              class="time-range-picker"
            />
            <a-button 
              type="link" 
              @click="resetTimeFilter"
              :disabled="!timeRange || timeRange.length === 0"
              class="reset-filter-btn"
            >
              重置
            </a-button>
          </div>
        </div>
      </template>
      <a-descriptions :column="{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }" bordered>
        <a-descriptions-item label="任务名称">{{ task.name || '-' }}</a-descriptions-item>
        <a-descriptions-item label="目标URL">{{ task.target || '-' }}</a-descriptions-item>
        <a-descriptions-item label="执行次数">{{ totalExecutions || 0 }}</a-descriptions-item>
        <a-descriptions-item label="平均响应时间">{{ avgResponseTime ? `${avgResponseTime.toFixed(2)} ms` : '-' }}</a-descriptions-item>
        <a-descriptions-item label="任务类型">API拨测</a-descriptions-item>
        <a-descriptions-item label="最新状态">
          <a-tag :color="latestStatus === 'success' ? 'green' : 'red'">
            {{ latestStatus === 'success' ? '成功' : '失败' }}
          </a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </a-card>

    <div class="page-content">
      <a-row :gutter="[16, 16]">
        <a-col :span="24">
          <a-card title="拨测地域分布" :bordered="false">
            <EnhancedChinaMap
              :map-data="mapData"
              :level="mapLevel"
              :selected-code="selectedMapCode"
              height="400px"
              @regionClick="handleRegionClick"
              @update:level="handleLevelChange"
              @update:selectedCode="handleCodeChange"
            />
          </a-card>
        </a-col>
        <a-col :span="24">
          <a-card title="拨测点详情列表" :bordered="false">
            <a-table
              :columns="columns"
              :data-source="agentAggregatedResults"
              :loading="loading"
              row-key="location"
              :pagination="{ pageSize: 10 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'status'">
                  <a-tag :color="record.status === 'success' ? 'green' : 'red'">
                    {{ record.status === 'success' ? '成功' : '失败' }}
                  </a-tag>
                </template>
                <template v-if="column.dataIndex === 'action'">
                  <a-button type="link" @click="showAggregatedProbeDetail(record)">查看详情</a-button>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed, defineEmits } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getTask } from '@/api/task'
import { getAggregatedResults, getProbeResult } from '@/api/result'
import EnhancedChinaMap from '@/components/EnhancedChinaMap/EnhancedChinaMap.vue'
import ApiResultDetailModal from './components/ApiResultDetailModal.vue'

const emit = defineEmits(['update:level', 'update:selectedCode'])

const route = useRoute()
const taskId = route.params.taskId || route.params.id

const task = ref({})
const aggregatedResults = ref([])
const loading = ref(false)
const activeTab = ref('overview')
const isModalOpen = ref(false)
const selectedProbeData = ref({})

// 聚合拨测点详情弹窗相关状态
const aggregatedProbeModalVisible = ref(false)
const selectedProbeGroup = ref([])

// 地图相关状态
const mapLevel = ref('country')
const selectedMapCode = ref('100000')

// 时间筛选相关状态
const timeRange = ref([])
const originalResults = ref([]) // 保存原始数据
const currentQuickTime = ref(null) // 当前选中的快捷时间 { value: 1, unit: 'hour' }

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

  return Object.keys(groupedByLocation).map(location => {
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
})

// 依据拨测结果聚合到地图数据：按地区名称统计拨测点数量
const mapData = computed(() => {
  return agentAggregatedResults.value.map(item => ({
    name: item.location,
    value: item.agentCount,
    successRate: item.successRate
  }))
})

// 聚合拨测点表格列定义
const columns = [
  { title: '拨测点', dataIndex: 'location', key: 'location' },
  { title: '拨测点数量', dataIndex: 'agentCount', key: 'agentCount' },
  { title: '成功率', dataIndex: 'successRate', key: 'successRate', 
    customRender: ({ text }) => `${(text * 100).toFixed(2)}%` },
  { title: '最新状态', dataIndex: 'status', key: 'status' },
  { title: '平均响应时间', dataIndex: 'avgResponseTime', key: 'avgResponseTime',
    customRender: ({ text }) => text ? `${text.toFixed(2)} ms` : '-' },
  { title: '操作', dataIndex: 'action', key: 'action' }
]

// 拨测点表格列定义
const probeColumns = [
  { title: '位置', dataIndex: 'location', key: 'location' },
  { title: '时间', dataIndex: 'created_at', key: 'created_at',
    customRender: ({ text }) => formatDate(text) },
  { title: '响应时间', dataIndex: 'response_time', key: 'response_time',
    customRender: ({ text }) => text ? `${text} ms` : '-' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', dataIndex: 'action', key: 'action' }
]

const fetchTaskDetails = async () => {
  try {
    // 使用axios直接调用tasks接口获取任务基本信息
    const axios = (await import('axios')).default
    const response = await axios.get(`http://localhost:5000/api/v1/tasks/${taskId}`)
    console.log('任务详情响应:', response)
    
    if (response.data && response.data.data) {
      task.value = response.data.data
    } else {
      console.warn('未获取到任务详情数据')
      message.warning('未获取到任务详情数据')
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    message.error('获取任务详情失败: ' + (error.response?.data?.message || error.message || '未知错误'))
  }
}

const fetchResults = async (startTime = null, endTime = null) => {
  loading.value = true
  try {
    // 使用axios直接调用results接口
    const axios = (await import('axios')).default
    const params = {
      task_id: taskId,
      type: 'api',
      page: 1,
      size: 100 // 获取足够多的数据以便聚合
    }
    
    // 如果有时间筛选条件，添加到参数中
     if (startTime && endTime) {
       params.start = startTime
       params.end = endTime
     }
    
    const response = await axios.get(`http://localhost:5000/api/v1/results`, { params })
    console.log('API response:', response)
    
    // 处理响应数据
    if (response.data && response.data.data && Array.isArray(response.data.data.list)) {
      // 提取list数组作为拨测结果
      const results = response.data.data.list.map(item => {
        // 确保每个结果都有必要的字段
        return {
          id: item.id,
          probe_id: item.id, // 使用结果ID作为探针ID
          task_id: item.task_id || taskId,
          agent_id: item.agent_id || (item.task && item.task.agent_ids ? item.task.agent_ids[0] : '未知'),
          location: item.agent_area || '未知位置',
          status: item.status || 'unknown',
          response_time: item.details && item.details.response_time ? item.details.response_time : (item.response_time || 0),
          created_at: item.created_at || new Date().toISOString(),
          details: item.details || {}
        }
      })
      
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
    // 使用axios获取单个探针的详细信息
    const axios = (await import('axios')).default
    const response = await axios.get(`http://localhost:5000/api/v1/results/${record.id}`)
    console.log('API详情响应:', response)
    
    let enriched = { ...record }
    
    if (response.data && response.data.data) {
      const resultData = response.data.data
      
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
    console.log('显示API详情:', enriched);
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

// 设置快捷时间
const setQuickTime = (value, unit) => {
  const now = dayjs()
  let startTime
  
  if (unit === 'hour') {
    startTime = now.subtract(value, 'hour')
  } else if (unit === 'day') {
    startTime = now.subtract(value, 'day')
  }
  
  const endTime = now
  
  // 设置时间范围选择器的值
  timeRange.value = [startTime, endTime]
  
  // 记录当前快捷时间选择
  currentQuickTime.value = { value, unit }
  
  // 执行筛选
  const startTimeStr = startTime.format('YYYY-MM-DDTHH:mm:ss')
  const endTimeStr = endTime.format('YYYY-MM-DDTHH:mm:ss')
  console.log('快捷时间筛选:', startTimeStr, endTimeStr)
  fetchResults(startTimeStr, endTimeStr)
}

// 判断快捷时间按钮是否激活
const isQuickTimeActive = (value, unit) => {
  return currentQuickTime.value && 
         currentQuickTime.value.value === value && 
         currentQuickTime.value.unit === unit
}

// 时间筛选处理
 const handleTimeRangeChange = (dates) => {
   // 清除快捷时间选择状态（因为用户手动选择了时间）
   currentQuickTime.value = null
   
   if (dates && dates.length === 2) {
     const startTime = dates[0].format('YYYY-MM-DDTHH:mm:ss')
     const endTime = dates[1].format('YYYY-MM-DDTHH:mm:ss')
     console.log('时间筛选:', startTime, endTime)
     fetchResults(startTime, endTime)
   } else {
     // 如果清空时间选择，恢复原始数据
     aggregatedResults.value = originalResults.value
   }
 }

// 重置时间筛选
const resetTimeFilter = () => {
  timeRange.value = []
  currentQuickTime.value = null // 清除快捷时间选择状态
  aggregatedResults.value = originalResults.value
  message.success('时间筛选已重置')
}

// 地图事件处理
const handleRegionClick = (payload) => {
  // 可根据点击区域进行筛选或联动，这里先保留占位
  console.log('区域点击:', payload)
  // 可以根据点击的区域筛选拨测点列表
}
const handleLevelChange = (level) => {
  mapLevel.value = level
  emit('update:level', level)
}
const handleCodeChange = (code) => {
  selectedMapCode.value = code
  emit('update:selectedCode', code)
}

onMounted(() => {
  fetchTaskDetails()
  fetchResults()
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

.task-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.time-filter-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.quick-time-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.quick-time-buttons .ant-btn {
  height: 28px;
  padding: 0 12px;
  font-size: 12px;
  border-radius: 4px;
  transition: all 0.2s;
}

.quick-time-buttons .ant-btn:hover {
  border-color: #40a9ff;
  color: #40a9ff;
}

.time-range-picker {
  width: 320px;
}

.reset-filter-btn {
  padding: 0 8px;
  font-size: 12px;
  color: #1890ff;
}

.reset-filter-btn:disabled {
  color: #d9d9d9;
}

@media (max-width: 768px) {
  .time-filter-wrapper {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .time-range-picker {
    width: 100%;
    max-width: 320px;
  }
}
</style>