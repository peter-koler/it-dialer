<template>
  <a-modal
    :open="open"
    :title="`拨测点: ${getLocationName(probeData.location)}`"
    width="80%"
    :footer="null"
    @cancel="handleCancel"
  >
    <div class="api-task-result">
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
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="执行步骤"
              :value="totalSteps"
              suffix="步"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="成功率"
              :value="successRate"
              suffix="%"
              :precision="1"
            />
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <a-statistic
              title="断言通过率"
              :value="assertionPassRate"
              suffix="%"
              :precision="1"
            />
          </a-col>
        </a-row>
      </a-card>

      <!-- 步骤时间轴 -->
      <a-card class="timeline-card" :bordered="false">
        <template #title>
          <a-space>
            <UnorderedListOutlined />
            <span>API执行步骤</span>
            <a-badge :count="stepsList.length" />
          </a-space>
        </template>
        <div class="timeline-container">
          <div class="timeline-left">
            <a-empty v-if="!stepsList.length" description="暂无执行步骤" />
            <ApiStepTimeline
              v-else
              :steps="stepsList"
              :active-step-index="activeStepIndex"
              @step-click="handleStepClick"
            />
          </div>
          <div class="timeline-right">
            <a-card v-if="activeStep" :bordered="false" class="step-detail-card">
              <template #title>
                <a-space>
                  <EyeOutlined />
                  <span>详细快照 (步骤 {{ activeStepIndex + 1 }})</span>
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
            <a-badge :count="Object.keys(finalVariables).length" />
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
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  DashboardOutlined, 
  UnorderedListOutlined, 
  EyeOutlined, 
  DatabaseOutlined 
} from '@ant-design/icons-vue'
import ApiStepSnapshot from './ApiStepSnapshot.vue'
import ApiStepTimeline from './ApiStepTimeline.vue'
import ApiVariableTracker from './ApiVariableTracker.vue'
import pinyinToChinese from '@/utils/pinyinToChinese'

const props = defineProps({
  open: Boolean,
  probeData: { // Changed from resultData to probeData to reflect it's for a specific probe
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:open'])

const activeStepIndex = ref(0)

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

const stepsList = computed(() => resultData.value.steps || [])
const activeStep = computed(() => stepsList.value[activeStepIndex.value] || null)
const finalVariables = computed(() => resultData.value.variables || {})

const totalResponseTime = computed(() => {
  if (resultData.value.end_time && resultData.value.start_time) {
    return new Date(resultData.value.end_time) - new Date(resultData.value.start_time)
  }
  return resultData.value.response_time || 0
})

const totalSteps = computed(() => stepsList.value.length)
const successSteps = computed(() => stepsList.value.filter(s => s.status === 'success').length)
const successRate = computed(() => totalSteps.value > 0 ? (successSteps.value / totalSteps.value) * 100 : 0)

const assertionPassRate = computed(() => {
  const total = resultData.value.total_assertions || 0
  const passed = resultData.value.passed_assertions || 0
  if (total === 0) return 100
  return (passed / total) * 100
})

const handleStepClick = (index) => {
  activeStepIndex.value = index
}

const getLocationName = (location) => {
  return pinyinToChinese[location] || location
}

const handleCancel = () => {
  emit('update:open', false)
}

watch(() => props.open, (newVal) => {
  if (newVal) {
    activeStepIndex.value = 0
  }
})
</script>

<style scoped>
.api-task-result {
  background: #f0f2f5;
  padding: 12px;
}
.overview-card, .timeline-card, .variables-card {
  margin-bottom: 12px;
}
.timeline-container {
  display: flex;
  gap: 12px;
  min-height: 400px;
}
.timeline-left {
  flex: 0 0 300px;
  border-right: 1px solid #f0f0f0;
  padding-right: 12px;
  max-height: 400px;
  overflow-y: auto;
}
.timeline-right {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
}
</style>