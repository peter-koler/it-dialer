<template>
  <a-card :bordered="false" class="task-info-card">
    <template #title>
      <div class="task-info-header">
        <span>任务基本信息</span>
        <div class="time-filter-wrapper">
          <div class="quick-time-buttons">
            <a-button 
              size="small" 
              @click="setQuickTime(1, 'hour')"
              :type="isQuickTimeActive(1, 'hour') ? 'primary' : 'default'"
            >
              最近1小时
            </a-button>
            <a-button 
              size="small" 
              @click="setQuickTime(8, 'hour')"
              :type="isQuickTimeActive(8, 'hour') ? 'primary' : 'default'"
            >
              最近8小时
            </a-button>
            <a-button 
              size="small" 
              @click="setQuickTime(1, 'day')"
              :type="isQuickTimeActive(1, 'day') ? 'primary' : 'default'"
            >
              最近1天
            </a-button>
            <a-button 
              size="small" 
              @click="setQuickTime(7, 'day')"
              :type="isQuickTimeActive(7, 'day') ? 'primary' : 'default'"
            >
              最近7天
            </a-button>
          </div>
          <a-range-picker
            v-model:value="timeRange"
            :placeholder="['开始时间', '结束时间']"
            format="YYYY-MM-DD HH:mm:ss"
            show-time
            @change="handleTimeRangeChange"
            class="time-range-picker"
          />
          <a-button 
            type="link" 
            @click="resetTimeFilter"
            :disabled="!timeRange || timeRange.length === 0"
            class="reset-filter-btn"
          >
            重置
          </a-button>
        </div>
      </div>
    </template>
    <a-descriptions :column="{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }" bordered>
      <a-descriptions-item label="任务名称">{{ task.name || '-' }}</a-descriptions-item>
      <a-descriptions-item label="目标地址">{{ task.target || '-' }}</a-descriptions-item>
      <a-descriptions-item label="端口">{{ task.port || '-' }}</a-descriptions-item>
      <a-descriptions-item label="执行次数">{{ totalExecutions || 0 }}</a-descriptions-item>
      <a-descriptions-item label="平均响应时间">{{ avgResponseTime ? `${avgResponseTime.toFixed(2)} ms` : '-' }}</a-descriptions-item>
      <a-descriptions-item label="任务类型">TCP拨测</a-descriptions-item>
      <a-descriptions-item label="最新状态">
        <a-tag :color="latestStatus === 'success' ? 'green' : 'red'">
          {{ latestStatus === 'success' ? '成功' : '失败' }}
        </a-tag>
      </a-descriptions-item>
    </a-descriptions>
  </a-card>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'
import dayjs from 'dayjs'

const props = defineProps({
  task: {
    type: Object,
    default: () => ({})
  },
  totalExecutions: {
    type: Number,
    default: 0
  },
  avgResponseTime: {
    type: Number,
    default: 0
  },
  latestStatus: {
    type: String,
    default: 'unknown'
  },
  timeRange: {
    type: Array,
    default: () => []
  },
  currentQuickTime: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:timeRange', 'update:currentQuickTime', 'timeRangeChange', 'resetTimeFilter'])

const timeRange = ref(props.timeRange)
const currentQuickTime = ref(props.currentQuickTime)

// 设置快捷时间
const setQuickTime = (value, unit) => {
  const endTime = dayjs()
  const startTime = dayjs().subtract(value, unit)
  
  timeRange.value = [startTime, endTime]
  currentQuickTime.value = { value, unit }
  
  emit('update:timeRange', timeRange.value)
  emit('update:currentQuickTime', currentQuickTime.value)
  emit('timeRangeChange', timeRange.value)
}

// 判断快捷时间是否激活
const isQuickTimeActive = (value, unit) => {
  return currentQuickTime.value && 
         currentQuickTime.value.value === value && 
         currentQuickTime.value.unit === unit
}

// 处理时间范围变化
const handleTimeRangeChange = (dates) => {
  if (dates && dates.length === 2) {
    currentQuickTime.value = null
    emit('update:currentQuickTime', null)
  }
  emit('update:timeRange', dates)
  emit('timeRangeChange', dates)
}

// 重置时间筛选
const resetTimeFilter = () => {
  timeRange.value = []
  currentQuickTime.value = null
  emit('update:timeRange', [])
  emit('update:currentQuickTime', null)
  emit('resetTimeFilter')
}
</script>

<style scoped>
.task-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.time-filter-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quick-time-buttons {
  display: flex;
  gap: 8px;
}

.time-range-picker {
  width: 300px;
}

.reset-filter-btn {
  padding: 0;
}
</style>