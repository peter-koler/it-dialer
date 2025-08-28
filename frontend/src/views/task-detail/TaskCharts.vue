<template>
  <div v-if="taskType === 'ping'">
    <div ref="latencyChartRef" style="width: 100%; height: 400px; margin-top: 20px;"></div>
  </div>
  <div v-else-if="taskType === 'tcp'">
    <div ref="tcpConnectedChartRef" style="width: 100%; height: 300px; margin-top: 20px;"></div>
    <div ref="tcpResponseTimeChartRef" style="width: 100%; height: 300px; margin-top: 20px;"></div>
    <div ref="tcpStatusChartRef" style="width: 100%; height: 300px; margin-top: 20px;"></div>
  </div>
  <div v-else-if="taskType === 'api'">
    <!-- ApiResultViewer组件已移除 -->
  </div>
  <div v-else>
    <a-empty description="暂不支持该类型任务的图表展示" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'
// 已移除对ApiResultViewer的引用

const props = defineProps({
  taskType: {
    type: String,
    required: true
  },
  results: {
    type: Array,
    default: () => []
  }
})

// 计算属性 - 获取任务ID
const taskId = computed(() => {
  if (props.results && props.results.length > 0) {
    return props.results[0].task_id
  }
  return null
})

const latencyChartRef = ref(null)
const tcpConnectedChartRef = ref(null)
const tcpResponseTimeChartRef = ref(null)
const tcpStatusChartRef = ref(null)

let latencyChart = null
let tcpConnectedChart = null
let tcpResponseTimeChart = null
let tcpStatusChart = null

// 监听结果变化，重新渲染图表
watch(
  () => props.results,
  (newResults) => {
    nextTick(() => {
      renderCharts()
    })
  },
  { deep: true }
)

// 监听任务类型变化
watch(
  () => props.taskType,
  () => {
    nextTick(() => {
      renderCharts()
    })
  }
)

onMounted(() => {
  renderCharts()
})

const renderCharts = () => {
  if (props.taskType === 'ping') {
    renderLatencyChart()
  } else if (props.taskType === 'tcp') {
    renderTcpCharts()
  }
}

// 渲染延迟图表（时间序列）
const renderLatencyChart = () => {
  if (!latencyChartRef.value) return
  
  if (latencyChart) {
    latencyChart.dispose()
  }
  
  latencyChart = echarts.init(latencyChartRef.value)
  
  // 按创建时间排序
  const sortedResults = [...props.results].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  
  // 按时间分组并聚合所有拨测点的数据
  const timeGroups = {}
  
  sortedResults.forEach(result => {
    try {
      // 检查details是否存在
      if (!result.details) return;
      
      // 使用创建时间作为键（精确到分钟）
      const timeKey = new Date(result.created_at).toISOString().slice(0, 16)
      const details = typeof result.details === 'string' 
        ? JSON.parse(result.details) 
        : result.details
      
      // 检查解析后的details是否有效
      if (!details) return;
      
      if (!timeGroups[timeKey]) {
        timeGroups[timeKey] = {
          count: 0,
          rtt_min_values: [],
          rtt_avg_values: [],
          rtt_max_values: []
        }
      }
      
      // 收集所有拨测点在该时间点的延迟数据
      if (details.rtt_min !== undefined && details.rtt_min !== null) timeGroups[timeKey].rtt_min_values.push(details.rtt_min)
      if (details.rtt_avg !== undefined && details.rtt_avg !== null) timeGroups[timeKey].rtt_avg_values.push(details.rtt_avg)
      if (details.rtt_max !== undefined && details.rtt_max !== null) timeGroups[timeKey].rtt_max_values.push(details.rtt_max)
      
      timeGroups[timeKey].count += 1
    } catch (e) {
      // 解析失败时跳过该记录
      console.error('解析详情数据失败:', e, result)
    }
  })
  
  // 计算每个时间点的统计数据（最少延迟、平均延迟、最大延迟的平均值）
  const timeData = []
  const overallMinData = []   // 所有拨测点的最少延迟平均值
  const overallAvgData = []   // 所有拨测点的平均延迟平均值
  const overallMaxData = []   // 所有拨测点的最大延迟平均值
  
  // 按时间排序
  const sortedTimeKeys = Object.keys(timeGroups).sort()
  
  sortedTimeKeys.forEach(timeKey => {
    const group = timeGroups[timeKey]
    
    // 计算该时间点所有拨测点的最少延迟平均值
    if (group.rtt_min_values.length > 0) {
      const avgMin = group.rtt_min_values.reduce((sum, val) => sum + val, 0) / group.rtt_min_values.length
      overallMinData.push(parseFloat(avgMin.toFixed(2)))
    } else {
      overallMinData.push(0)
    }
    
    // 计算该时间点所有拨测点的平均延迟平均值
    if (group.rtt_avg_values.length > 0) {
      const avgAvg = group.rtt_avg_values.reduce((sum, val) => sum + val, 0) / group.rtt_avg_values.length
      overallAvgData.push(parseFloat(avgAvg.toFixed(2)))
    } else {
      overallAvgData.push(0)
    }
    
    // 计算该时间点所有拨测点的最大延迟平均值
    if (group.rtt_max_values.length > 0) {
      const avgMax = group.rtt_max_values.reduce((sum, val) => sum + val, 0) / group.rtt_max_values.length
      overallMaxData.push(parseFloat(avgMax.toFixed(2)))
    } else {
      overallMaxData.push(0)
    }
    
    // 格式化时间显示，包含日期和时间
    const date = new Date(timeKey)
    // 根据时间范围调整时间显示格式
    const timeRangeInDays = calculateTimeRangeInDays(sortedResults)
    
    if (timeRangeInDays <= 1) {
      // 时间范围在1天内，显示小时:分钟
      timeData.push(date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }))
    } else if (timeRangeInDays <= 7) {
      // 时间范围在1周内，显示月-日 小时:分钟
      timeData.push(date.toLocaleString('zh-CN', { 
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }))
    } else {
      // 时间范围超过1周，显示月-日
      timeData.push(date.toLocaleDateString('zh-CN', { 
        month: '2-digit',
        day: '2-digit'
      }))
    }
  })

  const option = {
    title: {
      text: '延迟时间序列图',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['最少延迟平均值', '平均延迟平均值', '最大延迟平均值'],
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: timeData
    },
    yAxis: {
      type: 'value',
      name: '延迟 (ms)'
    },
    series: [
      {
        name: '最少延迟平均值',
        type: 'line',
        data: overallMinData,
        smooth: true
      },
      {
        name: '平均延迟平均值',
        type: 'line',
        data: overallAvgData,
        smooth: true
      },
      {
        name: '最大延迟平均值',
        type: 'line',
        data: overallMaxData,
        smooth: true
      }
    ]
  }

  latencyChart.setOption(option)
}

// 计算时间范围（天数）
const calculateTimeRangeInDays = (results) => {
  if (!results || results.length === 0) return 0
  
  const times = results.map(r => new Date(r.created_at).getTime())
  const minTime = Math.min(...times)
  const maxTime = Math.max(...times)
  
  return (maxTime - minTime) / (1000 * 60 * 60 * 24)
}

// 渲染TCP任务详情图表
const renderTcpCharts = () => {
  // 按创建时间排序
  const sortedResults = [...props.results].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  
  // 准备时间序列数据
  const timeData = sortedResults.map(result => {
    // 格式化时间显示
    const date = new Date(result.created_at)
    return date.toLocaleTimeString('zh-CN', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  })
  
  // 准备连通性数据
  const connectedData = sortedResults.map(result => {
    try {
      const details = typeof result.details === 'string' 
        ? JSON.parse(result.details) 
        : result.details
      return details.connected ? 1 : 0
    } catch (e) {
      return 0
    }
  })
  
  // 准备响应时间数据 (转换为毫秒)
  const responseTimeData = sortedResults.map(result => {
    try {
      const details = typeof result.details === 'string' 
        ? JSON.parse(result.details) 
        : result.details
      // TCP插件返回的是秒，转换为毫秒
      return details.execution_time ? details.execution_time * 1000 : 0
    } catch (e) {
      return 0
    }
  })
  
  // 准备状态和返回码数据
  const statusData = sortedResults.map(result => {
    try {
      const details = typeof result.details === 'string' 
        ? JSON.parse(result.details) 
        : result.details
      return details.return_code || 0
    } catch (e) {
      return -1 // 表示解析失败
    }
  })
  
  // 渲染连通性图表
  if (tcpConnectedChartRef.value) {
    if (tcpConnectedChart) {
      tcpConnectedChart.dispose()
    }
    tcpConnectedChart = echarts.init(tcpConnectedChartRef.value)
    const connectedOption = {
      title: {
        text: 'TCP连通性',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          const param = params[0]
          return `${param.name}<br/>${param.seriesName}: ${param.value === 1 ? '连通' : '未连通'}`
        }
      },
      xAxis: {
        type: 'category',
        data: timeData
      },
      yAxis: {
        type: 'value',
        name: '连通状态',
        axisLabel: {
          formatter: function(value) {
            return value === 1 ? '连通' : '未连通'
          }
        }
      },
      series: [{
        name: '连通性',
        type: 'line',
        step: 'middle',
        data: connectedData,
        markLine: {
          silent: true,
          data: [{
            yAxis: 1,
            lineStyle: {
              color: '#52c41a'
            },
            label: {
              show: false
            }
          }, {
            yAxis: 0,
            lineStyle: {
              color: '#f5222d'
            },
            label: {
              show: false
            }
          }]
        }
      }]
    }
    tcpConnectedChart.setOption(connectedOption)
  }
  
  // 渲染响应时间图表
  if (tcpResponseTimeChartRef.value) {
    if (tcpResponseTimeChart) {
      tcpResponseTimeChart.dispose()
    }
    tcpResponseTimeChart = echarts.init(tcpResponseTimeChartRef.value)
    const responseTimeOption = {
      title: {
        text: '响应时间',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: timeData
      },
      yAxis: {
        type: 'value',
        name: '响应时间 (毫秒)'
      },
      series: [{
        name: '响应时间',
        type: 'line',
        data: responseTimeData,
        smooth: true
      }]
    }
    tcpResponseTimeChart.setOption(responseTimeOption)
  }
  
  // 渲染状态码图表
  if (tcpStatusChartRef.value) {
    if (tcpStatusChart) {
      tcpStatusChart.dispose()
    }
    tcpStatusChart = echarts.init(tcpStatusChartRef.value)
    const statusOption = {
      title: {
        text: '连接返回码',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: timeData
      },
      yAxis: {
        type: 'value',
        name: '返回码'
      },
      series: [{
        name: '返回码',
        type: 'line',
        data: statusData,
        step: 'middle'
      }]
    }
    tcpStatusChart.setOption(statusOption)
  }
}
</script>