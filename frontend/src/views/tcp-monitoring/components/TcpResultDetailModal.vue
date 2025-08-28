<template>
  <a-modal
    :open="open"
    :title="`TCP拨测详情: ${getLocationName(probeData.location)}`"
    width="80%"
    :footer="null"
    @cancel="handleCancel"
  >
    <div class="tcp-task-result">
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
              :value="responseTime"
              suffix="ms"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="连接状态"
              :value="connectionStatus"
              :value-style="getConnectionStatusStyle(connectionStatus)"
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
              :value="formatExecutionTime(probeData.created_at)"
            />
          </a-col>
        </a-row>
      </a-card>

      <!-- TCP连接详情 -->
      <a-card class="request-card" :bordered="false">
        <template #title>
          <a-space>
            <SendOutlined />
            <span>TCP连接详情</span>
          </a-space>
        </template>
        <a-descriptions :column="1" bordered>
          <a-descriptions-item label="目标地址">
            <a-typography-text copyable>{{ targetHost }}</a-typography-text>
          </a-descriptions-item>
          <a-descriptions-item label="目标端口">
            {{ targetPort }}
          </a-descriptions-item>
          <a-descriptions-item label="连接超时">
            {{ timeout || 5 }}秒
          </a-descriptions-item>
          <a-descriptions-item label="连接协议">
            TCP
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- TCP响应详情 -->
      <a-card class="response-card" :bordered="false">
        <template #title>
          <a-space>
            <FileTextOutlined />
            <span>TCP响应详情</span>
          </a-space>
        </template>
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :md="12">
            <a-card size="small" title="连接统计">
              <a-descriptions :column="1" size="small">
                <a-descriptions-item label="连接状态">
                  <a-tag :color="getConnectionStatusColor(connectionStatus)">
                    {{ connectionStatus }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="响应时间">
                  {{ responseTime }} ms
                </a-descriptions-item>
                <a-descriptions-item label="返回码">
                  <a-tag :color="getReturnCodeColor(returnCode)">
                    {{ getReturnCodeText(returnCode) }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="错误信息">
                  {{ errorMessage || '无' }}
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-card size="small" title="网络信息">
              <a-descriptions :column="1" size="small">
                <a-descriptions-item label="本地地址">
                  {{ localAddress || 'N/A' }}
                </a-descriptions-item>
                <a-descriptions-item label="远程地址">
                  {{ remoteAddress || `${targetHost}:${targetPort}` }}
                </a-descriptions-item>
                <a-descriptions-item label="连接建立时间">
                  {{ connectionTime || responseTime }} ms
                </a-descriptions-item>
                <a-descriptions-item label="数据传输">
                  {{ dataTransferred || 'N/A' }}
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-col>
        </a-row>
      </a-card>

      <!-- TCP详细输出 -->
      <a-card class="content-card" :bordered="false">
        <template #title>
          <a-space>
            <EyeOutlined />
            <span>详细输出</span>
          </a-space>
        </template>
        <div class="tcp-output">
          <a-typography-paragraph>
            <pre class="tcp-summary">{{ tcpSummary }}</pre>
          </a-typography-paragraph>
        </div>
      </a-card>
    </div>
  </a-modal>
</template>

<script setup>
import { computed, defineProps, defineEmits } from 'vue'
import { 
  DashboardOutlined, 
  SendOutlined, 
  FileTextOutlined, 
  EyeOutlined 
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import pinyinToChinese from '@/utils/pinyinToChinese'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  probeData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:open'])

const handleCancel = () => {
  emit('update:open', false)
}

// 获取地点名称
const getLocationName = (location) => {
  if (!location) return '未知地点'
  return pinyinToChinese[location] || location
}

// 格式化执行时间
const formatExecutionTime = (timeStr) => {
  if (!timeStr) return '未知时间'
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm:ss')
}

// 计算属性
const resultData = computed(() => props.probeData || {})

// 基本信息
const targetHost = computed(() => {
  return resultData.value.target || resultData.value.host || 'Unknown'
})

const targetPort = computed(() => {
  return resultData.value.port || resultData.value.target_port || 80
})

const timeout = computed(() => {
  return resultData.value.timeout || 5
})

// 响应信息
const responseTime = computed(() => {
  return resultData.value.response_time || resultData.value.execution_time || 0
})

const connectionStatus = computed(() => {
  const status = resultData.value.connection_status || resultData.value.status
  if (status === 'success' || status === 'connected') return '连接成功'
  if (status === 'failed' || status === 'error') return '连接失败'
  if (status === 'timeout') return '连接超时'
  return status || '未知'
})

const executionStatus = computed(() => {
  const status = resultData.value.status
  if (status === 'success') return '成功'
  if (status === 'failed' || status === 'error') return '失败'
  if (status === 'timeout') return '超时'
  return status || '未知'
})

const returnCode = computed(() => {
  return resultData.value.return_code || (resultData.value.status === 'success' ? 0 : 1)
})

const errorMessage = computed(() => {
  return resultData.value.error_message || resultData.value.message || ''
})

// 网络信息
const localAddress = computed(() => {
  return resultData.value.local_address || resultData.value.local_ip
})

const remoteAddress = computed(() => {
  return resultData.value.remote_address || `${targetHost.value}:${targetPort.value}`
})

const connectionTime = computed(() => {
  return resultData.value.connection_time || responseTime.value
})

const dataTransferred = computed(() => {
  return resultData.value.data_transferred || resultData.value.bytes_sent
})

// 输出内容
const tcpSummary = computed(() => {
  const summary = resultData.value.summary || resultData.value.tcp_summary
  if (summary) return summary
  
  // 如果没有现成的汇总，生成一个简单的汇总
  return `TCP连接测试 ${targetHost.value}:${targetPort.value}\n` +
         `连接状态: ${connectionStatus.value}\n` +
         `响应时间: ${responseTime.value} ms\n` +
         `返回码: ${returnCode.value}\n` +
         `执行时间: ${formatExecutionTime(resultData.value.created_at)}\n` +
         (errorMessage.value ? `错误信息: ${errorMessage.value}\n` : '') +
         '\n--- TCP连接详情 ---\n' +
         `目标地址: ${targetHost.value}\n` +
         `目标端口: ${targetPort.value}\n` +
         `连接超时: ${timeout.value}秒\n` +
         `本地地址: ${localAddress.value || 'N/A'}\n` +
         `远程地址: ${remoteAddress.value}\n`
})

// 样式方法
const getConnectionStatusStyle = (status) => {
  if (status === '连接成功') {
    return { color: '#52c41a' }
  } else if (status === '连接失败') {
    return { color: '#ff4d4f' }
  } else if (status === '连接超时') {
    return { color: '#faad14' }
  }
  return { color: '#666' }
}

const getExecutionStatusStyle = (status) => {
  if (status === '成功') {
    return { color: '#52c41a' }
  } else if (status === '失败') {
    return { color: '#ff4d4f' }
  } else if (status === '超时') {
    return { color: '#faad14' }
  }
  return { color: '#666' }
}

const getConnectionStatusColor = (status) => {
  if (status === '连接成功') return 'green'
  if (status === '连接失败') return 'red'
  if (status === '连接超时') return 'orange'
  return 'default'
}

const getReturnCodeColor = (code) => {
  return code === 0 ? 'green' : 'red'
}

const getReturnCodeText = (code) => {
  const codeMap = {
    0: '连接成功',
    1: '连接失败',
    2: '连接超时',
    3: '网络不可达',
    4: '主机不可达',
    5: '连接被拒绝'
  }
  return codeMap[code] || `错误码: ${code}`
}
</script>

<style scoped>
.tcp-task-result {
  max-height: 70vh;
  overflow-y: auto;
}

.overview-card,
.request-card,
.response-card,
.content-card {
  margin-bottom: 16px;
}

.overview-card:last-child,
.request-card:last-child,
.response-card:last-child,
.content-card:last-child {
  margin-bottom: 0;
}

.tcp-output {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 16px;
}

.tcp-summary {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: transparent;
  border: none;
  color: #24292e;
}

.ant-descriptions-item-label {
  font-weight: 500;
}

.ant-statistic-title {
  font-size: 14px;
  color: #666;
}

.ant-statistic-content {
  font-size: 20px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .tcp-task-result {
    max-height: 60vh;
  }
  
  .ant-statistic-content {
    font-size: 16px;
  }
}
</style>