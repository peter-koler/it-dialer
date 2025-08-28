<template>
  <div class="http-report">
    <a-page-header title="HTTP专项报表" sub-title="HTTP请求性能专项分析" />
    
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
              <a-select-option v-for="task in httpTasks" :key="task.id" :value="task.id">
                {{ task.name }}
              </a-select-option>
            </a-select>
          </a-space>
        </a-col>
        <a-col :span="4">
          <a-space>
            <span>状态码筛选：</span>
            <a-select v-model:value="selectedStatusCode" style="width: 120px;" @change="handleStatusCodeChange">
              <a-select-option value="all">全部状态码</a-select-option>
              <a-select-option value="2xx">2xx成功</a-select-option>
              <a-select-option value="4xx">4xx客户端错误</a-select-option>
              <a-select-option value="5xx">5xx服务器错误</a-select-option>
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

    <!-- HTTP关键指标 -->
    <a-row :gutter="16" class="metrics-cards">
      <a-col :span="6" v-for="metric in httpMetrics" :key="metric.key">
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
      <!-- HTTP响应时间趋势 -->
      <a-col :span="12">
        <a-card title="HTTP响应时间趋势" :bordered="false">
          <div ref="responseTimeChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
      
      <!-- HTTP状态码分布 -->
      <a-col :span="12">
        <a-card title="HTTP状态码分布" :bordered="false">
          <div ref="statusCodeChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 性能分析 -->
    <a-row :gutter="16" class="chart-section">
      <a-col :span="24">
        <a-card title="HTTP性能分析" :bordered="false">
          <a-tabs v-model:activeKey="activePerformanceTab" @change="handlePerformanceTabChange">
            <a-tab-pane key="response-breakdown" tab="响应时间分解">
              <div ref="responseBreakdownChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="throughput-analysis" tab="吞吐量分析">
              <div ref="throughputChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="error-analysis" tab="错误分析">
              <div ref="errorAnalysisChart" style="height: 350px;"></div>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>

    <!-- HTTP任务详细列表 -->
    <a-row :gutter="16" class="table-section">
      <a-col :span="24">
        <a-card title="HTTP任务详细统计" :bordered="false">
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
                <a-tag :color="record.successRate >= 95 ? 'green' : record.successRate >= 80 ? 'orange' : 'red'">
                  {{ record.successRate >= 95 ? '正常' : record.successRate >= 80 ? '警告' : '异常' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'successRate'">
                <a-progress
                  :percent="record.successRate"
                  :status="record.successRate >= 95 ? 'success' : record.successRate >= 80 ? 'active' : 'exception'"
                  size="small"
                />
              </template>
              <template v-else-if="column.key === 'avgResponseTime'">
                <span :style="{ color: record.avgResponseTime > 2000 ? '#ff4d4f' : record.avgResponseTime > 1000 ? '#faad14' : '#52c41a' }">
                  {{ record.avgResponseTime }}ms
                </span>
              </template>
              <template v-else-if="column.key === 'statusCode'">
                <a-tag :color="getStatusCodeColor(record.mainStatusCode)">
                  {{ record.mainStatusCode }}
                </a-tag>
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
  GlobalOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'

// 筛选条件
const selectedTimeRange = ref('1d')
const selectedTask = ref('all')
const selectedStatusCode = ref('all')
const activePerformanceTab = ref('response-breakdown')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const totalTasks = ref(50)

// 图表引用
const responseTimeChart = ref(null)
const statusCodeChart = ref(null)
const responseBreakdownChart = ref(null)
const throughputChart = ref(null)
const errorAnalysisChart = ref(null)

// 图表实例
let responseTimeChartInstance = null
let statusCodeChartInstance = null
let responseBreakdownChartInstance = null
let throughputChartInstance = null
let errorAnalysisChartInstance = null

// HTTP任务列表
const httpTasks = ref([
  { id: 1, name: 'HTTP健康检查' },
  { id: 2, name: 'HTTP API测试' },
  { id: 3, name: 'HTTP文件下载' },
  { id: 4, name: 'HTTP登录页面' }
])

// HTTP关键指标
const httpMetrics = ref([
  {
    key: 'successRate',
    title: 'HTTP成功率',
    value: 92.5,
    suffix: '%',
    precision: 1,
    color: '#52c41a',
    icon: CheckCircleOutlined
  },
  {
    key: 'avgResponseTime',
    title: '平均响应时间',
    value: 285.6,
    suffix: 'ms',
    precision: 1,
    color: '#1890ff',
    icon: ClockCircleOutlined
  },
  {
    key: 'throughput',
    title: '平均吞吐量',
    value: 156.8,
    suffix: 'req/s',
    precision: 1,
    color: '#722ed1',
    icon: GlobalOutlined
  },
  {
    key: 'errorRate',
    title: 'HTTP错误率',
    value: 7.5,
    suffix: '%',
    precision: 1,
    color: '#ff4d4f',
    icon: WarningOutlined
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
    title: 'URL',
    dataIndex: 'url',
    key: 'url',
    width: 250,
    ellipsis: true
  },
  {
    title: '请求方法',
    dataIndex: 'method',
    key: 'method',
    width: 80
  },
  {
    title: '状态',
    key: 'status',
    width: 80
  },
  {
    title: '成功率',
    key: 'successRate',
    width: 120
  },
  {
    title: '平均响应时间',
    key: 'avgResponseTime',
    width: 120
  },
  {
    title: '主要状态码',
    key: 'statusCode',
    width: 100
  },
  {
    title: '总请求次数',
    dataIndex: 'totalRequests',
    key: 'totalRequests',
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
    taskName: 'HTTP健康检查',
    url: 'https://api.example.com/health',
    method: 'GET',
    successRate: 97.2,
    avgResponseTime: 150,
    mainStatusCode: '200',
    totalRequests: 2880,
    lastTestTime: '2024-01-15 14:30:25'
  },
  {
    key: '2',
    taskName: 'HTTP API测试',
    url: 'https://api.example.com/v1/users',
    method: 'POST',
    successRate: 89.5,
    avgResponseTime: 320,
    mainStatusCode: '201',
    totalRequests: 1440,
    lastTestTime: '2024-01-15 14:29:45'
  },
  {
    key: '3',
    taskName: 'HTTP文件下载',
    url: 'https://cdn.example.com/file.zip',
    method: 'GET',
    successRate: 85.3,
    avgResponseTime: 1200,
    mainStatusCode: '200',
    totalRequests: 720,
    lastTestTime: '2024-01-15 14:28:15'
  },
  {
    key: '4',
    taskName: 'HTTP登录页面',
    url: 'https://www.example.com/login',
    method: 'GET',
    successRate: 94.8,
    avgResponseTime: 280,
    mainStatusCode: '200',
    totalRequests: 1800,
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

const handleStatusCodeChange = (value) => {
  refreshData()
}

const handlePerformanceTabChange = (key) => {
  activePerformanceTab.value = key
  nextTick(() => {
    initPerformanceChart(key)
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
    await ExportUtils.quickExport('http', 'excel', selectedTimeRange.value)
  } catch (error) {
    console.error('导出HTTP报表失败:', error)
    message.error('导出HTTP报表失败，请稍后重试')
  }
}

const viewTaskDetail = (record) => {
  message.info(`查看任务详情: ${record.taskName}`)
}

const viewTaskTrend = (record) => {
  message.info(`查看趋势分析: ${record.taskName}`)
}

const getStatusCodeColor = (statusCode) => {
  if (statusCode.startsWith('2')) return 'green'
  if (statusCode.startsWith('3')) return 'blue'
  if (statusCode.startsWith('4')) return 'orange'
  if (statusCode.startsWith('5')) return 'red'
  return 'default'
}

// 初始化响应时间趋势图
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
      data: ['平均响应时间', '95%分位数', '99%分位数']
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
        name: '平均响应时间',
        type: 'line',
        data: [280, 250, 320, 300, 350, 290, 270],
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
        name: '95%分位数',
        type: 'line',
        data: [450, 420, 520, 480, 580, 460, 440],
        smooth: true,
        itemStyle: { color: '#faad14' },
        lineStyle: { type: 'dashed' }
      },
      {
        name: '99%分位数',
        type: 'line',
        data: [680, 650, 780, 720, 850, 690, 670],
        smooth: true,
        itemStyle: { color: '#ff4d4f' },
        lineStyle: { type: 'dashed' }
      }
    ]
  }
  
  responseTimeChartInstance.setOption(option)
}

// 初始化状态码分布图
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
          { value: 5, name: '201 Created', itemStyle: { color: '#1890ff' } },
          { value: 3, name: '301 Moved', itemStyle: { color: '#722ed1' } },
          { value: 4, name: '404 Not Found', itemStyle: { color: '#faad14' } },
          { value: 2, name: '500 Server Error', itemStyle: { color: '#ff4d4f' } },
          { value: 1, name: '其他', itemStyle: { color: '#d9d9d9' } }
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

// 初始化性能图表
const initPerformanceChart = (type) => {
  switch (type) {
    case 'response-breakdown':
      initResponseBreakdownChart()
      break
    case 'throughput-analysis':
      initThroughputChart()
      break
    case 'error-analysis':
      initErrorAnalysisChart()
      break
  }
}

// 初始化响应时间分解图表
const initResponseBreakdownChart = () => {
  if (!responseBreakdownChart.value) return
  
  responseBreakdownChartInstance = echarts.init(responseBreakdownChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['DNS解析', 'TCP连接', 'SSL握手', '请求发送', '等待响应', '内容下载']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['健康检查', 'API测试', '文件下载', '登录页面']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}ms'
      }
    },
    series: [
      {
        name: 'DNS解析',
        type: 'bar',
        stack: 'total',
        data: [15, 18, 12, 16],
        itemStyle: { color: '#ff7a45' }
      },
      {
        name: 'TCP连接',
        type: 'bar',
        stack: 'total',
        data: [25, 30, 28, 26],
        itemStyle: { color: '#1890ff' }
      },
      {
        name: 'SSL握手',
        type: 'bar',
        stack: 'total',
        data: [35, 40, 38, 36],
        itemStyle: { color: '#722ed1' }
      },
      {
        name: '请求发送',
        type: 'bar',
        stack: 'total',
        data: [5, 8, 6, 7],
        itemStyle: { color: '#faad14' }
      },
      {
        name: '等待响应',
        type: 'bar',
        stack: 'total',
        data: [45, 120, 800, 150],
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '内容下载',
        type: 'bar',
        stack: 'total',
        data: [25, 104, 318, 45],
        itemStyle: { color: '#13c2c2' }
      }
    ]
  }
  
  responseBreakdownChartInstance.setOption(option)
}

// 初始化吞吐量图表
const initThroughputChart = () => {
  if (!throughputChart.value) return
  
  throughputChartInstance = echarts.init(throughputChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['请求数/秒', '响应数/秒', '错误数/秒']
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
        formatter: '{value}/s'
      }
    },
    series: [
      {
        name: '请求数/秒',
        type: 'line',
        data: [150, 120, 180, 200, 220, 160, 140],
        smooth: true,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '响应数/秒',
        type: 'line',
        data: [145, 115, 175, 185, 200, 150, 135],
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '错误数/秒',
        type: 'line',
        data: [5, 5, 5, 15, 20, 10, 5],
        smooth: true,
        itemStyle: { color: '#ff4d4f' }
      }
    ]
  }
  
  throughputChartInstance.setOption(option)
}

// 初始化错误分析图表
const initErrorAnalysisChart = () => {
  if (!errorAnalysisChart.value) return
  
  errorAnalysisChartInstance = echarts.init(errorAnalysisChart.value)
  
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
        name: 'HTTP错误类型',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 40, name: '连接超时', itemStyle: { color: '#ff4d4f' } },
          { value: 25, name: '404未找到', itemStyle: { color: '#faad14' } },
          { value: 15, name: '500服务器错误', itemStyle: { color: '#ff7a45' } },
          { value: 10, name: '403禁止访问', itemStyle: { color: '#722ed1' } },
          { value: 6, name: '502网关错误', itemStyle: { color: '#eb2f96' } },
          { value: 4, name: '其他错误', itemStyle: { color: '#d9d9d9' } }
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
  
  errorAnalysisChartInstance.setOption(option)
}

// 初始化所有图表
const initAllCharts = () => {
  nextTick(() => {
    initResponseTimeChart()
    initStatusCodeChart()
    initPerformanceChart(activePerformanceTab.value)
  })
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  responseTimeChartInstance?.resize()
  statusCodeChartInstance?.resize()
  responseBreakdownChartInstance?.resize()
  throughputChartInstance?.resize()
  errorAnalysisChartInstance?.resize()
}

onMounted(() => {
  initAllCharts()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
const cleanup = () => {
  window.removeEventListener('resize', handleResize)
  responseTimeChartInstance?.dispose()
  statusCodeChartInstance?.dispose()
  responseBreakdownChartInstance?.dispose()
  throughputChartInstance?.dispose()
  errorAnalysisChartInstance?.dispose()
}

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(cleanup)
</script>

<style scoped>
.http-report {
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