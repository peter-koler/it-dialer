<template>
  <a-row :gutter="[16, 16]" class="chart-section">
    <a-col :span="12">
      <a-card title="TCP连接状态分布" :bordered="false">
        <div ref="pieChartRef" style="height: 300px;"></div>
      </a-card>
    </a-col>
    <a-col :span="12">
      <a-card title="TCP响应时间趋势" :bordered="false">
        <div ref="lineChartRef" style="height: 300px;"></div>
      </a-card>
    </a-col>
  </a-row>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, defineProps } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import pinyinToChinese from '@/utils/pinyinToChinese'

const props = defineProps({
  agentAggregatedResults: {
    type: Array,
    default: () => []
  }
})

const pieChartRef = ref(null)
const lineChartRef = ref(null)
let pieChart = null
let lineChart = null

// 初始化饼图
const initPieChart = () => {
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
  }
}

// 初始化折线图
const initLineChart = () => {
  if (lineChartRef.value) {
    lineChart = echarts.init(lineChartRef.value)
  }
}

// 更新饼图数据
const updatePieChart = () => {
  if (!pieChart || !props.agentAggregatedResults.length) return
  
  // 统计连接状态
  const statusCount = {
    success: 0,
    failed: 0
  }
  
  props.agentAggregatedResults.forEach(result => {
    if (result.status === 'success') {
      statusCount.success += result.count || 1
    } else {
      statusCount.failed += result.count || 1
    }
  })
  
  const pieData = [
    { value: statusCount.success, name: '连接成功', itemStyle: { color: '#52c41a' } },
    { value: statusCount.failed, name: '连接失败', itemStyle: { color: '#ff4d4f' } }
  ]
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: ['连接成功', '连接失败']
    },
    series: [
      {
        name: 'TCP连接状态',
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
  
  pieChart.setOption(option, true)
}

// 更新折线图数据
const updateLineChart = () => {
  if (!lineChart || !props.agentAggregatedResults.length) return
  
  // 按地区分组数据
  const locationGroups = {}
  props.agentAggregatedResults.forEach(result => {
    // 获取地域信息的优先级：
    // 1. 如果location字段已经是中文地名，直接使用
    // 2. 从probes数组中获取agent_area信息
    // 3. 尝试从agent_id或agent_area字段获取并转换
    let location = result.location
    
    // 如果location不存在、为空或为'Unknown'，尝试其他方式获取地域信息
     if (!location || location === 'Unknown' || location === '未知地区') {
       // 优先从probes数组中获取地域信息
       if (result.probes && result.probes.length > 0) {
         const firstProbe = result.probes[0]
         
         // 尝试从probe的agent_area获取（可能是中文或拼音）
         if (firstProbe.agent_area) {
           // 如果agent_area已经是中文，直接使用
           if (firstProbe.agent_area.match(/[\u4e00-\u9fa5]/)) {
             location = firstProbe.agent_area
           } else {
             // 如果是拼音，尝试转换
             const area = firstProbe.agent_area.toLowerCase()
             location = pinyinToChinese[area] || firstProbe.agent_area
           }
         }
         // 尝试从probe的agent_id获取
         else if (firstProbe.agent_id) {
           const agentId = firstProbe.agent_id.toLowerCase()
           location = pinyinToChinese[agentId] || firstProbe.agent_id
         }
       }
       
       // 如果probes中没有找到，尝试从result本身的字段获取
       if (!location || location === 'Unknown' || location === '未知地区') {
         if (result.agent_area) {
           // 如果agent_area已经是中文，直接使用
           if (result.agent_area.match(/[\u4e00-\u9fa5]/)) {
             location = result.agent_area
           } else {
             // 如果是拼音，尝试转换
             const area = result.agent_area.toLowerCase()
             location = pinyinToChinese[area] || result.agent_area
           }
         } else if (result.agent_id) {
           const agentId = result.agent_id.toLowerCase()
           location = pinyinToChinese[agentId] || result.agent_id
         } else {
           location = '未知地区'
         }
       }
     }
     
     // 如果location字段本身包含中文但不是标准地名，也进行处理
     else if (location && location.match(/[\u4e00-\u9fa5]/)) {
       // 如果已经是中文地名，保持不变
       // 这里可以添加地名标准化逻辑，比如将'广州'统一为'广州市'
       if (location === '广州') {
         location = '广州市'
       }
     }
    
    if (!locationGroups[location]) {
      locationGroups[location] = []
    }
    locationGroups[location].push(result)
  })
  
  // 生成时间轴（最近24小时）
  const timePoints = []
  const now = dayjs()
  for (let i = 23; i >= 0; i--) {
    timePoints.push(now.subtract(i, 'hour').format('HH:mm'))
  }
  
  // 为每个地区生成数据系列
  const series = Object.keys(locationGroups).map(location => {
    const locationData = locationGroups[location]
    
    // 生成模拟的响应时间数据（实际项目中应该从真实数据计算）
    const data = timePoints.map(() => {
      if (locationData.length > 0) {
        const avgResponseTime = locationData.reduce((sum, item) => {
          return sum + (parseFloat(item.response_time) || 0)
        }, 0) / locationData.length
        
        // 添加一些随机波动
        const variation = (Math.random() - 0.5) * avgResponseTime * 0.2
        return Math.max(0, avgResponseTime + variation)
      }
      return 0
    })
    
    return {
      name: location,
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: {
        width: 2
      }
    }
  })
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: function(params) {
        let result = params[0].name + '<br/>'
        params.forEach(param => {
          result += param.marker + param.seriesName + ': ' + param.value.toFixed(2) + 'ms<br/>'
        })
        return result
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timePoints,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '响应时间(ms)'
    },
    legend: {
      data: Object.keys(locationGroups)
    },
    series: series
  }
  
  lineChart.setOption(option, true)
}

// 处理窗口大小变化
const handleResize = () => {
  if (pieChart) {
    pieChart.resize()
  }
  if (lineChart) {
    lineChart.resize()
  }
}

// 监听数据变化
watch(() => props.agentAggregatedResults, () => {
  nextTick(() => {
    updatePieChart()
    updateLineChart()
  })
}, { deep: true, immediate: true })

// 组件挂载
onMounted(() => {
  initPieChart()
  initLineChart()
  
  // 等待DOM更新后再更新图表数据
  nextTick(() => {
    updatePieChart()
    updateLineChart()
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

// 组件卸载
onUnmounted(() => {
  if (pieChart) {
    pieChart.dispose()
  }
  if (lineChart) {
    lineChart.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.chart-section {
  margin-top: 16px;
}
</style>