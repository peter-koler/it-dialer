<template>
  <a-row :gutter="[16, 16]" class="chart-section">
    <a-col :span="12">
      <a-card title="拨测点结果统计" :bordered="false">
        <div ref="pieChartRef" style="height: 300px;"></div>
      </a-card>
    </a-col>
    <a-col :span="12">
      <a-card title="拨测点平均响应时间" :bordered="false">
        <div ref="lineChartRef" style="height: 300px;"></div>
      </a-card>
    </a-col>
  </a-row>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  agentAggregatedResults: {
    type: Array,
    default: () => []
  }
})

// 图表相关
const pieChartRef = ref(null)
const lineChartRef = ref(null)
let pieChart = null
let lineChart = null

// 初始化饼图
const initPieChart = () => {
  if (!pieChartRef.value) return
  
  pieChart = echarts.init(pieChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}次 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '拨测结果统计',
        type: 'pie',
        radius: '50%',
        data: [],
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
  
  pieChart.setOption(option)
}

// 初始化折线图
const initLineChart = () => {
  if (!lineChartRef.value) return
  
  lineChart = echarts.init(lineChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = params[0].axisValue + '<br/>'
        params.forEach(param => {
          if (param.value !== null) {
            result += param.marker + param.seriesName + ': ' + param.value + 'ms<br/>'
          }
        })
        return result
      }
    },
    legend: {
      data: []
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
      data: []
    },
    yAxis: {
      type: 'value',
      name: '响应时间(ms)'
    },
    series: []
  }
  
  lineChart.setOption(option)
}

// 更新饼图数据
const updatePieChart = () => {
  if (!pieChart || pieChart.isDisposed()) {
    return
  }
  
  // 延迟执行，避免在主进程中调用setOption
  setTimeout(() => {
    if (!pieChart || pieChart.isDisposed()) {
      return
    }
    
    // 如果没有数据，清空图表
    if (!props.agentAggregatedResults || props.agentAggregatedResults.length === 0) {
      pieChart.setOption({
        series: [{
          name: '拨测结果统计',
          type: 'pie',
          radius: '50%',
          data: [],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }, false)
      return
    }
    
    // 计算总的成功和失败次数
    let totalSuccess = 0
    let totalFailure = 0
    
    // 遍历所有位置的探针数据
    props.agentAggregatedResults.forEach(locationGroup => {
      if (locationGroup.probes && Array.isArray(locationGroup.probes)) {
        locationGroup.probes.forEach(probe => {
          if (probe.status === 'success' || probe.status === 1) {
            totalSuccess++
          } else {
            totalFailure++
          }
        })
      }
    })
    
    const data = [
      { value: totalSuccess, name: '成功', itemStyle: { color: '#52c41a' } },
      { value: totalFailure, name: '失败', itemStyle: { color: '#ff4d4f' } }
    ]
    
    pieChart.setOption({
      series: [{
        name: '拨测结果统计',
        type: 'pie',
        radius: '50%',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }, true) // 使用merge模式，确保图表正确更新
  }, 0)
}

// 更新折线图数据
const updateLineChart = () => {
  if (!lineChart || lineChart.isDisposed()) {
    return
  }
  
  // 延迟执行，避免在主进程中调用setOption
  setTimeout(() => {
    if (!lineChart || lineChart.isDisposed()) {
      return
    }
  
    // 如果没有数据，清空图表
    if (!props.agentAggregatedResults || props.agentAggregatedResults.length === 0) {
      lineChart.setOption({
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
        },
        yAxis: {
          type: 'value',
          name: '响应时间(ms)'
        },
        legend: {
          data: []
        },
        series: []
      }, false) // 清空时不使用merge模式，完全替换
      return
    }
  
    // 收集所有探针数据 - 注意：这里应该使用已经经过时间筛选的数据
    // 而不是从probes数组中获取所有历史数据
    const allProbes = []
    props.agentAggregatedResults.forEach(locationGroup => {
      if (locationGroup.probes && Array.isArray(locationGroup.probes)) {
        // 只使用当前时间范围内的探针数据
        locationGroup.probes.forEach(probe => {
          allProbes.push({
            ...probe,
            location: locationGroup.location
          })
        })
      }
    })
  
    if (allProbes.length === 0) {
      // 如果没有数据，清空图表
      lineChart.setOption({
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
        },
        yAxis: {
          type: 'value',
          name: '响应时间(ms)'
        },
        legend: {
          data: []
        },
        series: []
      }, false) // 清空时不使用merge模式，完全替换
      return
    }
  
    // 按时间排序数据
    const sortedData = allProbes.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    
    // 按位置分组数据
    const locationGroups = {}
    sortedData.forEach(item => {
      if (!locationGroups[item.location]) {
        locationGroups[item.location] = []
      }
      locationGroups[item.location].push({
        time: new Date(item.created_at).toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        }),
        responseTime: item.response_time || 0
      })
    })
    
    // 获取所有时间点
    const allTimes = [...new Set(sortedData.map(item => 
      new Date(item.created_at).toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit', 
        hour: '2-digit',
        minute: '2-digit'
      })
    ))].sort()
    
    // 为每个位置创建系列数据
    const series = Object.keys(locationGroups).map(location => {
      const locationData = locationGroups[location]
      const data = allTimes.map(time => {
        const found = locationData.find(item => item.time === time)
        return found ? found.responseTime : null
      })
      
      return {
        name: location,
        type: 'line',
        data: data,
        connectNulls: false
      }
    })
  
    lineChart.setOption({
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: allTimes
      },
      yAxis: {
        type: 'value',
        name: '响应时间(ms)'
      },
      legend: {
        data: Object.keys(locationGroups)
      },
      series: series
    }, true) // 使用merge模式，确保图表正确更新
  }, 0)
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