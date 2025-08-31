<template>
  <div class="report-overview">
    <a-page-header title="报表总览" sub-title="网络拨测性能总体分析" />
    
    <!-- 时间筛选器 -->
    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="12">
          <a-space>
            <span>时间范围：</span>
            <a-button-group>
              <a-button 
                v-for="item in timeRangeOptions" 
                :key="item.value"
                :type="selectedTimeRange === item.value ? 'primary' : 'default'"
                @click="handleTimeRangeChange(item.value)"
              >
                {{ item.label }}
              </a-button>
            </a-button-group>
          </a-space>
        </a-col>
        <a-col :span="12" style="text-align: right;">
          <a-space>
            <a-button type="primary" :icon="h(SyncOutlined)" @click="refreshData">
              刷新数据
            </a-button>
            <a-button :icon="h(DownloadOutlined)" @click="exportReport">
              导出报表
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- 总体可用性概览 -->
    <a-row :gutter="16" class="overview-cards">
      <a-col :span="6" v-for="item in overviewStats" :key="item.type">
        <a-card :bordered="false" class="stat-card">
          <a-statistic
            :title="item.title"
            :value="item.value"
            :suffix="item.suffix"
            :value-style="{ color: item.color }"
          >
            <template #prefix>
              <component :is="item.icon" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 主要图表区域 -->
    <a-row :gutter="16" class="chart-section">
      <!-- 成功率趋势图 -->
      <a-col :span="12">
        <a-card title="成功率趋势" :bordered="false">
          <div ref="successRateChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
      
      <!-- 成功率分布饼图 -->
      <a-col :span="12">
        <a-card title="任务类型成功率分布" :bordered="false">
          <div ref="successRatePieChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 延迟性能对比 -->
    <a-row :gutter="16" class="chart-section">
      <a-col :span="24">
        <a-card title="延迟性能对比" :bordered="false">
          <a-tabs v-model:activeKey="activePerformanceTab" @change="handlePerformanceTabChange">
            <a-tab-pane key="response-time" tab="平均响应时间">
              <div ref="responseTimeChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="packet-loss" tab="丢包率分析">
              <div ref="packetLossChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="status-code" tab="状态码分布">
              <div ref="statusCodeChart" style="height: 350px;"></div>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>

    <!-- TOP榜单 -->
    <a-row :gutter="16" class="top-section">
      <a-col :span="12">
        <a-card title="可用性TOP10任务" :bordered="false">
          <a-list
            :data-source="topAvailabilityTasks"
            size="small"
          >
            <template #renderItem="{ item, index }">
              <a-list-item class="clickable-list-item" @click="navigateToTaskDetail(item.taskId, item.originalTaskType)">
                <a-list-item-meta>
                  <template #title>
                    <a-space>
                      <a-tag :color="getTopRankColor(index)">{{ index + 1 }}</a-tag>
                      <span class="task-name-link">{{ item.taskName }}</span>
                      <a-tag :color="getTaskTypeColor(item.taskType)">{{ item.taskType }}</a-tag>
                    </a-space>
                  </template>
                  <template #description>
                    {{ item.target }}
                  </template>
                </a-list-item-meta>
                <div class="top-item-value">
                  <a-statistic 
                    :value="item.successRate" 
                    suffix="%" 
                    :precision="2"
                    :value-style="{ fontSize: '14px', color: '#52c41a' }"
                  />
                </div>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      
      <a-col :span="12">
        <a-card title="失败率最高任务" :bordered="false">
          <a-list
            :data-source="topFailureTasks"
            size="small"
          >
            <template #renderItem="{ item, index }">
              <a-list-item class="clickable-list-item" @click="navigateToTaskDetail(item.taskId, item.originalTaskType)">
                <a-list-item-meta>
                  <template #title>
                    <a-space>
                      <a-tag color="red">{{ index + 1 }}</a-tag>
                      <span class="task-name-link">{{ item.taskName }}</span>
                      <a-tag :color="getTaskTypeColor(item.taskType)">{{ item.taskType }}</a-tag>
                    </a-space>
                  </template>
                  <template #description>
                    {{ item.target }}
                  </template>
                </a-list-item-meta>
                <div class="top-item-value">
                  <a-statistic 
                    :value="item.failureRate" 
                    suffix="%" 
                    :precision="2"
                    :value-style="{ fontSize: '14px', color: '#ff4d4f' }"
                  />
                </div>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted, h, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import { useRouter } from 'vue-router'
import {
  SyncOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'
import { getReportOverview } from '@/api/reports'

// 路由实例
const router = useRouter()

// 时间范围选项
const timeRangeOptions = [
  { label: '1小时', value: '1h' },
  { label: '1天', value: '1d' },
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' }
]

const selectedTimeRange = ref('1d')
const activePerformanceTab = ref('response-time')

// 图表引用
const successRateChart = ref(null)
const successRatePieChart = ref(null)
const responseTimeChart = ref(null)
const packetLossChart = ref(null)
const statusCodeChart = ref(null)

// 图表实例
let successRateChartInstance = null
let successRatePieChartInstance = null
let responseTimeChartInstance = null
let packetLossChartInstance = null
let statusCodeChartInstance = null

// 新增：趋势与饼图所需数据
const trendXAxis = ref([])
const typeTrends = ref({ tcp: [], ping: [], http: [], api: [] })
const pieSeriesData = ref([])

// 新增：性能指标数据
const performanceData = ref({
  tcp_connection_time: { min: 0, avg: 0, max: 0, data: [] },
  ping_rtt: { min: 0, avg: 0, max: 0, data: [] },
  http_response_time: { min: 0, avg: 0, max: 0, data: [] },
  api_response_time: { min: 0, avg: 0, max: 0, data: [] },
  ping_packet_loss: { min: 0, avg: 0, max: 0, data: [] }
})

// 总体统计数据
const overviewStats = ref([
  {
    title: 'TCP任务成功率',
    value: 0,
    suffix: '%',
    color: '#52c41a',
    icon: CheckCircleOutlined,
    type: 'tcp'
  },
  {
    title: 'Ping任务成功率',
    value: 0,
    suffix: '%',
    color: '#52c41a',
    icon: CheckCircleOutlined,
    type: 'ping'
  },
  {
    title: 'HTTP任务成功率',
    value: 0,
    suffix: '%',
    color: '#faad14',
    icon: WarningOutlined,
    type: 'http'
  },
  {
    title: 'API任务成功率',
    value: 0,
    suffix: '%',
    color: '#faad14',
    icon: WarningOutlined,
    type: 'api'
  }
])

// TOP榜单数据改为由接口填充
const topAvailabilityTasks = ref([])

const topFailureTasks = ref([])

// 方法
const handleTimeRangeChange = (value) => {
  selectedTimeRange.value = value
  refreshData()
}

const handlePerformanceTabChange = (key) => {
  activePerformanceTab.value = key
  nextTick(() => {
    initPerformanceChart(key)
  })
}

const refreshData = async () => {
  try {
    message.loading('正在刷新数据...', 0.8)
    const res = await getReportOverview({ time_range: selectedTimeRange.value })
    if (res && res.code === 0 && res.data) {
      const data = res.data
      // 1) 任务类型成功率映射
      const rates = { tcp: 0, ping: 0, http: 0, api: 0 }
      ;(data.task_type_stats || []).forEach(item => {
        if (item && item.type in rates) {
          rates[item.type] = item.success_rate || 0
        }
      })
      // 更新四个概览卡片
      overviewStats.value = overviewStats.value.map(s => ({
        ...s,
        value: rates[s.type] ?? 0
      }))

      // 2) 饼图数据
      pieSeriesData.value = [
        { value: rates.tcp, name: 'TCP任务', itemStyle: { color: '#1890ff' } },
        { value: rates.ping, name: 'Ping任务', itemStyle: { color: '#52c41a' } },
        { value: rates.http, name: 'HTTP任务', itemStyle: { color: '#faad14' } },
        { value: rates.api, name: 'API任务', itemStyle: { color: '#722ed1' } }
      ]

      // 3) 成功率趋势（多折线）
      const tTrends = data.type_success_trends || {}
      trendXAxis.value = (tTrends.tcp || []).map(i => i.time)
      typeTrends.value = {
        tcp: (tTrends.tcp || []).map(i => i.success_rate),
        ping: (tTrends.ping || []).map(i => i.success_rate),
        http: (tTrends.http || []).map(i => i.success_rate),
        api: (tTrends.api || []).map(i => i.success_rate)
      }

      // 4) TOP榜单
      const formatType = (t) => ({ tcp: 'TCP', ping: 'Ping', http: 'HTTP', api: 'API' }[t] || t)
      topAvailabilityTasks.value = (data.top_tasks || []).map(r => ({
        taskId: r.task_id,
        taskName: r.task_name,
        taskType: formatType(r.task_type),
        originalTaskType: r.task_type,
        target: r.target,
        successRate: r.success_rate
      }))
      topFailureTasks.value = (data.worst_tasks || []).map(r => ({
        taskId: r.task_id,
        taskName: r.task_name,
        taskType: formatType(r.task_type),
        originalTaskType: r.task_type,
        target: r.target,
        failureRate: r.failure_rate
      }))

      // 5) 性能指标数据 - 适配后端返回的数据结构
      if (data.performance_stats) {
        const perfStats = data.performance_stats
        const responseStats = perfStats.response_time_stats || {}
        const packetStats = perfStats.packet_loss_stats || {}
        
        // 将后端的[min, avg, max]格式转换为前端期望的格式
        const convertStats = (stats) => {
          if (Array.isArray(stats) && stats.length >= 3) {
            // 生成与时间轴对应的数据点，使用平均值填充
            const dataPoints = trendXAxis.value.length > 0 
              ? new Array(trendXAxis.value.length).fill(stats[1] || 0)
              : [stats[1] || 0]
            return {
              min: stats[0] || 0,
              avg: stats[1] || 0, 
              max: stats[2] || 0,
              data: dataPoints
            }
          }
          // 如果没有数据，生成与时间轴对应的零值数据点
          const zeroPoints = trendXAxis.value.length > 0 
            ? new Array(trendXAxis.value.length).fill(0)
            : [0]
          return { min: 0, avg: 0, max: 0, data: zeroPoints }
        }
        
        performanceData.value = {
          tcp_connection_time: convertStats(responseStats.tcp_connect),
          ping_rtt: convertStats(responseStats.ping_latency),
          http_response_time: convertStats(responseStats.http_response),
          api_response_time: convertStats(responseStats.api_response),
          ping_packet_loss: {
            min: packetStats.ping_packet_loss ? packetStats.ping_packet_loss[0] || 0 : 0,
            avg: packetStats.ping_packet_loss ? packetStats.ping_packet_loss[1] || 0 : 0,
            max: packetStats.ping_packet_loss ? packetStats.ping_packet_loss[2] || 0 : 0,
            data: packetStats.ping_packet_loss_data || []
          }
        }
        
        console.log('性能数据处理结果:', performanceData.value)
        console.log('时间轴数据:', trendXAxis.value)
        console.log('原始后端数据:', data.performance_stats)
        console.log('丢包率原始数据:', packetStats.ping_packet_loss)
      }

      // 初始化/更新图表
      initAllCharts()
      message.success('数据刷新完成')
    } else {
      throw new Error(res?.message || '获取报表总览失败')
    }
  } catch (error) {
    console.error('刷新数据失败:', error)
    message.error(error.message || '刷新数据失败')
  }
}

const exportReport = async () => {
  try {
    const { ExportUtils } = await import('@/utils/exportUtils')
    await ExportUtils.quickExport('overview', 'excel', selectedTimeRange.value)
  } catch (error) {
    console.error('导出报表失败:', error)
    message.error('导出报表失败，请稍后重试')
  }
}

const getTopRankColor = (index) => {
  const colors = ['gold', 'silver', '#cd7f32', 'blue', 'green']
  return colors[index] || 'default'
}

const getTaskTypeColor = (type) => {
  const colors = {
    'TCP': 'blue',
    'Ping': 'green',
    'HTTP': 'orange',
    'API': 'purple'
  }
  return colors[type] || 'default'
}

// 跳转到任务详情页面
const navigateToTaskDetail = (taskId, taskType) => {
  if (!taskId) {
    message.warning('任务ID不存在')
    return
  }
  
  // 根据任务类型跳转到不同的详情页面
  switch (taskType?.toLowerCase()) {
    case 'api':
      router.push(`/api-monitoring/result/${taskId}`)
      break
    case 'http':
      router.push(`/task-management/http-result/${taskId}`)
      break
    case 'ping':
      router.push(`/task-management/ping-result/${taskId}`)
      break
    case 'tcp':
      router.push(`/task-management/tcp-result/${taskId}`)
      break
    default:
      // 默认跳转到任务管理列表页面
      router.push('/task-management/list')
      break
  }
}

// 初始化成功率趋势图
const initSuccessRateChart = () => {
  if (!successRateChart.value) return
  
  successRateChartInstance = echarts.init(successRateChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: { data: ['TCP', 'Ping', 'HTTP', 'API'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: trendXAxis.value },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { formatter: '{value}%' }
    },
    series: [
      { name: 'TCP', type: 'line', data: typeTrends.value.tcp, smooth: true, itemStyle: { color: '#1890ff' } },
      { name: 'Ping', type: 'line', data: typeTrends.value.ping, smooth: true, itemStyle: { color: '#52c41a' } },
      { name: 'HTTP', type: 'line', data: typeTrends.value.http, smooth: true, itemStyle: { color: '#faad14' } },
      { name: 'API', type: 'line', data: typeTrends.value.api, smooth: true, itemStyle: { color: '#722ed1' } }
    ]
  }
  
  successRateChartInstance.setOption(option)
}

// 初始化成功率饼图
const initSuccessRatePieChart = () => {
  if (!successRatePieChart.value) return
  
  successRatePieChartInstance = echarts.init(successRatePieChart.value)
  
  const option = {
    tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c}% ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [
      {
        name: '成功率',
        type: 'pie',
        radius: '50%',
        data: pieSeriesData.value,
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
      }
    ]
  }
  
  successRatePieChartInstance.setOption(option)
}

// 初始化性能图表
const initPerformanceChart = (type) => {
  switch (type) {
    case 'response-time':
      initResponseTimeChart()
      break
    case 'packet-loss':
      initPacketLossChart()
      break
    case 'status-code':
      initStatusCodeChart()
      break
  }
}

// 初始化响应时间图表
const initResponseTimeChart = () => {
  if (!responseTimeChart.value) return
  
  responseTimeChartInstance = echarts.init(responseTimeChart.value)
  
  // 生成时间轴数据，如果没有数据则使用默认时间点
  const timeLabels = trendXAxis.value.length > 0 
    ? trendXAxis.value.map(time => {
        const date = new Date(time)
        // 检查日期是否有效
        if (isNaN(date.getTime())) {
          return time // 如果无法解析，直接返回原始时间字符串
        }
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
      })
    : ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['TCP连接时间', 'Ping延迟', 'HTTP响应时间', 'API响应时间']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeLabels
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}ms'
      }
    },
    series: [
      {
        name: 'TCP连接时间',
        type: 'line',
        data: performanceData.value.tcp_connection_time.data || [],
        smooth: true,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: 'Ping延迟',
        type: 'line',
        data: performanceData.value.ping_rtt.data || [],
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: 'HTTP响应时间',
        type: 'line',
        data: performanceData.value.http_response_time.data || [],
        smooth: true,
        itemStyle: { color: '#faad14' }
      },
      {
        name: 'API响应时间',
        type: 'line',
        data: performanceData.value.api_response_time.data || [],
        smooth: true,
        itemStyle: { color: '#722ed1' }
      }
    ]
  }
  
  responseTimeChartInstance.setOption(option)
}

// 初始化丢包率图表
const initPacketLossChart = () => {
  if (!packetLossChart.value) return
  
  packetLossChartInstance = echarts.init(packetLossChart.value)
  
  // 生成时间轴数据，如果没有数据则使用默认时间点
  const timeLabels = trendXAxis.value.length > 0 
    ? trendXAxis.value.map(time => {
        const date = new Date(time)
        // 检查日期是否有效
        if (isNaN(date.getTime())) {
          return time // 如果无法解析，直接返回原始时间字符串
        }
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
      })
    : ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
  
  // 动态计算Y轴最大值
  const packetLossData = performanceData.value.ping_packet_loss.data || []
  const maxPacketLoss = packetLossData.length > 0 
    ? Math.max(...packetLossData, performanceData.value.ping_packet_loss.max || 0)
    : performanceData.value.ping_packet_loss.max || 0
  const yAxisMax = Math.max(5, Math.ceil((maxPacketLoss || 0) * 1.2))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['Ping丢包率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeLabels
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: yAxisMax,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'Ping丢包率',
        type: 'bar',
        data: performanceData.value.ping_packet_loss.data || [],
        itemStyle: { color: '#ff4d4f' }
      }
    ]
  }
  
  packetLossChartInstance.setOption(option)
}

// 初始化状态码图表
const initStatusCodeChart = () => {
  if (!statusCodeChart.value) return
  
  statusCodeChartInstance = echarts.init(statusCodeChart.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: 'HTTP状态码',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 85, name: '200 OK', itemStyle: { color: '#52c41a' } },
          { value: 8, name: '404 Not Found', itemStyle: { color: '#faad14' } },
          { value: 4, name: '500 Server Error', itemStyle: { color: '#ff4d4f' } },
          { value: 2, name: '超时', itemStyle: { color: '#d9d9d9' } },
          { value: 1, name: '其他', itemStyle: { color: '#722ed1' } }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  statusCodeChartInstance.setOption(option)
}

// 初始化所有图表
const initAllCharts = () => {
  nextTick(() => {
    initSuccessRateChart()
    initSuccessRatePieChart()
    initPerformanceChart(activePerformanceTab.value)
  })
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  successRateChartInstance?.resize()
  successRatePieChartInstance?.resize()
  responseTimeChartInstance?.resize()
  packetLossChartInstance?.resize()
  statusCodeChartInstance?.resize()
}

onMounted(() => {
  refreshData()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
const cleanup = () => {
  window.removeEventListener('resize', handleResize)
  successRateChartInstance?.dispose()
  successRatePieChartInstance?.dispose()
  responseTimeChartInstance?.dispose()
  packetLossChartInstance?.dispose()
  statusCodeChartInstance?.dispose()
}

// 在组件卸载时清理
import { onBeforeUnmount } from 'vue'
onBeforeUnmount(cleanup)
</script>

<style scoped>
.report-overview {
  padding: 0;
}

.filter-card {
  margin-bottom: 16px;
}

.overview-cards {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
}

.chart-section {
  margin-bottom: 16px;
}

.top-section {
  margin-bottom: 16px;
}

.top-item-value {
  text-align: right;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

:deep(.ant-statistic-content) {
  font-size: 24px;
  font-weight: 600;
}

:deep(.ant-card-head-title) {
  font-size: 16px;
  font-weight: 600;
}

:deep(.ant-list-item-meta-title) {
  margin-bottom: 4px;
}

:deep(.ant-list-item-meta-description) {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.clickable-list-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.clickable-list-item:hover {
  background-color: #f5f5f5;
}

.task-name-link {
  color: #1890ff;
  transition: color 0.2s;
}

.task-name-link:hover {
  color: #40a9ff;
}
</style>