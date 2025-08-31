<template>
  <div class="http-monitoring-result-page">
    <!-- 页面头部 -->
    <a-card :bordered="false" class="page-header-card">
      <a-page-header :title="task.name || 'HTTP 拨测'" @back="() => $router.back()">
        <template #extra>
          <div class="header-extra">
            <a-tag :color="task.status === 'active' ? 'green' : 'red'">
              {{ task.status === 'active' ? '运行中' : '已停止' }}
            </a-tag>
            <!-- 时间筛选控件移到右上角 -->
            <div class="time-filter-wrapper">
              <div class="quick-time-buttons">
                <a-button 
                  size="small" 
                  @click="setQuickTime(1, 'hour')"
                  :type="isQuickTimeActive(1, 'hour') ? 'primary' : 'default'"
                >
                  1小时
                </a-button>
                <a-button 
                  size="small" 
                  @click="setQuickTime(8, 'hour')"
                  :type="isQuickTimeActive(8, 'hour') ? 'primary' : 'default'"
                >
                  8小时
                </a-button>
                <a-button 
                  size="small" 
                  @click="setQuickTime(1, 'day')"
                  :type="isQuickTimeActive(1, 'day') ? 'primary' : 'default'"
                >
                  今天
                </a-button>
                <a-button 
                  size="small" 
                  @click="setQuickTime(7, 'day')"
                  :type="isQuickTimeActive(7, 'day') ? 'primary' : 'default'"
                >
                  7天
                </a-button>
              </div>
              <a-range-picker
                v-model:value="timeRange"
                :placeholder="['开始时间', '结束时间']"
                format="YYYY-MM-DD HH:mm:ss"
                show-time
                @change="handleTimeRangeChange"
                class="time-range-picker"
                size="small"
              />
              <a-button 
                type="link" 
                @click="resetTimeFilter"
                :disabled="!timeRange || timeRange.length === 0"
                size="small"
              >
                重置
              </a-button>
            </div>
          </div>
        </template>
        <template #footer>
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="overview" tab="总览"></a-tab-pane>
          </a-tabs>
        </template>
      </a-page-header>
    </a-card>
    
    <!-- 任务基本信息面板 -->
    <a-card :bordered="false" class="task-info-card">
      <template #title>任务基本信息</template>
      <a-descriptions :column="{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }" bordered>
        <a-descriptions-item label="任务名称">{{ task.name || '-' }}</a-descriptions-item>
        <a-descriptions-item label="目标URL">{{ task.target || '-' }}</a-descriptions-item>
        <a-descriptions-item label="执行次数">{{ totalExecutions || 0 }}</a-descriptions-item>
        <a-descriptions-item label="平均响应时间">{{ avgResponseTime ? `${avgResponseTime.toFixed(2)} ms` : '-' }}</a-descriptions-item>
        <a-descriptions-item label="任务类型">HTTP拨测</a-descriptions-item>
        <a-descriptions-item label="最新状态">
          <a-tag :color="latestStatus === 'success' ? 'green' : 'red'">
            {{ latestStatus === 'success' ? '成功' : '失败' }}
          </a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </a-card>

    <div class="page-content">
      <!-- 地图和列表面板 -->
      <MapListPanel
        :data="agentAggregatedResults"
        :mapData="mapData"
        :alertsByRegion="alertsByRegion"
        :getRegionAlertLevel="getRegionAlertLevel"
        :level="level"
        :selectedCode="selectedCode"
        @update:level="level = $event"
        @update:selectedCode="selectedCode = $event"
        @probe-click="handleProbeClick"
        @show-probe-detail="showProbeDetail"
        @showDetails="showDetails"
        @goToProbeDetail="goToProbeDetail"
      />
      
      <!-- WebStatus图表面板 -->
      <a-card :bordered="false" class="chart-card">
        <template #title>WebStatus 响应时间趋势</template>
        <div ref="webStatusChartRef" class="webstatus-chart"></div>
      </a-card>
      
      <!-- 告警面板 -->
      <a-card :bordered="false" class="alert-card">
        <template #title>任务告警</template>
        <a-table
          :dataSource="alertData"
          :columns="alertColumns"
          :pagination="{ pageSize: 10 }"
          rowKey="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'alertLevel'">
              <a-tag :color="getAlertLevelColor(record.alertLevel)">
                {{ getAlertLevelText(record.alertLevel) }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <a-button type="link" size="small" @click="viewAlertSnapshot(record)">
                查看快照
              </a-button>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>
    
    <!-- 单次拨测结果弹窗 -->
    <HttpResultDetailModal
      v-model:open="isModalOpen"
      :probe-data="selectedProbeData"
    />
    
    <!-- 聚合拨测点详情弹窗 -->
    <a-modal
      v-model:open="aggregatedProbeModalVisible"
      title="拨测点详情"
      width="70%"
      :footer="null"
      @cancel="handleAggregatedModalCancel"
    >
      <a-table
        :dataSource="selectedProbeGroup"
        :columns="probeColumns"
        :pagination="{ pageSize: 5 }"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'status'">
            <a-tag :color="record.status === 'success' ? 'green' : 'red'">
              {{ record.status === 'success' ? '成功' : '失败' }}
            </a-tag>
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <a-space>
              <a-button type="link" @click="showDetails(record)">查看HTTP详情</a-button>
              <a-button type="link" @click="goToProbeDetail(record)">查看拨测点详情</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-modal>
    
    <!-- 快照查看弹窗 -->
    <a-modal
      v-model:open="snapshotModalVisible"
      title="HTTP拨测快照详情"
      width="1000px"
      :footer="null"
    >
      <div v-if="currentSnapshot">
        <!-- 基本信息 -->
        <a-card size="small" title="基本信息" class="mb-16">
          <a-descriptions :column="3" size="small">
            <a-descriptions-item label="任务名称">
              {{ currentSnapshot.task_name }}
            </a-descriptions-item>
            <a-descriptions-item label="任务类型">
              <a-tag color="blue">HTTP</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="告警级别">
              <a-tag :color="getAlertLevelColor(currentSnapshot.alertLevel)">
                {{ getAlertLevelText(currentSnapshot.alertLevel) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="拨测点">
              {{ currentSnapshot.probeName || 'N/A' }}
            </a-descriptions-item>
            <a-descriptions-item label="触发时间">
              {{ formatDate(currentSnapshot.created_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="告警状态">
              <a-tag color="orange">待处理</a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
        
        <!-- 快照详情 -->
        <SnapshotViewer 
          task-type="http" 
          :snapshot-data="getSnapshotData(currentSnapshot)"
        />
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, defineEmits, nextTick, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getTask } from '@/api/task'
import { getAggregatedResults } from '@/api/result'
import { getAlerts } from '@/api/alerts'
import MapListPanel from './components/MapListPanel.vue'
import HttpResultDetailModal from './components/HttpResultDetailModal.vue'
import SnapshotViewer from '@/components/SnapshotViewer.vue'
import * as echarts from 'echarts'
import pinyinToChinese from '@/utils/pinyinToChinese'
import { statisticsByProvince, statisticsByCity, getProvinceByPinyin } from '@/utils/regionStatistics'

const components = {
  MapListPanel,
  HttpResultDetailModal,
  SnapshotViewer
}

const emit = defineEmits(['update:level', 'update:selectedCode'])
// HTTP 拨测任务详情页面
const route = useRoute()
const router = useRouter()
const taskId = route.params.id || route.params.taskId

const task = ref({})
const aggregatedResults = ref([])
const loading = ref(false)
const activeTab = ref('overview')
const isModalOpen = ref(false)
const selectedProbeData = ref({})

// 聚合拨测点详情弹窗相关状态
const aggregatedProbeModalVisible = ref(false)
const selectedProbeGroup = ref([])

// 快照查看弹窗相关状态
const snapshotModalVisible = ref(false)
const currentSnapshot = ref({})

// 时间筛选相关状态
const timeRange = ref([])
const originalResults = ref([]) // 保存原始数据
const currentQuickTime = ref(null) // 当前选中的快捷时间 { value: 1, unit: 'hour' }

// 地图相关状态
const level = ref('province')
const selectedCode = ref('')

// 图表引用
const webStatusChartRef = ref(null)
let webStatusChart = null

// 计算属性：总执行次数
const totalExecutions = computed(() => aggregatedResults.value.length)

// 计算属性：平均响应时间
const avgResponseTime = computed(() => {
  const validTimes = aggregatedResults.value
    .map(item => item.response_time)
    .filter(time => time !== undefined && time !== null && time > 0)
  
  if (validTimes.length === 0) return 0
  return validTimes.reduce((sum, time) => sum + time, 0) / validTimes.length
})

// 计算属性：最新状态
const latestStatus = computed(() => {
  if (aggregatedResults.value.length === 0) return 'unknown'
  return aggregatedResults.value[0].status || 'unknown'
})

// 按Agent ID聚合数据
const agentAggregatedResults = computed(() => {
  const groupedByLocation = aggregatedResults.value.reduce((acc, probe) => {
    if (!acc[probe.location]) {
      acc[probe.location] = []
    }
    acc[probe.location].push(probe)
    return acc
  }, {})

  const result = Object.keys(groupedByLocation).map(location => {
    const probes = groupedByLocation[location]
    const successCount = probes.filter(p => p.status === 'success').length
    const latestProbe = probes.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
    const agentIds = new Set(probes.map(p => p.agent_id).filter(id => id))
    
    // 计算平均响应时间
    const validTimes = probes
      .map(item => item.response_time)
      .filter(time => time !== undefined && time !== null && time > 0)
    const avgTime = validTimes.length > 0 
      ? validTimes.reduce((sum, time) => sum + time, 0) / validTimes.length 
      : 0

    return {
      location,
      agentCount: agentIds.size || probes.length,
      successRate: probes.length > 0 ? successCount / probes.length : 0,
      status: latestProbe.status,
      avgResponseTime: avgTime,
      probes,
    }
  })
  
  return result
})

// 地图数据 - 按省份统计拨测点
const mapData = computed(() => {
  if (!aggregatedResults.value.length) {
    return []
  }
  
  // 使用地域统计工具按省份统计
  const provinceStats = statisticsByProvince(aggregatedResults.value)
  
  // 转换为地图组件需要的格式
  const result = Object.values(provinceStats).map(province => {
    // 转换城市数据，将count字段转换为value字段
    const cities = {}
    Object.keys(province.cities).forEach(cityName => {
      const cityData = province.cities[cityName]
      cities[cityName] = {
        name: cityData.name,
        value: cityData.count,
        count: cityData.count,
        probes: cityData.probes
      }
    })
    
    return {
      name: province.name,
      value: province.count,
      probes: province.probes,
      cities: cities
    }
  })
  
  return result
})

// 告警数据状态
const alertData = ref([])

const alertsByRegion = computed(() => {
  const regionAlerts = {}
  
  alertData.value.forEach(alert => {
    const province = getProvinceByPinyin(alert.probeName || alert.agent_area)
    const cityName = pinyinToChinese[alert.probeName || alert.agent_area] || alert.probeName || alert.agent_area
    
    // 按省份统计告警
    if (!regionAlerts[province]) {
      regionAlerts[province] = {
        critical: 0,
        warning: 0,
        info: 0
      }
    }
    
    // 按城市统计告警
    if (!regionAlerts[cityName]) {
      regionAlerts[cityName] = {
        critical: 0,
        warning: 0,
        info: 0
      }
    }
    
    if (alert.alertLevel) {
      regionAlerts[province][alert.alertLevel]++
      regionAlerts[cityName][alert.alertLevel]++
    }
  })
  
  return regionAlerts
})

// 获取区域告警级别（最高级别）
const getRegionAlertLevel = (regionName) => {
  const alerts = alertsByRegion.value[regionName]
  if (!alerts) return null
  
  if (alerts.critical > 0) return 'critical'
  if (alerts.warning > 0) return 'warning'
  if (alerts.info > 0) return 'info'
  return null
}

// 告警表格列定义
const alertColumns = [
  { title: '任务名称', dataIndex: 'taskName', key: 'taskName' },
  { title: '拨测点', dataIndex: 'probeName', key: 'probeName' },
  { title: '告警级别', dataIndex: 'alertLevel', key: 'alertLevel' },
  { title: '告警内容', dataIndex: 'content', key: 'content' },
  { title: '触发时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', dataIndex: 'action', key: 'action' }
]

// 拨测点表格列定义
const probeColumns = [
  { title: '位置', dataIndex: 'location', key: 'location',
    customRender: ({ text }) => {
      const chineseName = pinyinToChinese[text] || text;
      return chineseName;
    }
  },
  { title: '时间', dataIndex: 'created_at', key: 'created_at',
    customRender: ({ text }) => formatDate(text) },
  { title: '响应时间', dataIndex: 'response_time', key: 'response_time',
    customRender: ({ text }) => text ? `${text} ms` : '-' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', dataIndex: 'action', key: 'action' }
]

// 获取告警数据
const fetchAlerts = async (startTime = null, endTime = null) => {
  try {
    const params = {
      task_id: taskId,
      task_type: 'http',
      page: 1,
      size: 1000
    }
    
    if (startTime && endTime) {
      params.start = startTime
      params.end = endTime
    }
    
    const response = await getAlerts(params)
    console.log('HTTP告警API响应:', response)
    
    if (response && response.code === 0) {
      // 过滤当前任务的告警
      const allAlerts = response.data?.alerts || response.data?.list || []
      const taskAlerts = allAlerts.filter(alert => alert.task_id == taskId)
      
      alertData.value = taskAlerts.map(alert => ({
        id: alert.id,
        taskName: alert.taskName || alert.task_name || task.value.name,
        probeName: alert.agent_area || alert.probeName || alert.agent_id,
        agent_area: alert.agent_area || alert.probeName || alert.agent_id,
        alertLevel: alert.alertLevel || alert.alert_level,
        content: alert.content,
        created_at: alert.created_at || alert.triggerTime
      }))
      
      console.log('获取到告警数据:', alertData.value)
    } else {
      console.warn('获取告警数据失败:', response?.message)
      alertData.value = []
    }
  } catch (error) {
    console.error('获取告警数据失败:', error)
    alertData.value = []
  }
}

// 获取任务详情
const fetchTaskDetails = async () => {
  try {
    const response = await getTask(taskId)
    
    if (response && response.code === 0) {
      task.value = response.data
    } else {
      console.warn('未获取到任务详情数据')
      message.warning('未获取到任务详情数据')
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    message.error('获取任务详情失败: ' + (error.response?.data?.message || error.message || '未知错误'))
  }
}

// 获取拨测结果
const fetchResults = async (startTime = null, endTime = null) => {
  loading.value = true
  try {
    const params = {
      type: 'http',
      page: 1,
      size: 100
    }
    
    // 如果有时间筛选条件，添加到参数中
    if (startTime && endTime) {
      params.start = startTime
      params.end = endTime
    }
    
    // 同时获取拨测结果和告警数据
    const [response] = await Promise.all([
      getAggregatedResults(taskId, params),
      fetchAlerts(startTime, endTime)
    ])
    
    // 处理响应数据
    if (response && response.data && Array.isArray(response.data.list)) {
      // 提取list数组作为拨测结果
      const results = response.data.list.map(item => {
        // 获取原始的agent_area（拼音格式）
        const agentArea = item.agent_area || item.location || '默认位置'
        // 将拼音地区名转换为中文
        const locationName = pinyinToChinese[agentArea] || agentArea
        
        // 确保每个结果都有必要的字段
        return {
          id: item.id,
          probe_id: item.id,
          task_id: item.task_id || taskId,
          agent_id: item.agent_id || (item.task && item.task.agent_ids ? item.task.agent_ids[0] : '未知'),
          location: locationName,
          agent_area: agentArea,
          status: item.status || 'unknown',
          response_time: item.details && item.details.response_time ? item.details.response_time : (item.response_time || 0),
          created_at: item.created_at || new Date().toISOString(),
          details: item.details || {},
          webstatus: item.details && item.details.webstatus ? item.details.webstatus : (item.status === 'success' ? 200 : 500)
        }
      })
      
      // 如果没有时间筛选，保存为原始数据
      if (!startTime && !endTime) {
        originalResults.value = results
      }
      
      aggregatedResults.value = results
      
      // 更新WebStatus图表
      updateWebStatusChart()
    } else {
      aggregatedResults.value = []
    }
    
    if (aggregatedResults.value.length === 0) {
      message.warning('未找到拨测结果数据')
    }
  } catch (error) {
    console.error('Failed to fetch results:', error)
    message.error('获取拨测结果失败: ' + (error.response?.data?.message || error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 更新WebStatus图表
const updateWebStatusChart = () => {
  if (!webStatusChart || !aggregatedResults.value.length) return
  
  // 获取当前时间范围
  let filteredData = aggregatedResults.value
  let startTime = null
  let endTime = null
  
  // 如果有时间筛选条件，过滤数据
  if (timeRange.value && timeRange.value.length === 2) {
    startTime = timeRange.value[0]
    endTime = timeRange.value[1]
    
    filteredData = aggregatedResults.value.filter(item => {
      const itemTime = dayjs(item.created_at)
      return itemTime.isAfter(startTime) && itemTime.isBefore(endTime)
    })
  }
  
  // 按时间和agent聚合数据
  const timeSeriesData = {}
  
  filteredData.forEach(item => {
    const time = dayjs(item.created_at).format('YYYY-MM-DD HH:mm')
    const agentArea = item.agent_area || item.location
    
    if (!timeSeriesData[agentArea]) {
      timeSeriesData[agentArea] = {}
    }
    
    if (!timeSeriesData[agentArea][time]) {
      timeSeriesData[agentArea][time] = {
        total: 0,
        sum: 0,
        count: 0
      }
    }
    
    timeSeriesData[agentArea][time].sum += item.response_time || 0
    timeSeriesData[agentArea][time].count += 1
  })
  
  // 转换为ECharts需要的格式
  const series = []
  const timePoints = new Set()
  
  Object.keys(timeSeriesData).forEach(agentArea => {
    const data = []
    Object.keys(timeSeriesData[agentArea]).forEach(time => {
      const avg = timeSeriesData[agentArea][time].sum / timeSeriesData[agentArea][time].count
      data.push([time, parseFloat(avg.toFixed(2))])
      timePoints.add(time)
    })
    
    series.push({
      name: pinyinToChinese[agentArea] || agentArea,
      type: 'line',
      data: data.sort((a, b) => new Date(a[0]) - new Date(b[0])),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6
    })
  })
  
  // 构建图表配置
  const option = {
    title: {
      text: 'WebStatus 平均响应时间趋势',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = `<div style="margin-bottom: 5px;">${dayjs(params[0].axisValue).format('YYYY-MM-DD HH:mm')}</div>`
        params.forEach(param => {
          result += `<div style="margin: 2px 0;">
            <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color};"></span>
            ${param.seriesName}: ${param.value[1]} ms
          </div>`
        })
        return result
      }
    },
    legend: {
      top: 30,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      min: startTime ? startTime.valueOf() : 'dataMin',
      max: endTime ? endTime.valueOf() : 'dataMax',
      axisLabel: {
        formatter: function(value) {
          // 根据时间范围动态调整显示格式
          if (startTime && endTime) {
            const duration = endTime.diff(startTime, 'hour')
            if (duration <= 24) {
              return dayjs(value).format('HH:mm')
            } else if (duration <= 168) { // 7天内
              return dayjs(value).format('MM-DD HH:mm')
            } else {
              return dayjs(value).format('MM-DD')
            }
          }
          return dayjs(value).format('HH:mm')
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '响应时间 (ms)',
      axisLabel: {
        formatter: '{value} ms'
      }
    },
    series: series
  }
  
  webStatusChart.setOption(option, true) // 使用notMerge=true确保完全更新
}

// 初始化WebStatus图表
const initWebStatusChart = () => {
  if (webStatusChartRef.value) {
    webStatusChart = echarts.init(webStatusChartRef.value)
    updateWebStatusChart()
    
    // 监听窗口大小变化
    window.addEventListener('resize', () => {
      webStatusChart?.resize()
    })
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 获取告警级别颜色
const getAlertLevelColor = (level) => {
  const colors = {
    critical: 'red',
    warning: 'orange',
    info: 'blue'
  }
  return colors[level] || 'default'
}

// 获取告警级别文本
const getAlertLevelText = (level) => {
  const texts = {
    critical: '严重',
    warning: '警告',
    info: '信息'
  }
  return texts[level] || level
}

// 显示详情
const showDetails = async (record) => {
  try {
    // 使用API方法获取单个探针的详细信息
    const { getResultDetail } = await import('@/api/result')
    const response = await getResultDetail(record.id)
    
    let enriched = { ...record }
    
    if (response && response.data) {
      const resultData = response.data
      const detailsData = resultData.details || {}
      
      enriched = {
        ...record,
        details: {
          total_time: detailsData.response_time || record.response_time || 0,
          message: detailsData.message || '',
          status: detailsData.status || resultData.status || 'unknown',
          webstatus: detailsData.webstatus || (record.status === 'success' ? 200 : 500),
          steps: [],
          variables: [],
          assertions: {
            total: 0,
            passed: detailsData.status === 'success' ? 1 : 0,
            failed: detailsData.status === 'success' ? 0 : 1
          }
        }
      }
      
      // 构建HTTP步骤
      enriched.details.steps = [
        {
          id: '1',
          name: 'HTTP请求',
          method: 'GET',
          url: resultData.task?.config?.url || '',
          status: detailsData.status || resultData.status || 'unknown',
          status_code: detailsData.webstatus || (record.status === 'success' ? 200 : 500),
          response_time: detailsData.response_time || 0,
          request: {
            headers: {},
            body: '{}'
          },
          response: {
            headers: {},
            body: '{}',
            size: 0
          },
          assertions: [],
          variables: []
        }
      ]
    }
    
    selectedProbeData.value = enriched
    isModalOpen.value = true
  } catch (error) {
    console.error('获取HTTP详情失败:', error)
    message.error('获取HTTP详情失败: ' + (error.response?.data?.message || error.message || '未知错误'))
  }
}

// 显示聚合拨测点详情
const showAggregatedProbeDetail = (record) => {
  selectedProbeGroup.value = aggregatedResults.value.filter(item => item.location === record.location)
  aggregatedProbeModalVisible.value = true
}

// 关闭聚合拨测点详情弹窗
const handleAggregatedModalCancel = () => {
  aggregatedProbeModalVisible.value = false
}

// 处理拨测点点击
const handleProbeClick = (probe) => {
  console.log('Probe clicked:', probe)
}

// 显示拨测点详情
const showProbeDetail = (probe) => {
  showAggregatedProbeDetail(probe)
}

// 跳转到拨测点详情页面
const goToProbeDetail = (record) => {
  const probeName = pinyinToChinese[record.agent_area] || record.agent_area || record.location
  const agentArea = record.agent_area || record.location
  
  // 跳转到拨测点详情页面
  router.push({
    name: 'HttpProbeDetail',
    params: {
      taskId: taskId,
      probeName: probeName,
      agentArea: agentArea
    }
  })
}

// 查看告警快照
const viewAlertSnapshot = (record) => {
  currentSnapshot.value = record
  snapshotModalVisible.value = true
}

// 获取快照数据
const getSnapshotData = (snapshot) => {
  return {
    task_name: snapshot.taskName,
    target: task.value.target,
    status: snapshot.status || 'failed',
    response_time: snapshot.response_time || 0,
    webstatus: snapshot.webstatus || 500,
    message: snapshot.content || '告警触发',
    created_at: snapshot.created_at
  }
}

// 时间筛选相关方法
// 设置快捷时间
const setQuickTime = async (value, unit) => {
  const now = dayjs()
  let startTime
  
  if (unit === 'hour') {
    startTime = now.subtract(value, 'hour')
  } else if (unit === 'day') {
    if (value === 1) {
      // 今天：从今天00:00开始
      startTime = now.startOf('day')
    } else {
      // 其他天数：从N天前开始
      startTime = now.subtract(value, 'day')
    }
  }
  
  timeRange.value = [startTime, now]
  currentQuickTime.value = { value, unit }
  
  await Promise.all([
    fetchResults(
      startTime.format('YYYY-MM-DD HH:mm:ss'),
      now.format('YYYY-MM-DD HH:mm:ss')
    ),
    fetchAlerts(
      startTime.format('YYYY-MM-DD HH:mm:ss'),
      now.format('YYYY-MM-DD HH:mm:ss')
    )
  ])
  
  // 更新图表
  updateWebStatusChart()
}

// 判断快捷时间是否激活
const isQuickTimeActive = (value, unit) => {
  return currentQuickTime.value && 
         currentQuickTime.value.value === value && 
         currentQuickTime.value.unit === unit
}

// 处理时间范围变化
const handleTimeRangeChange = async (dates) => {
  if (dates && dates.length === 2) {
    const startTime = dates[0].format('YYYY-MM-DD HH:mm:ss')
    const endTime = dates[1].format('YYYY-MM-DD HH:mm:ss')
    
    // 清除快捷时间选择状态
    currentQuickTime.value = null
    
    await Promise.all([
      fetchResults(startTime, endTime),
      fetchAlerts(startTime, endTime)
    ])
    
    // 更新图表
    updateWebStatusChart()
  } else {
    // 如果清空时间范围，恢复原始数据
    aggregatedResults.value = originalResults.value
    await fetchAlerts()
    updateWebStatusChart()
  }
}

// 重置时间筛选
const resetTimeFilter = async () => {
  timeRange.value = []
  currentQuickTime.value = null
  
  // 恢复原始数据
  aggregatedResults.value = originalResults.value
  await fetchAlerts()
  updateWebStatusChart()
}

// 组件挂载
onMounted(async () => {
  await fetchTaskDetails()
  await fetchResults()
  await fetchAlerts()
  
  // 延迟初始化图表，确保DOM已渲染
  nextTick(() => {
    initWebStatusChart()
  })
})

// 组件卸载时清理
onBeforeUnmount(() => {
  if (webStatusChart) {
    webStatusChart.dispose()
    webStatusChart = null
  }
  window.removeEventListener('resize', () => {
    webStatusChart?.resize()
  })
})
</script>

<style scoped>
.http-monitoring-result-page {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.page-header-card {
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-extra {
  display: flex;
  align-items: center;
  gap: 16px;
}

.time-filter-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quick-time-buttons {
  display: flex;
  gap: 8px;
}

.time-range-picker {
  width: 280px;
}

.task-info-card {
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.chart-card,
.alert-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.webstatus-chart {
  width: 100%;
  height: 400px;
}

/* Ant Design Pro 风格调整 */
:deep(.ant-card-head) {
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

:deep(.ant-card-head-title) {
  font-weight: 500;
  color: #262626;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  color: #595959;
}

:deep(.ant-table-thead > tr > th) {
  background: #fafafa;
  font-weight: 500;
}

:deep(.ant-btn-primary) {
  background: #1890ff;
  border-color: #1890ff;
}

:deep(.ant-btn-primary:hover) {
  background: #40a9ff;
  border-color: #40a9ff;
}

@media (max-width: 1200px) {
  .header-extra {
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
  }
  
  .time-filter-wrapper {
    flex-wrap: wrap;
  }
  
  .time-range-picker {
    width: 240px;
  }
}

@media (max-width: 768px) {
  .http-monitoring-result-page {
    padding: 16px;
  }
  
  .quick-time-buttons {
    flex-wrap: wrap;
  }
  
  .time-range-picker {
    width: 200px;
  }
}
/* 快照弹窗样式 */
.mb-16 {
  margin-bottom: 16px;
}

.content-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.ant-modal) {
  .ant-modal-content {
    border-radius: 8px;
  }
  
  .ant-modal-header {
    border-bottom: 1px solid #f0f0f0;
    padding: 16px 24px;
  }
  
  .ant-modal-body {
    padding: 24px;
  }
}

:deep(.ant-card) {
  .ant-card-head {
    border-bottom: 1px solid #f0f0f0;
    min-height: 48px;
  }
  
  .ant-card-body {
    padding: 16px;
  }
}

:deep(.ant-descriptions) {
  .ant-descriptions-item-label {
    font-weight: 500;
    color: #262626;
  }
  
  .ant-descriptions-item-content {
    color: #595959;
  }
}
</style>