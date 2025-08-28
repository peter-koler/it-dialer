<template>
  <div class="snapshot-viewer">
    <!-- HTTP任务快照 -->
    <div v-if="taskType === 'http'" class="http-snapshot">
      <a-descriptions title="HTTP拨测失败详情" :column="2" bordered>
        <a-descriptions-item label="请求URL">
          {{ snapshotData.url || snapshotData.target }}
        </a-descriptions-item>
        <a-descriptions-item label="请求方法">
          <a-tag color="blue">{{ snapshotData.method || 'GET' }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="响应状态码">
          <a-tag :color="getStatusCodeColor(snapshotData.response_code)">
            {{ snapshotData.response_code || 'N/A' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="响应时间">
          <span :class="getResponseTimeClass(snapshotData.response_time)">
            {{ snapshotData.response_time ? `${snapshotData.response_time}ms` : 'N/A' }}
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="DNS解析时间">
          {{ snapshotData.dns_time ? `${snapshotData.dns_time}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="连接时间">
          {{ snapshotData.connect_time ? `${snapshotData.connect_time}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="SSL握手时间">
          {{ snapshotData.ssl_time ? `${snapshotData.ssl_time}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="首字节时间">
          {{ snapshotData.ttfb ? `${snapshotData.ttfb}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="错误信息" :span="2" v-if="snapshotData.error">
          <a-alert :message="snapshotData.error" type="error" show-icon />
        </a-descriptions-item>
        <a-descriptions-item label="响应头" :span="2" v-if="snapshotData.response_headers">
          <a-collapse size="small">
            <a-collapse-panel key="headers" header="查看响应头">
              <pre class="response-headers">{{ formatHeaders(snapshotData.response_headers) }}</pre>
            </a-collapse-panel>
          </a-collapse>
        </a-descriptions-item>
        <a-descriptions-item label="响应内容" :span="2" v-if="snapshotData.response_body">
          <a-collapse size="small">
            <a-collapse-panel key="body" header="查看响应内容">
              <pre class="response-body">{{ formatResponseBody(snapshotData.response_body) }}</pre>
            </a-collapse-panel>
          </a-collapse>
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- Ping任务快照 -->
    <div v-else-if="taskType === 'ping'" class="ping-snapshot">
      <a-descriptions title="Ping拨测失败详情" :column="2" bordered>
        <a-descriptions-item label="目标主机">
          {{ snapshotData.host || snapshotData.target }}
        </a-descriptions-item>
        <a-descriptions-item label="IP地址">
          {{ snapshotData.ip || 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="数据包大小">
          {{ snapshotData.packet_size ? `${snapshotData.packet_size} bytes` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="发送数量">
          {{ snapshotData.count || 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="成功数量">
          <span :class="getSuccessRateClass(snapshotData.success_count, snapshotData.count)">
            {{ snapshotData.success_count || 0 }}
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="丢包率">
          <span :class="getPacketLossClass(snapshotData.packet_loss)">
            {{ snapshotData.packet_loss ? `${snapshotData.packet_loss}%` : 'N/A' }}
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="平均延迟">
          <span :class="getLatencyClass(snapshotData.avg_time)">
            {{ snapshotData.avg_time ? `${snapshotData.avg_time}ms` : 'N/A' }}
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="最大延迟">
          {{ snapshotData.max_time ? `${snapshotData.max_time}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="最小延迟">
          {{ snapshotData.min_time ? `${snapshotData.min_time}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="标准差">
          {{ snapshotData.stddev ? `${snapshotData.stddev}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="错误信息" :span="2" v-if="snapshotData.error">
          <a-alert :message="snapshotData.error" type="error" show-icon />
        </a-descriptions-item>
        <a-descriptions-item label="详细输出" :span="2" v-if="snapshotData.output">
          <a-collapse size="small">
            <a-collapse-panel key="output" header="查看详细输出">
              <pre class="ping-output">{{ snapshotData.output }}</pre>
            </a-collapse-panel>
          </a-collapse>
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- TCP任务快照 -->
    <div v-else-if="taskType === 'tcp'" class="tcp-snapshot">
      <a-descriptions title="TCP拨测失败详情" :column="2" bordered>
        <a-descriptions-item label="目标地址">
          {{ snapshotData.target }}
        </a-descriptions-item>
        <a-descriptions-item label="主机">
          {{ snapshotData.host }}
        </a-descriptions-item>
        <a-descriptions-item label="端口">
          <a-tag color="purple">{{ snapshotData.port }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="连接状态">
          <a-tag :color="snapshotData.connected ? 'green' : 'red'">
            {{ snapshotData.connected ? '已连接' : '连接失败' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="执行时间">
          {{ snapshotData.execution_time ? `${(snapshotData.execution_time * 1000).toFixed(2)}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="返回码">
          <a-tag :color="getReturnCodeColor(snapshotData.return_code)">
            {{ snapshotData.return_code }} - {{ getReturnCodeText(snapshotData.return_code) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="错误信息" :span="2" v-if="snapshotData.message">
          <a-alert :message="snapshotData.message" type="error" show-icon />
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- API任务快照 -->
    <div v-else-if="taskType === 'api'" class="api-snapshot">
      <a-descriptions title="API拨测失败详情" :column="2" bordered>
        <a-descriptions-item label="API名称">
          {{ snapshotData.api_name || 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="总步骤数">
          {{ snapshotData.total_steps || 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="成功步骤数">
          <span :class="getStepSuccessClass(snapshotData.success_steps, snapshotData.total_steps)">
            {{ snapshotData.success_steps || 0 }}
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="失败步骤数">
          <span class="text-error">
            {{ (snapshotData.total_steps || 0) - (snapshotData.success_steps || 0) }}
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="总执行时间">
          {{ snapshotData.total_time ? `${snapshotData.total_time}ms` : 'N/A' }}
        </a-descriptions-item>
        <a-descriptions-item label="失败原因" :span="2" v-if="snapshotData.error">
          <a-alert :message="snapshotData.error" type="error" show-icon />
        </a-descriptions-item>
        <a-descriptions-item label="步骤详情" :span="2" v-if="snapshotData.steps">
          <a-collapse size="small">
            <a-collapse-panel key="steps" header="查看步骤详情">
              <div v-for="(step, index) in snapshotData.steps" :key="index" class="step-detail">
                <a-card size="small" :title="`步骤 ${index + 1}: ${step.name}`" class="step-card">
                  <a-descriptions :column="2" size="small">
                    <a-descriptions-item label="状态">
                      <a-tag :color="step.success ? 'green' : 'red'">
                        {{ step.success ? '成功' : '失败' }}
                      </a-tag>
                    </a-descriptions-item>
                    <a-descriptions-item label="响应时间">
                      {{ step.response_time ? `${step.response_time}ms` : 'N/A' }}
                    </a-descriptions-item>
                    <a-descriptions-item label="状态码" v-if="step.status_code">
                      <a-tag :color="getStatusCodeColor(step.status_code)">
                        {{ step.status_code }}
                      </a-tag>
                    </a-descriptions-item>
                    <a-descriptions-item label="错误信息" :span="2" v-if="step.error">
                      <a-alert :message="step.error" type="error" show-icon size="small" />
                    </a-descriptions-item>
                  </a-descriptions>
                </a-card>
              </div>
            </a-collapse-panel>
          </a-collapse>
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- 未知类型 -->
    <div v-else class="unknown-snapshot">
      <a-descriptions title="拨测失败详情" :column="2" bordered>
        <a-descriptions-item label="任务类型">
          <a-tag color="gray">{{ taskType || '未知' }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="原始数据" :span="2">
          <pre class="raw-data">{{ JSON.stringify(snapshotData, null, 2) }}</pre>
        </a-descriptions-item>
      </a-descriptions>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  taskType: {
    type: String,
    required: true
  },
  snapshotData: {
    type: Object,
    required: true
  }
})

// 获取状态码颜色
const getStatusCodeColor = (code) => {
  if (!code) return 'default'
  if (code >= 200 && code < 300) return 'green'
  if (code >= 300 && code < 400) return 'blue'
  if (code >= 400 && code < 500) return 'orange'
  if (code >= 500) return 'red'
  return 'default'
}

// 获取响应时间样式类
const getResponseTimeClass = (time) => {
  if (!time) return ''
  if (time < 200) return 'text-success'
  if (time < 1000) return 'text-warning'
  return 'text-error'
}

// 获取成功率样式类
const getSuccessRateClass = (success, total) => {
  if (!success || !total) return ''
  const rate = success / total
  if (rate === 1) return 'text-success'
  if (rate > 0.8) return 'text-warning'
  return 'text-error'
}

// 获取丢包率样式类
const getPacketLossClass = (loss) => {
  if (!loss) return 'text-success'
  if (loss < 5) return 'text-warning'
  return 'text-error'
}

// 获取延迟样式类
const getLatencyClass = (time) => {
  if (!time) return ''
  if (time < 50) return 'text-success'
  if (time < 200) return 'text-warning'
  return 'text-error'
}

// 获取返回码颜色
const getReturnCodeColor = (code) => {
  if (code === 0) return 'green'
  return 'red'
}

// 获取返回码文本
const getReturnCodeText = (code) => {
  const codeMap = {
    0: '连接成功',
    61: '连接被拒绝',
    110: '连接超时',
    111: '连接被拒绝',
    113: '无路由到主机'
  }
  return codeMap[code] || '未知错误'
}

// 获取步骤成功率样式类
const getStepSuccessClass = (success, total) => {
  if (!success || !total) return 'text-error'
  const rate = success / total
  if (rate === 1) return 'text-success'
  if (rate > 0.5) return 'text-warning'
  return 'text-error'
}

// 格式化响应头
const formatHeaders = (headers) => {
  if (typeof headers === 'string') {
    try {
      headers = JSON.parse(headers)
    } catch {
      return headers
    }
  }
  if (typeof headers === 'object') {
    return Object.entries(headers)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n')
  }
  return headers
}

// 格式化响应内容
const formatResponseBody = (body) => {
  if (typeof body === 'string') {
    try {
      return JSON.stringify(JSON.parse(body), null, 2)
    } catch {
      return body
    }
  }
  return JSON.stringify(body, null, 2)
}
</script>

<style scoped>
.snapshot-viewer {
  padding: 16px;
}

.text-success {
  color: #52c41a;
  font-weight: 500;
}

.text-warning {
  color: #faad14;
  font-weight: 500;
}

.text-error {
  color: #ff4d4f;
  font-weight: 500;
}

.response-headers,
.response-body,
.ping-output,
.raw-data {
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.4;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.step-detail {
  margin-bottom: 12px;
}

.step-card {
  border-left: 4px solid #1890ff;
}

.step-card.error {
  border-left-color: #ff4d4f;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  background-color: #fafafa;
}

:deep(.ant-collapse-content-box) {
  padding: 8px 16px;
}
</style>