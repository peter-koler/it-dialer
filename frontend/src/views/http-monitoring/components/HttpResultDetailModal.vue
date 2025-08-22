<template>
  <a-modal
    :open="open"
    :title="`HTTP拨测详情: ${getLocationName(probeData.location)}`"
    width="80%"
    :footer="null"
    @cancel="handleCancel"
  >
    <div class="http-task-result">
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
              title="HTTP状态码"
              :value="httpStatusCode"
              :value-style="getStatusStyle(httpStatusCode)"
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

      <!-- HTTP请求详情 -->
      <a-card class="request-card" :bordered="false">
        <template #title>
          <a-space>
            <SendOutlined />
            <span>HTTP请求详情</span>
          </a-space>
        </template>
        <a-descriptions :column="1" bordered>
          <a-descriptions-item label="请求URL">
            <a-typography-text copyable>{{ requestUrl }}</a-typography-text>
          </a-descriptions-item>
          <a-descriptions-item label="请求方法">
            <a-tag :color="getMethodColor(requestMethod)">{{ requestMethod }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="用户代理">
            {{ userAgent || 'Default User Agent' }}
          </a-descriptions-item>
          <a-descriptions-item label="超时设置">
            {{ timeout || 30 }}秒
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- HTTP响应详情 -->
      <a-card class="response-card" :bordered="false">
        <template #title>
          <a-space>
            <FileTextOutlined />
            <span>HTTP响应详情</span>
          </a-space>
        </template>
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :md="12">
            <a-card size="small" title="响应头信息">
              <div class="response-headers">
                <div v-if="!Object.keys(responseHeaders).length" class="no-data">
                  暂无响应头信息
                </div>
                <div v-else>
                  <div v-for="(value, key) in responseHeaders" :key="key" class="header-item">
                    <strong>{{ key }}:</strong> {{ value }}
                  </div>
                </div>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-card size="small" title="响应统计">
              <a-descriptions :column="1" size="small">
                <a-descriptions-item label="内容长度">
                  {{ formatBytes(contentLength) }}
                </a-descriptions-item>
                <a-descriptions-item label="内容类型">
                  {{ contentType || '未知' }}
                </a-descriptions-item>
                <a-descriptions-item label="编码方式">
                  {{ contentEncoding || '未指定' }}
                </a-descriptions-item>
                <a-descriptions-item label="缓存控制">
                  {{ cacheControl || '未设置' }}
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-col>
        </a-row>
      </a-card>

      <!-- 响应内容预览 -->
      <a-card class="content-card" :bordered="false">
        <template #title>
          <a-space>
            <EyeOutlined />
            <span>响应内容预览</span>
            <a-tag v-if="responseSize" color="blue">{{ formatBytes(responseSize) }}</a-tag>
          </a-space>
        </template>
        <div class="response-content">
          <a-tabs v-model:activeKey="contentTab">
            <a-tab-pane key="preview" tab="内容预览">
              <div class="content-preview">
                <a-typography-paragraph v-if="responsePreview" copyable>
                  <pre>{{ responsePreview }}</pre>
                </a-typography-paragraph>
                <a-empty v-else description="暂无响应内容" />
              </div>
            </a-tab-pane>
            <a-tab-pane key="raw" tab="原始数据">
              <div class="raw-content">
                <a-typography-paragraph v-if="rawResponse" copyable>
                  <pre>{{ rawResponse }}</pre>
                </a-typography-paragraph>
                <a-empty v-else description="暂无原始数据" />
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

const contentTab = ref('preview')

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
  return resultData.value.response_time || props.probeData.response_time || 0
})

const httpStatusCode = computed(() => {
  return resultData.value.webstatus || resultData.value.status_code || 
         (props.probeData.status === 'success' ? 200 : 500)
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
const requestUrl = computed(() => {
  return resultData.value.url || props.probeData.task?.config?.url || '未知URL'
})

const requestMethod = computed(() => {
  return resultData.value.method || 'GET'
})

const userAgent = computed(() => {
  return resultData.value.user_agent || 'HTTP Monitor Agent/1.0'
})

const timeout = computed(() => {
  return resultData.value.timeout || 30
})

// 响应信息
const responseHeaders = computed(() => {
  return resultData.value.response_headers || resultData.value.headers || {}
})

const contentLength = computed(() => {
  return responseHeaders.value['content-length'] || 
         responseHeaders.value['Content-Length'] || 
         resultData.value.content_length || 0
})

const contentType = computed(() => {
  return responseHeaders.value['content-type'] || 
         responseHeaders.value['Content-Type'] || 
         resultData.value.content_type
})

const contentEncoding = computed(() => {
  return responseHeaders.value['content-encoding'] || 
         responseHeaders.value['Content-Encoding']
})

const cacheControl = computed(() => {
  return responseHeaders.value['cache-control'] || 
         responseHeaders.value['Cache-Control']
})

const responseSize = computed(() => {
  return resultData.value.response_size || contentLength.value
})

const responsePreview = computed(() => {
  const content = resultData.value.response_body || resultData.value.content
  if (!content) return ''
  
  // 如果内容太长，只显示前1000个字符
  if (content.length > 1000) {
    return content.substring(0, 1000) + '\n\n... (内容已截断，查看原始数据获取完整内容)'
  }
  return content
})

const rawResponse = computed(() => {
  return resultData.value.response_body || resultData.value.content || ''
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

const getStatusStyle = (statusCode) => {
  if (statusCode >= 200 && statusCode < 300) {
    return { color: '#52c41a' }
  } else if (statusCode >= 300 && statusCode < 400) {
    return { color: '#faad14' }
  } else if (statusCode >= 400) {
    return { color: '#f5222d' }
  }
  return { color: '#8c8c8c' }
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

const getMethodColor = (method) => {
  const colors = {
    'GET': 'blue',
    'POST': 'green',
    'PUT': 'orange',
    'DELETE': 'red',
    'PATCH': 'purple',
    'HEAD': 'cyan',
    'OPTIONS': 'geekblue'
  }
  return colors[method] || 'default'
}

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
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
    contentTab.value = 'preview'
  }
})
</script>

<style scoped>
.http-task-result {
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

.response-headers {
  max-height: 200px;
  overflow-y: auto;
}

.header-item {
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
  word-break: break-all;
}

.header-item:last-child {
  border-bottom: none;
}

.no-data {
  color: #8c8c8c;
  text-align: center;
  padding: 20px;
}

.response-content {
  max-height: 400px;
  overflow-y: auto;
}

.content-preview,
.raw-content {
  max-height: 350px;
  overflow-y: auto;
}

.content-preview pre,
.raw-content pre {
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
  .http-task-result {
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