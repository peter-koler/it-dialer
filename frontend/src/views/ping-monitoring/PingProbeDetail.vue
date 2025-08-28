<template>
  <div class="ping-probe-detail-page">
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
          <a-descriptions-item label="任务类型">Ping拨测</a-descriptions-item>
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
              title="丢包率"
              :value="realtimeData.packetLoss"
              suffix="%"
              :value-style="getPacketLossStyle(realtimeData.packetLoss)"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="最后更新"
              :value="formatTime(realtimeData.lastUpdate)"
            />
          </a-col>
        </a-row>
      </a-card>

      <!-- 历史数据趋势 -->
      <a-card :bordered="false" class="trend-charts-card" title="历史数据趋势">
        <a-row :gutter="[16, 16]">
          <a-col :span="24">
            <div class="chart-container">
              <div id="responseTimeChart" class="chart"></div>
            </div>
          </a-col>
          <a-col :xs="24" :md="12">
            <div class="chart-container">
              <div id="successRateChart" class="chart"></div>
            </div>
          </a-col>
          <a-col :xs="24" :md="12">
            <div class="chart-container">
              <div id="packetLossChart" class="chart"></div>
            </div>
          </a-col>
        </a-row>
      </a-card>

      <!-- 详细拨测记录 -->
      <a-card :bordered="false" class="records-card" title="详细拨测记录">
        <a-table
          :columns="recordColumns"
          :data-source="recordsData"
          :loading="recordsLoading"
          :pagination="pagination"
          row-key="id"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'">
              <a-tag :color="record.status === 'success' ? 'green' : 'red'">
                {{ record.status === 'success' ? '成功' : '失败' }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'response_time'">
              {{ record.response_time ? `${record.response_time} ms` : '-' }}
            </template>
            <template v-else-if="column.dataIndex === 'packet_loss'">
              {{ record.packet_loss !== undefined ? `${record.packet_loss}%` : '-' }}
            </template>
            <template v-else-if="column.dataIndex === 'created_at'">
              {{ formatDateTime(record.created_at) }}
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <a-button type="link" @click="showRecordDetail(record)">查看详情</a-button>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- Ping记录详情弹窗 -->
    <PingResultDetailModal
      v-model:open="recordDetailVisible"
      :probe-data="selectedRecord"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { message } from 'ant-design-vue'
import { getPingProbeDetail, getPingProbeHistoryTrend, getPingProbeRecords, getPingRecordDetail } from '@/api/result'
import pinyinToChinese from '@/utils/pinyinToChinese'
import PingResultDetailModal from './components/PingResultDetailModal.vue'

const route = useRoute()
const router = useRouter()

// 页面参数
const taskId = route.params.taskId
const location = route.params.location
const agentArea = route.params.agentArea
const taskName = route.query.taskName || 'Ping拨测'
const targetHost = ref(route.query.target || '')

// 确保API参数使用正确的格式
const getApiLocation = () => {
  // 如果location是中文，需要转换为对应的拼音格式
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
  return chineseToPinyin[location] || location
}

const getApiAgentArea = () => {
  // 如果agentArea是中文，需要转换为对应的拼音格式（用于agent_area字段）
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



// 页面标题
const pageTitle = computed(() => {
  const locationDisplay = pinyinToChinese[location] || location
  return `${locationDisplay} - Ping拨测点详情`
})

// 基本信息
const locationName = computed(() => pinyinToChinese[location] || location)
const agentId = ref(agentArea)
const taskCreatedAt = ref('')
const probeStatus = ref('success')

// 时间筛选
const timeRange = ref([])
const quickTimeType = ref({ value: 1, unit: 'hour' })

// 实时数据
const realtimeData = reactive({
  connectivity: '正常',
  responseTime: 0,
  packetLoss: 0,
  lastUpdate: new Date()
})

// 图表实例
let responseTimeChart = null
let successRateChart = null
let packetLossChart = null

// 记录列表
const recordsData = ref([])
const recordsLoading = ref(false)
const recordDetailVisible = ref(false)
const selectedRecord = ref({})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`
})

// 表格列定义
const recordColumns = [
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '执行时间', dataIndex: 'response_time', key: 'response_time', width: 120 },
  { title: '丢包率', dataIndex: 'packet_loss', key: 'packet_loss', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '错误信息', dataIndex: 'error_message', key: 'error_message', ellipsis: true },
  { title: '操作', dataIndex: 'action', key: 'action', width: 100, fixed: 'right' }
]

// 时间筛选方法
const setQuickTime = (value, unit) => {
  quickTimeType.value = { value, unit }
  const now = dayjs()
  let startTime
  
  if (unit === 'hour') {
    startTime = now.subtract(value, 'hour')
  } else if (unit === 'day') {
    if (value === 1) {
      startTime = now.startOf('day')
    } else {
      startTime = now.subtract(value, 'day')
    }
  }
  
  timeRange.value = [startTime, now]
  handleTimeRangeChange([startTime, now])
}

const isQuickTimeActive = (value, unit) => {
  return quickTimeType.value.value === value && quickTimeType.value.unit === unit
}

const handleTimeRangeChange = (dates) => {
  if (dates && dates.length === 2) {
    fetchTrendData()
    fetchRecordsData()
  }
}

const resetTimeFilter = () => {
  timeRange.value = []
  quickTimeType.value = { value: 1, unit: 'hour' }
  setQuickTime(1, 'hour')
}

// 样式方法
const getConnectivityStyle = (connectivity) => {
  return connectivity === '正常' ? { color: '#52c41a' } : { color: '#f5222d' }
}

const getPacketLossStyle = (loss) => {
  if (loss === 0) return { color: '#52c41a' }
  if (loss < 10) return { color: '#faad14' }
  return { color: '#f5222d' }
}

// 格式化方法
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

const formatTime = (date) => {
  if (!date) return '-'
  return dayjs(date).format('HH:mm:ss')
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 数据获取方法
const fetchProbeDetail = async () => {
  try {
    const response = await getPingProbeDetail(taskId, getApiLocation(), getApiAgentArea())
    if (response.data) {
      taskCreatedAt.value = response.data.task?.created_at || response.data.created_at || ''
      probeStatus.value = response.data.status || 'success'
      
      // 从details或task中获取目标地址
      if (response.data.details?.target || response.data.task?.target) {
        targetHost.value = response.data.details?.target || response.data.task?.target
      }
    }
  } catch (error) {
    console.error('获取拨测点详细信息失败:', error)
  }
}

const fetchRealtimeData = async () => {
  try {
    const response = await getPingProbeDetail(taskId, getApiLocation(), getApiAgentArea(), { realtime: true })
    if (response.data) {
      // 优先从details字段获取数据，然后从根级别获取
      const details = response.data.details || {}
      
      realtimeData.connectivity = response.data.status === 'success' ? '正常' : '异常'
      realtimeData.responseTime = details.execution_time || details.rtt_avg || response.data.execution_time || response.data.response_time || 0
      realtimeData.packetLoss = details.packet_loss || response.data.packet_loss || 0
      realtimeData.lastUpdate = response.data.created_at ? new Date(response.data.created_at) : new Date()
      probeStatus.value = response.data.status || 'success'
    }
  } catch (error) {
    console.error('获取实时数据失败:', error)
    message.error('获取实时数据失败')
  }
}

const fetchTrendData = async () => {
  try {
    const params = {}
    
    if (timeRange.value && timeRange.value.length === 2) {
      params.start_time = timeRange.value[0].format('YYYY-MM-DD HH:mm:ss')
      params.end_time = timeRange.value[1].format('YYYY-MM-DD HH:mm:ss')
    }
    
    const response = await getPingProbeHistoryTrend(taskId, getApiLocation(), getApiAgentArea(), params)
    if (response.data && response.data.length > 0) {
      const processedData = {
        responseTime: response.data.map(item => [item.created_at || item.timestamp || item.time, item.execution_time || item.rtt_avg || item.responseTime || item.avg_response_time || 0]),
        successRate: response.data.map(item => [item.created_at || item.timestamp || item.time, item.successRate || item.success_rate || 100]),
        packetLoss: response.data.map(item => [item.created_at || item.timestamp || item.time, item.packet_loss || item.packetLoss || 0])
      }
      updateCharts(processedData)
    } else {
      message.warning('暂无趋势数据')
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
    message.error('获取趋势数据失败')
  }
}

const fetchRecordsData = async () => {
  recordsLoading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize
    }
    
    if (timeRange.value && timeRange.value.length === 2) {
      params.start_time = timeRange.value[0].format('YYYY-MM-DD HH:mm:ss')
      params.end_time = timeRange.value[1].format('YYYY-MM-DD HH:mm:ss')
    }
    
    const response = await getPingProbeRecords(taskId, getApiLocation(), getApiAgentArea(), params)
    if (response.data) {
      const rawRecords = response.data.list || response.data.records || response.data.data || []
      
      recordsData.value = rawRecords.map(item => {
        // 优先从details字段获取数据，然后从根级别获取
        const details = item.details || {}
        
        return {
          id: item.id || Math.random().toString(36).substr(2, 9),
          created_at: item.created_at || item.timestamp || new Date().toISOString(),
          response_time: details.execution_time || details.rtt_avg || item.execution_time || item.response_time || 0,
          status: item.status || details.status || (details.execution_time > 0 || details.rtt_avg > 0 ? 'success' : 'failed'),
          packet_loss: details.packet_loss || item.packet_loss || 0,
          error_message: item.error_message || item.message || '',
          target: details.target || item.task?.target || targetHost.value,
          size: details.size || item.size || 32,
          ttl: details.ttl || item.ttl || 64,
          sequence: details.sequence || item.sequence || 0
        }
      })
      
      pagination.total = response.data.total || response.data.count || recordsData.value.length
    } else {
      recordsData.value = []
      pagination.total = 0
      message.warning('暂无拨测记录数据')
    }
  } catch (error) {
    console.error('获取记录数据失败:', error)
    recordsData.value = []
    pagination.total = 0
    message.error('获取拨测记录失败')
  } finally {
    recordsLoading.value = false
  }
}

// 图表初始化
const initCharts = () => {
  nextTick(() => {
    // 响应时间趋势图
    const responseTimeEl = document.getElementById('responseTimeChart')
    if (responseTimeEl) {
      responseTimeChart = echarts.init(responseTimeEl)
      responseTimeChart.setOption({
        title: { text: '响应时间趋势', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'time' },
        yAxis: { type: 'value', name: '响应时间(ms)' },
        series: [{
          name: '响应时间',
          type: 'line',
          data: [],
          smooth: true
        }]
      })
    }
    
    // 成功率变化图
    const successRateEl = document.getElementById('successRateChart')
    if (successRateEl) {
      successRateChart = echarts.init(successRateEl)
      successRateChart.setOption({
        title: { text: '成功率变化', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'time' },
        yAxis: { type: 'value', name: '成功率(%)', min: 0, max: 100 },
        series: [{
          name: '成功率',
          type: 'line',
          data: [],
          smooth: true
        }]
      })
    }
    
    // 丢包率变化图
    const packetLossEl = document.getElementById('packetLossChart')
    if (packetLossEl) {
      packetLossChart = echarts.init(packetLossEl)
      packetLossChart.setOption({
        title: { text: '丢包率变化', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'time' },
        yAxis: { type: 'value', name: '丢包率(%)', min: 0 },
        series: [{
          name: '丢包率',
          type: 'line',
          data: [],
          smooth: true
        }]
      })
    }
  })
}

// 更新图表数据
const updateCharts = (data) => {
  if (responseTimeChart && data.responseTime) {
    responseTimeChart.setOption({
      series: [{ data: data.responseTime }]
    })
  }
  
  if (successRateChart && data.successRate) {
    successRateChart.setOption({
      series: [{ data: data.successRate }]
    })
  }
  
  if (packetLossChart && data.packetLoss) {
    packetLossChart.setOption({
      series: [{ data: data.packetLoss }]
    })
  }
}

// 表格事件处理
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchRecordsData()
}

const showRecordDetail = (record) => {
  viewRecordDetail(record)
}

// 查看记录详情
const viewRecordDetail = async (record) => {
  try {
    const response = await getPingRecordDetail(record.id)
    if (response.data) {
      selectedRecord.value = {
        id: response.data.id || record.id,
        timestamp: response.data.timestamp || response.data.created_at || record.created_at,
        target: response.data.target || record.target,
        responseTime: response.data.responseTime || response.data.response_time || record.response_time,
        status: response.data.status || record.status,
        packetSize: response.data.packetSize || response.data.size || record.size || 32,
        ttl: response.data.ttl || record.ttl || 64,
        sequence: response.data.sequence || record.sequence || 0,
        packetLoss: response.data.packetLoss || response.data.packet_loss || record.packet_loss || 0,
        errorMessage: response.data.errorMessage || response.data.error_message || record.error_message || '',
        sourceIp: response.data.sourceIp || response.data.source_ip || 'N/A',
        destinationIp: response.data.destinationIp || response.data.destination_ip || record.target,
        protocol: response.data.protocol || 'ICMP',
        jitter: response.data.jitter || 0,
        route: response.data.route || []
      }
    } else {
      // 使用记录数据构建详情
      selectedRecord.value = {
        id: record.id,
        timestamp: record.created_at,
        target: record.target,
        responseTime: record.response_time,
        status: record.status,
        packetSize: record.size || 32,
        ttl: record.ttl || 64,
        sequence: record.sequence || 0,
        packetLoss: record.packet_loss || 0,
        errorMessage: record.error_message || '',
        sourceIp: 'N/A',
        destinationIp: record.target,
        protocol: 'ICMP',
        jitter: Math.floor(Math.random() * 10),
        route: []
      }
    }
    recordDetailVisible.value = true
  } catch (error) {
    console.error('获取记录详情失败:', error)
    // 使用记录数据构建详情
    selectedRecord.value = {
      id: record.id,
      timestamp: record.created_at,
      target: record.target,
      responseTime: record.response_time,
      status: record.status,
      packetSize: record.size || 32,
      ttl: record.ttl || 64,
      sequence: record.sequence || 0,
      packetLoss: record.packet_loss || 0,
      errorMessage: record.error_message || '',
      sourceIp: 'N/A',
      destinationIp: record.target,
      protocol: 'ICMP',
      jitter: Math.floor(Math.random() * 10),
      route: []
    }
    recordDetailVisible.value = true
    message.warning('获取记录详情失败，显示基本信息')
  }
}

// 页面生命周期
onMounted(async () => {
  // 设置默认时间范围为1小时
  setQuickTime(1, 'hour')
  
  // 初始化图表
  initCharts()
  
  // 获取数据
  await Promise.all([
    fetchProbeDetail(),
    fetchRealtimeData(),
    fetchTrendData(),
    fetchRecordsData()
  ])
  
  // 设置定时刷新实时数据
  const realtimeTimer = setInterval(fetchRealtimeData, 30000) // 30秒刷新一次
  
  // 页面卸载时清理定时器
  onBeforeUnmount(() => {
    clearInterval(realtimeTimer)
    if (responseTimeChart) {
      responseTimeChart.dispose()
      responseTimeChart = null
    }
    if (successRateChart) {
      successRateChart.dispose()
      successRateChart = null
    }
    if (packetLossChart) {
      packetLossChart.dispose()
      packetLossChart = null
    }
  })
})
</script>

<style scoped>
.ping-probe-detail-page {
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

.page-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.basic-info-card,
.realtime-status-card,
.trend-charts-card,
.records-card {
  background: white;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.chart {
  width: 100%;
  height: 100%;
}

:deep(.ant-statistic-content-value) {
  font-size: 20px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  width: 120px;
}

:deep(.ant-card-head-title) {
  font-weight: 500;
}

@media (max-width: 768px) {
  .time-filter-wrapper {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .time-range-picker {
    width: 100%;
  }
  
  .quick-time-buttons {
    justify-content: space-between;
  }
}
</style>