<template>
  <a-modal
    :open="open"
    :title="`Ping拨测详情: ${formatExecutionTime(probeData.timestamp || probeData.created_at)}`"
    width="80%"
    :footer="null"
    @cancel="handleCancel"
  >
    <div class="ping-task-result">
      <!-- 总览卡片 -->
      <a-card class="overview-card" :bordered="false">
        <template #title>
          <a-space>
            <DashboardOutlined />
            <span>执行概览</span>
          </a-space>
        </template>
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="响应时间"
              :value="parseFloat(responseTime).toFixed(2)"
              suffix="ms"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="丢包率"
              :value="packetLoss"
              suffix="%"
              :value-style="getPacketLossStyle(packetLoss)"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="执行状态"
              :value="executionStatus"
              :value-style="getExecutionStatusStyle(executionStatus)"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="执行时间"
              :value="formatExecutionTime(probeData.timestamp || probeData.created_at)"
            />
          </a-col>
        </a-row>
      </a-card>

      <!-- Ping请求详情 -->
      <a-card class="request-card" :bordered="false">
        <template #title>
          <a-space>
            <SendOutlined />
            <span>Ping请求详情</span>
          </a-space>
        </template>
        <a-descriptions :column="1" bordered>
          <a-descriptions-item label="目标地址">
            <a-typography-text copyable>{{ targetHost }}</a-typography-text>
          </a-descriptions-item>
          <a-descriptions-item label="数据包大小">
            {{ packetSize }} 字节
          </a-descriptions-item>
          <a-descriptions-item label="发送数量">
            {{ packetCount }} 个数据包
          </a-descriptions-item>
          <a-descriptions-item label="超时设置">
            {{ timeout || 5 }}秒
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- Ping响应详情 -->
      <a-card class="response-card" :bordered="false">
        <template #title>
          <a-space>
            <FileTextOutlined />
            <span>Ping响应详情</span>
          </a-space>
        </template>
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :md="12">
            <a-card size="small" title="响应统计">
              <a-descriptions :column="1" size="small">
                <a-descriptions-item label="最小响应时间">
                  {{ minResponseTime }} ms
                </a-descriptions-item>
                <a-descriptions-item label="最大响应时间">
                  {{ maxResponseTime }} ms
                </a-descriptions-item>          
                <a-descriptions-item label="平均响应时间">
                  {{ parseFloat(avgResponseTime).toFixed(2) }} ms
                </a-descriptions-item>
                <a-descriptions-item label="标准差">
                  {{ responseTimeStdDev }} ms
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-card size="small" title="网络统计">
              <a-descriptions :column="1" size="small">
                <a-descriptions-item label="发送数据包">
                  {{ packetsSent }} 个
                </a-descriptions-item>
                <a-descriptions-item label="接收数据包">
                  {{ packetsReceived }} 个
                </a-descriptions-item>
                <a-descriptions-item label="丢包数量">
                  {{ packetsLost }} 个
                </a-descriptions-item>
                <a-descriptions-item label="丢包率">
                  <a-tag :color="getPacketLossColor(packetLoss)">{{ packetLoss }}%</a-tag>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-col>
        </a-row>
      </a-card>

      <!-- Ping详细输出 -->
      <a-card class="content-card" :bordered="false">
        <template #title>
          <a-space>
            <EyeOutlined />
            <span>Ping详细输出</span>
          </a-space>
        </template>
        <div class="ping-output">
          <a-tabs v-model:activeKey="contentTab">
            <a-tab-pane key="summary" tab="汇总信息">
              <div class="ping-summary">
                <a-typography-paragraph v-if="pingSummary" copyable>
                  <pre>{{ pingSummary }}</pre>
                </a-typography-paragraph>
                <a-empty v-else description="暂无汇总信息" />
              </div>
            </a-tab-pane>
            <a-tab-pane key="raw" tab="原始输出">
              <div class="raw-output">
                <a-typography-paragraph v-if="rawOutput" copyable>
                  <pre>{{ rawOutput }}</pre>
                </a-typography-paragraph>
                <a-empty v-else description="暂无原始输出" />
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
      </a-card>

      <!-- 错误信息 -->
      <a-card v-if="errorMessage" class="error-card" :bordered="false">
        <template #title>
          <a-space>
            <ExclamationCircleOutlined />
            <span>错误信息</span>
          </a-space>
        </template>
        <a-alert
          :message="errorMessage"
          type="error"
          show-icon
          :description="errorDetails"
        />
      </a-card>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  DashboardOutlined, 
  SendOutlined,
  FileTextOutlined,
  EyeOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import pinyinToChinese from '@/utils/pinyinToChinese'

const props = defineProps({
  open: Boolean,
  probeData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:open'])

const contentTab = ref('summary')

const resultData = computed(() => {
  if (typeof props.probeData.details === 'string') {
    try {
      return JSON.parse(props.probeData.details)
    } catch (e) {
      console.error('Failed to parse details', e)
      return {}
    }
  }
  return props.probeData.details || {}
})

// 基本信息
const responseTime = computed(() => {
  return props.probeData.responseTime || resultData.value.response_time || props.probeData.response_time || 0
})

const packetLoss = computed(() => {
  return props.probeData.packetLoss !== undefined ? props.probeData.packetLoss :
         (resultData.value.packet_loss !== undefined ? resultData.value.packet_loss : 
         (props.probeData.packet_loss !== undefined ? props.probeData.packet_loss : 0))
})

const executionStatus = computed(() => {
  const status = props.probeData.status || 'unknown'
  const statusMap = {
    'success': '成功',
    'failed': '失败',
    'timeout': '超时',
    'error': '错误',
    'unknown': '未知'
  }
  return statusMap[status] || status
})

// 请求信息
const targetHost = computed(() => {
  return props.probeData.target || props.probeData.destinationIp || 
         resultData.value.target || props.probeData.task?.config?.target || 
         props.probeData.task?.target || '未知目标'
})

const packetSize = computed(() => {
  return props.probeData.packetSize || resultData.value.packet_size || 32
})

const packetCount = computed(() => {
  return resultData.value.packet_count || 4
})

const timeout = computed(() => {
  return resultData.value.timeout || 5
})

// 响应统计信息
const minResponseTime = computed(() => {
  return resultData.value.min_response_time || resultData.value.min_time || 0
})

const maxResponseTime = computed(() => {
  return resultData.value.max_response_time || resultData.value.max_time || 0
})

const avgResponseTime = computed(() => {
  return resultData.value.avg_response_time || resultData.value.avg_time || responseTime.value
})

const responseTimeStdDev = computed(() => {
  return resultData.value.stddev_response_time || resultData.value.stddev || 0
})

// 网络统计
const packetsSent = computed(() => {
  return resultData.value.packets_sent || packetCount.value
})

const packetsReceived = computed(() => {
  return resultData.value.packets_received || 
         (packetsSent.value - Math.round(packetsSent.value * packetLoss.value / 100))
})

const packetsLost = computed(() => {
  return packetsSent.value - packetsReceived.value
})

// 输出内容
const pingSummary = computed(() => {
  const summary = resultData.value.summary || resultData.value.ping_summary
  if (summary) return summary
  
  // 如果没有现成的汇总，生成一个简单的汇总
  return `PING ${targetHost.value}\n` +
         `${packetsSent.value} packets transmitted, ${packetsReceived.value} received, ${packetLoss.value}% packet loss\n` +
         `round-trip min/avg/max/stddev = ${minResponseTime.value}/${avgResponseTime.value}/${maxResponseTime.value}/${responseTimeStdDev.value} ms`
})

const rawOutput = computed(() => {
  return resultData.value.raw_output || resultData.value.output || resultData.value.ping_output || ''
})

// 错误信息
const errorMessage = computed(() => {
  if (props.probeData.status === 'success') return ''
  return resultData.value.error || resultData.value.message || '执行失败'
})

const errorDetails = computed(() => {
  return resultData.value.error_details || resultData.value.error_message || ''
})

// 工具方法
const getLocationName = (location) => {
  return pinyinToChinese[location] || location
}

const getPacketLossStyle = (loss) => {
  if (loss === 0) {
    return { color: '#52c41a' }
  } else if (loss < 10) {
    return { color: '#faad14' }
  } else {
    return { color: '#f5222d' }
  }
}

const getPacketLossColor = (loss) => {
  if (loss === 0) {
    return 'green'
  } else if (loss < 10) {
    return 'orange'
  } else {
    return 'red'
  }
}

const getExecutionStatusStyle = (status) => {
  if (status === '成功') {
    return { color: '#52c41a' }
  } else if (status === '超时') {
    return { color: '#faad14' }
  } else if (status === '失败' || status === '错误') {
    return { color: '#f5222d' }
  }
  return { color: '#8c8c8c' }
}

const formatExecutionTime = (dateString) => {
  if (!dateString) return '未知时间'
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

const handleCancel = () => {
  emit('update:open', false)
}

watch(() => props.open, (newVal) => {
  if (newVal) {
    contentTab.value = 'summary'
  }
})
</script>

<style scoped>
.ping-task-result {
  background: #f0f2f5;
  padding: 12px;
}

.overview-card, 
.request-card, 
.response-card, 
.content-card, 
.error-card {
  margin-bottom: 12px;
}

.ping-output {
  max-height: 400px;
  overflow-y: auto;
}

.ping-summary,
.raw-output {
  max-height: 350px;
  overflow-y: auto;
}

.ping-summary pre,
.raw-output pre {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-all;
}

:deep(.ant-statistic-content-value) {
  font-size: 20px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  width: 120px;
}

:deep(.ant-card-head-title) {
  font-weight: 500;
}

:deep(.ant-typography) {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .ping-task-result {
    padding: 8px;
  }
  
  .overview-card, 
  .request-card, 
  .response-card, 
  .content-card, 
  .error-card {
    margin-bottom: 8px;
  }
}
</style>