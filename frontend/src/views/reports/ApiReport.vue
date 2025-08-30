<template>
  <div class="api-report">
    <a-page-header title="API专项报表" sub-title="API事务性能专项分析" />
    
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
              <a-select-option v-for="task in apiTasks" :key="task.id" :value="task.id">
                {{ task.name }}
              </a-select-option>
            </a-select>
          </a-space>
        </a-col>
        <a-col :span="4">
          <a-space>
            <span>事务类型：</span>
            <a-select v-model:value="selectedTransactionType" style="width: 120px;" @change="handleTransactionTypeChange">
              <a-select-option value="all">全部事务</a-select-option>
              <a-select-option value="login">登录事务</a-select-option>
              <a-select-option value="payment">支付事务</a-select-option>
              <a-select-option value="query">查询事务</a-select-option>
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

    <!-- API关键指标 -->
    <a-row :gutter="16" class="metrics-cards">
      <a-col :span="6" v-for="metric in apiMetrics" :key="metric.key">
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
      <!-- API事务成功率趋势 -->
      <a-col :span="12">
        <a-card title="API事务成功率趋势" :bordered="false">
          <div ref="transactionSuccessChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
      
      <!-- 断言通过率分析 -->
      <a-col :span="12">
        <a-card title="断言通过率分析" :bordered="false">
          <div ref="assertionChart" style="height: 300px;"></div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 性能分析 -->
    <a-row :gutter="16" class="chart-section">
      <a-col :span="24">
        <a-card title="API性能分析" :bordered="false">
          <a-tabs v-model:activeKey="activePerformanceTab" @change="handlePerformanceTabChange">
            <a-tab-pane key="step-breakdown" tab="多步骤耗时分解">
              <div ref="stepBreakdownChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="transaction-analysis" tab="事务性能对比">
              <div ref="transactionPerformanceChart" style="height: 350px;"></div>
            </a-tab-pane>
            <a-tab-pane key="failure-analysis" tab="失败原因分析">
              <div ref="failureAnalysisChart" style="height: 350px;"></div>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>

    <!-- API任务详细列表 -->
    <a-row :gutter="16" class="table-section">
      <a-col :span="24">
        <a-card title="API任务详细统计" :bordered="false">
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
              <template v-else-if="column.key === 'assertionPassRate'">
                <a-progress
                  :percent="record.assertionPassRate"
                  :status="record.assertionPassRate >= 95 ? 'success' : record.assertionPassRate >= 80 ? 'active' : 'exception'"
                  size="small"
                />
              </template>
              <template v-else-if="column.key === 'avgResponseTime'">
                <span :style="{ color: record.avgResponseTime > 3000 ? '#ff4d4f' : record.avgResponseTime > 1500 ? '#faad14' : '#52c41a' }">
                  {{ record.avgResponseTime }}ms
                </span>
              </template>
              <template v-else-if="column.key === 'transactionType'">
                <a-tag :color="getTransactionTypeColor(record.transactionType)">
                  {{ record.transactionType }}
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
import { getApiReport } from '@/api/reports'
import request from '@/utils/request'
import {
  SyncOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ApiOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'

// 筛选条件
const selectedTimeRange = ref('1d')
const selectedTask = ref('all')
const selectedTransactionType = ref('all')
const activePerformanceTab = ref('step-breakdown')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const totalTasks = ref(50)

// 图表引用
const transactionSuccessChart = ref(null)
const assertionChart = ref(null)
const stepBreakdownChart = ref(null)
const transactionPerformanceChart = ref(null)
const failureAnalysisChart = ref(null)

// 图表实例
let transactionSuccessChartInstance = null
let assertionChartInstance = null
let stepBreakdownChartInstance = null
let transactionPerformanceChartInstance = null
let failureAnalysisChartInstance = null

// 数据状态
const loading = ref(false)
const apiTasks = ref([
  { value: 'all', label: '全部任务' }
])

// API关键指标
const apiMetrics = ref([
  {
    key: 'transactionSuccessRate',
    title: '事务成功率',
    value: 0,
    suffix: '%',
    precision: 1,
    color: '#52c41a',
    icon: CheckCircleOutlined
  },
  {
    key: 'assertionPassRate',
    title: '断言通过率',
    value: 0,
    suffix: '%',
    precision: 1,
    color: '#1890ff',
    icon: ApiOutlined
  },
  {
    key: 'avgTransactionTime',
    title: '平均事务时间',
    value: 0,
    suffix: 'ms',
    precision: 1,
    color: '#722ed1',
    icon: ClockCircleOutlined
  },
  {
    key: 'failureRate',
    title: '事务失败率',
    value: 0,
    suffix: '%',
    precision: 1,
    color: '#ff4d4f',
    icon: WarningOutlined
  }
])

// API数据获取
const fetchApiTasks = async () => {
  try {
    const response = await request.get('/tasks', {
      params: { task_type: 'api' }
    })
    // 处理API返回格式: {code: 0, data: {list: [...], total: N}, message: ""}
    if (response && response.code === 0 && response.data) {
      let taskList = []
      if (Array.isArray(response.data.list)) {
        // v1 API格式: data.list
        taskList = response.data.list
      } else if (Array.isArray(response.data)) {
        // v2 API格式: data直接是数组
        taskList = response.data
      }
      
      if (taskList.length > 0) {
        apiTasks.value = [
          { value: 'all', label: '全部任务' },
          ...taskList.map(task => ({
            value: task.id,
            label: task.name
          }))
        ]
      } else {
        console.warn('API任务数据格式不正确:', response)
        apiTasks.value = [{ value: 'all', label: '全部任务' }]
      }
    } else if (response && Array.isArray(response.data)) {
      // 兼容直接返回data数组的情况
      apiTasks.value = [
        { value: 'all', label: '全部任务' },
        ...response.data.map(task => ({
          value: task.id,
          label: task.name
        }))
      ]
    } else {
      console.warn('API任务数据格式不正确:', response)
      apiTasks.value = [{ value: 'all', label: '全部任务' }]
    }
  } catch (error) {
    console.error('获取API任务列表失败:', error)
    message.error('获取API任务列表失败')
    apiTasks.value = [{ value: 'all', label: '全部任务' }]
  }
}

const fetchApiMetrics = async () => {
  try {
    const response = await request.get('/metrics', {
      params: {
        timeRange: selectedTimeRange.value,
        taskId: selectedTask.value !== 'all' ? selectedTask.value : null,
        transactionType: selectedTransactionType.value !== 'all' ? selectedTransactionType.value : null
      }
    })
    
    const metrics = response.data
    apiMetrics.value[0].value = metrics.transactionSuccessRate || 0
    apiMetrics.value[1].value = metrics.assertionPassRate || 0
    apiMetrics.value[2].value = metrics.avgTransactionTime || 0
    apiMetrics.value[3].value = metrics.failureRate || 0
  } catch (error) {
    console.error('获取API指标失败:', error)
    message.error('获取API指标失败')
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
    title: '事务类型',
    key: 'transactionType',
    width: 100
  },
  {
    title: '步骤数量',
    dataIndex: 'stepCount',
    key: 'stepCount',
    width: 80
  },
  {
    title: '状态',
    key: 'status',
    width: 80
  },
  {
    title: '事务成功率',
    key: 'successRate',
    width: 120
  },
  {
    title: '断言通过率',
    key: 'assertionPassRate',
    width: 120
  },
  {
    title: '平均事务时间',
    key: 'avgResponseTime',
    width: 120
  },
  {
    title: '总执行次数',
    dataIndex: 'totalExecutions',
    key: 'totalExecutions',
    width: 100
  },
  {
    title: '最后执行时间',
    dataIndex: 'lastExecutionTime',
    key: 'lastExecutionTime',
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

// 获取API报表数据
const fetchApiReportData = async () => {
  loading.value = true
  try {
    const response = await getApiReport({
      time_range: selectedTimeRange.value,
      task_id: selectedTask.value !== 'all' ? selectedTask.value : null,
      transaction_type: selectedTransactionType.value !== 'all' ? selectedTransactionType.value : null
    })
    
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
        apiMetrics.value[0].value = data.metrics.transaction_success_rate || 0
        apiMetrics.value[1].value = data.metrics.assertion_pass_rate || 0
        apiMetrics.value[2].value = data.metrics.avg_transaction_time || 0
        apiMetrics.value[3].value = data.metrics.failure_rate || 0
      }
      
      // 更新表格数据
      if (data.task_list || data.task_details) {
        const taskList = data.task_list || data.task_details
        taskTableData.value = taskList.map((task, index) => ({
          key: task.task_id.toString(),
          taskName: task.task_name,
          transactionType: task.transaction_type || 'API',
          stepCount: task.step_count || (task.step_breakdown ? task.step_breakdown.length : 0),
          successRate: task.success_rate,
          assertionPassRate: task.assertion_pass_rate || 0,
          avgResponseTime: task.avg_response_time || 0,
          totalExecutions: task.total || task.total_executions || 0,
          lastExecutionTime: task.last_execution || task.last_execution_time
        }))
      }
      
      // 更新图表数据
      updateChartData(data)
      
      // 重新初始化图表
      nextTick(() => {
        initAllCharts()
      })
    } else {
      console.warn('API报表数据格式不正确:', response)
    }
   } catch (error) {
     console.error('获取API报表数据失败:', error)
     message.error('获取API报表数据失败')
   } finally {
     loading.value = false
   }
 }

 // 存储图表数据
 let chartData = {
   successRateTrend: [],
   taskList: [],
   failureReasons: []
 }

 // 更新图表数据
const updateChartData = (data) => {
  chartData.successRateTrend = data.success_rate_trend || data.transaction_success_trend || []
  chartData.taskList = data.task_list || data.task_details || []
  chartData.failureReasons = data.failure_reasons || data.failure_analysis || []
}

// 方法
const handleTimeRangeChange = (value) => {
  fetchApiReportData()
}

const handleTaskChange = (value) => {
  fetchApiReportData()
}

const handleTransactionTypeChange = (value) => {
  fetchApiReportData()
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
  await fetchApiReportData()
  initAllCharts()
  message.success('数据刷新完成')
}

const exportReport = async () => {
  try {
    const { ExportUtils } = await import('@/utils/exportUtils')
    await ExportUtils.quickExport('api', 'excel', selectedTimeRange.value, {
      transaction_type: selectedTransactionType.value !== 'all' ? selectedTransactionType.value : null
    })
  } catch (error) {
    console.error('导出API报表失败:', error)
    message.error('导出API报表失败，请稍后重试')
  }
}

const router = useRouter()

const viewTaskDetail = (record) => {
  // 跳转到API任务结果列表页面
  if (record.key) {
    router.push(`/task-management/api-result/${record.key}`)
  } else {
    message.error('任务ID不存在，无法查看详情')
  }
}

const viewTaskTrend = (record) => {
  message.info(`查看趋势分析: ${record.taskName}`)
}

const getTransactionTypeColor = (type) => {
  const colors = {
    '登录事务': 'blue',
    '支付事务': 'red',
    '查询事务': 'green',
    '注册事务': 'purple'
  }
  return colors[type] || 'default'
}

// 初始化事务成功率趋势图表
const initTransactionSuccessChart = () => {
  if (!transactionSuccessChart.value) return
  
  // 销毁已存在的图表实例
  if (transactionSuccessChartInstance) {
    transactionSuccessChartInstance.dispose()
  }
  
  transactionSuccessChartInstance = echarts.init(transactionSuccessChart.value)
  
  const timeLabels = chartData.successRateTrend.map(item => item.time) || []
  const successRates = chartData.successRateTrend.map(item => item.success_rate) || []
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = params[0].name + '<br/>'
        params.forEach(param => {
          result += param.marker + param.seriesName + ': ' + param.value + '%<br/>'
        })
        return result
      }
    },
    legend: {
      data: ['事务成功率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeLabels.length > 0 ? timeLabels : ['暂无数据']
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '事务成功率',
        type: 'line',
        data: successRates.length > 0 ? successRates : [0],
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
      }
    ]
  }
  
  transactionSuccessChartInstance.setOption(option)
}

// 初始化断言通过率图表
const initAssertionChart = () => {
  if (!assertionChart.value) return
  
  // 销毁已存在的图表实例
  if (assertionChartInstance) {
    assertionChartInstance.dispose()
  }
  
  assertionChartInstance = echarts.init(assertionChart.value)
  
  const taskNames = chartData.taskList.map(item => item.task_name) || []
  const passRates = chartData.taskList.map(item => item.assertion_pass_rate) || []
  const failRates = chartData.taskList.map(item => 100 - item.assertion_pass_rate) || []
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['断言通过', '断言失败']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: taskNames.length > 0 ? taskNames : ['暂无数据']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '断言通过',
        type: 'bar',
        stack: 'total',
        data: passRates.length > 0 ? passRates : [0],
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '断言失败',
        type: 'bar',
        stack: 'total',
        data: failRates.length > 0 ? failRates : [0],
        itemStyle: { color: '#ff4d4f' }
      }
    ]
  }
  
  assertionChartInstance.setOption(option)
}

// 初始化性能图表
const initPerformanceChart = (type) => {
  switch (type) {
    case 'step-breakdown':
      initStepBreakdownChart()
      break
    case 'transaction-analysis':
      initTransactionPerformanceChart()
      break
    case 'failure-analysis':
      initFailureAnalysisChart()
      break
  }
}

// 初始化步骤分解图表
const initStepBreakdownChart = () => {
  if (!stepBreakdownChart.value) return
  
  // 销毁已存在的图表实例
  if (stepBreakdownChartInstance) {
    stepBreakdownChartInstance.dispose()
  }
  
  stepBreakdownChartInstance = echarts.init(stepBreakdownChart.value)
  
  const taskNames = chartData.taskList.map(item => item.task_name) || []
  const stepBreakdown = chartData.taskList.map(item => {
    const breakdown = item.step_breakdown || []
    // 转换后端数据格式 {name, avg_time} -> 数值数组
    if (breakdown.length > 0 && typeof breakdown[0] === 'object' && breakdown[0].avg_time !== undefined) {
      return breakdown.map(step => step.avg_time || 0)
    }
    return breakdown
  }) || []
  
  // 获取最大步骤数
  const maxSteps = Math.max(...stepBreakdown.map(steps => steps.length), 0)
  const stepSeries = []
  const colors = ['#1890ff', '#52c41a', '#faad14', '#722ed1', '#ff7a45']
  
  // 检查是否有有效的步骤数据
  const hasValidStepData = maxSteps > 0 && stepBreakdown.some(steps => steps.length > 0)
  
  if (hasValidStepData) {
    for (let i = 0; i < maxSteps; i++) {
      stepSeries.push({
        name: `步骤${i + 1}`,
        type: 'bar',
        stack: 'total',
        data: stepBreakdown.map(steps => steps[i] || 0),
        itemStyle: { color: colors[i % colors.length] }
      })
    }
  } else {
    // 当没有步骤数据时，显示提示信息
    stepSeries.push({
      name: '暂无步骤数据',
      type: 'bar',
      data: taskNames.length > 0 ? taskNames.map(() => 0) : [0],
      itemStyle: { color: '#d9d9d9' }
    })
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: stepSeries.map(series => series.name)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: taskNames.length > 0 ? taskNames : ['暂无数据']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}ms'
      }
    },
    series: stepSeries,
    graphic: !hasValidStepData ? {
      type: 'text',
      left: 'center',
      top: 'middle',
      style: {
        text: '暂无步骤分解数据\n请检查任务配置是否包含多个步骤',
        fontSize: 14,
        fill: '#999',
        textAlign: 'center'
      }
    } : null
  }
  
  stepBreakdownChartInstance.setOption(option)
}

// 初始化事务性能对比图表
const initTransactionPerformanceChart = () => {
  if (!transactionPerformanceChart.value) return
  
  // 销毁已存在的图表实例
  if (transactionPerformanceChartInstance) {
    transactionPerformanceChartInstance.dispose()
  }
  
  transactionPerformanceChartInstance = echarts.init(transactionPerformanceChart.value)
  
  const taskNames = chartData.taskList.map(item => item.task_name) || []
  const avgResponseTimes = chartData.taskList.map(item => item.avg_response_time) || []
  const p95ResponseTimes = chartData.taskList.map(item => item.p95_response_time || item.avg_response_time * 1.5) || []
  const p99ResponseTimes = chartData.taskList.map(item => item.p99_response_time || item.avg_response_time * 2) || []
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = params[0].name + '<br/>'
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
      data: taskNames.length > 0 ? taskNames : ['暂无数据']
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
        data: avgResponseTimes.length > 0 ? avgResponseTimes : [0],
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '95%分位数',
        type: 'bar',
        data: p95ResponseTimes.length > 0 ? p95ResponseTimes : [0],
        itemStyle: { color: '#faad14' }
      },
      {
        name: '99%分位数',
        type: 'bar',
        data: p99ResponseTimes.length > 0 ? p99ResponseTimes : [0],
        itemStyle: { color: '#ff4d4f' }
      }
    ]
  }
  
  transactionPerformanceChartInstance.setOption(option)
}

// 初始化失败原因分析图表
const initFailureAnalysisChart = () => {
  if (!failureAnalysisChart.value) return
  
  // 销毁已存在的图表实例
  if (failureAnalysisChartInstance) {
    failureAnalysisChartInstance.dispose()
  }
  
  failureAnalysisChartInstance = echarts.init(failureAnalysisChart.value)
  
  // 从chartData中获取失败原因统计数据，转换格式
  let failureReasons = []
  if (chartData.failureReasons && chartData.failureReasons.length > 0) {
    failureReasons = chartData.failureReasons.map(item => ({
      name: item.reason || item.name,
      value: item.count || item.value
    }))
  } else {
    // 默认数据
    failureReasons = [
      { name: '断言失败', value: 35 },
      { name: '接口超时', value: 25 },
      { name: '服务器错误', value: 20 },
      { name: '参数错误', value: 10 },
      { name: '网络异常', value: 6 },
      { name: '其他错误', value: 4 }
    ]
  }
  
  const colors = ['#ff4d4f', '#faad14', '#ff7a45', '#722ed1', '#eb2f96', '#d9d9d9']
  const pieData = failureReasons.map((item, index) => ({
    value: item.value,
    name: item.name,
    itemStyle: { color: colors[index % colors.length] }
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
        name: 'API失败原因',
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
  
  failureAnalysisChartInstance.setOption(option)
}

// 初始化所有图表
const initAllCharts = () => {
  nextTick(() => {
    initTransactionSuccessChart()
    initAssertionChart()
    initPerformanceChart(activePerformanceTab.value)
  })
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  transactionSuccessChartInstance?.resize()
  assertionChartInstance?.resize()
  stepBreakdownChartInstance?.resize()
  transactionPerformanceChartInstance?.resize()
  failureAnalysisChartInstance?.resize()
}

onMounted(() => {
  fetchApiReportData()
  initAllCharts()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
const cleanup = () => {
  window.removeEventListener('resize', handleResize)
  transactionSuccessChartInstance?.dispose()
  assertionChartInstance?.dispose()
  stepBreakdownChartInstance?.dispose()
  transactionPerformanceChartInstance?.dispose()
  failureAnalysisChartInstance?.dispose()
}

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(cleanup)
</script>

<style scoped>
.api-report {
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