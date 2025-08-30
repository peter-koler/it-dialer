<template>
  <div class="tcp-report">
    <a-page-header title="TCP专项报表" sub-title="TCP连接性能专项分析" />
    
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
              <a-select-option v-for="task in tcpTasks" :key="task.id" :value="task.id">
                {{ task.name }}
              </a-select-option>
            </a-select>
          </a-space>
        </a-col>
        <a-col :span="4">
          <a-space>
            <span>端口筛选：</span>
            <a-select v-model:value="selectedPort" style="width: 120px;" @change="handlePortChange">
              <a-select-option value="all">全部端口</a-select-option>
              <a-select-option value="80">80</a-select-option>
              <a-select-option value="443">443</a-select-option>
              <a-select-option value="3306">3306</a-select-option>
              <a-select-option value="8080">8080</a-select-option>
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

    <!-- TCP关键指标 -->
    <a-row :gutter="16" class="metrics-cards">
      <a-col :span="6" v-for="metric in tcpMetrics" :key="metric.key">
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
      <!-- TCP连接成功率趋势 -->
      <a-col :span="12">
        <a-card title="TCP连接成功率趋势" :bordered="false">
          <div ref="successRateChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
      
      <!-- TCP连接时间分布 -->
      <a-col :span="12">
        <a-card title="TCP连接时间分布" :bordered="false">
          <div ref="connectionTimeChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 端口连通性分析 -->
    <a-row :gutter="16" class="chart-section">
      <a-col :span="24">
        <a-card title="端口连通性分析" :bordered="false">
          <a-tabs v-model:activeKey="activePortTab" @change="handlePortTabChange">
            <a-tab-pane key="port-success" tab="端口成功率统计">
              <div ref="portSuccessChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="port-response" tab="端口响应时间对比">
              <div ref="portResponseChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="error-analysis" tab="连接错误分析">
              <div ref="errorAnalysisChart" style="height: 350px;"></div>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>

    <!-- TCP任务详细列表 -->
    <a-row :gutter="16" class="table-section">
      <a-col :span="24">
        <a-card title="TCP任务详细统计" :bordered="false">
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
                <span :style="{ color: record.avgResponseTime > 1000 ? '#ff4d4f' : record.avgResponseTime > 500 ? '#faad14' : '#52c41a' }">
                  {{ record.avgResponseTime }}ms
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
import {
  SyncOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  LinkOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'
import { getTasks } from '@/api/task'
import { getTcpReport } from '@/api/reports'

// 筛选条件
const selectedTimeRange = ref('1d')
const selectedTask = ref('all')
const selectedPort = ref('all')
const activePortTab = ref('port-success')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const totalTasks = ref(50)

// 数据状态
const loading = ref(false)
const chartData = ref({
  successRateTrend: { times: [], successRates: [], targetRates: [] },
  connectionTimeDistribution: [],
  portAnalysis: {
    portSuccess: { ports: [], successRates: [] },
    portResponse: { ports: [], avgTimes: [], maxTimes: [] },
    errorAnalysis: []
  }
})

// 图表引用
const successRateChart = ref(null)
const connectionTimeChart = ref(null)
const portSuccessChart = ref(null)
const portResponseChart = ref(null)
const errorAnalysisChart = ref(null)

// 图表实例
let successRateChartInstance = null
let connectionTimeChartInstance = null
let portSuccessChartInstance = null
let portResponseChartInstance = null
let errorAnalysisChartInstance = null

// TCP任务列表
const tcpTasks = ref([])

// 获取TCP任务列表
const fetchTcpTasks = async () => {
  try {
    const response = await getTasks({ task_type: 'tcp' })
    // 处理API返回格式: {code: 0, data: {list: [...], total: N}, message: ""}
    if (response && response.code === 0 && response.data) {
      if (Array.isArray(response.data.list)) {
        // v1 API格式: data.list
        tcpTasks.value = response.data.list.map(task => ({
          id: task.id,
          name: task.name
        }))
      } else if (Array.isArray(response.data)) {
        // v2 API格式: data直接是数组
        tcpTasks.value = response.data.map(task => ({
          id: task.id,
          name: task.name
        }))
      } else {
        console.warn('TCP任务数据格式不正确:', response)
        tcpTasks.value = []
      }
    } else if (response && Array.isArray(response.data)) {
      // 兼容直接返回data数组的情况
      tcpTasks.value = response.data.map(task => ({
        id: task.id,
        name: task.name
      }))
    } else {
      console.warn('TCP任务数据格式不正确:', response)
      tcpTasks.value = []
    }
  } catch (error) {
    console.error('获取TCP任务列表失败:', error)
    message.error('获取TCP任务列表失败')
    tcpTasks.value = []
  }
}

// 获取TCP报表数据
const fetchTcpReportData = async () => {
  loading.value = true
  try {
    const params = {
      task_type: 'tcp',
      time_range: selectedTimeRange.value,
      task_id: selectedTask.value !== 'all' ? selectedTask.value : undefined,
      port: selectedPort.value !== 'all' ? selectedPort.value : undefined
    }
    
    const response = await getTcpReport(params)
    if (response && response.data) {
      // 处理TCP报表数据
      processTcpReportData(response.data)
    }
  } catch (error) {
    console.error('获取TCP报表数据失败:', error)
    message.error('获取TCP报表数据失败')
  } finally {
    loading.value = false
  }
}

// 处理TCP报表数据
const processTcpReportData = (data) => {
  // 更新关键指标
  if (data.metrics) {
    tcpMetrics.value[0].value = data.metrics.success_rate || 0
    tcpMetrics.value[1].value = data.metrics.avg_connect_time || 0
    tcpMetrics.value[2].value = data.metrics.total_connections || 0
    tcpMetrics.value[3].value = data.metrics.failure_rate || 0
  }
  
  // 处理连接时间趋势数据（v2 API返回connect_time_trend）
  if (data.connect_time_trend) {
    chartData.value.successRateTrend = {
      times: data.connect_time_trend.map(item => item.time),
      successRates: data.connect_time_trend.map(item => item.success_rate),
      targetRates: data.connect_time_trend.map(() => 98) // 目标成功率
    }
    
    // 处理连接时间分布数据（从趋势数据中提取）
    const timeRanges = ['0-50ms', '50-100ms', '100-200ms', '200-500ms', '500ms+']
    const timeCounts = [0, 0, 0, 0, 0]
    
    data.connect_time_trend.forEach(item => {
      const avgTime = item.avg_connect_time || 0
      if (avgTime <= 50) timeCounts[0]++
      else if (avgTime <= 100) timeCounts[1]++
      else if (avgTime <= 200) timeCounts[2]++
      else if (avgTime <= 500) timeCounts[3]++
      else timeCounts[4]++
    })
    
    chartData.value.connectionTimeDistribution = timeRanges.map((range, index) => ({
      range: range,
      count: timeCounts[index]
    }))
  }
  
  // 处理任务列表数据
  if (data.task_list) {
    taskTableData.value = data.task_list.map(task => ({
      key: task.task_id,
      taskName: task.task_name,
      target: task.target_address,
      port: task.target_address ? task.target_address.split(':')[1] : 'N/A',
      status: task.success_rate > 80 ? 'success' : 'warning',
      successRate: task.success_rate,
      avgResponseTime: task.avg_connect_time,
      totalTests: task.total_connections,
      lastTestTime: task.last_execution_time
    }))
  }
  
  // 处理端口分析数据（从任务列表中提取）
  if (data.task_list) {
    const portMap = new Map()
    data.task_list.forEach(task => {
      const port = task.target_address ? task.target_address.split(':')[1] : 'unknown'
      if (!portMap.has(port)) {
        portMap.set(port, { total: 0, success: 0, avgTime: 0, count: 0 })
      }
      const portData = portMap.get(port)
      portData.total += task.total_connections
      portData.success += Math.round(task.total_connections * task.success_rate / 100)
      portData.avgTime += task.avg_connect_time
      portData.count++
    })
    
    const portAnalysis = []
    portMap.forEach((data, port) => {
      portAnalysis.push({
        port: port,
        success_rate: data.total > 0 ? (data.success / data.total * 100) : 0,
        avg_response_time: data.count > 0 ? (data.avgTime / data.count) : 0,
        total_tests: data.total
      })
    })
    
    // 设置端口分析数据结构
    chartData.value.portAnalysis = {
      portSuccess: {
        ports: portAnalysis.map(item => item.port),
        successRates: portAnalysis.map(item => item.success_rate)
      },
      portResponse: {
        ports: portAnalysis.map(item => item.port),
        avgTimes: portAnalysis.map(item => item.avg_response_time),
        maxTimes: portAnalysis.map(item => item.avg_response_time * 1.2) // 模拟最大时间
      },
      errorAnalysis: []
    }
  }
  
  // 处理连接时间分布数据（如果v2 API有专门的字段）
  if (data.connection_time_distribution) {
    chartData.value.connectionTimeDistribution = data.connection_time_distribution
  }
  
  // 如果v2 API有专门的端口分析数据，则覆盖上面的计算结果
  if (data.port_analysis) {
    if (data.port_analysis.port_success) {
      chartData.value.portAnalysis.portSuccess = {
        ports: data.port_analysis.port_success.map(item => item.port),
        successRates: data.port_analysis.port_success.map(item => item.success_rate)
      }
    }
    if (data.port_analysis.port_response) {
      chartData.value.portAnalysis.portResponse = {
        ports: data.port_analysis.port_response.map(item => item.port),
        avgTimes: data.port_analysis.port_response.map(item => item.avg_time),
        maxTimes: data.port_analysis.port_response.map(item => item.max_time) || []
      }
    }
    if (data.port_analysis.error_analysis) {
      chartData.value.portAnalysis.errorAnalysis = data.port_analysis.error_analysis
    }
  }
  
  // 更新表格数据
  if (data.task_details) {
    taskTableData.value = data.task_details.map(task => ({
      key: task.id.toString(),
      taskName: task.name,
      target: task.target,
      port: task.port,
      successRate: task.success_rate,
      avgResponseTime: task.avg_response_time,
      totalTests: task.total_tests,
      lastTestTime: task.last_test_time
    }))
  }
  
  // 更新关键指标
  if (data.metrics) {
    tcpMetrics.value = [
      {
        key: 'successRate',
        title: '总体连接成功率',
        value: data.metrics.overall_success_rate || 0,
        suffix: '%',
        precision: 1,
        color: '#52c41a',
        icon: CheckCircleOutlined
      },
      {
        key: 'avgConnectionTime',
        title: '平均连接时间',
        value: data.metrics.avg_connection_time || 0,
        suffix: 'ms',
        precision: 1,
        color: '#1890ff',
        icon: ClockCircleOutlined
      },
      {
        key: 'totalConnections',
        title: '总连接次数',
        value: data.metrics.total_connections || 0,
        suffix: '',
        precision: 0,
        color: '#722ed1',
        icon: LinkOutlined
      },
      {
        key: 'errorRate',
        title: '连接错误率',
        value: data.metrics.error_rate || 0,
        suffix: '%',
        precision: 1,
        color: '#ff4d4f',
        icon: WarningOutlined
      }
    ]
  }
  
  // 重新初始化图表
  nextTick(() => {
    initAllCharts()
  })
}

// TCP关键指标
const tcpMetrics = ref([
  {
    key: 'successRate',
    title: '总体连接成功率',
    value: 0,
    suffix: '%',
    precision: 1,
    color: '#52c41a',
    icon: CheckCircleOutlined
  },
  {
    key: 'avgConnectionTime',
    title: '平均连接时间',
    value: 0,
    suffix: 'ms',
    precision: 1,
    color: '#1890ff',
    icon: ClockCircleOutlined
  },
  {
    key: 'totalConnections',
    title: '总连接次数',
    value: 0,
    suffix: '',
    precision: 0,
    color: '#722ed1',
    icon: LinkOutlined
  },
  {
    key: 'errorRate',
    title: '连接错误率',
    value: 0,
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
    title: '目标地址',
    dataIndex: 'target',
    key: 'target',
    width: 200
  },
  {
    title: '端口',
    dataIndex: 'port',
    key: 'port',
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

// 方法
const handleTimeRangeChange = (value) => {
  fetchTcpReportData()
}

const handleTaskChange = (value) => {
  fetchTcpReportData()
}

const handlePortChange = (value) => {
  fetchTcpReportData()
}

const handlePortTabChange = (key) => {
  activePortTab.value = key
  nextTick(() => {
    initPortChart(key)
  })
}

const handleTableChange = (pagination) => {
  currentPage.value = pagination.current
  pageSize.value = pagination.pageSize
  fetchTcpReportData()
}

const refreshData = async () => {
  message.loading('正在刷新数据...', 1)
  await fetchTcpReportData()
  message.success('数据刷新完成')
}

const exportReport = async () => {
  try {
    message.loading('正在导出报表...', 0)
    
    // 获取最新数据
    await fetchTcpReportData()
    
    const { ExportUtils } = await import('@/utils/exportUtils')
    await ExportUtils.quickExport('tcp', 'excel', selectedTimeRange.value)
    
    message.destroy()
    message.success('报表导出成功')
  } catch (error) {
    message.destroy()
    console.error('导出TCP报表失败:', error)
    message.error('导出TCP报表失败，请稍后重试')
  }
}

const router = useRouter()

const viewTaskDetail = (record) => {
  // 跳转到TCP任务结果列表页面
  if (record.key) {
    router.push(`/task-management/tcp-result/${record.key}`)
  } else {
    message.error('任务ID不存在，无法查看详情')
  }
}

const viewTaskTrend = (record) => {
  message.info(`查看趋势分析: ${record.taskName}`)
}

// 初始化成功率趋势图
const initSuccessRateChart = () => {
  if (!successRateChart.value) return
  
  // 销毁已存在的实例
  if (successRateChartInstance) {
    successRateChartInstance.dispose()
    successRateChartInstance = null
  }
  
  successRateChartInstance = echarts.init(successRateChart.value)
  
  // 检查数据是否存在
  if (!chartData.value.successRateTrend.times.length) {
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
    successRateChartInstance.setOption(option)
    return
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = params[0].axisValue + '<br/>'
        params.forEach(param => {
          result += param.marker + param.seriesName + ': ' + param.value + '%<br/>'
        })
        return result
      }
    },
    legend: {
      data: ['连接成功率', '目标成功率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.successRateTrend.times
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '连接成功率',
        type: 'line',
        data: chartData.value.successRateTrend.successRates,
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
        name: '目标成功率',
        type: 'line',
        data: chartData.value.successRateTrend.targetRates,
        lineStyle: {
          type: 'dashed',
          color: '#52c41a'
        },
        itemStyle: { color: '#52c41a' }
      }
    ]
  }
  
  successRateChartInstance.setOption(option)
}

// 初始化连接时间分布图
const initConnectionTimeChart = () => {
  if (!connectionTimeChart.value) return
  
  // 销毁已存在的实例
  if (connectionTimeChartInstance) {
    connectionTimeChartInstance.dispose()
    connectionTimeChartInstance = null
  }
  
  connectionTimeChartInstance = echarts.init(connectionTimeChart.value)
  
  // 检查数据是否存在
  if (!chartData.value.connectionTimeDistribution.length) {
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
    connectionTimeChartInstance.setOption(option)
    return
  }
  
  // 为连接时间分布数据设置颜色
  const distributionData = chartData.value.connectionTimeDistribution.map(item => {
    let color = '#52c41a' // 默认绿色
    if (item.range.includes('50-100')) color = '#1890ff'
    else if (item.range.includes('100-200')) color = '#faad14'
    else if (item.range.includes('200-500')) color = '#ff7a45'
    else if (item.range.includes('>500') || item.range.includes('500+')) color = '#ff4d4f'
    
    return {
      name: item.range,
      value: item.count,
      itemStyle: { color }
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
        name: '连接时间分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        data: distributionData,
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
  
  connectionTimeChartInstance.setOption(option)
}

// 初始化端口图表
const initPortChart = (type) => {
  switch (type) {
    case 'port-success':
      initPortSuccessChart()
      break
    case 'port-response':
      initPortResponseChart()
      break
    case 'error-analysis':
      initErrorAnalysisChart()
      break
  }
}

// 初始化端口成功率图表
const initPortSuccessChart = () => {
  if (!portSuccessChart.value) return
  
  // 销毁已存在的实例
  if (portSuccessChartInstance) {
    portSuccessChartInstance.dispose()
    portSuccessChartInstance = null
  }
  
  portSuccessChartInstance = echarts.init(portSuccessChart.value)
  
  // 检查数据是否存在
  if (!chartData.value.portAnalysis.portSuccess.ports.length) {
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
    portSuccessChartInstance.setOption(option)
    return
  }
  
  // 根据成功率设置颜色
  const successRateData = chartData.value.portAnalysis.portSuccess.successRates.map(rate => {
    let color = '#52c41a' // 绿色 >= 95%
    if (rate < 85) color = '#ff4d4f' // 红色 < 85%
    else if (rate < 95) color = '#faad14' // 黄色 85-95%
    
    return {
      value: rate,
      itemStyle: { color }
    }
  })
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        const param = params[0]
        return `端口: ${param.axisValue}<br/>${param.marker}${param.seriesName}: ${param.value}%`
      }
    },
    legend: {
      data: ['成功率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.portAnalysis.portSuccess.ports
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '成功率',
        type: 'bar',
        data: successRateData
      }
    ]
  }
  
  portSuccessChartInstance.setOption(option)
}

// 初始化端口响应时间图表
const initPortResponseChart = () => {
  if (!portResponseChart.value) return
  
  // 销毁已存在的实例
  if (portResponseChartInstance) {
    portResponseChartInstance.dispose()
    portResponseChartInstance = null
  }
  
  portResponseChartInstance = echarts.init(portResponseChart.value)
  
  // 检查数据是否存在
  if (!chartData.value.portAnalysis.portResponse.ports.length) {
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
    portResponseChartInstance.setOption(option)
    return
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        let result = `端口: ${params[0].axisValue}<br/>`
        params.forEach(param => {
          result += `${param.marker}${param.seriesName}: ${param.value}ms<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['平均响应时间', '最大响应时间']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.portAnalysis.portResponse.ports
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
        type: 'bar',
        data: chartData.value.portAnalysis.portResponse.avgTimes,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '最大响应时间',
        type: 'bar',
        data: chartData.value.portAnalysis.portResponse.maxTimes,
        itemStyle: { color: '#ff7a45' }
      }
    ]
  }
  
  portResponseChartInstance.setOption(option)
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
  if (!chartData.value.portAnalysis.errorAnalysis.length) {
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
  
  // 为错误类型设置颜色
  const errorData = chartData.value.portAnalysis.errorAnalysis.map((item, index) => {
    const colors = ['#ff4d4f', '#ff7a45', '#faad14', '#722ed1', '#d9d9d9']
    return {
      ...item,
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
        name: '连接错误类型',
        type: 'pie',
        radius: '50%',
        data: errorData,
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
    initSuccessRateChart()
    initConnectionTimeChart()
    initPortChart(activePortTab.value)
  })
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  successRateChartInstance?.resize()
  connectionTimeChartInstance?.resize()
  portSuccessChartInstance?.resize()
  portResponseChartInstance?.resize()
  errorAnalysisChartInstance?.resize()
}

onMounted(async () => {
  // 获取TCP任务列表
  await fetchTcpTasks()
  
  // 获取报表数据
  await fetchTcpReportData()
  
  // 初始化所有图表
  initAllCharts()
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
const cleanup = () => {
  window.removeEventListener('resize', handleResize)
  successRateChartInstance?.dispose()
  connectionTimeChartInstance?.dispose()
  portSuccessChartInstance?.dispose()
  portResponseChartInstance?.dispose()
  errorAnalysisChartInstance?.dispose()
}

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(cleanup)
</script>

<style scoped>
.tcp-report {
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