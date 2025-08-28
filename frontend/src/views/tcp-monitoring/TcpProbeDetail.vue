<template>
  <div class="tcp-probe-detail-page">
    <!-- 页面头部 -->
    <a-card :bordered="false" class="page-header-card">
      <a-page-header :title="pageTitle" @back="() => $router.back()">
        <template #extra>
          <div class="header-extra">
            <a-tag :color="probeStatus === 'success' ? 'green' : 'red'">
              {{ probeStatus === 'success' ? '正常' : '异常' }}
            </a-tag>
            <!-- 时间筛选控件 -->
            <div class="time-filter-wrapper">
              <div class="quick-time-buttons">
                <a-button 
                  size="small" 
                  @click="setQuickTime(1, 'hour')"
                  :type="isQuickTimeActive(1, 'hour') ? 'primary' : 'default'"
                >
                  1小时
                </a-button>
                <a-button 
                  size="small" 
                  @click="setQuickTime(8, 'hour')"
                  :type="isQuickTimeActive(8, 'hour') ? 'primary' : 'default'"
                >
                  8小时
                </a-button>
                <a-button 
                  size="small" 
                  @click="setQuickTime(1, 'day')"
                  :type="isQuickTimeActive(1, 'day') ? 'primary' : 'default'"
                >
                  今天
                </a-button>
                <a-button 
                  size="small" 
                  @click="setQuickTime(7, 'day')"
                  :type="isQuickTimeActive(7, 'day') ? 'primary' : 'default'"
                >
                  7天
                </a-button>
              </div>
              <a-range-picker
                v-model:value="timeRange"
                :placeholder="['开始时间', '结束时间']"
                format="YYYY-MM-DD HH:mm:ss"
                show-time
                @change="handleTimeRangeChange"
                class="time-range-picker"
                size="small"
              />
              <a-button 
                type="link" 
                @click="resetTimeFilter"
                :disabled="!timeRange || timeRange.length === 0"
                size="small"
              >
                重置
              </a-button>
            </div>
          </div>
        </template>
      </a-page-header>
    </a-card>

    <div class="page-content">
      <!-- 拨测点基本信息 -->
      <a-card :bordered="false" class="basic-info-card" title="拨测点基本信息">
        <a-descriptions :column="{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }" bordered>
          <a-descriptions-item label="拨测点位置">{{ locationName }}</a-descriptions-item>
          <a-descriptions-item label="Agent ID">{{ agentId }}</a-descriptions-item>
          <a-descriptions-item label="任务名称">{{ taskName }}</a-descriptions-item>
          <a-descriptions-item label="目标地址">{{ targetHost }}</a-descriptions-item>
          <a-descriptions-item label="任务类型">TCP拨测</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatDate(taskCreatedAt) }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- 实时状态监控 -->
      <a-card :bordered="false" class="realtime-status-card" title="实时状态监控">
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="当前连通性"
              :value="realtimeData.connectivity"
              :value-style="getConnectivityStyle(realtimeData.connectivity)"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="响应时间"
              :value="realtimeData.responseTime"
              suffix="ms"
              :precision="2"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="连接状态"
              :value="realtimeData.connectionStatus"
              :value-style="getConnectionStatusStyle(realtimeData.connectionStatus)"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="最后更新"
              :value="formatDate(realtimeData.lastUpdate)"
            />
          </a-col>
        </a-row>
      </a-card>

      <!-- 历史数据趋势 -->
      <a-card :bordered="false" class="trend-chart-card" title="历史数据趋势">
        <div class="chart-container">
          <div ref="trendChart" class="trend-chart"></div>
        </div>
      </a-card>

      <!-- 详细拨测记录 -->
      <a-card :bordered="false" class="records-card" title="详细拨测记录">
        <a-table
          :columns="recordColumns"
          :data-source="recordList"
          :pagination="recordPagination"
          :loading="recordLoading"
          @change="handleRecordTableChange"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.status === 'success' ? 'green' : 'red'">
                {{ record.status === 'success' ? '成功' : '失败' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'response_time'">
              {{ record.response_time ? record.response_time.toFixed(2) : '-' }}ms
            </template>
            <template v-else-if="column.key === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            <template v-else-if="column.key === 'action'">
              <a-button type="link" size="small" @click="viewRecordDetail(record)">
                查看详情
              </a-button>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- 记录详情模态框 -->
    <a-modal
      v-model:open="recordDetailVisible"
      title="拨测记录详情"
      width="800px"
      :footer="null"
      @cancel="closeRecordDetail"
    >
      <a-descriptions :column="2" bordered>
        <a-descriptions-item label="记录ID">{{ selectedRecord.id }}</a-descriptions-item>
        <a-descriptions-item label="拨测时间">{{ formatDate(selectedRecord.created_at) }}</a-descriptions-item>
        <a-descriptions-item label="拨测状态">
          <a-tag :color="selectedRecord.status === 'success' ? 'green' : 'red'">
            {{ selectedRecord.status === 'success' ? '成功' : '失败' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="响应时间">{{ selectedRecord.response_time ? selectedRecord.response_time.toFixed(2) + 'ms' : '-' }}</a-descriptions-item>
        <a-descriptions-item label="Agent区域">{{ selectedRecord.agent_area }}</a-descriptions-item>
        <a-descriptions-item label="Agent ID">{{ selectedRecord.agent_id }}</a-descriptions-item>
        <a-descriptions-item label="目标地址" :span="2">{{ selectedRecord.task?.target }}</a-descriptions-item>
        <a-descriptions-item label="错误信息" :span="2">
          {{ selectedRecord.message || '无' }}
        </a-descriptions-item>
      </a-descriptions>
      
      <a-divider>详细信息</a-divider>
      
      <a-descriptions :column="1" bordered>
        <a-descriptions-item label="连接详情">
          <div v-if="selectedRecord.details">
            <p><strong>主机:</strong> {{ selectedRecord.details.host }}</p>
            <p><strong>端口:</strong> {{ selectedRecord.details.port }}</p>
            <p><strong>连接状态:</strong> {{ selectedRecord.details.connected ? '已连接' : '连接失败' }}</p>
            <p><strong>执行时间:</strong> {{ selectedRecord.details.execution_time ? (selectedRecord.details.execution_time * 1000).toFixed(2) + 'ms' : '-' }}</p>
            <p><strong>返回码:</strong> {{ selectedRecord.details.return_code }}</p>
          </div>
          <span v-else>暂无详细信息</span>
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import pinyinToChinese from '@/utils/pinyinToChinese'
import { getApiBaseUrl } from '@/utils/request'

// 路由参数
const route = useRoute()
const taskId = route.params.taskId
const probeName = route.params.probeName
const agentArea = route.params.agentArea

// 页面数据
const pageTitle = ref('TCP拨测点详情')
const probeStatus = ref('success')
const locationName = ref('')
const agentId = ref('')
const taskName = ref('')
const targetHost = ref('')
const taskCreatedAt = ref('')

// 时间筛选
const timeRange = ref([])
const currentQuickTime = ref({ value: 1, unit: 'hour' })

// 实时数据
const realtimeData = reactive({
  connectivity: '正常',
  responseTime: 0,
  connectionStatus: '已连接',
  lastUpdate: new Date()
})

// 图表实例
const trendChart = ref(null)
let chartInstance = null

// 记录列表
const recordList = ref([])
const recordLoading = ref(false)
const recordPagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`
})

// 表格列定义
const recordColumns = [
  {
    title: '时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 180,
    sorter: true
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 80
  },
  {
    title: '响应时间',
    dataIndex: 'response_time',
    key: 'response_time',
    width: 100,
    sorter: true
  },
  {
    title: '连接状态',
    dataIndex: 'connection_status',
    key: 'connection_status',
    width: 100
  },
  {
    title: '错误信息',
    dataIndex: 'message',
    key: 'message',
    ellipsis: true
  },
  {
    title: '操作',
    key: 'action',
    width: 100
  }
]

// 计算属性
const getApiLocation = () => {
  // 将中文地点转换为拼音格式
  const chineseToPinyin = {
    '广州市': 'guangzhou',
    '广州': 'guangzhou',
    '北京市': 'beijing',
    '北京': 'beijing',
    '上海市': 'shanghai',
    '上海': 'shanghai',
    '深圳市': 'shenzhen',
    '深圳': 'shenzhen'
  }
  return chineseToPinyin[probeName] || probeName
}

const getApiAgentArea = () => {
  // 将中文地点转换为拼音格式
  const chineseToPinyin = {
    '广州市': 'guangzhou',
    '广州': 'guangzhou',
    '北京市': 'beijing',
    '北京': 'beijing',
    '上海市': 'shanghai',
    '上海': 'shanghai',
    '深圳市': 'shenzhen',
    '深圳': 'shenzhen'
  }
  return chineseToPinyin[agentArea] || agentArea
}

// 方法
const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const getConnectivityStyle = (connectivity) => {
  return {
    color: connectivity === '正常' ? '#52c41a' : '#ff4d4f'
  }
}

const getConnectionStatusStyle = (status) => {
  return {
    color: status === '已连接' ? '#52c41a' : '#ff4d4f'
  }
}

const setQuickTime = (value, unit) => {
  currentQuickTime.value = { value, unit }
  const now = dayjs()
  let startTime
  
  if (unit === 'hour') {
    startTime = now.subtract(value, 'hour')
  } else if (unit === 'day') {
    startTime = now.subtract(value, 'day')
  }
  
  timeRange.value = [startTime, now]
  handleTimeRangeChange([startTime, now])
}

const isQuickTimeActive = (value, unit) => {
  return currentQuickTime.value.value === value && currentQuickTime.value.unit === unit
}

const handleTimeRangeChange = (dates) => {
  if (dates && dates.length === 2) {
    fetchTrendData()
    fetchRecordList()
  }
}

const resetTimeFilter = () => {
  timeRange.value = []
  currentQuickTime.value = { value: 1, unit: 'hour' }
  fetchTrendData()
  fetchRecordList()
}

const fetchProbeDetail = async () => {
  try {
    const apiLocation = getApiLocation()
    const apiAgentArea = getApiAgentArea()
    
    const response = await fetch(`${getApiBaseUrl()}/tasks/${taskId}/tcp/probes/${apiLocation}/${apiAgentArea}/detail`)
    const result = await response.json()
    
    if (result.code === 0) {
      const data = result.data
      taskName.value = data.task_name || ''
      targetHost.value = data.target || ''
      taskCreatedAt.value = data.created_at || '暂无数据'
      agentId.value = data.agent_area || ''
      locationName.value = pinyinToChinese[probeName] || probeName
    } else {
      message.error(result.message || '获取拨测点详情失败')
    }
  } catch (error) {
    console.error('获取拨测点详情失败:', error)
    message.error('获取拨测点详情失败')
  }
}

const fetchRealtimeData = async () => {
  try {
    const apiLocation = getApiLocation()
    const apiAgentArea = getApiAgentArea()
    
    const response = await fetch(`${getApiBaseUrl()}/tasks/${taskId}/tcp/probes/${apiLocation}/${apiAgentArea}/detail?realtime=true`)
    const result = await response.json()
    
    if (result.code === 0) {
      const data = result.data
      realtimeData.connectivity = data.status === 'success' ? '正常' : '异常'
      realtimeData.responseTime = data.response_time || 0
      realtimeData.connectionStatus = data.status === 'success' ? '已连接' : '连接失败'
      realtimeData.lastUpdate = data.created_at || new Date()
      probeStatus.value = data.status || 'failed'
    }
  } catch (error) {
    console.error('获取实时数据失败:', error)
  }
}

const fetchTrendData = async () => {
  try {
    const apiLocation = getApiLocation()
    const apiAgentArea = getApiAgentArea()
    
    let url = `${getApiBaseUrl()}/tasks/${taskId}/tcp/probes/${apiLocation}/${apiAgentArea}/trend`
    
    if (timeRange.value && timeRange.value.length === 2) {
      const startTime = timeRange.value[0].toISOString()
      const endTime = timeRange.value[1].toISOString()
      url += `?start_time=${startTime}&end_time=${endTime}`
    }
    
    const response = await fetch(url)
    const result = await response.json()
    
    if (result.code === 0) {
      updateTrendChart(result.data)
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
  }
}

const fetchRecordList = async () => {
  recordLoading.value = true
  try {
    const apiLocation = getApiLocation()
    const apiAgentArea = getApiAgentArea()
    
    let url = `${getApiBaseUrl()}/tasks/${taskId}/tcp/probes/${apiLocation}/${apiAgentArea}/records?page=${recordPagination.current}&page_size=${recordPagination.pageSize}`
    
    if (timeRange.value && timeRange.value.length === 2) {
      const startTime = timeRange.value[0].toISOString()
      const endTime = timeRange.value[1].toISOString()
      url += `&start_time=${startTime}&end_time=${endTime}`
    }
    
    const response = await fetch(url)
    const result = await response.json()
    
    if (result.code === 0) {
      recordList.value = result.data.records || []
      recordPagination.total = result.data.total || 0
    } else {
      message.error(result.message || '获取记录列表失败')
    }
  } catch (error) {
    console.error('获取记录列表失败:', error)
    message.error('获取记录列表失败')
  } finally {
    recordLoading.value = false
  }
}

const updateTrendChart = (data) => {
  if (!chartInstance || !data) return
  
  // 处理API返回的数据结构：{response_time: [...], timestamps: [...]}
  const times = data.timestamps ? data.timestamps.map(timestamp => dayjs(timestamp).format('MM-DD HH:mm')) : []
  const responseTimes = data.response_time || []
  // 对于TCP拨测，假设所有记录都是成功的（因为API只返回成功的记录）
  const successRates = responseTimes.map(() => 100)
  
  const option = {
    title: {
      text: 'TCP拨测趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['响应时间', '成功率'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: times
    },
    yAxis: [
      {
        type: 'value',
        name: '响应时间(ms)',
        position: 'left'
      },
      {
        type: 'value',
        name: '成功率(%)',
        position: 'right',
        max: 100
      }
    ],
    series: [
      {
        name: '响应时间',
        type: 'line',
        data: responseTimes,
        smooth: true,
        itemStyle: {
          color: '#1890ff'
        }
      },
      {
        name: '成功率',
        type: 'line',
        yAxisIndex: 1,
        data: successRates,
        smooth: true,
        itemStyle: {
          color: '#52c41a'
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

const initTrendChart = () => {
  if (trendChart.value) {
    chartInstance = echarts.init(trendChart.value)
    window.addEventListener('resize', () => {
      chartInstance?.resize()
    })
  }
}

const handleRecordTableChange = (pagination, filters, sorter) => {
  recordPagination.current = pagination.current
  recordPagination.pageSize = pagination.pageSize
  fetchRecordList()
}

// 记录详情模态框
const recordDetailVisible = ref(false)
const selectedRecord = ref({})

const viewRecordDetail = (record) => {
  selectedRecord.value = record
  recordDetailVisible.value = true
}

const closeRecordDetail = () => {
  recordDetailVisible.value = false
  selectedRecord.value = {}
}

// 生命周期
onMounted(async () => {
  // 设置默认时间范围为1小时
  setQuickTime(1, 'hour')
  
  // 获取基本信息
  await fetchProbeDetail()
  
  // 获取实时数据
  await fetchRealtimeData()
  
  // 初始化图表
  await nextTick()
  initTrendChart()
  
  // 获取趋势数据
  await fetchTrendData()
  
  // 获取记录列表
  await fetchRecordList()
  
  // 设置定时刷新实时数据
  setInterval(fetchRealtimeData, 30000) // 30秒刷新一次
})
</script>

<style scoped>
.tcp-probe-detail-page {
  padding: 0;
  background-color: #f0f2f5;
  min-height: 100vh;
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

.page-content {
  padding: 0 24px 24px;
}

.basic-info-card,
.realtime-status-card,
.trend-chart-card,
.records-card {
  margin-bottom: 16px;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.trend-chart {
  width: 100%;
  height: 100%;
}

@media (max-width: 768px) {
  .header-extra {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .time-filter-wrapper {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
  
  .time-range-picker {
    width: 100%;
  }
  
  .page-content {
    padding: 0 16px 16px;
  }
}
</style>