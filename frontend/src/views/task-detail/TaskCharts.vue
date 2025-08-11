<template>
  <div v-if="taskType === 'ping'">
    <div ref="latencyChartRef" style="width: 100%; height: 400px; margin-top: 20px;"></div>
  </div>
  <div v-else-if="taskType === 'tcp'">
    <div ref="tcpConnectedChartRef" style="width: 100%; height: 300px; margin-top: 20px;"></div>
    <div ref="tcpResponseTimeChartRef" style="width: 100%; height: 300px; margin-top: 20px;"></div>
    <div ref="tcpStatusChartRef" style="width: 100%; height: 300px; margin-top: 20px;"></div>
  </div>
  <div v-else>
    <a-empty description="暂不支持该类型任务的图表展示" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

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
  () => {
    nextTick(() => {
      renderCharts()
    })
  },
  { deep: true }
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
  
  // 准备延迟数据
  const rttMinData = []
  const rttAvgData = []
  const rttMaxData = []
  
  sortedResults.forEach(result => {
    try {
      const details = typeof result.details === 'string' 
        ? JSON.parse(result.details) 
        : result.details
      
      rttMinData.push(details.rtt_min || 0)
      rttAvgData.push(details.rtt_avg || 0)
      rttMaxData.push(details.rtt_max || 0)
    } catch (e) {
      // 解析失败时使用默认值
      rttMinData.push(0)
      rttAvgData.push(0)
      rttMaxData.push(0)
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
      data: ['最小延迟', '平均延迟', '最大延迟'],
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
        name: '最小延迟',
        type: 'line',
        data: rttMinData,
        smooth: true
      },
      {
        name: '平均延迟',
        type: 'line',
        data: rttAvgData,
        smooth: true
      },
      {
        name: '最大延迟',
        type: 'line',
        data: rttMaxData,
        smooth: true
      }
    ]
  }

  latencyChart.setOption(option)
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