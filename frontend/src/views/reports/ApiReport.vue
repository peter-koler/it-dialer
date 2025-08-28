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
import * as echarts from 'echarts'
import {
  SyncOutlined,
  DownloadOutlined,
  ApiOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
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

// API任务列表
const apiTasks = ref([
  { id: 1, name: 'API登录事务' },
  { id: 2, name: 'API支付事务' },
  { id: 3, name: 'API查询事务' },
  { id: 4, name: 'API注册事务' }
])

// API关键指标
const apiMetrics = ref([
  {
    key: 'transactionSuccessRate',
    title: '事务成功率',
    value: 89.7,
    suffix: '%',
    precision: 1,
    color: '#52c41a',
    icon: CheckCircleOutlined
  },
  {
    key: 'assertionPassRate',
    title: '断言通过率',
    value: 94.3,
    suffix: '%',
    precision: 1,
    color: '#1890ff',
    icon: ApiOutlined
  },
  {
    key: 'avgTransactionTime',
    title: '平均事务时间',
    value: 1285.6,
    suffix: 'ms',
    precision: 1,
    color: '#722ed1',
    icon: ClockCircleOutlined
  },
  {
    key: 'failureRate',
    title: '事务失败率',
    value: 10.3,
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
const taskTableData = ref([
  {
    key: '1',
    taskName: 'API登录事务',
    transactionType: '登录事务',
    stepCount: 3,
    successRate: 96.8,
    assertionPassRate: 98.2,
    avgResponseTime: 850,
    totalExecutions: 2880,
    lastExecutionTime: '2024-01-15 14:30:25'
  },
  {
    key: '2',
    taskName: 'API支付事务',
    transactionType: '支付事务',
    stepCount: 5,
    successRate: 87.2,
    assertionPassRate: 92.5,
    avgResponseTime: 1650,
    totalExecutions: 1440,
    lastExecutionTime: '2024-01-15 14:29:45'
  },
  {
    key: '3',
    taskName: 'API查询事务',
    transactionType: '查询事务',
    stepCount: 2,
    successRate: 94.5,
    assertionPassRate: 96.8,
    avgResponseTime: 420,
    totalExecutions: 3600,
    lastExecutionTime: '2024-01-15 14:28:15'
  },
  {
    key: '4',
    taskName: 'API注册事务',
    transactionType: '注册事务',
    stepCount: 4,
    successRate: 82.3,
    assertionPassRate: 89.7,
    avgResponseTime: 1200,
    totalExecutions: 720,
    lastExecutionTime: '2024-01-15 14:27:30'
  }
])

// 方法
const handleTimeRangeChange = (value) => {
  refreshData()
}

const handleTaskChange = (value) => {
  refreshData()
}

const handleTransactionTypeChange = (value) => {
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
    await ExportUtils.quickExport('api', 'excel', selectedTimeRange.value, {
      transaction_type: selectedTransaction.value !== 'all' ? selectedTransaction.value : null
    })
  } catch (error) {
    console.error('导出API报表失败:', error)
    message.error('导出API报表失败，请稍后重试')
  }
}

const viewTaskDetail = (record) => {
  message.info(`查看任务详情: ${record.taskName}`)
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

// 初始化事务成功率趋势图
const initTransactionSuccessChart = () => {
  if (!transactionSuccessChart.value) return
  
  transactionSuccessChartInstance = echarts.init(transactionSuccessChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['登录事务', '支付事务', '查询事务', '注册事务']
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
      min: 70,
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '登录事务',
        type: 'line',
        data: [96, 95, 97, 96, 98, 97, 96],
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
        name: '支付事务',
        type: 'line',
        data: [87, 85, 89, 88, 90, 86, 87],
        smooth: true,
        itemStyle: { color: '#ff4d4f' }
      },
      {
        name: '查询事务',
        type: 'line',
        data: [94, 93, 96, 95, 97, 94, 94],
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '注册事务',
        type: 'line',
        data: [82, 80, 85, 83, 86, 81, 82],
        smooth: true,
        itemStyle: { color: '#722ed1' }
      }
    ]
  }
  
  transactionSuccessChartInstance.setOption(option)
}

// 初始化断言通过率图表
const initAssertionChart = () => {
  if (!assertionChart.value) return
  
  assertionChartInstance = echarts.init(assertionChart.value)
  
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
      data: ['登录事务', '支付事务', '查询事务', '注册事务']
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
        data: [98.2, 92.5, 96.8, 89.7],
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '断言失败',
        type: 'bar',
        stack: 'total',
        data: [1.8, 7.5, 3.2, 10.3],
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
  
  stepBreakdownChartInstance = echarts.init(stepBreakdownChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['步骤1', '步骤2', '步骤3', '步骤4', '步骤5']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['登录事务', '支付事务', '查询事务', '注册事务']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}ms'
      }
    },
    series: [
      {
        name: '步骤1',
        type: 'bar',
        stack: 'total',
        data: [200, 300, 150, 250],
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '步骤2',
        type: 'bar',
        stack: 'total',
        data: [350, 450, 180, 380],
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '步骤3',
        type: 'bar',
        stack: 'total',
        data: [300, 500, 90, 320],
        itemStyle: { color: '#faad14' }
      },
      {
        name: '步骤4',
        type: 'bar',
        stack: 'total',
        data: [0, 250, 0, 180],
        itemStyle: { color: '#722ed1' }
      },
      {
        name: '步骤5',
        type: 'bar',
        stack: 'total',
        data: [0, 150, 0, 70],
        itemStyle: { color: '#ff7a45' }
      }
    ]
  }
  
  stepBreakdownChartInstance.setOption(option)
}

// 初始化事务性能对比图表
const initTransactionPerformanceChart = () => {
  if (!transactionPerformanceChart.value) return
  
  transactionPerformanceChartInstance = echarts.init(transactionPerformanceChart.value)
  
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
        data: [1200, 1100, 1350, 1280, 1450, 1180, 1220],
        smooth: true,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '95%分位数',
        type: 'line',
        data: [2100, 1950, 2350, 2200, 2500, 2050, 2150],
        smooth: true,
        itemStyle: { color: '#faad14' },
        lineStyle: { type: 'dashed' }
      },
      {
        name: '99%分位数',
        type: 'line',
        data: [3200, 2980, 3580, 3350, 3800, 3120, 3280],
        smooth: true,
        itemStyle: { color: '#ff4d4f' },
        lineStyle: { type: 'dashed' }
      }
    ]
  }
  
  transactionPerformanceChartInstance.setOption(option)
}

// 初始化失败原因分析图表
const initFailureAnalysisChart = () => {
  if (!failureAnalysisChart.value) return
  
  failureAnalysisChartInstance = echarts.init(failureAnalysisChart.value)
  
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
        data: [
          { value: 35, name: '断言失败', itemStyle: { color: '#ff4d4f' } },
          { value: 25, name: '接口超时', itemStyle: { color: '#faad14' } },
          { value: 20, name: '服务器错误', itemStyle: { color: '#ff7a45' } },
          { value: 10, name: '参数错误', itemStyle: { color: '#722ed1' } },
          { value: 6, name: '网络异常', itemStyle: { color: '#eb2f96' } },
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