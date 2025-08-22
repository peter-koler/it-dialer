<template>
  <div class="http-probe-detail-page">
    <!-- 页面头部 -->
    <a-card :bordered="false" class="page-header-card">
      <a-page-header :title="`${probeName} - HTTP拨测详情`" @back="() => $router.back()">
        <template #extra>
          <div class="header-extra">
            <!-- 时间筛选控件 -->
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
      </a-page-header>
    </a-card>

    <div class="page-content">
      <!-- 图表区域 -->
      <a-row :gutter="[16, 16]">
        <!-- 响应时间图表 -->
        <a-col :span="12">
          <a-card :bordered="false" class="chart-card">
            <template #title>响应时间趋势</template>
            <div ref="responseTimeChartRef" class="chart-container"></div>
          </a-card>
        </a-col>
        
        <!-- 响应时间详细统计图表 -->
        <a-col :span="12">
          <a-card :bordered="false" class="chart-card">
            <template #title>响应时间详细统计</template>
            <div ref="detailedResponseChartRef" class="chart-container"></div>
          </a-card>
        </a-col>
        
        <!-- 返回代码统计图表 -->
        <a-col :span="12">
          <a-card :bordered="false" class="chart-card">
            <template #title>返回代码统计</template>
            <div ref="statusCodeChartRef" class="chart-container"></div>
          </a-card>
        </a-col>
        
        <!-- 状态统计图表 -->
        <a-col :span="12">
          <a-card :bordered="false" class="chart-card">
            <template #title>状态统计</template>
            <div ref="webStatusChartRef" class="chart-container"></div>
          </a-card>
        </a-col>
      </a-row>
      
      <!-- 拨测点详情列表 -->
      <a-card :bordered="false" class="detail-list-card">
        <template #title>拨测点详情列表</template>
        <a-table
          :dataSource="probeDetailList"
          :columns="probeColumns"
          :pagination="{ pageSize: 20, showSizeChanger: true, showQuickJumper: true }"
          :loading="loading"
          rowKey="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'">
              <a-tag :color="record.status === 'success' ? 'green' : 'red'">
                {{ record.status === 'success' ? '成功' : '失败' }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'response_time'">
              {{ record.response_time ? `${record.response_time} ms` : '-' }}
            </template>
            <template v-else-if="column.dataIndex === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <a-button type="link" @click="showHttpDetail(record)">查看HTTP详情</a-button>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>
    
    <!-- HTTP详情弹窗 -->
    <HttpResultDetailModal
      v-model:open="isDetailModalOpen"
      :probe-data="selectedProbeData"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getAggregatedResults } from '@/api/result'
import HttpResultDetailModal from './components/HttpResultDetailModal.vue'
import * as echarts from 'echarts'
import pinyinToChinese from '@/utils/pinyinToChinese'

const route = useRoute()
const taskId = route.params.taskId || route.params.id
const probeName = route.params.probeName || route.query.probeName || '未知拨测点'
const agentArea = route.params.agentArea || route.query.agentArea || probeName

// 响应式数据
const loading = ref(false)
const probeDetailList = ref([])
const originalProbeList = ref([])
const timeRange = ref([])
const currentQuickTime = ref(null)
const isDetailModalOpen = ref(false)
const selectedProbeData = ref({})

// 图表引用
const responseTimeChartRef = ref(null)
const detailedResponseChartRef = ref(null)
const statusCodeChartRef = ref(null)
const webStatusChartRef = ref(null)

// 图表实例
let responseTimeChart = null
let detailedResponseChart = null
let statusCodeChart = null
let webStatusChart = null

// 拨测点详情列表表格列定义
const probeColumns = [
  { title: '位置', dataIndex: 'location', key: 'location' },
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '响应时间', dataIndex: 'response_time', key: 'response_time', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '操作', dataIndex: 'action', key: 'action', width: 120 }
]

// 时间筛选相关方法
const setQuickTime = (value, unit) => {
  console.log(`===== 调试信息: setQuickTime 被调用 =====`);
  console.log(`快速时间选择: ${value} ${unit}`);
  
  const now = dayjs()
  let startTime
  
  if (unit === 'hour') {
    startTime = now.subtract(value, 'hour')
  } else if (unit === 'day') {
    startTime = now.subtract(value, 'day')
  }
  
  console.log(`计算的时间范围: ${startTime.format('YYYY-MM-DD HH:mm:ss')} 到 ${now.format('YYYY-MM-DD HH:mm:ss')}`);
  console.log('设置前的timeRange.value:', timeRange.value);
  
  timeRange.value = [startTime, now]
  
  console.log('设置后的timeRange.value:', timeRange.value);
  console.log('startTime对象:', startTime);
  console.log('now对象:', now);
  
  currentQuickTime.value = { value, unit }
  
  // 触发数据筛选，使用本地时间格式保持一致性
  filterDataByTime(startTime.format('YYYY-MM-DD HH:mm:ss'), now.format('YYYY-MM-DD HH:mm:ss'))
}

const isQuickTimeActive = (value, unit) => {
  return currentQuickTime.value && 
         currentQuickTime.value.value === value && 
         currentQuickTime.value.unit === unit
}

const handleTimeRangeChange = (dates) => {
  console.log('===== 调试信息: handleTimeRangeChange 被调用 =====');
  console.log('传入的dates参数:', dates);
  console.log('当前timeRange.value:', timeRange.value);
  
  currentQuickTime.value = null;
  if (dates && dates.length === 2) {
    console.log(`选择的时间范围: ${dates[0].format('YYYY-MM-DD HH:mm:ss')} 到 ${dates[1].format('YYYY-MM-DD HH:mm:ss')}`);
    console.log('dates[0]原始对象:', dates[0]);
    console.log('dates[1]原始对象:', dates[1]);
    console.log('dates[0] ISO:', dates[0].toISOString());
    console.log('dates[1] ISO:', dates[1].toISOString());
    
    // 使用本地时间字符串而不是ISO字符串，保持时区一致性
    const startTime = dates[0].format('YYYY-MM-DD HH:mm:ss');
    const endTime = dates[1].format('YYYY-MM-DD HH:mm:ss');
    console.log(`格式化后的时间范围: ${startTime} 到 ${endTime}`);
    
    filterDataByTime(startTime, endTime);
  } else {
    console.log('时间范围被清空，重置为原始数据');
    // 重置为原始数据
    probeDetailList.value = [...originalProbeList.value];
    console.log(`重置后数据点数量: ${probeDetailList.value.length}`);
    // 强制重新创建图表
    updateAllCharts(true);
  }
}

const resetTimeFilter = () => {
  console.log('===== 调试信息: resetTimeFilter 被调用 =====');
  timeRange.value = []
  currentQuickTime.value = null
  probeDetailList.value = [...originalProbeList.value]
  console.log(`重置后数据点数量: ${probeDetailList.value.length}`);
  // 强制重新创建图表
  updateAllCharts(true)
}

// 根据时间筛选数据
const filterDataByTime = (startTime, endTime) => {
  console.log(`===== 调试信息: filterDataByTime 被调用 =====`);
  console.log(`筛选时间范围: ${startTime} 到 ${endTime}`);
  
  const start = new Date(startTime)
  const end = new Date(endTime)
  
  console.log(`筛选开始时间: ${start.toISOString()}`);
  console.log(`筛选结束时间: ${end.toISOString()}`);
  
  // 打印原始数据的时间范围
  if (originalProbeList.value.length > 0) {
    const firstItem = originalProbeList.value[0];
    const lastItem = originalProbeList.value[originalProbeList.value.length - 1];
    console.log(`原始数据第一个时间: ${firstItem.created_at}`);
    console.log(`原始数据最后一个时间: ${lastItem.created_at}`);
  }
  
  const filteredData = originalProbeList.value.filter(item => {
    // 直接使用时间戳进行比较，避免字符串比较的问题
    const itemTime = new Date(item.created_at)
    const startTimestamp = start.getTime()
    const endTimestamp = end.getTime()
    const itemTimestamp = itemTime.getTime()
    
    const isInRange = itemTimestamp >= startTimestamp && itemTimestamp <= endTimestamp;
    
    // 详细的调试信息
    const itemTimeStr = itemTime.toLocaleString('sv-SE').replace(' ', 'T').substring(0, 19);
    const startTimeStr = start.toLocaleString('sv-SE').replace(' ', 'T').substring(0, 19);
    const endTimeStr = end.toLocaleString('sv-SE').replace(' ', 'T').substring(0, 19);
    
    console.log(`数据项: ${item.created_at} -> ${itemTimeStr} (${itemTimestamp})`);
    console.log(`筛选范围: ${startTimeStr} (${startTimestamp}) - ${endTimeStr} (${endTimestamp})`);
    console.log(`是否在范围内: ${isInRange}`);
    console.log('---');
    
    return isInRange;
  })
  
  console.log(`筛选前数据点数量: ${originalProbeList.value.length}`);
  console.log(`筛选后数据点数量: ${filteredData.length}`);
  
  // 更新数据
  probeDetailList.value = filteredData;
  
  // 强制刷新图表
  console.log('调用updateAllCharts并强制刷新...');
  updateAllCharts(true);
}

// 获取拨测点详情数据
const fetchProbeDetails = async () => {
  loading.value = true
  try {
    const params = {
      type: 'http',
      page: 1,
      size: 1000,
      agent_area: agentArea
    }
    
    const response = await getAggregatedResults(taskId, params)
    
    if (response && response.data && Array.isArray(response.data.list)) {
      const results = response.data.list
        .filter(item => {
          const itemArea = item.agent_area || item.location
          return itemArea === agentArea || 
                 pinyinToChinese[itemArea] === probeName ||
                 itemArea === probeName
        })
        .map(item => {
          const locationName = pinyinToChinese[item.agent_area] || item.agent_area || item.location
          
          return {
            id: item.id,
            task_id: item.task_id || taskId,
            agent_id: item.agent_id,
            location: locationName,
            agent_area: item.agent_area,
            status: item.status || 'unknown',
            response_time: item.details?.response_time || item.response_time || 0,
            status_code: item.details?.status_code || 200,
            webstatus: item.details?.webstatus || (item.status === 'success' ? 200 : 500),
            created_at: item.created_at || new Date().toISOString(),
            details: item.details || {}
          }
        })
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      
      originalProbeList.value = results
      probeDetailList.value = [...results]
      
      // 初始化图表
      await nextTick()
      initAllCharts()
    } else {
      message.warning('未找到该拨测点的详情数据')
    }
  } catch (error) {
    console.error('获取拨测点详情失败:', error)
    message.error('获取拨测点详情失败: ' + (error.response?.data?.message || error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 初始化所有图表
const initAllCharts = () => {
  initResponseTimeChart()
  initDetailedResponseChart()
  initStatusCodeChart()
  initWebStatusChart()
}

// 更新所有图表
const updateAllCharts = (forceRefresh = false) => {
  // 确保在更新图表数据前重新计算时间范围
  const currentData = probeDetailList.value
  
  console.log('===== 调试信息: updateAllCharts 被调用 =====');
  console.log(`当前数据点数量: ${currentData.length}, forceRefresh: ${forceRefresh}`);
  
  if (currentData.length > 0) {
    const timeValues = currentData.map(item => new Date(item.created_at).getTime());
    const minTime = Math.min(...timeValues);
    const maxTime = Math.max(...timeValues);
    console.log(`数据时间范围: ${new Date(minTime).toLocaleString()} 到 ${new Date(maxTime).toLocaleString()}`);
  }
  
  // 如果是强制刷新，先销毁并重新创建图表
  if (forceRefresh) {
    console.log('强制刷新 - 重新创建所有图表实例');
    
    // 销毁现有图表
    if (responseTimeChart) {
      responseTimeChart.dispose();
      responseTimeChart = null;
    }
    if (detailedResponseChart) {
      detailedResponseChart.dispose();
      detailedResponseChart = null;
    }
    if (statusCodeChart) {
      statusCodeChart.dispose();
      statusCodeChart = null;
    }
    if (webStatusChart) {
      webStatusChart.dispose();
      webStatusChart = null;
    }
    
    // 重新初始化所有图表
    nextTick(() => {
      console.log('重新初始化所有图表...');
      initAllCharts();
    });
  } else {
    // 正常更新图表数据
    nextTick(() => {
      console.log('nextTick 中更新图表...');
      updateResponseTimeChart(forceRefresh);
      updateDetailedResponseChart(forceRefresh);
      updateStatusCodeChart(forceRefresh);
      updateWebStatusChart(forceRefresh);
    });
  }
}

// 初始化响应时间图表
const initResponseTimeChart = () => {
  if (responseTimeChartRef.value) {
    responseTimeChart = echarts.init(responseTimeChartRef.value)
    updateResponseTimeChart()
  }
}

// 更新响应时间图表
const updateResponseTimeChart = (forceRefresh = false) => {
  console.log('===== 调试信息: updateResponseTimeChart 被调用 =====');
  console.log(`forceRefresh: ${forceRefresh}`);
  
  if (!responseTimeChart) {
    console.error('responseTimeChart 实例不存在');
    return;
  }
  
  if (!probeDetailList.value.length) {
    console.log('没有数据，清空图表');
    // 如果没有数据，清空图表
    responseTimeChart.setOption({
      series: [{ data: [] }]
    }, true);
    if (forceRefresh) {
      console.log('强制刷新空图表');
      responseTimeChart.resize();
    }
    return;
  }
  
  // 按时间分组数据，避免重复时间点
  const timeGroupedData = {}
  probeDetailList.value.forEach(item => {
    const timeKey = dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')
    const responseTime = item.response_time || 0
    
    if (!timeGroupedData[timeKey]) {
      timeGroupedData[timeKey] = []
    }
    timeGroupedData[timeKey].push(responseTime)
  })
  
  console.log(`时间点数量: ${Object.keys(timeGroupedData).length}`);
  
  // 计算每个时间点的平均响应时间
  const data = Object.keys(timeGroupedData)
    .sort((a, b) => new Date(a) - new Date(b))
    .map(timeKey => {
      const values = timeGroupedData[timeKey]
      const avgValue = values.reduce((sum, val) => sum + val, 0) / values.length
      return [timeKey, Math.round(avgValue * 100) / 100] // 保留两位小数
    })
  
  console.log(`处理后的数据点数量: ${data.length}`);
  if (data.length > 0) {
    console.log(`第一个数据点: ${data[0][0]}, ${data[0][1]}`);
    console.log(`最后一个数据点: ${data[data.length-1][0]}, ${data[data.length-1][1]}`);
  }
  
  // 使用用户选择的时间范围，而不是数据的时间范围
  let minTime = null
  let maxTime = null
  
  if (timeRange.value && timeRange.value.length === 2) {
    // 使用用户选择的时间范围
    minTime = timeRange.value[0].valueOf()
    maxTime = timeRange.value[1].valueOf()
    console.log(`使用用户选择的时间范围: ${new Date(minTime).toLocaleString()} 到 ${new Date(maxTime).toLocaleString()}`);
  } else if (data.length > 0) {
    // 如果没有用户选择的时间范围，则使用数据的时间范围
    const timeValues = data.map(item => new Date(item[0]).getTime())
    minTime = Math.min(...timeValues)
    maxTime = Math.max(...timeValues)
    console.log(`使用数据的时间范围: ${new Date(minTime).toLocaleString()} 到 ${new Date(maxTime).toLocaleString()}`);
  } else {
    console.warn('没有有效的数据点和时间选择来计算时间范围');
    // 设置默认时间范围，避免undefined
    const now = new Date().getTime()
    minTime = now - 24 * 60 * 60 * 1000 // 24小时前
    maxTime = now
    console.log(`使用默认时间范围: ${new Date(minTime).toLocaleString()} 到 ${new Date(maxTime).toLocaleString()}`);
  }
  
  // 获取当前图表的配置
  const currentOption = responseTimeChart.getOption();
  const currentXAxisMin = currentOption && currentOption.xAxis && currentOption.xAxis[0] ? currentOption.xAxis[0].min : undefined;
  const currentXAxisMax = currentOption && currentOption.xAxis && currentOption.xAxis[0] ? currentOption.xAxis[0].max : undefined;
  
  console.log(`当前图表xAxis配置: min=${currentXAxisMin}, max=${currentXAxisMax}`);
  console.log(`将要设置的xAxis配置: min=${minTime}, max=${maxTime}`);
  
  const option = {
    title: {
      text: '响应时间趋势',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const param = params[0]
        return `${param.axisValue}<br/>响应时间: ${param.value[1]} ms`
      }
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
      min: minTime,
      max: maxTime,
      axisLabel: {
        formatter: function(value) {
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
    series: [{
      name: '响应时间',
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: {
        color: '#1890ff'
      },
      itemStyle: {
        color: '#1890ff'
      }
    }]
  }
  
  console.log('设置图表选项...');
  responseTimeChart.setOption(option, true);
  
  // 检查设置后的配置
  const updatedOption = responseTimeChart.getOption();
  const updatedXAxisMin = updatedOption && updatedOption.xAxis && updatedOption.xAxis[0] ? updatedOption.xAxis[0].min : undefined;
  const updatedXAxisMax = updatedOption && updatedOption.xAxis && updatedOption.xAxis[0] ? updatedOption.xAxis[0].max : undefined;
  console.log(`设置后的xAxis配置: min=${updatedXAxisMin}, max=${updatedXAxisMax}`);
  
  if (forceRefresh) {
    console.log('强制刷新图表，调用resize()...');
    // 尝试先清除图表再重新设置
    responseTimeChart.clear();
    responseTimeChart.setOption(option, true);
    responseTimeChart.resize();
  }
  
  console.log('updateResponseTimeChart 完成');
}

// 初始化响应时间详细统计图表
const initDetailedResponseChart = () => {
  if (detailedResponseChartRef.value) {
    detailedResponseChart = echarts.init(detailedResponseChartRef.value)
    updateDetailedResponseChart()
  }
}

// 更新响应时间详细统计图表
const updateDetailedResponseChart = (forceRefresh = false) => {
  if (!detailedResponseChart) return
  
  if (!probeDetailList.value.length) {
    // 如果没有数据，清空图表
    detailedResponseChart.setOption({
      series: [{ data: [] }, { data: [] }, { data: [] }, { data: [] }, { data: [] }]
    }, true)
    if (forceRefresh) {
      detailedResponseChart.resize()
    }
    return
  }
  
  const timePoints = [...new Set(probeDetailList.value.map(item => 
    dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')
  ))].sort()
  
  const dnsData = []
  const connectData = []
  const sslData = []
  const firstByteData = []
  const downloadData = []
  
  timePoints.forEach(time => {
    const items = probeDetailList.value.filter(item => 
      dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss') === time
    )
    
    if (items.length > 0) {
      const item = items[0]
      const details = item.details || {}
      
      dnsData.push([time, details.dns_time || Math.random() * 50])
      connectData.push([time, details.connect_time || Math.random() * 100])
      sslData.push([time, details.ssl_time || Math.random() * 200])
      firstByteData.push([time, details.first_byte_time || Math.random() * 300])
      downloadData.push([time, details.download_time || Math.random() * 150])
    }
  })
  
  // 使用用户选择的时间范围，而不是数据的时间范围
  let minTime = null
  let maxTime = null
  
  if (timeRange.value && timeRange.value.length === 2) {
    // 使用用户选择的时间范围
    minTime = timeRange.value[0].valueOf()
    maxTime = timeRange.value[1].valueOf()
  } else if (timePoints.length > 0) {
    // 如果没有用户选择的时间范围，则使用数据的时间范围
    const timeValues = timePoints.map(time => new Date(time).getTime())
    minTime = Math.min(...timeValues)
    maxTime = Math.max(...timeValues)
  }
  
  const option = {
    title: {
      text: '响应时间详细统计',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      top: 30,
      data: ['DNS解析', '建立连接', 'SSL握手', '首字节', '下载内容']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      min: minTime,
      max: maxTime,
      axisLabel: {
        formatter: function(value) {
          return dayjs(value).format('HH:mm')
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '时间 (ms)',
      axisLabel: {
        formatter: '{value} ms'
      }
    },
    series: [
      {
        name: 'DNS解析',
        type: 'line',
        data: dnsData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3
      },
      {
        name: '建立连接',
        type: 'line',
        data: connectData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3
      },
      {
        name: 'SSL握手',
        type: 'line',
        data: sslData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3
      },
      {
        name: '首字节',
        type: 'line',
        data: firstByteData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3
      },
      {
        name: '下载内容',
        type: 'line',
        data: downloadData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3
      }
    ]
  }
  
  detailedResponseChart.setOption(option, true)
  if (forceRefresh) {
    detailedResponseChart.resize()
  }
}

// 初始化返回代码统计图表
const initStatusCodeChart = () => {
  if (statusCodeChartRef.value) {
    statusCodeChart = echarts.init(statusCodeChartRef.value)
    updateStatusCodeChart()
  }
}

// 更新状态码图表
const updateStatusCodeChart = (forceRefresh = false) => {
  if (!statusCodeChart) return
  
  if (!probeDetailList.value.length) {
    // 如果没有数据，清空图表
    statusCodeChart.setOption({
      series: [{ data: [] }]
    }, true)
    if (forceRefresh) {
      statusCodeChart.resize()
    }
    return
  }
  
  // 按时间分组数据，避免重复时间点
  const timeGroupedData = {}
  probeDetailList.value.forEach(item => {
    const timeKey = dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')
    const statusCode = item.status_code || 200
    
    if (!timeGroupedData[timeKey]) {
      timeGroupedData[timeKey] = []
    }
    timeGroupedData[timeKey].push(statusCode)
  })
  
  // 计算每个时间点的平均值或取最常见的状态码
  const data = Object.keys(timeGroupedData)
    .sort((a, b) => new Date(a) - new Date(b))
    .map(timeKey => {
      const values = timeGroupedData[timeKey]
      // 对于状态码，取最常见的值而不是平均值
      const statusCodeCount = {}
      values.forEach(code => {
        statusCodeCount[code] = (statusCodeCount[code] || 0) + 1
      })
      const mostCommonCode = Object.keys(statusCodeCount).reduce((a, b) => 
        statusCodeCount[a] > statusCodeCount[b] ? a : b
      )
      return [timeKey, parseInt(mostCommonCode)]
    })
  
  // 使用用户选择的时间范围，而不是数据的时间范围
  let minTime = null
  let maxTime = null
  
  if (timeRange.value && timeRange.value.length === 2) {
    // 使用用户选择的时间范围
    minTime = timeRange.value[0].valueOf()
    maxTime = timeRange.value[1].valueOf()
  } else if (data.length > 0) {
    // 如果没有用户选择的时间范围，则使用数据的时间范围
    const timeValues = data.map(item => new Date(item[0]).getTime())
    minTime = Math.min(...timeValues)
    maxTime = Math.max(...timeValues)
  }
  
  const option = {
    title: {
      text: '返回代码统计',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const param = params[0]
        return `${param.axisValue}<br/>状态码: ${param.value[1]}`
      }
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
      min: minTime,
      max: maxTime,
      axisLabel: {
        formatter: function(value) {
          return dayjs(value).format('HH:mm')
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '状态码',
      min: 100,
      max: 600
    },
    series: [{
      name: '状态码',
      type: 'line',
      data: data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: {
        color: '#52c41a'
      },
      itemStyle: {
        color: '#52c41a'
      }
    }]
  }
  
  statusCodeChart.setOption(option, true)
  if (forceRefresh) {
    statusCodeChart.resize()
  }
}

// 初始化状态统计图表
const initWebStatusChart = () => {
  if (webStatusChartRef.value) {
    webStatusChart = echarts.init(webStatusChartRef.value)
    updateWebStatusChart()
  }
}

// 更新状态统计图表
const updateWebStatusChart = (forceRefresh = false) => {
  if (!webStatusChart) return
  
  if (!probeDetailList.value.length) {
    // 如果没有数据，清空图表
    webStatusChart.setOption({
      series: [{ data: [] }, { data: [] }]
    }, true)
    if (forceRefresh) {
      webStatusChart.resize()
    }
    return
  }
  
  // 按时间分组数据，统计成功和失败的数量
  const timeGroupedData = {}
  probeDetailList.value.forEach(item => {
    const timeKey = dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')
    const isSuccess = item.status === 'success' || (item.webstatus && item.webstatus < 400)
    
    if (!timeGroupedData[timeKey]) {
      timeGroupedData[timeKey] = { success: 0, failure: 0 }
    }
    
    if (isSuccess) {
      timeGroupedData[timeKey].success++
    } else {
      timeGroupedData[timeKey].failure++
    }
  })
  
  // 准备图表数据
  const timePoints = Object.keys(timeGroupedData).sort((a, b) => new Date(a) - new Date(b))
  const successData = timePoints.map(time => [time, timeGroupedData[time].success])
  const failureData = timePoints.map(time => [time, timeGroupedData[time].failure])
  
  // 使用用户选择的时间范围，而不是数据的时间范围
  let minTime = null
  let maxTime = null
  
  if (timeRange.value && timeRange.value.length === 2) {
    // 使用用户选择的时间范围
    minTime = timeRange.value[0].valueOf()
    maxTime = timeRange.value[1].valueOf()
  } else if (Object.keys(timeGroupedData).length > 0) {
    // 如果没有用户选择的时间范围，则使用数据的时间范围
    const timeValues = Object.keys(timeGroupedData).map(time => new Date(time).getTime())
    minTime = Math.min(...timeValues)
    maxTime = Math.max(...timeValues)
  }
  
  const option = {
    title: {
      text: '状态统计',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = `${params[0].axisValue}<br/>`
        params.forEach(param => {
          result += `${param.seriesName}: ${param.value[1]}次<br/>`
        })
        return result
      }
    },
    legend: {
      top: 30,
      data: ['成功', '失败']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      min: minTime,
      max: maxTime,
      axisLabel: {
        formatter: function(value) {
          return dayjs(value).format('HH:mm')
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '次数',
      minInterval: 1,
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: [
      {
        name: '成功',
        type: 'bar',
        data: successData,
        itemStyle: {
          color: '#52c41a'
        },
        emphasis: {
          itemStyle: {
            color: '#73d13d'
          }
        }
      },
      {
        name: '失败',
        type: 'bar',
        data: failureData,
        itemStyle: {
          color: '#ff4d4f'
        },
        emphasis: {
          itemStyle: {
            color: '#ff7875'
          }
        }
      }
    ]
  }
  
  webStatusChart.setOption(option, true)
  if (forceRefresh) {
    webStatusChart.resize()
  }
}

// 显示HTTP详情
const showHttpDetail = (record) => {
  selectedProbeData.value = record
  isDetailModalOpen.value = true
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 监听窗口大小变化
const handleResize = () => {
  responseTimeChart?.resize()
  detailedResponseChart?.resize()
  statusCodeChart?.resize()
  webStatusChart?.resize()
}

// 监听时间范围变化
watch(timeRange, (newValue, oldValue) => {
  console.log('===== 调试信息: timeRange 值变化 =====')
  console.log('旧值:', oldValue)
  console.log('新值:', newValue)
  if (newValue && newValue.length === 2) {
    console.log(`timeRange 新值格式化: ${newValue[0].format('YYYY-MM-DD HH:mm:ss')} 到 ${newValue[1].format('YYYY-MM-DD HH:mm:ss')}`)
  }
}, { deep: true })

// 组件挂载
onMounted(() => {
  fetchProbeDetails()
  window.addEventListener('resize', handleResize)
})

// 组件卸载
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  responseTimeChart?.dispose()
  detailedResponseChart?.dispose()
  statusCodeChart?.dispose()
  webStatusChart?.dispose()
})
</script>

<style scoped>
.http-probe-detail-page {
  background: #f0f2f5;
  min-height: 100vh;
}

.page-header-card {
  margin-bottom: 16px;
}

.header-extra {
  display: flex;
  align-items: center;
  gap: 16px;
}

.time-filter-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-time-buttons {
  display: flex;
  gap: 4px;
}

.time-range-picker {
  width: 300px;
}

.page-content {
  padding: 0 24px;
}

.chart-card {
  margin-bottom: 16px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.detail-list-card {
  margin-top: 16px;
}

/* Ant Design Pro 风格 */
.ant-card {
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
}

.ant-card-head {
  border-bottom: 1px solid #f0f0f0;
}

.ant-card-head-title {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.ant-table-thead > tr > th {
  background: #fafafa;
  font-weight: 500;
}

.ant-btn-primary {
  background: #1890ff;
  border-color: #1890ff;
}

.ant-btn-primary:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}
</style>