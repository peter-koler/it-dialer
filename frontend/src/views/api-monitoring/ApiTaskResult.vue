<template>
  <div class="api-task-result">
    <!-- 页面头部 -->
    <a-page-header
      class="page-header"
      :title="taskInfo.name || 'API拨测任务结果'"
      :sub-title="`任务ID: ${taskInfo.id || '-'}`"
      @back="() => $router.go(-1)"
    >
      <template #extra>
        <a-space>
          <a-button @click="refreshData" :loading="loading">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
          <a-button type="primary" @click="exportResult">
            <template #icon><DownloadOutlined /></template>
            导出
          </a-button>
          <a-button @click="viewRawData" type="dashed">
            <template #icon><CodeOutlined /></template>
            原始数据
          </a-button>
        </a-space>
      </template>
    </a-page-header>

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
            title="总耗时"
            :value="totalResponseTime"
            suffix="ms"
            :value-style="{ color: getTotalDurationColor() }"
          >
            <template #prefix>
              <ClockCircleOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-statistic
            title="执行步骤"
            :value="totalSteps"
            suffix="步"
          >
            <template #prefix>
              <OrderedListOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-statistic
            title="成功率"
            :value="successRate"
            suffix="%"
            :precision="1"
            :value-style="{ color: getSuccessRateColor() }"
          >
            <template #prefix>
              <CheckCircleOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-statistic
            title="断言通过率"
            :value="assertionPassRate"
            suffix="%"
            :precision="1"
            :value-style="{ color: getAssertionPassRateColor() }"
          >
            <template #prefix>
              <SafetyCertificateOutlined />
            </template>
          </a-statistic>
        </a-col>
      </a-row>
      
      <a-divider />
      
      <a-descriptions :column="{ xxl: 4, xl: 3, lg: 2, md: 2, sm: 1, xs: 1 }" bordered>
        <a-descriptions-item label="执行时间">
          {{ formatDateTime(resultData.created_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="执行节点">
          {{ resultData.agent_area || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="最终状态">
          <a-tag :color="getStatusColor(resultData.status)">
            <template #icon>
              <CheckCircleOutlined v-if="resultData.status === 'success'" />
              <CloseCircleOutlined v-else />
            </template>
            {{ getStatusText(resultData.status) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="目标地址">
          <a-typography-text copyable>{{ taskInfo.target || '-' }}</a-typography-text>
        </a-descriptions-item>
      </a-descriptions>
    </a-card>

    <!-- 步骤时间轴 -->
    <a-card class="timeline-card" :bordered="false">
      <template #title>
        <a-space>
          <UnorderedListOutlined />
          <span>API执行步骤</span>
          <a-badge :count="stepsList.length" :number-style="{ backgroundColor: '#52c41a' }" />
        </a-space>
      </template>
      
      <div class="timeline-container">
        <div class="timeline-left">
          <a-empty v-if="!stepsList.length" description="暂无执行步骤" />
          <ApiStepTimeline
            v-else
            :steps="stepsList"
            :active-step-index="activeStepIndex"
            :show-preview="true"
            @step-click="handleStepClick"
            @expand-all="expandAllSteps"
            @collapse-all="collapseAllSteps"
          />
        </div>
        
        <div class="timeline-right">
          <a-card 
            v-if="activeStep" 
            :bordered="false"
            class="step-detail-card"
          >
            <template #title>
              <a-space>
                <EyeOutlined />
                <span>详细快照</span>
                <span class="step-indicator">
                  步骤 {{ activeStepIndex + 1 }}
                </span>
              </a-space>
            </template>
            <ApiStepSnapshot :step="activeStep" :step-index="activeStepIndex" />
          </a-card>
          
          <a-empty v-else description="点击左侧步骤查看详细执行快照" />
        </div>
      </div>
    </a-card>

    <!-- 变量状态 -->
    <a-card class="variables-card" :bordered="false">
      <template #title>
        <a-space>
          <DatabaseOutlined />
          <span>变量最终状态</span>
          <a-badge :count="Object.keys(finalVariables).length" :number-style="{ backgroundColor: '#1890ff' }" />
        </a-space>
      </template>
      
      <div class="variables-content">
        <a-empty v-if="!Object.keys(finalVariables).length" description="暂无变量数据" />
        <ApiVariableTracker
          v-else
          :variables="finalVariables"
          :steps="stepsList"
        />
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { h } from 'vue'
import {
  ReloadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CheckOutlined,
  CloseOutlined,
  LoadingOutlined,
  DashboardOutlined,
  ClockCircleOutlined,
  OrderedListOutlined,
  SafetyCertificateOutlined,
  UnorderedListOutlined,
  EyeOutlined,
  DatabaseOutlined,
  CodeOutlined
} from '@ant-design/icons-vue'
import request from '@/utils/request'
import ApiStepSnapshot from './components/ApiStepSnapshot.vue'
import ApiStepTimeline from './components/ApiStepTimeline.vue'
import ApiVariableTracker from './components/ApiVariableTracker.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const taskInfo = ref({})
const resultData = ref({})
const activeStepIndex = ref(0)
const rawDataVisible = ref(false)

// 计算属性
const stepsList = computed(() => {
  if (!resultData.value || !resultData.value.details || !resultData.value.details.steps) {
    return []
  }
  return resultData.value.details.steps || []
})

const activeStep = computed(() => {
  return stepsList.value[activeStepIndex.value] || null
})

const totalResponseTime = computed(() => {
  if (!resultData.value || !resultData.value.details) return 0
  const details = resultData.value.details
  
  if (details.end_time && details.start_time) {
    return new Date(details.end_time) - new Date(details.start_time)
  }
  
  return details.response_time || 0
})

const successRate = computed(() => {
  if (totalSteps.value === 0) return 0
  return (successSteps.value / totalSteps.value) * 100
})

const totalSteps = computed(() => {
  return stepsList.value.length
})

const successSteps = computed(() => {
  return stepsList.value.filter(step => step.status === 'success').length
})

const assertionPassRate = computed(() => {
  const totalAssertions = resultData.value.details?.total_assertions || 0
  const passedAssertions = resultData.value.details?.passed_assertions || 0
  
  if (totalAssertions === 0) return 100
  return (passedAssertions / totalAssertions) * 100
})

const finalVariables = computed(() => {
  if (!resultData.value || !resultData.value.details || !resultData.value.details.variables) {
    return {}
  }
  
  return resultData.value.details.variables || {}
})

// 变量表格列定义
const variableColumns = [
  {
    title: '变量名',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    fixed: 'left'
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
    width: 100
  },
  {
    title: '值',
    dataIndex: 'value',
    key: 'value',
    ellipsis: true
  }
]

// 方法
const fetchData = async () => {
  loading.value = true
  try {
    const taskId = route.params.id
    const resultId = route.params.resultId
    
    // 获取任务信息
    const taskResponse = await request.get(`/tasks/${taskId}`)
    taskInfo.value = taskResponse.data
    
    // 获取结果详情
    const resultResponse = await request.get(`/results/${resultId}`)
    resultData.value = resultResponse.data
    
    // 解析details字段
    if (typeof resultData.value.details === 'string') {
      try {
        resultData.value.details = JSON.parse(resultData.value.details)
      } catch (e) {
        console.error('解析details字段失败:', e)
        resultData.value.details = {}
      }
    }
    
  } catch (error) {
    console.error('获取数据失败:', error)
    message.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchData()
}

const exportResult = () => {
  const reportData = {
    taskInfo: taskInfo.value,
    overview: {
      totalResponseTime: totalResponseTime.value,
      totalSteps: totalSteps.value,
      successSteps: successSteps.value,
      assertionPassRate: assertionPassRate.value
    },
    steps: stepsList.value,
    variables: finalVariables.value,
    exportTime: new Date().toISOString()
  }
  
  const dataStr = JSON.stringify(reportData, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `api-result-${resultData.value.id || 'unknown'}-${Date.now()}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  message.success('报告已导出')
}

const viewRawData = () => {
  Modal.info({
    title: '原始数据',
    width: '80%',
    content: h('pre', {
      style: {
        background: '#f5f5f5',
        padding: '16px',
        borderRadius: '6px',
        maxHeight: '500px',
        overflow: 'auto',
        fontSize: '12px',
        fontFamily: 'Monaco, Menlo, Ubuntu Mono, monospace'
      }
    }, JSON.stringify(resultData.value, null, 2))
  })
}

const expandAllSteps = () => {
  // 展开所有步骤的预览
  message.info('展开所有步骤')
}

const collapseAllSteps = () => {
  // 收起所有步骤的预览
  message.info('收起所有步骤')
}

const handleStepClick = (index) => {
  activeStepIndex.value = index
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const getStatusColor = (status) => {
  return status === 'success' ? 'success' : 'error'
}

const getStatusText = (status) => {
  return status === 'success' ? '成功' : '失败'
}

const getTotalDurationColor = () => {
  const duration = totalResponseTime.value
  if (duration < 1000) return '#52c41a'
  if (duration < 5000) return '#faad14'
  return '#ff4d4f'
}

const getSuccessRateColor = () => {
  const rate = successRate.value
  if (rate >= 95) return '#52c41a'
  if (rate >= 80) return '#faad14'
  return '#ff4d4f'
}

const getAssertionPassRateColor = () => {
  const rate = assertionPassRate.value
  if (rate >= 95) return '#52c41a'
  if (rate >= 80) return '#faad14'
  return '#ff4d4f'
}

const getStepTimelineColor = (step) => {
  if (step.status === 'success') return 'green'
  if (step.status === 'failed') return 'red'
  return 'blue'
}

const getStepDotClass = (step) => {
  return {
    'dot-success': step.status === 'success',
    'dot-error': step.status === 'failed',
    'dot-processing': step.status !== 'success' && step.status !== 'failed'
  }
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

const getAssertionSummary = (assertions) => {
  if (!assertions || assertions.length === 0) return '无断言'
  const passed = assertions.filter(a => a.result === true).length
  const total = assertions.length
  return `断言 ${passed}/${total}`
}

const getVariableType = (value) => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'string') return 'string'
  if (typeof value === 'number') return 'number'
  if (typeof value === 'boolean') return 'boolean'
  if (Array.isArray(value)) return 'array'
  if (typeof value === 'object') return 'object'
  return 'unknown'
}

const getVariableTypeColor = (type) => {
  const colors = {
    'string': 'blue',
    'number': 'green',
    'boolean': 'orange',
    'array': 'purple',
    'object': 'cyan',
    'null': 'default',
    'undefined': 'default'
  }
  return colors[type] || 'default'
}

const isSimpleValue = (value) => {
  return typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
}

const formatComplexValue = (value) => {
  try {
    return JSON.stringify(value, null, 2)
  } catch (e) {
    return String(value)
  }
}

// 生命周期
onMounted(() => {
  fetchData()
})

// 监听路由变化
watch(() => route.params, () => {
  if (route.params.id && route.params.resultId) {
    fetchData()
  }
}, { deep: true })
</script>

<style scoped>
.api-task-result {
  padding: 24px;
  background: #f0f2f5;
  min-height: 100vh;
}

.page-header {
  background: #fff;
  margin-bottom: 24px;
  border-radius: 8px;
}

.overview-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.timeline-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.timeline-container {
  display: flex;
  gap: 24px;
  min-height: 600px;
}

.timeline-left {
  flex: 0 0 400px;
  border-right: 1px solid #f0f0f0;
  padding-right: 24px;
  max-height: 600px;
  overflow-y: auto;
}

.timeline-right {
  flex: 1;
  overflow-y: auto;
  max-height: 600px;
}

.timeline-item-active {
  background: #f6ffed;
  border-radius: 8px;
  padding: 8px;
  margin: -8px;
}

.timeline-content {
  cursor: pointer;
  padding: 8px 0;
}

.timeline-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #fff;
}

.dot-success {
  background: #52c41a;
}

.dot-error {
  background: #ff4d4f;
}

.dot-processing {
  background: #1890ff;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.step-time {
  color: #666;
  font-size: 12px;
  font-weight: 500;
}

.step-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.step-url {
  color: #666;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.step-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-assertions {
  color: #666;
  font-size: 12px;
}

.step-detail-card {
  height: 100%;
}

.variables-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.variable-value {
  max-width: 400px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .api-task-result {
    padding: 16px;
  }
  
  .timeline-container {
    flex-direction: column;
  }
  
  .timeline-left {
    flex: none;
    border-right: none;
    border-bottom: 1px solid #f0f0f0;
    padding-right: 0;
    padding-bottom: 16px;
    margin-bottom: 16px;
    max-height: 400px;
  }
  
  .timeline-right {
    flex: none;
    max-height: none;
  }
}
</style>