<template>
  <a-row :gutter="16" style="margin-bottom: 16px;">
    <a-col :span="6">
      <a-input-search 
        v-model:value="localSearchParams.keyword" 
        placeholder="搜索任务名称或目标地址" 
        enter-button 
        @search="handleSearch" 
      />
    </a-col>
    <a-col :span="6">
      <a-select 
        v-model:value="localSearchParams.type" 
        placeholder="选择任务类型" 
        style="width: 100%" 
        allow-clear
        @change="handleTypeChange"
      >
        <a-select-option value="ping">Ping</a-select-option>
        <a-select-option value="tcp">TCP</a-select-option>
        <a-select-option value="http">HTTP</a-select-option>
      </a-select>
    </a-col>
    <a-col :span="6">
      <a-select 
        v-model:value="localSearchParams.status" 
        placeholder="选择状态" 
        style="width: 100%" 
        allow-clear
        @change="handleStatusChange"
      >
        <a-select-option value="true">启用</a-select-option>
        <a-select-option value="false">禁用</a-select-option>
      </a-select>
    </a-col>
    <a-col :span="6">
      <a-button @click="resetFilters">重置</a-button>
    </a-col>
  </a-row>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  searchParams: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:searchParams', 'search', 'reset'])

// 本地搜索参数
const localSearchParams = reactive({
  keyword: '',
  type: undefined,
  status: undefined // 改为undefined而不是布尔值
})

// 监听props变化
watch(() => props.searchParams, (newVal) => {
  // 转换布尔值为字符串
  const transformedParams = { ...newVal }
  if (typeof transformedParams.status === 'boolean') {
    transformedParams.status = transformedParams.status.toString()
  } else if (transformedParams.status === undefined || transformedParams.status === null) {
    transformedParams.status = undefined
  }
  Object.assign(localSearchParams, transformedParams)
}, { immediate: true, deep: true })

// 监听本地搜索参数变化
watch(localSearchParams, (newVal) => {
  // 转换字符串为布尔值
  const transformedParams = { ...newVal }
  if (transformedParams.status === 'true') {
    transformedParams.status = true
  } else if (transformedParams.status === 'false') {
    transformedParams.status = false
  } else {
    transformedParams.status = undefined
  }
  emit('update:searchParams', transformedParams)
}, { deep: true })

// 处理搜索
const handleSearch = () => {
  emit('search')
}

// 处理类型变更
const handleTypeChange = () => {
  emit('search')
}

// 处理状态变更
const handleStatusChange = () => {
  emit('search')
}

// 重置筛选
const resetFilters = () => {
  localSearchParams.keyword = ''
  localSearchParams.type = undefined
  localSearchParams.status = undefined
  emit('reset')
}
</script>