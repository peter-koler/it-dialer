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
        <a-card title="丢包率分布" :bordered="false">
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
                  <a-button type="link" size="small" @click="viewTaskTrend(record)">
                    趋势分析
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
import * as echarts from 'echarts'
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
const pingTasks = ref([
  { id: 1, name: 'Ping百度' },
  { id: 2, name: 'Ping谷歌DNS' },
  { id: 3, name: 'Ping阿里DNS' },
  { id: 4, name: 'Ping本地网关' }
])

// Ping关键指标
const pingMetrics = ref([
  {
    key: 'avgLatency',
    title: '平均延迟',
    value: 28.5,
    suffix: 'ms',
    precision: 1,
    color: '#1890ff',
    icon: ThunderboltOutlined
  },
  {
    key: 'packetLoss',
    title: '平均丢包率',
    value: 1.2,
    suffix: '%',
    precision: 1,
    color: '#ff4d4f',
    icon: DisconnectOutlined
  },
  {
    key: 'jitter',
    title: '平均抖动',
    value: 12.8,
    suffix: 'ms',
    precision: 1,
    color: '#faad14',
    icon: WarningOutlined
  },
  {
    key: 'availability',
    title: '可用性',
    value: 98.8,
    suffix: '%',
    precision: 1,
    color: '#52c41a',
    icon: ClockCircleOutlined
  }
])

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
const taskTableData = ref([
  {
    key: '1',
    taskName: 'Ping百度',
    target: 'www.baidu.com',
    region: '国内',
    avgLatency: 25,
    packetLoss: 0.5,
    jitter: 8,
    totalTests: 2880,
    lastTestTime: '2024-01-15 14:30:25'
  },
  {
    key: '2',
    taskName: 'Ping谷歌DNS',
    target: '8.8.8.8',
    region: '海外',
    avgLatency: 180,
    packetLoss: 2.1,
    jitter: 25,
    totalTests: 1440,
    lastTestTime: '2024-01-15 14:29:45'
  },
  {
    key: '3',
    taskName: 'Ping阿里DNS',
    target: '223.5.5.5',
    region: '国内',
    avgLatency: 18,
    packetLoss: 0.2,
    jitter: 5,
    totalTests: 2160,
    lastTestTime: '2024-01-15 14:28:15'
  },
  {
    key: '4',
    taskName: 'Ping本地网关',
    target: '192.168.1.1',
    region: '本地',
    avgLatency: 2,
    packetLoss: 0.0,
    jitter: 1,
    totalTests: 1800,
    lastTestTime: '2024-01-15 14:27:30'
  }
])

// 方法
const handleTimeRangeChange = (value) => {
  refreshData()
}

const handleTaskChange = (value) => {
  refreshData()
}

const handleRegionChange = (value) => {
  refreshData()
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
  refreshData()
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
    await ExportUtils.quickExport('ping', 'excel', selectedTimeRange.value)
  } catch (error) {
    console.error('导出Ping报表失败:', error)
    message.error('导出Ping报表失败，请稍后重试')
  }
}

const viewTaskDetail = (record) => {
  message.info(`查看任务详情: ${record.taskName}`)
}

const viewTaskTrend = (record) => {
  message.info(`查看趋势分析: ${record.taskName}`)
}

// 初始化延迟趋势图
const initLatencyTrendChart = () => {
  if (!latencyTrendChart.value) return
  
  latencyTrendChartInstance = echarts.init(latencyTrendChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
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
        name: '平均延迟',
        type: 'line',
        data: [28, 25, 32, 30, 35, 29, 27],
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
        data: [15, 12, 18, 16, 20, 14, 13],
        smooth: true,
        itemStyle: { color: '#52c41a' },
        lineStyle: { type: 'dashed' }
      },
      {
        name: '最大延迟',
        type: 'line',
        data: [45, 42, 58, 52, 68, 48, 46],
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
  
  packetLossChartInstance = echarts.init(packetLossChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
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
        name: '丢包率',
        type: 'bar',
        data: [
          { value: 1.2, itemStyle: { color: '#52c41a' } },
          { value: 0.8, itemStyle: { color: '#52c41a' } },
          { value: 2.1, itemStyle: { color: '#faad14' } },
          { value: 1.5, itemStyle: { color: '#52c41a' } },
          { value: 3.2, itemStyle: { color: '#ff7a45' } },
          { value: 1.0, itemStyle: { color: '#52c41a' } },
          { value: 0.9, itemStyle: { color: '#52c41a' } }
        ]
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
  
  latencyDistributionChartInstance = echarts.init(latencyDistributionChart.value)
  
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
        data: [
          { value: 35, name: '0-20ms', itemStyle: { color: '#52c41a' } },
          { value: 30, name: '20-50ms', itemStyle: { color: '#1890ff' } },
          { value: 20, name: '50-100ms', itemStyle: { color: '#faad14' } },
          { value: 10, name: '100-200ms', itemStyle: { color: '#ff7a45' } },
          { value: 5, name: '>200ms', itemStyle: { color: '#ff4d4f' } }
        ],
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
  
  jitterAnalysisChartInstance = echarts.init(jitterAnalysisChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
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
        name: '抖动值',
        type: 'line',
        data: [12, 8, 18, 15, 25, 10, 9],
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
        data: [20, 20, 20, 20, 20, 20, 20],
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
  
  geographicChartInstance = echarts.init(geographicChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
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
      data: ['本地网关', '国内DNS', '国内网站', '亚洲服务器', '欧洲服务器', '美洲服务器']
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
        data: [2, 18, 25, 120, 180, 220],
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '丢包率',
        type: 'line',
        yAxisIndex: 1,
        data: [0.0, 0.2, 0.5, 1.8, 3.2, 4.5],
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

onMounted(() => {
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