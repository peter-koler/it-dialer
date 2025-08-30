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
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getHttpReport } from '@/api/reports'
import request from '@/utils/request'
import {
  SyncOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'

// 筛选条件
const selectedTimeRange = ref('1d')
const selectedTask = ref('all')
const selectedStatusCode = ref('all')
const activePerformanceTab = ref('response-breakdown')

// 加载状态
const loading = ref(false)

// 图表数据存储
const chartData = ref({
  responseTimeTrend: [],
  statusCodeDistribution: [],
  taskList: [],
  performanceMetrics: {}
})

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
const httpTasks = ref([])

// HTTP关键指标
const httpMetrics = ref([
  {
    key: 'successRate',
    title: 'HTTP成功率',
    value: 0,
    suffix: '%',
    precision: 1,
    color: '#52c41a',
    icon: CheckCircleOutlined
  },
  {
    key: 'avgResponseTime',
    title: '平均响应时间',
    value: 0,
    suffix: 'ms',
    precision: 1,
    color: '#1890ff',
    icon: ClockCircleOutlined
  },
  {
    key: 'throughput',
    title: '平均吞吐量',
    value: 0,
    suffix: 'req/s',
    precision: 1,
    color: '#722ed1',
    icon: GlobalOutlined
  },
  {
    key: 'errorRate',
    title: 'HTTP错误率',
    value: 0,
    suffix: '%',
    precision: 1,
    color: '#ff4d4f',
    icon: WarningOutlined
  }
])

// 获取HTTP任务列表
const fetchHttpTasks = async () => {
  try {
    const response = await request.get('/tasks', {
      params: { task_type: 'http' }
    })
    // 处理API返回格式: {code: 0, data: {list: [...], total: N}, message: ""}
    if (response && response.code === 0 && response.data) {
      if (Array.isArray(response.data.list)) {
        // v1 API格式: data.list
        httpTasks.value = response.data.list.map(task => ({
          id: task.id,
          name: task.name
        }))
      } else if (Array.isArray(response.data)) {
        // v2 API格式: data直接是数组
        httpTasks.value = response.data.map(task => ({
          id: task.id,
          name: task.name
        }))
      } else {
        console.warn('HTTP任务数据格式不正确:', response)
        httpTasks.value = []
      }
    } else if (response.data && response.data.tasks && Array.isArray(response.data.tasks)) {
      // 兼容旧格式 {data: {tasks: [...]}}
      httpTasks.value = response.data.tasks.map(task => ({
        id: task.id,
        name: task.name
      }))
    } else {
      console.warn('HTTP任务数据格式不正确:', response)
      httpTasks.value = []
    }
  } catch (error) {
    console.error('获取HTTP任务列表失败:', error)
    message.error('获取HTTP任务列表失败')
    httpTasks.value = []
  }
}

// 获取HTTP指标数据
const fetchHttpMetrics = async () => {
  try {
    const params = {
      time_range: selectedTimeRange.value
    }
    if (selectedTask.value !== 'all') {
      params.task_id = selectedTask.value
    }
    if (selectedStatusCode.value !== 'all') {
      params.status_code = selectedStatusCode.value
    }
    
    const response = await getHttpReport(params)
    if (response.data && response.data.metrics) {
      const metrics = response.data.metrics
      httpMetrics.value[0].value = metrics.success_rate || 0
      httpMetrics.value[1].value = metrics.avg_response_time || 0
      httpMetrics.value[2].value = metrics.throughput || 0
      httpMetrics.value[3].value = metrics.error_rate || 0
    }
  } catch (error) {
    console.error('获取HTTP指标数据失败:', error)
    message.error('获取HTTP指标数据失败')
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
const taskTableData = ref([])

// 获取HTTP报表数据
const fetchHttpReportData = async () => {
  loading.value = true
  try {
    const params = {
      time_range: selectedTimeRange.value
    }
    if (selectedTask.value !== 'all') {
      params.task_id = selectedTask.value
    }
    if (selectedStatusCode.value !== 'all') {
      params.status_code = selectedStatusCode.value
    }
    
    const response = await request.get('/reports/http', { params })
    
    // 处理新的API响应格式 {code: 0, data: {...}}
    let reportData = null
    if (response && response.code === 0 && response.data) {
      reportData = response.data
    } else if (response && response.data) {
      // 兼容旧格式
      reportData = response.data
    }
    
    if (reportData) {
      const data = reportData
      
      // 更新指标数据
      if (data.metrics) {
        const metrics = data.metrics
        httpMetrics.value[0].value = metrics.success_rate || 0
        httpMetrics.value[1].value = metrics.avg_response_time || 0
        httpMetrics.value[2].value = metrics.total_requests || 0  // v2 API返回total_requests而不是throughput
        httpMetrics.value[3].value = metrics.failure_rate || 0   // v2 API返回failure_rate而不是error_rate
      }
      
      // 更新表格数据
      if (data.task_list) {
        taskTableData.value = data.task_list.map((task, index) => ({
          key: task.task_id || index.toString(),
          taskName: task.task_name || task.name,
          url: task.target_url || '-',  // v2 API返回target_url
          method: task.method || 'GET',
          successRate: task.success_rate || 0,
          avgResponseTime: task.avg_response_time || 0,
          mainStatusCode: task.main_status_code || '200',
          totalRequests: task.total_requests || 0,
          lastTestTime: task.last_execution_time || '-'  // v2 API返回last_execution_time
        }))
        totalTasks.value = taskTableData.value.length
      }
      
      // 更新图表数据
      updateChartData(data)
      
      // 重新初始化图表
      nextTick(() => {
        initAllCharts()
      })
    } else {
      console.warn('HTTP报表数据格式不正确:', response)
    }
  } catch (error) {
    console.error('获取HTTP报表数据失败:', error)
    message.error('获取HTTP报表数据失败')
  } finally {
    loading.value = false
  }
}

// 更新图表数据
const updateChartData = (data) => {
  // v2 API返回response_time_trend而不是trend_data
  if (data.response_time_trend) {
    chartData.value.responseTimeTrend = data.response_time_trend
  }
  // 从response_time_trend中提取状态码分布数据
  if (data.response_time_trend) {
    // 简化处理：从趋势数据中生成状态码分布
    const statusCodes = { '200': 0, '404': 0, '500': 0, 'others': 0 }
    data.response_time_trend.forEach(item => {
      statusCodes['200'] += item.success || 0
      statusCodes['500'] += (item.total - item.success) || 0
    })
    chartData.value.statusCodeDistribution = Object.entries(statusCodes).map(([code, count]) => ({
      status_code: code,
      count: count
    }))
  }
  if (data.task_list) {
    chartData.value.taskList = data.task_list
  }
  // 从metrics中生成性能指标数据
  if (data.metrics) {
    chartData.value.performanceMetrics = {
      response_time: data.metrics.avg_response_time || 0,
      success_rate: data.metrics.success_rate || 0,
      total_requests: data.metrics.total_requests || 0,
      // 响应时间分解数据
      responseBreakdown: data.response_breakdown || data.performance_breakdown || [
        { task_name: '示例任务', dns_time: 10, tcp_time: 20, ssl_time: 30, request_time: 5, wait_time: 100, download_time: 50 }
      ],
      // 吞吐量分析数据
      throughputAnalysis: data.throughput_analysis || (data.response_time_trend || []).map(item => ({
        time: item.time || item.timestamp,
        requests_per_second: item.total || 0,
        responses_per_second: item.success || 0,
        errors_per_second: (item.total - item.success) || 0
      })),
      // 错误分析数据
      errorAnalysis: data.error_analysis || [
        { error_type: '连接超时', count: 0 },
        { error_type: '服务器错误', count: 0 },
        { error_type: '网络错误', count: 0 }
      ]
    }
  }
}

// 方法
const handleTimeRangeChange = (value) => {
  fetchHttpReportData()
}

const handleTaskChange = (value) => {
  fetchHttpReportData()
}

const handleStatusCodeChange = (value) => {
  fetchHttpReportData()
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
  fetchHttpReportData()
}

const refreshData = async () => {
  await fetchHttpReportData()
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

const router = useRouter()

const viewTaskDetail = (record) => {
  // 跳转到HTTP任务结果列表页面
  if (record.key) {
    router.push(`/task-management/http-result/${record.key}`)
  } else {
    message.error('任务ID不存在，无法查看详情')
  }
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
  
  const trendData = chartData.value.responseTimeTrend || []
  
  if (trendData.length === 0) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    responseTimeChartInstance.setOption(option)
    return
  }
  
  const timeLabels = trendData.map(item => item.time_label || item.time)
  const avgResponseTimes = trendData.map(item => item.avg_response_time || 0)
  const p95ResponseTimes = trendData.map(item => item.p95_response_time || 0)
  const p99ResponseTimes = trendData.map(item => item.p99_response_time || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = params[0].axisValue + '<br/>'
        params.forEach(param => {
          result += param.marker + param.seriesName + ': ' + param.value + 'ms<br/>'
        })
        return result
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
        name: '平均响应时间',
        type: 'line',
        data: avgResponseTimes,
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
        data: p95ResponseTimes,
        smooth: true,
        itemStyle: { color: '#faad14' },
        lineStyle: { type: 'dashed' }
      },
      {
        name: '99%分位数',
        type: 'line',
        data: p99ResponseTimes,
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
  
  const statusCodeData = chartData.value.statusCodeDistribution || []
  
  if (statusCodeData.length === 0) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    statusCodeChartInstance.setOption(option)
    return
  }
  
  const pieData = statusCodeData.map(item => ({
    value: item.count || item.value,
    name: item.status_code || item.name,
    itemStyle: { color: getStatusCodeColor(item.status_code || item.name) }
  }))
  
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
        data: pieData,
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
  
  // 销毁已存在的实例
  if (responseBreakdownChartInstance) {
    responseBreakdownChartInstance.dispose()
    responseBreakdownChartInstance = null
  }
  
  responseBreakdownChartInstance = echarts.init(responseBreakdownChart.value)
  
  // 检查数据是否存在
  const breakdownData = chartData.value.performanceMetrics?.responseBreakdown || []
  if (!breakdownData.length) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    responseBreakdownChartInstance.setOption(option)
    return
  }
  
  const taskNames = breakdownData.map(item => item.task_name || item.name)
  const dnsData = breakdownData.map(item => item.dns_time || 0)
  const tcpData = breakdownData.map(item => item.tcp_time || 0)
  const sslData = breakdownData.map(item => item.ssl_time || 0)
  const requestData = breakdownData.map(item => item.request_time || 0)
  const waitData = breakdownData.map(item => item.wait_time || 0)
  const downloadData = breakdownData.map(item => item.download_time || 0)
  
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
      data: taskNames
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
        data: dnsData,
        itemStyle: { color: '#ff7a45' }
      },
      {
        name: 'TCP连接',
        type: 'bar',
        stack: 'total',
        data: tcpData,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: 'SSL握手',
        type: 'bar',
        stack: 'total',
        data: sslData,
        itemStyle: { color: '#722ed1' }
      },
      {
        name: '请求发送',
        type: 'bar',
        stack: 'total',
        data: requestData,
        itemStyle: { color: '#faad14' }
      },
      {
        name: '等待响应',
        type: 'bar',
        stack: 'total',
        data: waitData,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '内容下载',
        type: 'bar',
        stack: 'total',
        data: downloadData,
        itemStyle: { color: '#13c2c2' }
      }
    ]
  }
  
  responseBreakdownChartInstance.setOption(option)
}

// 初始化吞吐量图表
const initThroughputChart = () => {
  if (!throughputChart.value) return
  
  // 销毁已存在的实例
  if (throughputChartInstance) {
    throughputChartInstance.dispose()
    throughputChartInstance = null
  }
  
  throughputChartInstance = echarts.init(throughputChart.value)
  
  // 检查数据是否存在
  const throughputData = chartData.value.performanceMetrics?.throughputAnalysis || []
  if (!throughputData.length) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    throughputChartInstance.setOption(option)
    return
  }
  
  const timeLabels = throughputData.map(item => item.time || item.timestamp)
  const requestData = throughputData.map(item => item.requests_per_second || 0)
  const responseData = throughputData.map(item => item.responses_per_second || 0)
  const errorData = throughputData.map(item => item.errors_per_second || 0)
  
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
      data: timeLabels
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
        data: requestData,
        smooth: true,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '响应数/秒',
        type: 'line',
        data: responseData,
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '错误数/秒',
        type: 'line',
        data: errorData,
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
  
  // 销毁已存在的实例
  if (errorAnalysisChartInstance) {
    errorAnalysisChartInstance.dispose()
    errorAnalysisChartInstance = null
  }
  
  errorAnalysisChartInstance = echarts.init(errorAnalysisChart.value)
  
  // 检查数据是否存在
  const errorData = chartData.value.performanceMetrics?.errorAnalysis || []
  if (!errorData.length) {
    const option = {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999',
          fontSize: 14
        }
      }
    }
    errorAnalysisChartInstance.setOption(option)
    return
  }
  
  const pieData = errorData.map((item, index) => {
    const colors = ['#ff4d4f', '#faad14', '#ff7a45', '#722ed1', '#eb2f96', '#d9d9d9']
    return {
      value: item.count || item.value,
      name: item.error_type || item.name,
      itemStyle: { color: colors[index % colors.length] }
    }
  })
  
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
        data: pieData,
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

onMounted(async () => {
  await fetchHttpTasks()
  await fetchHttpReportData()
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