<template>
  <a-row :gutter="16" style="margin-bottom: 16px;">
    <a-col :span="6">
      <a-input-search 
        v-model:value="localSearchParams.keyword" 
        placeholder="搜索任务名称" 
        enter-button 
        @search="handleSearch" 
      />
    </a-col>
    <a-col :span="6">
      <a-select 
        v-model:value="localSearchParams.status" 
        placeholder="选择状态" 
        style="width: 100%" 
        allow-clear
        @change="handleStatusChange"
      >
        <a-select-option value="success">成功</a-select-option>
        <a-select-option value="failed">失败</a-select-option>
        <a-select-option value="timeout">超时</a-select-option>
      </a-select>
    </a-col>
  </a-row>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  searchParams: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['search', 'status-change'])

const localSearchParams = ref({ ...props.searchParams })

watch(
  () => props.searchParams,
  (newVal) => {
    localSearchParams.value = { ...newVal }
  },
  { deep: true }
)

const handleSearch = () => {
  emit('search')
}

const handleStatusChange = () => {
  emit('status-change')
}
</script>