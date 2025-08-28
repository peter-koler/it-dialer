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
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <a-space>
                      <a-tag :color="getTopRankColor(index)">{{ index + 1 }}</a-tag>
                      <span>{{ item.taskName }}</span>
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
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <a-space>
                      <a-tag color="red">{{ index + 1 }}</a-tag>
                      <span>{{ item.taskName }}</span>
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
import {
  SyncOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'

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

// 总体统计数据
const overviewStats = ref([
  {
    title: 'TCP任务成功率',
    value: 95.8,
    suffix: '%',
    color: '#52c41a',
    icon: CheckCircleOutlined,
    type: 'tcp'
  },
  {
    title: 'Ping任务成功率',
    value: 98.2,
    suffix: '%',
    color: '#52c41a',
    icon: CheckCircleOutlined,
    type: 'ping'
  },
  {
    title: 'HTTP任务成功率',
    value: 92.5,
    suffix: '%',
    color: '#faad14',
    icon: WarningOutlined,
    type: 'http'
  },
  {
    title: 'API任务成功率',
    value: 89.7,
    suffix: '%',
    color: '#faad14',
    icon: WarningOutlined,
    type: 'api'
  }
])

// TOP榜单数据
const topAvailabilityTasks = ref([
  { taskName: 'Ping百度', taskType: 'Ping', target: 'www.baidu.com', successRate: 99.8 },
  { taskName: 'TCP本地测试', taskType: 'TCP', target: '127.0.0.1:8080', successRate: 98.5 },
  { taskName: 'HTTP健康检查', taskType: 'HTTP', target: 'https://api.example.com/health', successRate: 97.2 },
  { taskName: 'API登录接口', taskType: 'API', target: '/api/v1/login', successRate: 96.8 },
  { taskName: 'Ping谷歌DNS', taskType: 'Ping', target: '8.8.8.8', successRate: 96.5 }
])

const topFailureTasks = ref([
  { taskName: 'TCP远程连接', taskType: 'TCP', target: 'remote.server.com:3306', failureRate: 15.2 },
  { taskName: 'API支付接口', taskType: 'API', target: '/api/v1/payment', failureRate: 12.8 },
  { taskName: 'HTTP文件下载', taskType: 'HTTP', target: 'https://cdn.example.com/file.zip', failureRate: 10.5 },
  { taskName: 'Ping国外服务器', taskType: 'Ping', target: 'overseas.server.com', failureRate: 8.7 },
  { taskName: 'TCP数据库连接', taskType: 'TCP', target: 'db.server.com:5432', failureRate: 7.3 }
])

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
  message.loading('正在刷新数据...', 1)
  // 这里应该调用API获取最新数据
  await new Promise(resolve => setTimeout(resolve, 1000))
  initAllCharts()
  message.success('数据刷新完成')
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

// 初始化成功率趋势图
const initSuccessRateChart = () => {
  if (!successRateChart.value) return
  
  successRateChartInstance = echarts.init(successRateChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['TCP', 'Ping', 'HTTP', 'API']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
    },
    yAxis: {
      type: 'value',
      min: 80,
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'TCP',
        type: 'line',
        data: [95, 94, 96, 95, 97, 96, 95],
        smooth: true,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: 'Ping',
        type: 'line',
        data: [98, 97, 99, 98, 98, 99, 98],
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: 'HTTP',
        type: 'line',
        data: [92, 91, 94, 93, 92, 93, 92],
        smooth: true,
        itemStyle: { color: '#faad14' }
      },
      {
        name: 'API',
        type: 'line',
        data: [89, 88, 91, 90, 89, 90, 89],
        smooth: true,
        itemStyle: { color: '#722ed1' }
      }
    ]
  }
  
  successRateChartInstance.setOption(option)
}

// 初始化成功率饼图
const initSuccessRatePieChart = () => {
  if (!successRatePieChart.value) return
  
  successRatePieChartInstance = echarts.init(successRatePieChart.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '成功率',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 95.8, name: 'TCP任务', itemStyle: { color: '#1890ff' } },
          { value: 98.2, name: 'Ping任务', itemStyle: { color: '#52c41a' } },
          { value: 92.5, name: 'HTTP任务', itemStyle: { color: '#faad14' } },
          { value: 89.7, name: 'API任务', itemStyle: { color: '#722ed1' } }
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
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
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
        data: [50, 45, 55, 48, 52, 49, 51],
        smooth: true,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: 'Ping延迟',
        type: 'line',
        data: [20, 18, 22, 19, 21, 20, 19],
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: 'HTTP响应时间',
        type: 'line',
        data: [200, 180, 220, 195, 205, 190, 200],
        smooth: true,
        itemStyle: { color: '#faad14' }
      },
      {
        name: 'API响应时间',
        type: 'line',
        data: [350, 320, 380, 340, 360, 330, 350],
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
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 5,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'Ping丢包率',
        type: 'bar',
        data: [0.5, 0.2, 0.8, 0.3, 0.6, 0.4, 0.5],
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
  initAllCharts()
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
</style>