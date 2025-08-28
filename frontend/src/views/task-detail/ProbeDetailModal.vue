<template>
  <a-modal
    v-model:open="isVisible"
    title="拨测点详情"
    width="800px"
    @cancel="handleCancel"
    :footer="null"
    :z-index="1001"
  >
    <div v-if="selectedProbe">
      <a-row :gutter="16">
        <a-col :span="12">
          <a-descriptions bordered :column="1" size="small">
            <a-descriptions-item label="时间">
              {{ formatDate(selectedProbe.created_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="响应时间">
              <span v-if="selectedProbe.response_time">{{ parseFloat(selectedProbe.response_time).toFixed(2) }} ms</span>
              <span v-else>-</span>
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <StatusTag :status="selectedProbe.status" />
            </a-descriptions-item>
          </a-descriptions>
        </a-col>
        <a-col :span="12">
          <div ref="probeDetailChartRef" style="width: 100%; height: 200px;"></div>
        </a-col>
      </a-row>
      
      <!-- 历史记录表格 -->
      <a-card title="历史记录" style="margin-top: 20px;">
        <ProbeHistoryTable 
          :history-data="probeDetails[selectedProbe.agent_area] || []"
        />
      </a-card>
      
      <a-descriptions title="详细信息" bordered :column="1" size="small" style="margin-top: 16px;">
        <a-descriptions-item label="原始数据">
          <pre style="max-height: 200px; overflow: auto;">{{ formatDetails(selectedProbe.details) }}</pre>
        </a-descriptions-item>
      </a-descriptions>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import StatusTag from './StatusTag.vue'
import ProbeHistoryTable from './ProbeHistoryTable.vue'

const props = defineProps({
  open: {
    type: Boolean,
    required: true
  },
  selectedProbe: {
    type: Object,
    default: null
  },
  probeDetails: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:open', 'cancel'])

const probeDetailChartRef = ref(null)
let probeDetailChart = null
const isVisible = ref(props.open)

// 监听props.open的变化
watch(() => props.open, (newVal) => {
  isVisible.value = newVal
})

// 监听选中的拨测点变化，重新渲染图表
watch(
  () => props.selectedProbe,
  () => {
    if (props.selectedProbe) {
      nextTick(() => {
        renderProbeDetailChart()
      })
    }
  }
)

// 格式化时间
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 格式化详情信息
const formatDetails = (details) => {
  if (typeof details === 'string') {
    try {
      return JSON.stringify(JSON.parse(details), null, 2)
    } catch (e) {
      return details
    }
  } else {
    return JSON.stringify(details, null, 2)
  }
}

const handleCancel = () => {
  isVisible.value = false
  emit('update:open', false)
  emit('cancel')
}

// 渲染拨测点详情图表
const renderProbeDetailChart = () => {
  if (!probeDetailChartRef.value) return
  
  if (probeDetailChart) {
    probeDetailChart.dispose()
  }
  
  probeDetailChart = echarts.init(probeDetailChartRef.value)
  
  let option = {}
  
  try {
    const details = typeof props.selectedProbe.details === 'string' 
      ? JSON.parse(props.selectedProbe.details) 
      : props.selectedProbe.details
    
    if (props.selectedProbe.task_type === 'ping' && details) {
      option = {
        title: {
          text: 'Ping详情',
          textStyle: {
            fontSize: 14
          }
        },
        tooltip: {},
        radar: {
          indicator: [
            { name: '最小延迟\n(ms)', max: 100 },
            { name: '平均延迟\n(ms)', max: 100 },
            { name: '最大延迟\n(ms)', max: 100 },
            { name: '丢包率\n(%)', max: 100 }
          ]
        },
        series: [{
          type: 'radar',
          data: [
            {
              value: [
                details.rtt_min || 0,
                details.rtt_avg || 0,
                details.rtt_max || 0,
                details.packet_loss || 0
              ],
              name: '性能指标'
            }
          ]
        }]
      }
    } else if (props.selectedProbe.task_type === 'tcp' && details) {
      option = {
        title: {
          text: 'TCP详情',
          textStyle: {
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: ['连接状态', '响应时间']
        },
        yAxis: {},
        series: [{
          type: 'bar',
          data: [
            {
              value: details.connected ? 1 : 0,
              itemStyle: {
                color: details.connected ? '#52c41a' : '#ff4d4f'
              }
            },
            {
              value: details.execution_time ? (details.execution_time * 1000).toFixed(2) : 0
            }
          ]
        }]
      }
    } else {
      option = {
        title: {
          text: '无图表数据',
          left: 'center',
          top: 'center'
        }
      }
    }
  } catch (e) {
    option = {
      title: {
        text: '数据解析失败',
        left: 'center',
        top: 'center'
      }
    }
  }
  
  probeDetailChart.setOption(option)
}
</script>