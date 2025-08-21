<template>
  <div class="api-step-snapshot">
    <a-tabs v-model:activeKey="activeTab" type="card" size="small">
      <!-- 请求信息 -->
      <a-tab-pane key="request" tab="请求信息">
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="请求方法">
            <a-tag :color="getMethodColor(step.request?.method)">
              {{ step.request?.method || 'GET' }}
            </a-tag>
          </a-descriptions-item>
          
          <a-descriptions-item label="完整URL">
            <a-typography-text copyable :ellipsis="{ tooltip: true }">
              {{ step.request?.url || '-' }}
            </a-typography-text>
          </a-descriptions-item>
          
          <a-descriptions-item label="请求头" v-if="requestHeaders.length > 0">
            <a-table
              :dataSource="requestHeaders"
              :columns="headerColumns"
              :pagination="false"
              size="small"
              :scroll="{ y: 200 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'value'">
                  <a-typography-text copyable :ellipsis="{ tooltip: true }">
                    {{ record.value }}
                  </a-typography-text>
                </template>
              </template>
            </a-table>
          </a-descriptions-item>
          
          <a-descriptions-item label="URL参数" v-if="urlParameters.length > 0">
            <a-table
              :dataSource="urlParameters"
              :columns="headerColumns"
              :pagination="false"
              size="small"
              :scroll="{ y: 200 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'value'">
                  <a-typography-text copyable :ellipsis="{ tooltip: true }">
                    {{ record.value }}
                  </a-typography-text>
                </template>
              </template>
            </a-table>
          </a-descriptions-item>
          
          <a-descriptions-item label="请求体" v-if="step.request?.body !== undefined && step.request?.body !== null">
            <div class="code-container">
              <div class="code-header">
                <a-space>
                  <a-tag size="small">{{ getContentType(step.request.headers) }}</a-tag>
                  <a-button size="small" type="text" @click="copyToClipboard(formatRequestBody())">
                    <template #icon><CopyOutlined /></template>
                    复制
                  </a-button>
                </a-space>
              </div>
              <pre class="code-block">{{ formatRequestBody() }}</pre>
            </div>
          </a-descriptions-item>
        </a-descriptions>
      </a-tab-pane>
      
      <!-- 响应信息 -->
      <a-tab-pane key="response" tab="响应信息">
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="状态码">
            <a-tag :color="getStatusCodeColor(step.response?.status_code)">
              {{ step.response?.status_code || '-' }}
            </a-tag>
            <span class="status-text">{{ getStatusText(step.response?.status_code) }}</span>
          </a-descriptions-item>
          
          <a-descriptions-item label="响应时间">
            <a-statistic
              :value="step.response_time || 0"
              suffix="ms"
              :value-style="{ fontSize: '14px', color: getResponseTimeColor(step.response_time) }"
            />
          </a-descriptions-item>
          
          <a-descriptions-item label="响应大小" v-if="step.response?.size">
            {{ formatBytes(step.response.size) }}
          </a-descriptions-item>
          
          <a-descriptions-item label="响应头" v-if="responseHeaders.length > 0">
            <a-table
              :dataSource="responseHeaders"
              :columns="headerColumns"
              :pagination="false"
              size="small"
              :scroll="{ y: 200 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'value'">
                  <a-typography-text copyable :ellipsis="{ tooltip: true }">
                    {{ record.value }}
                  </a-typography-text>
                </template>
              </template>
            </a-table>
          </a-descriptions-item>
          
          <a-descriptions-item label="响应体">
            <div class="code-container">
              <div class="code-header">
                <a-space>
                  <a-tag size="small">{{ step.response?.content_type || 'text/plain' }}</a-tag>
                  <a-button-group size="small">
                    <a-button 
                      :type="responseViewMode === 'formatted' ? 'primary' : 'default'"
                      @click="responseViewMode = 'formatted'"
                    >
                      格式化
                    </a-button>
                    <a-button 
                      :type="responseViewMode === 'raw' ? 'primary' : 'default'"
                      @click="responseViewMode = 'raw'"
                    >
                      原始
                    </a-button>
                  </a-button-group>
                  <a-button size="small" type="text" @click="copyToClipboard(getResponseBody())">
                    <template #icon><CopyOutlined /></template>
                    复制
                  </a-button>
                </a-space>
              </div>
              <pre class="code-block response-body">{{ getResponseBody() }}</pre>
            </div>
          </a-descriptions-item>
        </a-descriptions>
      </a-tab-pane>
      
      <!-- 断言结果 -->
      <a-tab-pane key="assertions" tab="断言结果">
        <div v-if="!step.assertions || step.assertions.length === 0" class="empty-state">
          <a-empty description="该步骤未配置断言" />
        </div>
        
        <div v-else class="assertions-container">
          <div class="assertions-summary">
            <a-statistic-countdown
              :value="Date.now()"
              format=""
              :value-style="{ display: 'none' }"
            />
            <a-row :gutter="16">
              <a-col :span="8">
                <a-statistic
                  title="总断言数"
                  :value="step.assertions.length"
                  :value-style="{ fontSize: '16px' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="通过数"
                  :value="passedAssertions"
                  :value-style="{ fontSize: '16px', color: '#52c41a' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="失败数"
                  :value="failedAssertions"
                  :value-style="{ fontSize: '16px', color: '#ff4d4f' }"
                />
              </a-col>
            </a-row>
          </div>
          
          <a-divider />
          
          <div class="assertions-list">
            <a-card
              v-for="(assertion, index) in step.assertions"
              :key="index"
              size="small"
              :class="['assertion-card', assertion.result ? 'assertion-success' : 'assertion-failed']"
            >
              <template #title>
                <a-space>
                  <span>断言 {{ index + 1 }}</span>
                  <a-tag :color="assertion.result ? 'success' : 'error'" size="small">
                    <template #icon>
                      <CheckOutlined v-if="assertion.result" />
                      <CloseOutlined v-else />
                    </template>
                    {{ assertion.result ? '通过' : '失败' }}
                  </a-tag>
                </a-space>
              </template>
              
              <a-descriptions :column="1" size="small">
                <a-descriptions-item label="断言类型">
                  {{ getAssertionTypeText(assertion.type) }}
                </a-descriptions-item>
                
                <a-descriptions-item label="目标路径" v-if="assertion.target">
                  <a-typography-text code>{{ assertion.target }}</a-typography-text>
                </a-descriptions-item>
                
                <a-descriptions-item label="比较方式">
                  {{ getComparisonText(assertion.operator) }}
                </a-descriptions-item>
                
                <a-descriptions-item label="期望值">
                  <div class="assertion-value">
                    <a-typography-text copyable>
                      {{ formatAssertionValue(assertion.expected) }}
                    </a-typography-text>
                  </div>
                </a-descriptions-item>
                
                <a-descriptions-item label="实际值" v-if="assertion.actual_value !== undefined">
                  <div class="assertion-value">
                    <a-typography-text 
                      copyable
                      :type="assertion.result ? 'success' : 'danger'"
                    >
                      {{ formatAssertionValue(assertion.actual_value) }}
                    </a-typography-text>
                  </div>
                </a-descriptions-item>
                
                <a-descriptions-item label="错误信息" v-if="!assertion.result && assertion.message">
                  <a-alert :message="assertion.message" type="error" size="small" />
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </div>
        </div>
      </a-tab-pane>
      
      <!-- 变量变化 -->
      <a-tab-pane key="variables" tab="变量变化">
        <div v-if="!step.extractions || step.extractions.length === 0" class="empty-state">
          <a-empty description="该步骤未提取变量" />
        </div>
        
        <div v-else class="extractions-container">
          <a-card
            v-for="(extraction, index) in step.extractions"
            :key="index"
            size="small"
            :class="['extraction-card', extraction.success ? 'extraction-success' : 'extraction-failed']"
          >
            <template #title>
              <a-space>
                <span>变量提取 {{ index + 1 }}</span>
                <a-tag :color="extraction.success ? 'success' : 'error'" size="small">
                  <template #icon>
                    <CheckOutlined v-if="extraction.success" />
                    <CloseOutlined v-else />
                  </template>
                  {{ extraction.success ? '成功' : '失败' }}
                </a-tag>
              </a-space>
            </template>
            
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="变量名">
                <a-typography-text code>{{ extraction.variable_name }}</a-typography-text>
              </a-descriptions-item>
              
              <a-descriptions-item label="提取来源">
                {{ getExtractionSourceText(extraction.source) }}
              </a-descriptions-item>
              
              <a-descriptions-item label="提取表达式">
                <a-typography-text code>{{ extraction.expression }}</a-typography-text>
              </a-descriptions-item>
              
              <a-descriptions-item label="提取值" v-if="extraction.extracted_value !== undefined">
                <div class="extraction-value">
                  <a-typography-paragraph 
                    copyable
                    :code="typeof extraction.extracted_value === 'object'"
                  >
                    {{ formatExtractionValue(extraction.extracted_value) }}
                  </a-typography-paragraph>
                </div>
              </a-descriptions-item>
              
              <a-descriptions-item label="错误信息" v-if="!extraction.success && extraction.message">
                <a-alert :message="extraction.message" type="error" size="small" />
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </div>
      </a-tab-pane>
      
      <!-- 原始报文 -->
      <a-tab-pane key="raw" tab="原始报文">
        <a-tabs v-model:activeKey="rawActiveTab" type="line" size="small">
          <!-- 原始请求 -->
          <a-tab-pane key="rawRequest" tab="原始请求">
            <div class="code-container">
              <div class="code-header">
                <a-space>
                  <a-tag size="small">HTTP Request</a-tag>
                  <a-button size="small" type="text" @click="copyToClipboard(formatRawRequest())">
                    <template #icon><CopyOutlined /></template>
                    复制
                  </a-button>
                </a-space>
              </div>
              <pre class="code-block raw-message">{{ formatRawRequest() }}</pre>
            </div>
          </a-tab-pane>
          
          <!-- 原始响应 -->
          <a-tab-pane key="rawResponse" tab="原始响应">
            <div class="code-container">
              <div class="code-header">
                <a-space>
                  <a-tag size="small">HTTP Response</a-tag>
                  <a-button size="small" type="text" @click="copyToClipboard(formatRawResponse())">
                    <template #icon><CopyOutlined /></template>
                    复制
                  </a-button>
                </a-space>
              </div>
              <pre class="code-block raw-message">{{ formatRawResponse() }}</pre>
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { CopyOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  step: {
    type: Object,
    required: true
  },
  stepIndex: {
    type: Number,
    default: 0
  }
})

// 响应式数据
const activeTab = ref('request')
const responseViewMode = ref('formatted')
const rawActiveTab = ref('rawRequest')

// 计算属性
const requestHeaders = computed(() => {
  return formatHeaders(props.step.request?.headers)
})

const responseHeaders = computed(() => {
  return formatHeaders(props.step.response?.headers)
})

const urlParameters = computed(() => {
  const params = []
  const paramMap = new Map()
  
  // 优先处理 urlParameters 字段
  if (props.step.request?.urlParameters && Array.isArray(props.step.request.urlParameters)) {
    props.step.request.urlParameters.forEach(param => {
      const key = param.key || param.name
      const value = param.value
      const mapKey = `${key}:${value}`
      if (!paramMap.has(mapKey)) {
        paramMap.set(mapKey, { key, value })
        params.push({ key, value })
      }
    })
  }
  
  // 如果没有 urlParameters，则处理 params 字段
  if (params.length === 0 && props.step.request?.params && Array.isArray(props.step.request.params)) {
    props.step.request.params.forEach(param => {
      const key = param.key || param.name
      const value = param.value
      const mapKey = `${key}:${value}`
      if (!paramMap.has(mapKey)) {
        paramMap.set(mapKey, { key, value })
        params.push({ key, value })
      }
    })
  }
  
  return params
})

const passedAssertions = computed(() => {
  if (!props.step.assertions) return 0
  return props.step.assertions.filter(a => a.result === true).length
})

const failedAssertions = computed(() => {
  if (!props.step.assertions) return 0
  return props.step.assertions.filter(a => a.result === false).length
})

// 表格列定义
const headerColumns = [
  {
    title: '名称',
    dataIndex: 'key',
    width: '30%',
    ellipsis: true
  },
  {
    title: '值',
    dataIndex: 'value',
    ellipsis: true
  }
]

// 方法
const formatHeaders = (headers) => {
  if (!headers) return []
  
  if (Array.isArray(headers)) {
    return headers.map((header, index) => ({
      key: header.key || header.name || `header-${index}`,
      value: header.value || '',
      id: index
    }))
  } else if (typeof headers === 'object') {
    return Object.entries(headers).map(([key, value], index) => ({
      key,
      value: String(value),
      id: index
    }))
  }
  
  return []
}

const formatRequestBody = () => {
  const body = props.step.request?.body
  if (body === undefined || body === null) return ''
  
  // 处理空字符串的情况
  if (body === '') return '(空请求体)'
  
  // 处理agent返回的body结构 {type: 'json', content: '...'}
  if (typeof body === 'object' && body.content !== undefined) {
    const content = body.content
    if (content === '') return '(空请求体)'
    if (typeof content === 'string') {
      try {
        // 尝试格式化JSON
        return JSON.stringify(JSON.parse(content), null, 2)
      } catch (e) {
        // 如果不是有效JSON，返回原始内容
        return content
      }
    }
    return String(content)
  }
  
  // 处理直接的字符串或对象body
  if (typeof body === 'string') {
    try {
      return JSON.stringify(JSON.parse(body), null, 2)
    } catch (e) {
      return body
    }
  } else if (typeof body === 'object') {
    return JSON.stringify(body, null, 2)
  }
  
  return String(body)
}

const getResponseBody = () => {
  const body = props.step.response?.body
  if (!body) return ''
  
  if (responseViewMode.value === 'raw') {
    return String(body)
  }
  
  // 格式化模式
  if (typeof body === 'string') {
    try {
      return JSON.stringify(JSON.parse(body), null, 2)
    } catch (e) {
      return body
    }
  } else if (typeof body === 'object') {
    return JSON.stringify(body, null, 2)
  }
  
  return String(body)
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
  return colors[method?.toUpperCase()] || 'default'
}

const getStatusCodeColor = (statusCode) => {
  const code = parseInt(statusCode)
  if (code >= 200 && code < 300) return 'success'
  if (code >= 300 && code < 400) return 'processing'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'error'
  return 'default'
}

const getStatusText = (statusCode) => {
  const code = parseInt(statusCode)
  if (code >= 200 && code < 300) return 'OK'
  if (code >= 300 && code < 400) return 'Redirect'
  if (code >= 400 && code < 500) return 'Client Error'
  if (code >= 500) return 'Server Error'
  return 'Unknown'
}

const getResponseTimeColor = (responseTime) => {
  if (!responseTime) return '#666'
  if (responseTime < 1000) return '#52c41a'
  if (responseTime < 3000) return '#faad14'
  return '#ff4d4f'
}

const getContentType = (headers) => {
  // 首先尝试从请求体的type字段获取
  const body = props.step.request?.body
  if (body && typeof body === 'object' && body.type) {
    const typeMap = {
      'json': 'application/json',
      'form': 'application/x-www-form-urlencoded',
      'text': 'text/plain',
      'xml': 'application/xml'
    }
    const mappedType = typeMap[body.type]
    if (mappedType) return mappedType
  }
  
  // 然后从headers中查找
  if (!headers) return 'application/json'
  
  if (Array.isArray(headers)) {
    const contentTypeHeader = headers.find(h => 
      (h.key || h.name || '').toLowerCase() === 'content-type'
    )
    return contentTypeHeader?.value || 'application/json'
  } else if (typeof headers === 'object') {
    return headers['Content-Type'] || headers['content-type'] || 'application/json'
  }
  
  return 'application/json'
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getAssertionTypeText = (type) => {
  const types = {
    'status_code': '状态码',
    'json': 'JSON路径',
    'xpath': 'XPath',
    'regex': '正则表达式',
    'header': '响应头',
    'body': '响应体',
    'response_time': '响应时间'
  }
  return types[type] || type
}

const getComparisonText = (operator) => {
  const operators = {
    'equals': '等于',
    'not_equals': '不等于',
    'greater_than': '大于',
    'less_than': '小于',
    'greater_equal': '大于等于',
    'less_equal': '小于等于',
    'contains': '包含',
    'not_contains': '不包含',
    'exists': '存在',
    'not_exists': '不存在',
    'empty': '为空',
    'not_empty': '不为空',
    'regex_match': '正则匹配'
  }
  return operators[operator] || operator
}

const getExtractionSourceText = (source) => {
  const sources = {
    'response_body': '响应体',
    'response_headers': '响应头',
    'status_code': '状态码'
  }
  return sources[source] || source
}

const formatAssertionValue = (value) => {
  if (value === null || value === undefined) return String(value)
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const formatExtractionValue = (value) => {
  if (value === null || value === undefined) return String(value)
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

// 格式化原始HTTP请求报文
const formatRawRequest = () => {
  if (!props.step) return ''
  
  const { method, url, headers, body } = props.step
  let rawRequest = `${method} ${url} HTTP/1.1\r\n`
  
  // 添加请求头
  if (headers && typeof headers === 'object') {
    Object.entries(headers).forEach(([key, value]) => {
      rawRequest += `${key}: ${value}\r\n`
    })
  }
  
  rawRequest += '\r\n'
  
  // 添加请求体
  if (body) {
    if (typeof body === 'object') {
      rawRequest += JSON.stringify(body, null, 2)
    } else {
      rawRequest += body
    }
  }
  
  return rawRequest
}

// 格式化原始HTTP响应报文
const formatRawResponse = () => {
  if (!props.step || !props.step.response) return ''
  
  const { status_code, headers, body, response_time } = props.step.response
  let rawResponse = `HTTP/1.1 ${status_code} ${getStatusText(status_code)}\r\n`
  
  // 添加响应头
  if (headers && typeof headers === 'object') {
    Object.entries(headers).forEach(([key, value]) => {
      rawResponse += `${key}: ${value}\r\n`
    })
  }
  
  rawResponse += '\r\n'
  
  // 添加响应体
  if (body) {
    if (typeof body === 'object') {
      rawResponse += JSON.stringify(body, null, 2)
    } else {
      rawResponse += body
    }
  }
  
  return rawResponse
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  } catch (err) {
    message.error('复制失败')
  }
}
</script>

<style scoped>
.api-step-snapshot {
  height: 100%;
}

.code-container {
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}

.code-header {
  background: #fafafa;
  padding: 8px 12px;
  border-bottom: 1px solid #d9d9d9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.code-block {
  background: #f5f5f5;
  padding: 12px;
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.response-body {
  max-height: 400px;
}

.raw-message {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 11px;
  line-height: 1.4;
  background: #f8f8f8;
  color: #333;
  border: none;
  max-height: 500px;
  overflow-y: auto;
}

.status-text {
  margin-left: 8px;
  color: #666;
  font-size: 12px;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.assertions-summary {
  background: #fafafa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.assertions-container,
.extractions-container {
  max-height: 500px;
  overflow-y: auto;
}

.assertions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.assertion-card,
.extraction-card {
  border-radius: 6px;
  transition: all 0.3s;
}

.assertion-success {
  border-color: #b7eb8f;
  background: #f6ffed;
}

.assertion-failed {
  border-color: #ffccc7;
  background: #fff2f0;
}

.extraction-success {
  border-color: #b7eb8f;
  background: #f6ffed;
}

.extraction-failed {
  border-color: #ffccc7;
  background: #fff2f0;
}

.assertion-value,
.extraction-value {
  max-height: 200px;
  overflow-y: auto;
}

/* 滚动条样式 */
.code-block::-webkit-scrollbar,
.assertions-container::-webkit-scrollbar,
.extractions-container::-webkit-scrollbar {
  width: 6px;
}

.code-block::-webkit-scrollbar-track,
.assertions-container::-webkit-scrollbar-track,
.extractions-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.code-block::-webkit-scrollbar-thumb,
.assertions-container::-webkit-scrollbar-thumb,
.extractions-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.code-block::-webkit-scrollbar-thumb:hover,
.assertions-container::-webkit-scrollbar-thumb:hover,
.extractions-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>