<template>
  <a-table 
    :dataSource="historyData" 
    :columns="columns"
    :pagination="{ pageSize: 5 }"
    :rowKey="(record) => record.id"
  >
    <template #bodyCell="{ column, record }">
      <template v-if="column.dataIndex === 'time'">
        {{ formatDate(record.created_at) }}
      </template>
      <template v-if="column.dataIndex === 'responseTime'">
        <span v-if="record.response_time">{{ parseFloat(record.response_time).toFixed(2) }} ms</span>
        <span v-else>-</span>
      </template>
      <template v-if="column.dataIndex === 'status'">
        <StatusTag :status="record.status" />
      </template>
    </template>
  </a-table>
</template>

<script setup>
import StatusTag from './StatusTag.vue'

defineProps({
  historyData: {
    type: Array,
    default: () => []
  }
})

// 拨测点详情表格列定义
const columns = [
  {
    title: '时间',
    dataIndex: 'time'
  },
  {
    title: '响应时间',
    dataIndex: 'responseTime'
  },
  {
    title: '状态',
    dataIndex: 'status'
  }
]

// 格式化时间
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}
</script>