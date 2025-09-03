<template>
  <div class="ping-report">
    <a-page-header title="Ping专项报表" sub-title="Ping网络延迟专项分析" />
    
    <!-- 筛选条件 -->
    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="4">
          <a-space>
            <span>时间范围：</span>
            <a-select v-model:value="selectedTimeRange" style="width: 120px;" @change="handleTimeRangeChange">
              <a-select-option value="1h">1小时</a-select-option>
              <a-select-option value="1d">1天</a-select-option>
              <a-select-option value="7d">7天</a-select-option>
              <a-select-option value="30d">30天</a-select-option>
            </a-select>
          </a-space>
        </a-col>
        <a-col :span="4">
          <a-space>
            <span>任务筛选：</span>
            <a-select v-model:value="selectedTask" style="width: 150px;" @change="handleTaskChange">
              <a-select-option value="all">全部任务</a-select-option>
              <a-select-option v-for="task in pingTasks" :key="task.id" :value="task.id">
                {{ task.name }}
              </a-select-option>
            </a-select>
          </a-space>
        </a-col>
        <a-col :span="4">
          <a-space>
            <span>地域筛选：</span>
            <a-select v-model:value="selectedRegion" style="width: 120px;" @change="handleRegionChange">
              <a-select-option value="all">全部地域</a-select-option>
              <a-select-option value="domestic">国内</a-select-option>
              <a-select-option value="overseas">海外</a-select-option>
            </a-select>
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

    <!-- Ping关键指标 -->
    <a-row :gutter="16" class="metrics-cards">
      <a-col :span="6" v-for="metric in pingMetrics" :key="metric.key">
        <a-card :bordered="false" class="metric-card">
          <a-statistic
            :title="metric.title"
            :value="metric.value"
            :suffix="metric.suffix"
            :precision="metric.precision"
            :value-style="{ color: metric.color }"
          >
            <template #prefix>
              <component :is="metric.icon" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 主要图表区域 -->
    <a-row :gutter="16" class="chart-section">
      <!-- Ping延迟趋势图 -->
      <a-col :span="12">
        <a-card title="Ping延迟趋势" :bordered="false">
          <div ref="latencyTrendChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
      
      <!-- 丢包率分布 -->
      <a-col :span="12">
        <a-card title="成功率分布" :bordered="false">
          <div ref="packetLossChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 延迟分析 -->
    <a-row :gutter="16" class="chart-section">
      <a-col :span="24">
        <a-card title="延迟性能分析" :bordered="false">
          <a-tabs v-model:activeKey="activeLatencyTab" @change="handleLatencyTabChange">
            <a-tab-pane key="latency-distribution" tab="延迟分布统计">
              <div ref="latencyDistributionChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="jitter-analysis" tab="抖动分析">
              <div ref="jitterAnalysisChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="geographic-analysis" tab="地理位置分析">
              <div ref="geographicChart" style="height: 350px;"></div>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>

    <!-- Ping任务详细列表 -->
    <a-row :gutter="16" class="table-section">
      <a-col :span="24">
        <a-card title="Ping任务详细统计" :bordered="false">
          <a-table
            :columns="taskColumns"
            :data-source="taskTableData"
            :loading="loading"
            :pagination="{
              current: currentPage,
              pageSize: pageSize,
              total: totalTasks,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
            }"
            @change="handleTableChange"
            size="middle"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="record.packetLoss <= 1 ? 'green' : record.packetLoss <= 5 ? 'orange' : 'red'">
                  {{ record.packetLoss <= 1 ? '正常' : record.packetLoss <= 5 ? '警告' : '异常' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'packetLoss'">
                <a-progress
                  :percent="Math.min(record.packetLoss * 10, 100)"
                  :status="record.packetLoss <= 1 ? 'success' : record.packetLoss <= 5 ? 'active' : 'exception'"
                  size="small"
                  :format="() => `${record.packetLoss}%`"
                />
              </template>
              <template v-else-if="column.key === 'avgLatency'">
                <span :style="{ color: record.avgLatency > 200 ? '#ff4d4f' : record.avgLatency > 100 ? '#faad14' : '#52c41a' }">
                  {{ record.avgLatency }}ms
                </span>
              </template>
              <template v-else-if="column.key === 'jitter'">
                <span :style="{ color: record.jitter > 50 ? '#ff4d4f' : record.jitter > 20 ? '#faad14' : '#52c41a' }">
                  {{ record.jitter }}ms
                </span>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" size="small" @click="viewTaskDetail(record)">
                    查看详情
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted, h, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getPingReport } from '@/api/reports'
import request from '@/utils/request'
import {
  SyncOutlined,
  DownloadOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  DisconnectOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'

// 筛选条件
const selectedTimeRange = ref('1d')
const selectedTask = ref('all')
const selectedRegion = ref('all')
const activeLatencyTab = ref('latency-distribution')

// 加载状态
const loading = ref(false)

// 图表数据存储
const chartData = ref({
  latencyTrend: [],
  packetLossDistribution: [],
  taskList: [],
  performanceMetrics: {}
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const totalTasks = ref(50)

// 图表引用
const latencyTrendChart = ref(null)
const packetLossChart = ref(null)
const latencyDistributionChart = ref(null)
const jitterAnalysisChart = ref(null)
const geographicChart = ref(null)

// 图表实例
let latencyTrendChartInstance = null
let packetLossChartInstance = null
let latencyDistributionChartInstance = null
let jitterAnalysisChartInstance = null
let geographicChartInstance = null

// Ping任务列表
const pingTasks = ref([])

// Ping关键指标
const pingMetrics = ref([
  {
    key: 'avgLatency',
    title: '平均延迟',
    value: 0,
    suffix: 'ms',
    precision: 1,
    color: '#1890ff',
    icon: ThunderboltOutlined
  },
  {
    key: 'packetLoss',
    title: '平均丢包率',
    value: 0,
    suffix: '%',
    precision: 1,
    color: '#ff4d4f',
    icon: DisconnectOutlined
  },
  {
    key: 'jitter',
    title: '平均抖动',
    value: 0,
    suffix: 'ms',
    precision: 1,
    color: '#faad14',
    icon: WarningOutlined
  },
  {
    key: 'availability',
    title: '可用性',
    value: 0,
    suffix: '%',
    precision: 1,
    color: '#52c41a',
    icon: ClockCircleOutlined
  }
])

// 获取Ping任务列表
const fetchPingTasks = async () => {
  try {
    const response = await request.get('/tasks', {
      params: { task_type: 'ping' }
    })
    // 处理API返回格式: {code: 0, data: {list: [...], total: N}, message: ""}
    if (response && response.code === 0 && response.data) {
      if (Array.isArray(response.data.list)) {
        // v1 API格式: data.list
        pingTasks.value = response.data.list.map(task => ({
          id: task.id,
          name: task.name
        }))
      } else if (Array.isArray(response.data)) {
        // v2 API格式: data直接是数组
        pingTasks.value = response.data.map(task => ({
          id: task.id,
          name: task.name
        }))
      } else {
        console.warn('Ping任务数据格式不正确:', response)
        pingTasks.value = []
      }
    } else if (response.data && response.data.tasks && Array.isArray(response.data.tasks)) {
      // 兼容旧格式 {data: {tasks: [...]}}
      pingTasks.value = response.data.tasks.map(task => ({
        id: task.id,
        name: task.name
      }))
    } else {
      console.warn('Ping任务数据格式不正确:', response)
      pingTasks.value = []
    }
  } catch (error) {
    console.error('获取Ping任务列表失败:', error)
    message.error('获取Ping任务列表失败')
    pingTasks.value = []
  }
}

// 表格列定义
const taskColumns = [
  {
    title: '任务名称',
    dataIndex: 'taskName',
    key: 'taskName',
    width: 150
  },
  {
    title: '目标地址',
    dataIndex: 'target',
    key: 'target',
    width: 200
  },
  {
    title: '地域',
    dataIndex: 'region',
    key: 'region',
    width: 100
  },
  {
    title: '状态',
    key: 'status',
    width: 80
  },
  {
    title: '平均延迟',
    key: 'avgLatency',
    width: 100
  },
  {
    title: '丢包率',
    key: 'packetLoss',
    width: 120
  },
  {
    title: '抖动',
    key: 'jitter',
    width: 80
  },
  {
    title: '总测试次数',
    dataIndex: 'totalTests',
    key: 'totalTests',
    width: 100
  },
  {
    title: '最后测试时间',
    dataIndex: 'lastTestTime',
    key: 'lastTestTime',
    width: 150
  },
  {
    title: '操作',
    key: 'action',
    width: 150
  }
]

// 表格数据
const taskTableData = ref([])

// 获取Ping报表数据
const fetchPingReportData = async () => {
  try {
    loading.value = true
    const params = {
      time_range: selectedTimeRange.value,
      task_id: selectedTask.value === 'all' ? undefined : selectedTask.value,
      region: selectedRegion.value === 'all' ? undefined : selectedRegion.value
    }
    
    const response = await getPingReport(params)
    
    // 处理新的API响应格式 {code: 0, data: {...}}
    let reportData = null
    if (response && response.code === 0 && response.data) {
      reportData = response.data
    } else if (response && response.data) {
      // 兼容旧格式
      reportData = response.data
    }
    
    if (reportData) {
      // 更新关键指标 - 映射API字段到前端期望的字段
      const metrics = reportData.metrics || {}
      pingMetrics.value.forEach(metric => {
        switch (metric.key) {
          case 'avgLatency':
            metric.value = metrics.avg_latency || 0
            break
          case 'packetLoss':
            metric.value = metrics.packet_loss_rate || 0
            break
          case 'jitter':
            metric.value = metrics.jitter || 0
            break
          case 'availability':
            metric.value = metrics.success_rate || 0
            break
          default:
            if (metrics[metric.key] !== undefined) {
              metric.value = metrics[metric.key]
            }
        }
      })
      
      // 更新表格数据
      if (reportData.task_list) {
        taskTableData.value = reportData.task_list.map((task, index) => ({
          key: task.task_id || task.id || index.toString(),
          taskName: task.task_name || task.name,
          target: task.target_host || task.target,
          region: task.region,
          avgLatency: task.avg_latency || 0,
          packetLoss: task.packet_loss_rate || 0,
          jitter: task.jitter || 0,
          totalTests: task.total_pings || task.total_tests || 0,
          lastTestTime: task.last_execution_time
        }))
        totalTasks.value = reportData.total_tasks || taskTableData.value.length
      }
      
      // 更新图表数据 - 转换API数据格式到图表期望格式
       const latencyTrendData = (reportData.latency_trend || []).map(item => ({
         time: item.time || item.timestamp,
         avgLatency: item.avg_latency || 0,
         minLatency: item.min_latency || 0,
         maxLatency: item.max_latency || 0,
         successRate: item.success_rate || 0
       }))
       
       // 基于latency_trend数据计算丢包率分布
       const packetLossData = (reportData.latency_trend || []).map(item => {
         const successRate = item.success_rate || 0
         // 判断success_rate是百分比(0-100)还是小数(0-1)
         const packetLoss = successRate > 1 
           ? (100 - successRate)  // 如果>1，说明是百分比格式
           : ((1 - successRate) * 100)  // 如果<=1，说明是小数格式
         return {
           time: item.time || item.timestamp,
           packetLoss: Math.max(0, packetLoss)  // 确保不为负数
         }
       })
       
       // 处理延迟分布数据和字段名转换
       const performanceMetrics = {
         ...reportData.performance_metrics,
         latencyDistribution: reportData.latency_distribution || reportData.performance_metrics?.latency_distribution || [
           { range: '0-20ms', value: 0 },
           { range: '20-50ms', value: 0 },
           { range: '50-100ms', value: 0 },
           { range: '100-200ms', value: 0 },
           { range: '>200ms', value: 0 }
         ],
         // 字段名转换：后端使用下划线命名，前端使用驼峰命名
         jitterAnalysis: reportData.performance_metrics?.jitter_analysis || [],
         geographicAnalysis: reportData.performance_metrics?.geographic_analysis || []
       }
       
       chartData.value = {
         latencyTrend: latencyTrendData,
         packetLossDistribution: packetLossData,
         taskList: reportData.task_list || [],
         performanceMetrics: performanceMetrics
       }
      
      // 更新图表
      updateChartData()
    } else {
      console.warn('Ping报表数据格式不正确:', response)
    }
  } catch (error) {
    console.error('获取Ping报表数据失败:', error)
    message.error('获取Ping报表数据失败')
  } finally {
    loading.value = false
  }
}

// 更新图表数据
const updateChartData = () => {
  nextTick(() => {
    initLatencyTrendChart()
    initPacketLossChart()
    initLatencyChart(activeLatencyTab.value)
  })
}

// 方法
const handleTimeRangeChange = (value) => {
  fetchPingReportData()
}

const handleTaskChange = (value) => {
  fetchPingReportData()
}

const handleRegionChange = (value) => {
  fetchPingReportData()
}

const handleLatencyTabChange = (key) => {
  activeLatencyTab.value = key
  nextTick(() => {
    initLatencyChart(key)
  })
}

const handleTableChange = (pagination) => {
  currentPage.value = pagination.current
  pageSize.value = pagination.pageSize
  fetchPingReportData()
}

const refreshData = async () => {
  await fetchPingReportData()
  message.success('数据刷新完成')
}

const exportReport = async () => {
  try {
    const { ExportUtils } = await import('@/utils/exportUtils')
    await ExportUtils.quickExport('ping', 'excel', selectedTimeRange.value)
  } catch (error) {
    console.error('导出Ping报表失败:', error)
    message.error('导出Ping报表失败，请稍后重试')
  }
}

const router = useRouter()

const viewTaskDetail = (record) => {
  // 跳转到Ping任务结果列表页面
  if (record.key) {
    router.push(`/task-management/ping-result/${record.key}`)
  } else {
    message.error('任务ID不存在，无法查看详情')
  }
}

const viewTaskTrend = (record) => {
  message.info(`查看趋势分析: ${record.taskName}`)
}

// 初始化延迟趋势图
const initLatencyTrendChart = () => {
  if (!latencyTrendChart.value) return
  
  // 销毁已存在的实例
  if (latencyTrendChartInstance) {
    latencyTrendChartInstance.dispose()
    latencyTrendChartInstance = null
  }
  
  latencyTrendChartInstance = echarts.init(latencyTrendChart.value)
  
  const trendData = chartData.value.latencyTrend || []
  
  if (trendData.length === 0) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    latencyTrendChartInstance.setOption(option)
    return
  }
  
  const timeLabels = trendData.map(item => item.time || item.timestamp)
  const avgLatencyData = trendData.map(item => item.avgLatency || 0)
  const minLatencyData = trendData.map(item => item.minLatency || 0)
  const maxLatencyData = trendData.map(item => item.maxLatency || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = `时间: ${params[0].axisValue}<br/>`
        params.forEach(param => {
          result += `${param.seriesName}: ${param.value}ms<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['平均延迟', '最小延迟', '最大延迟']
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
        name: '平均延迟',
        type: 'line',
        data: avgLatencyData,
        smooth: true,
        itemStyle: { color: '#1890ff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.1)' }
            ]
          }
        }
      },
      {
        name: '最小延迟',
        type: 'line',
        data: minLatencyData,
        smooth: true,
        itemStyle: { color: '#52c41a' },
        lineStyle: { type: 'dashed' }
      },
      {
        name: '最大延迟',
        type: 'line',
        data: maxLatencyData,
        smooth: true,
        itemStyle: { color: '#ff4d4f' },
        lineStyle: { type: 'dashed' }
      }
    ]
  }
  
  latencyTrendChartInstance.setOption(option)
}

// 初始化丢包率图表
const initPacketLossChart = () => {
  if (!packetLossChart.value) return
  
  // 销毁已存在的实例
  if (packetLossChartInstance) {
    packetLossChartInstance.dispose()
    packetLossChartInstance = null
  }
  
  packetLossChartInstance = echarts.init(packetLossChart.value)
  
  const lossData = chartData.value.packetLossDistribution || []
  
  if (lossData.length === 0) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    packetLossChartInstance.setOption(option)
    return
  }
  
  const timeLabels = lossData.map(item => item.time || item.timestamp)
  const packetLossData = lossData.map(item => {
    const value = item.packetLoss || 0
    let color = '#52c41a' // 绿色：正常
    if (value > 3) {
      color = '#ff4d4f' // 红色：严重
    } else if (value > 1) {
      color = '#faad14' // 黄色：警告
    }
    return { value, itemStyle: { color } }
  })
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        const param = params[0]
        return `时间: ${param.axisValue}<br/>成功率: ${param.value}%`
      }
    },
    legend: {
      data: ['丢包率']
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
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '成功率',
        type: 'bar',
        data: packetLossData
      }
    ]
  }
  
  packetLossChartInstance.setOption(option)
}

// 初始化延迟图表
const initLatencyChart = (type) => {
  switch (type) {
    case 'latency-distribution':
      initLatencyDistributionChart()
      break
    case 'jitter-analysis':
      initJitterAnalysisChart()
      break
    case 'geographic-analysis':
      initGeographicChart()
      break
  }
}

// 初始化延迟分布图表
const initLatencyDistributionChart = () => {
  if (!latencyDistributionChart.value) return
  
  // 销毁已存在的实例
  if (latencyDistributionChartInstance) {
    latencyDistributionChartInstance.dispose()
    latencyDistributionChartInstance = null
  }
  
  latencyDistributionChartInstance = echarts.init(latencyDistributionChart.value)
  
  const distributionData = chartData.value.performanceMetrics?.latencyDistribution || []
  
  if (distributionData.length === 0) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    latencyDistributionChartInstance.setOption(option)
    return
  }
  
  const pieData = distributionData.map(item => {
    const range = item.range || item.name
    let color = '#52c41a'
    if (range.includes('200')) {
      color = '#ff4d4f'
    } else if (range.includes('100')) {
      color = '#ff7a45'
    } else if (range.includes('50')) {
      color = '#faad14'
    } else if (range.includes('20')) {
      color = '#1890ff'
    }
    return {
      value: item.value || item.count,
      name: range,
      itemStyle: { color }
    }
  })
  
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
        name: '延迟分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        data: pieData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          show: false,
          position: 'center'
        },
        labelLine: {
          show: false
        }
      }
    ]
  }
  
  latencyDistributionChartInstance.setOption(option)
}

// 初始化抖动分析图表
const initJitterAnalysisChart = () => {
  if (!jitterAnalysisChart.value) return
  
  // 销毁已存在的实例
  if (jitterAnalysisChartInstance) {
    jitterAnalysisChartInstance.dispose()
    jitterAnalysisChartInstance = null
  }
  
  jitterAnalysisChartInstance = echarts.init(jitterAnalysisChart.value)
  
  const jitterData = chartData.value.performanceMetrics?.jitterAnalysis || []
  
  if (jitterData.length === 0) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    jitterAnalysisChartInstance.setOption(option)
    return
  }
  
  // 处理API返回的数字数组格式
  let timeLabels, jitterValues
  if (Array.isArray(jitterData) && typeof jitterData[0] === 'number') {
    // API返回的是数字数组，生成时间标签
    timeLabels = jitterData.map((_, index) => `${index + 1}`)
    jitterValues = jitterData
  } else {
    // 期望的对象数组格式
    timeLabels = jitterData.map(item => item.time || item.timestamp)
    jitterValues = jitterData.map(item => item.jitter || 0)
  }
  const threshold = 20 // 抖动阈值
  const thresholdData = new Array(timeLabels.length).fill(threshold)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = `时间: ${params[0].axisValue}<br/>`
        params.forEach(param => {
          result += `${param.seriesName}: ${param.value}ms<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['抖动值', '抖动阈值']
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
        name: '抖动值',
        type: 'line',
        data: jitterValues,
        smooth: true,
        itemStyle: { color: '#faad14' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(250, 173, 20, 0.3)' },
              { offset: 1, color: 'rgba(250, 173, 20, 0.1)' }
            ]
          }
        }
      },
      {
        name: '抖动阈值',
        type: 'line',
        data: thresholdData,
        lineStyle: {
          type: 'dashed',
          color: '#ff4d4f'
        },
        itemStyle: { color: '#ff4d4f' }
      }
    ]
  }
  
  jitterAnalysisChartInstance.setOption(option)
}

// 初始化地理位置分析图表
const initGeographicChart = () => {
  if (!geographicChart.value) return
  
  // 销毁已存在的实例
  if (geographicChartInstance) {
    geographicChartInstance.dispose()
    geographicChartInstance = null
  }
  
  geographicChartInstance = echarts.init(geographicChart.value)
  
  const geographicData = chartData.value.performanceMetrics?.geographicAnalysis || []
  
  if (geographicData.length === 0) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    geographicChartInstance.setOption(option)
    return
  }
  
  const regions = geographicData.map(item => item.region || item.name)
  const latencyData = geographicData.map(item => item.avg_latency || item.avgLatency || 0)
  const packetLossData = geographicData.map(item => item.packet_loss || item.packetLoss || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        let result = `地区: ${params[0].axisValue}<br/>`
        params.forEach(param => {
          const unit = param.seriesName === '平均延迟' ? 'ms' : '%'
          result += `${param.seriesName}: ${param.value}${unit}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['平均延迟', '丢包率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: regions
    },
    yAxis: [
      {
        type: 'value',
        name: '延迟(ms)',
        position: 'left',
        axisLabel: {
          formatter: '{value}ms'
        }
      },
      {
        type: 'value',
        name: '丢包率(%)',
        position: 'right',
        axisLabel: {
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: '平均延迟',
        type: 'bar',
        yAxisIndex: 0,
        data: latencyData,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '丢包率',
        type: 'line',
        yAxisIndex: 1,
        data: packetLossData,
        itemStyle: { color: '#ff4d4f' }
      }
    ]
  }
  
  geographicChartInstance.setOption(option)
}

// 初始化所有图表
const initAllCharts = () => {
  nextTick(() => {
    initLatencyTrendChart()
    initPacketLossChart()
    initLatencyChart(activeLatencyTab.value)
  })
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  latencyTrendChartInstance?.resize()
  packetLossChartInstance?.resize()
  latencyDistributionChartInstance?.resize()
  jitterAnalysisChartInstance?.resize()
  geographicChartInstance?.resize()
}

onMounted(async () => {
  await fetchPingTasks()
  await fetchPingReportData()
  initAllCharts()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
const cleanup = () => {
  window.removeEventListener('resize', handleResize)
  latencyTrendChartInstance?.dispose()
  packetLossChartInstance?.dispose()
  latencyDistributionChartInstance?.dispose()
  jitterAnalysisChartInstance?.dispose()
  geographicChartInstance?.dispose()
}

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(cleanup)
</script>

<style scoped>
.ping-report {
  padding: 0;
}

.filter-card {
  margin-bottom: 16px;
}

.metrics-cards {
  margin-bottom: 16px;
}

.metric-card {
  text-align: center;
}

.chart-section {
  margin-bottom: 16px;
}

.table-section {
  margin-bottom: 16px;
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

:deep(.ant-progress-text) {
  font-size: 12px;
}
</style>