<template>
  <a-space :size="8">
    <a-range-picker
      v-model:value="timeRangeValue"
      :presets="presets"
      :disabled-date="disabledDate"
      :show-time="{ format: 'HH:mm' }"
      format="YYYY-MM-DD HH:mm:ss"
      @change="onRangeChange"
    />
  </a-space>
</template>

<script setup>
import { ref, watch } from 'vue'
import dayjs from 'dayjs'

// 定义属性
const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

// 定义事件
const emit = defineEmits(['update:modelValue', 'change'])

// 响应式数据
const timeRangeValue = ref(props.modelValue && props.modelValue.length === 2 
  ? [dayjs(props.modelValue[0]), dayjs(props.modelValue[1])] 
  : getDefaultTimeRange())

// 预设时间范围
const presets = [
  { label: '1小时', value: [dayjs().subtract(1, 'hour'), dayjs()] },
  { label: '6小时', value: [dayjs().subtract(6, 'hour'), dayjs()] },
  { label: '12小时', value: [dayjs().subtract(12, 'hour'), dayjs()] },
  { label: '1天', value: [dayjs().subtract(1, 'day'), dayjs()] },
  { label: '3天', value: [dayjs().subtract(3, 'day'), dayjs()] },
  { label: '7天', value: [dayjs().subtract(7, 'day'), dayjs()] }
]

// 禁用未来时间
const disabledDate = (current) => {
  return current && current > dayjs().endOf('day')
}

// 获取默认时间范围（1小时）
function getDefaultTimeRange() {
  return [dayjs().subtract(1, 'hour'), dayjs()]
}

// 处理时间范围变化
const onRangeChange = (dates) => {
  if (dates && dates.length === 2) {
    // 检查时间跨度是否超过30天
    const diffDays = dates[1].diff(dates[0], 'day')
    if (diffDays > 30) {
      // 提示用户选择30天内范围
      console.warn('请选择 30 天内范围')
      return
    }
    
    // 使用本地时间格式而不是UTC
    const timeRange = [dates[0].format(), dates[1].format()]
    emit('update:modelValue', timeRange)
    emit('change', {
      start: timeRange[0],
      end: timeRange[1]
    })
  }
}

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.length === 2) {
    timeRangeValue.value = [dayjs(newVal[0]), dayjs(newVal[1])]
  }
}, { immediate: true })
</script>