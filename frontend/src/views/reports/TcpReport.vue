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
  CheckCircleOutlined,
  ClockCircleOutlined,
  LinkOutlined,
  WarningOutlined
} from '@ant-design/icons-vue'

// 筛选条件
const selectedTimeRange = ref('1d')
const selectedTask = ref('all')
const selectedPort = ref('all')
const activePortTab = ref('port-success')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const totalTasks = ref(50)

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
const tcpTasks = ref([
  { id: 1, name: 'TCP本地测试' },
  { id: 2, name: 'TCP数据库连接' },
  { id: 3, name: 'TCP Web服务' },
  { id: 4, name: 'TCP API服务' }
])

// TCP关键指标
const tcpMetrics = ref([
  {
    key: 'successRate',
    title: '总体连接成功率',
    value: 95.8,
    suffix: '%',
    precision: 1,
    color: '#52c41a',
    icon: CheckCircleOutlined
  },
  {
    key: 'avgConnectionTime',
    title: '平均连接时间',
    value: 45.2,
    suffix: 'ms',
    precision: 1,
    color: '#1890ff',
    icon: ClockCircleOutlined
  },
  {
    key: 'totalConnections',
    title: '总连接次数',
    value: 12580,
    suffix: '',
    precision: 0,
    color: '#722ed1',
    icon: LinkOutlined
  },
  {
    key: 'errorRate',
    title: '连接错误率',
    value: 4.2,
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
const taskTableData = ref([
  {
    key: '1',
    taskName: 'TCP本地测试',
    target: '127.0.0.1',
    port: 8080,
    successRate: 98.5,
    avgResponseTime: 25,
    totalTests: 2880,
    lastTestTime: '2024-01-15 14:30:25'
  },
  {
    key: '2',
    taskName: 'TCP数据库连接',
    target: 'db.server.com',
    port: 3306,
    successRate: 92.3,
    avgResponseTime: 85,
    totalTests: 1440,
    lastTestTime: '2024-01-15 14:29:45'
  },
  {
    key: '3',
    taskName: 'TCP Web服务',
    target: 'web.server.com',
    port: 80,
    successRate: 96.7,
    avgResponseTime: 45,
    totalTests: 2160,
    lastTestTime: '2024-01-15 14:28:15'
  },
  {
    key: '4',
    taskName: 'TCP API服务',
    target: 'api.server.com',
    port: 443,
    successRate: 89.2,
    avgResponseTime: 120,
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

const handlePortChange = (value) => {
  refreshData()
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
    await ExportUtils.quickExport('tcp', 'excel', selectedTimeRange.value)
  } catch (error) {
    console.error('导出TCP报表失败:', error)
    message.error('导出TCP报表失败，请稍后重试')
  }
}

const viewTaskDetail = (record) => {
  message.info(`查看任务详情: ${record.taskName}`)
}

const viewTaskTrend = (record) => {
  message.info(`查看趋势分析: ${record.taskName}`)
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
        name: '连接成功率',
        type: 'line',
        data: [95, 94, 96, 95, 97, 96, 95],
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
        data: [98, 98, 98, 98, 98, 98, 98],
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
  
  connectionTimeChartInstance = echarts.init(connectionTimeChart.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}ms ({d}%)'
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
        data: [
          { value: 45, name: '0-50ms', itemStyle: { color: '#52c41a' } },
          { value: 30, name: '50-100ms', itemStyle: { color: '#1890ff' } },
          { value: 15, name: '100-200ms', itemStyle: { color: '#faad14' } },
          { value: 8, name: '200-500ms', itemStyle: { color: '#ff7a45' } },
          { value: 2, name: '>500ms', itemStyle: { color: '#ff4d4f' } }
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
  
  portSuccessChartInstance = echarts.init(portSuccessChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
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
      data: ['80', '443', '3306', '8080', '22', '21', '25', '53']
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
        name: '成功率',
        type: 'bar',
        data: [
          { value: 96.7, itemStyle: { color: '#52c41a' } },
          { value: 89.2, itemStyle: { color: '#faad14' } },
          { value: 92.3, itemStyle: { color: '#52c41a' } },
          { value: 98.5, itemStyle: { color: '#52c41a' } },
          { value: 85.6, itemStyle: { color: '#ff7a45' } },
          { value: 82.1, itemStyle: { color: '#ff4d4f' } },
          { value: 88.9, itemStyle: { color: '#faad14' } },
          { value: 94.3, itemStyle: { color: '#52c41a' } }
        ]
      }
    ]
  }
  
  portSuccessChartInstance.setOption(option)
}

// 初始化端口响应时间图表
const initPortResponseChart = () => {
  if (!portResponseChart.value) return
  
  portResponseChartInstance = echarts.init(portResponseChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
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
      data: ['80', '443', '3306', '8080', '22', '21', '25', '53']
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
        data: [45, 120, 85, 25, 180, 220, 150, 35],
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '最大响应时间',
        type: 'bar',
        data: [120, 350, 280, 80, 500, 800, 450, 120],
        itemStyle: { color: '#ff7a45' }
      }
    ]
  }
  
  portResponseChartInstance.setOption(option)
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
        name: '连接错误类型',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 45, name: '连接超时', itemStyle: { color: '#ff4d4f' } },
          { value: 25, name: '连接拒绝', itemStyle: { color: '#ff7a45' } },
          { value: 15, name: '网络不可达', itemStyle: { color: '#faad14' } },
          { value: 10, name: '主机不可达', itemStyle: { color: '#722ed1' } },
          { value: 5, name: '其他错误', itemStyle: { color: '#d9d9d9' } }
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

onMounted(() => {
  initAllCharts()
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