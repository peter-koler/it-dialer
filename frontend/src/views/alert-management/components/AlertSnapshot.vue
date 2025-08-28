<template>
  <div class="alert-snapshot">
    <a-tabs v-model:activeKey="activeTab" type="card" size="small">
      <!-- 告警概览 -->
      <a-tab-pane key="overview" tab="告警概览">
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="任务名称">
            <a-tag color="blue">{{ snapshot.task_name }}</a-tag>
          </a-descriptions-item>
          
          <a-descriptions-item label="触发时间">
            {{ formatTime(snapshot.trigger_time) }}
          </a-descriptions-item>
          
          <a-descriptions-item label="任务状态">
            <a-tag :color="getStatusColor(snapshot.result_data?.status)">
              {{ snapshot.result_data?.status || '-' }}
            </a-tag>
          </a-descriptions-item>
          
          <a-descriptions-item label="响应时间" v-if="snapshot.result_data?.response_time">
            <a-statistic
              :value="snapshot.result_data.response_time"
              suffix="ms"
              :value-style="{ fontSize: '14px', color: getResponseTimeColor(snapshot.result_data.response_time) }"
            />
          </a-descriptions-item>
          
          <a-descriptions-item label="错误信息" v-if="snapshot.result_data?.message">
            <a-alert 
              :message="snapshot.result_data.message" 
              type="error" 
              size="small" 
              show-icon
            />
          </a-descriptions-item>
          
          <a-descriptions-item label="Agent信息" v-if="snapshot.result_data?.agent_id">
            <a-space>
              <a-tag>{{ snapshot.result_data.agent_id }}</a-tag>
              <a-tag v-if="snapshot.result_data.agent_area">{{ snapshot.result_data.agent_area }}</a-tag>
            </a-space>
          </a-descriptions-item>
        </a-descriptions>
      </a-tab-pane>
      
      <!-- 执行详情 -->
      <a-tab-pane key="details" tab="执行详情" v-if="executionDetails">
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="开始时间">
            {{ formatTime(executionDetails.start_time) }}
          </a-descriptions-item>
          
          <a-descriptions-item label="结束时间">
            {{ formatTime(executionDetails.end_time) }}
          </a-descriptions-item>
          
          <a-descriptions-item label="总耗时">
            <a-statistic
              :value="executionDetails.response_time || 0"
              suffix="ms"
              :value-style="{ fontSize: '14px' }"
            />
          </a-descriptions-item>
          
          <a-descriptions-item label="断言统计" v-if="executionDetails.total_assertions !== undefined">
            <a-space>
              <a-statistic
                title="总数"
                :value="executionDetails.total_assertions"
                :value-style="{ fontSize: '14px' }"
              />
              <a-statistic
                title="通过"
                :value="executionDetails.passed_assertions"
                :value-style="{ fontSize: '14px', color: '#52c41a' }"
              />
              <a-statistic
                title="失败"
                :value="executionDetails.total_assertions - executionDetails.passed_assertions"
                :value-style="{ fontSize: '14px', color: '#ff4d4f' }"
              />
            </a-space>
          </a-descriptions-item>
          
          <a-descriptions-item label="变量" v-if="executionDetails.variables">
            <div class="variables-container">
              <a-tag 
                v-for="(value, key) in executionDetails.variables" 
                :key="key"
                color="geekblue"
              >
                {{ key }}: {{ value }}
              </a-tag>
            </div>
          </a-descriptions-item>
        </a-descriptions>
      </a-tab-pane>
      
      <!-- 步骤详情 -->
      <a-tab-pane key="steps" tab="步骤详情" v-if="steps && steps.length > 0">
        <div class="steps-container">
          <a-collapse v-model:activeKey="activeSteps" ghost>
            <a-collapse-panel 
              v-for="(step, index) in steps" 
              :key="index"
              :header="getStepHeader(step, index)"
            >
              <template #extra>
                <a-tag :color="getStepStatusColor(step.status)">
                  {{ step.status }}
                </a-tag>
              </template>
              
              <ApiStepSnapshot :step="step" :step-index="index" />
            </a-collapse-panel>
          </a-collapse>
        </div>
      </a-tab-pane>
      
      <!-- 原始数据 -->
      <a-tab-pane key="raw" tab="原始数据">
        <div class="code-container">
          <div class="code-header">
            <a-space>
              <a-tag size="small">JSON</a-tag>
              <a-button size="small" type="text" @click="copyToClipboard(JSON.stringify(snapshot, null, 2))">
                <template #icon><CopyOutlined /></template>
                复制
              </a-button>
            </a-space>
          </div>
          <pre class="code-block">{{ JSON.stringify(snapshot, null, 2) }}</pre>
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { CopyOutlined } from '@ant-design/icons-vue'
import ApiStepSnapshot from '../../api-monitoring/components/ApiStepSnapshot.vue'

const props = defineProps({
  snapshot: {
    type: Object,
    required: true
  }
})

// 响应式数据
const activeTab = ref('overview')
const activeSteps = ref([0]) // 默认展开第一个步骤

// 计算属性
const executionDetails = computed(() => {
  return props.snapshot.result_data?.details
})

const steps = computed(() => {
  return props.snapshot.result_data?.details?.steps || []
})

// 方法
const formatTime = (timeString) => {
  if (!timeString) return '-'
  try {
    return new Date(timeString).toLocaleString('zh-CN')
  } catch (e) {
    return timeString
  }
}

const getStatusColor = (status) => {
  const colors = {
    'success': 'green',
    'failed': 'red',
    'running': 'blue',
    'pending': 'orange'
  }
  return colors[status] || 'default'
}

const getStepStatusColor = (status) => {
  const colors = {
    'success': 'green',
    'failed': 'red',
    'running': 'blue',
    'pending': 'orange'
  }
  return colors[status] || 'default'
}

const getResponseTimeColor = (responseTime) => {
  if (!responseTime) return '#666'
  if (responseTime < 1000) return '#52c41a'
  if (responseTime < 3000) return '#faad14'
  return '#ff4d4f'
}

const getStepHeader = (step, index) => {
  const stepName = step.name || `步骤 ${index + 1}`
  const responseTime = step.response_time ? ` (${step.response_time}ms)` : ''
  return `${stepName}${responseTime}`
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
.alert-snapshot {
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
  max-height: 400px;
  overflow-y: auto;
}

.variables-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.steps-container {
  max-height: 600px;
  overflow-y: auto;
}

/* 滚动条样式 */
.code-block::-webkit-scrollbar,
.steps-container::-webkit-scrollbar {
  width: 6px;
}

.code-block::-webkit-scrollbar-track,
.steps-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.code-block::-webkit-scrollbar-thumb,
.steps-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.code-block::-webkit-scrollbar-thumb:hover,
.steps-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>