<template>
  <div class="api-step-timeline">
    <div class="timeline-header">
      <h4>执行步骤</h4>
      <a-space>
        <a-button size="small" @click="expandAll">
          <template #icon><ExpandOutlined /></template>
          展开全部
        </a-button>
        <a-button size="small" @click="collapseAll">
          <template #icon><ShrinkOutlined /></template>
          收起全部
        </a-button>
      </a-space>
    </div>
    
    <div class="timeline-container">
      <a-timeline mode="left" class="custom-timeline">
        <a-timeline-item
          v-for="(step, index) in steps"
          :key="index"
          :color="getStepColor(step)"
          :class="['timeline-item', { 'active': activeStepIndex === index }]"
        >
          <template #dot>
            <div class="step-dot" :class="getStepStatus(step)">
              <CheckOutlined v-if="step.status === 'success'" />
              <CloseOutlined v-if="step.status === 'failed'" />
              <LoadingOutlined v-if="step.status === 'running'" spin />
              <ClockCircleOutlined v-if="step.status === 'pending'" />
              <span v-else class="step-number">{{ index + 1 }}</span>
            </div>
          </template>
          
          <div class="step-content" @click="handleStepClick(index)">
            <div class="step-header">
              <div class="step-title">
                <a-space>
                  <span class="step-name">{{ step.name || `步骤 ${index + 1}` }}</span>
                  <a-tag :color="getMethodColor(step.request?.method)" size="small">
                    {{ step.request?.method || 'GET' }}
                  </a-tag>
                  <a-tag :color="getStatusCodeColor(step.response?.status_code)" size="small" v-if="step.response?.status_code">
                    {{ step.response.status_code }}
                  </a-tag>
                </a-space>
              </div>
              
              <div class="step-meta">
                <a-space size="small">
                  <span class="response-time" v-if="step.response_time">
                    <ClockCircleOutlined />
                    {{ step.response_time }}ms
                  </span>
                  <span class="step-time" v-if="step.start_time">
                    {{ formatTime(step.start_time) }}
                  </span>
                </a-space>
              </div>
            </div>
            
            <div class="step-url" v-if="step.request?.url">
              <a-typography-text 
                :ellipsis="{ tooltip: true }" 
                type="secondary"
                class="url-text"
              >
                {{ step.request.url }}
              </a-typography-text>
            </div>
            
            <!-- 步骤状态指示器 -->
            <div class="step-indicators">
              <a-space size="small">
                <!-- 断言状态 -->
                <div class="indicator" v-if="step.assertions && step.assertions.length > 0">
                  <a-tooltip :title="`断言: ${getAssertionSummary(step.assertions)}`">
                    <a-badge 
                      :count="getFailedAssertions(step.assertions)" 
                      :show-zero="false"
                      :number-style="{ backgroundColor: '#ff4d4f' }"
                    >
                      <CheckCircleOutlined 
                        :style="{ color: getAssertionColor(step.assertions) }"
                      />
                    </a-badge>
                  </a-tooltip>
                </div>
                
                <!-- 变量提取状态 -->
                <div class="indicator" v-if="step.extractions && step.extractions.length > 0">
                  <a-tooltip :title="`变量提取: ${getExtractionSummary(step.extractions)}`">
                    <a-badge 
                      :count="getFailedExtractions(step.extractions)" 
                      :show-zero="false"
                      :number-style="{ backgroundColor: '#ff4d4f' }"
                    >
                      <DatabaseOutlined 
                        :style="{ color: getExtractionColor(step.extractions) }"
                      />
                    </a-badge>
                  </a-tooltip>
                </div>
                
                <!-- 响应大小 -->
                <div class="indicator" v-if="step.response?.size">
                  <a-tooltip :title="`响应大小: ${formatBytes(step.response.size)}`">
                    <FileTextOutlined style="color: #666" />
                  </a-tooltip>
                </div>
              </a-space>
            </div>
            
            <!-- 错误信息 -->
            <div class="step-error" v-if="step.error">
              <a-alert 
                :message="step.error" 
                type="error" 
                size="small" 
                show-icon 
                :closable="false"
              />
            </div>
            
            <!-- 快速预览 -->
            <div class="step-preview" v-if="showPreview && activeStepIndex === index">
              <a-divider style="margin: 8px 0" />
              <div class="preview-content">
                <a-row :gutter="8">
                  <a-col :span="12" v-if="step.request">
                    <div class="preview-section">
                      <div class="preview-title">请求</div>
                      <div class="preview-item">
                        <span class="preview-label">URL:</span>
                        <a-typography-text 
                          :ellipsis="{ tooltip: true }" 
                          class="preview-value"
                        >
                          {{ step.request.url }}
                        </a-typography-text>
                      </div>
                      <div class="preview-item" v-if="step.request.body">
                        <span class="preview-label">Body:</span>
                        <a-typography-text 
                          :ellipsis="{ tooltip: true, rows: 2 }" 
                          class="preview-value"
                        >
                          {{ getPreviewBody(step.request.body) }}
                        </a-typography-text>
                      </div>
                    </div>
                  </a-col>
                  
                  <a-col :span="12" v-if="step.response">
                    <div class="preview-section">
                      <div class="preview-title">响应</div>
                      <div class="preview-item">
                        <span class="preview-label">状态:</span>
                        <a-tag :color="getStatusCodeColor(step.response.status_code)" size="small">
                          {{ step.response.status_code }}
                        </a-tag>
                      </div>
                      <div class="preview-item" v-if="step.response.body">
                        <span class="preview-label">Body:</span>
                        <a-typography-text 
                          :ellipsis="{ tooltip: true, rows: 2 }" 
                          class="preview-value"
                        >
                          {{ getPreviewBody(step.response.body) }}
                        </a-typography-text>
                      </div>
                    </div>
                  </a-col>
                </a-row>
              </div>
            </div>
          </div>
        </a-timeline-item>
      </a-timeline>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { 
  CheckOutlined, 
  CloseOutlined, 
  LoadingOutlined, 
  ClockCircleOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  ExpandOutlined,
  ShrinkOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  steps: {
    type: Array,
    default: () => []
  },
  activeStepIndex: {
    type: Number,
    default: -1
  },
  showPreview: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['step-click', 'expand-all', 'collapse-all'])

// 方法
const handleStepClick = (index) => {
  emit('step-click', index)
}

const expandAll = () => {
  emit('expand-all')
}

const collapseAll = () => {
  emit('collapse-all')
}

const getStepColor = (step) => {
  if (step.status === 'success') return '#52c41a'
  if (step.status === 'failed') return '#ff4d4f'
  if (step.status === 'running') return '#1890ff'
  if (step.status === 'pending') return '#d9d9d9'
  
  // 根据响应状态码判断
  if (step.response?.status_code) {
    const code = parseInt(step.response.status_code)
    if (code >= 200 && code < 300) return '#52c41a'
    if (code >= 400) return '#ff4d4f'
  }
  
  return '#d9d9d9'
}

const getStepStatus = (step) => {
  if (step.status) return step.status
  
  // 根据响应状态码判断
  if (step.response?.status_code) {
    const code = parseInt(step.response.status_code)
    if (code >= 200 && code < 300) return 'success'
    if (code >= 400) return 'failed'
  }
  
  return 'pending'
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

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3
  })
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getAssertionSummary = (assertions) => {
  const total = assertions.length
  const passed = assertions.filter(a => a.result === true).length
  return `${passed}/${total} 通过`
}

const getAssertionColor = (assertions) => {
  const failed = assertions.filter(a => a.result === false).length
  return failed > 0 ? '#ff4d4f' : '#52c41a'
}

const getFailedAssertions = (assertions) => {
  return assertions.filter(a => a.result === false).length
}

const getExtractionSummary = (extractions) => {
  const total = extractions.length
  const success = extractions.filter(e => e.success === true).length
  return `${success}/${total} 成功`
}

const getExtractionColor = (extractions) => {
  const failed = extractions.filter(e => e.success === false).length
  return failed > 0 ? '#ff4d4f' : '#52c41a'
}

const getFailedExtractions = (extractions) => {
  return extractions.filter(e => e.success === false).length
}

const getPreviewBody = (body) => {
  if (!body) return ''
  
  if (typeof body === 'string') {
    return body.length > 100 ? body.substring(0, 100) + '...' : body
  } else if (typeof body === 'object') {
    const str = JSON.stringify(body)
    return str.length > 100 ? str.substring(0, 100) + '...' : str
  }
  
  return String(body)
}
</script>

<style scoped>
.api-step-timeline {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 0 16px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.timeline-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.timeline-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.custom-timeline {
  padding-left: 0;
}

.timeline-item {
  cursor: pointer;
  transition: all 0.3s;
}

.timeline-item:hover {
  background: #fafafa;
  border-radius: 8px;
}

.timeline-item.active {
  background: #e6f7ff;
  border-radius: 8px;
}

.step-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: white;
  border: 2px solid transparent;
}

.step-dot.success {
  background: #52c41a;
  border-color: #52c41a;
}

.step-dot.failed {
  background: #ff4d4f;
  border-color: #ff4d4f;
}

.step-dot.running {
  background: #1890ff;
  border-color: #1890ff;
}

.step-dot.pending {
  background: #d9d9d9;
  border-color: #d9d9d9;
  color: #666;
}

.step-number {
  font-size: 10px;
}

.step-content {
  padding: 8px 12px;
  border-radius: 6px;
  margin-left: 8px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
}

.step-title {
  flex: 1;
}

.step-name {
  font-weight: 500;
  font-size: 14px;
}

.step-meta {
  font-size: 12px;
  color: #666;
}

.response-time {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.step-time {
  color: #999;
}

.step-url {
  margin: 4px 0;
}

.url-text {
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.step-indicators {
  margin: 8px 0 4px 0;
}

.indicator {
  display: inline-flex;
  align-items: center;
}

.step-error {
  margin-top: 8px;
}

.step-preview {
  margin-top: 8px;
}

.preview-content {
  background: #fafafa;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
}

.preview-section {
  margin-bottom: 8px;
}

.preview-title {
  font-weight: 500;
  margin-bottom: 4px;
  color: #666;
}

.preview-item {
  margin-bottom: 4px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.preview-label {
  font-weight: 500;
  color: #666;
  min-width: 40px;
  flex-shrink: 0;
}

.preview-value {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* 滚动条样式 */
.timeline-container::-webkit-scrollbar {
  width: 6px;
}

.timeline-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.timeline-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.timeline-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .step-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .step-meta {
    align-self: flex-end;
  }
  
  .preview-content .ant-row {
    flex-direction: column;
  }
}
</style>