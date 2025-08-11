<template>
  <a-table 
    :dataSource="results" 
    :columns="columns"
    :pagination="{ pageSize: 5 }"
    :rowKey="(record) => record.id"
    :scroll="{ y: 300 }"
    :rowClassName="getRowClassName"
  >
    <template #bodyCell="{ column, record }">
      <template v-if="column.dataIndex === 'location'">
        {{ record.location }}
      </template>
      <template v-if="column.dataIndex === 'time'">
        {{ formatDate(record.created_at) }}
      </template>
      <template v-if="column.dataIndex === 'responseTime'">
        <span v-if="record.response_time">{{ record.response_time }} ms</span>
        <span v-else>-</span>
      </template>
      <template v-if="column.dataIndex === 'status'">
        <StatusTag :status="record.status" />
      </template>
      <template v-if="column.dataIndex === 'actions'">
        <a-button type="link" @click="showProbeDetail(record)">查看详情</a-button>
      </template>
    </template>
  </a-table>
</template>

<script setup>
import StatusTag from './StatusTag.vue'

const props = defineProps({
  results: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['show-probe-detail'])

// 详情表格列定义
const columns = [
  {
    title: '位置',
    dataIndex: 'location'
  },
  {
    title: '时间',
    dataIndex: 'time'
  },
  {
    title: '响应时间',
    dataIndex: 'responseTime',
    sorter: (a, b) => (a.response_time || 0) - (b.response_time || 0)
  },
  {
    title: '状态',
    dataIndex: 'status'
  },
  {
    title: '操作',
    dataIndex: 'actions'
  }
]

// 格式化时间
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 获取行类名
const getRowClassName = (record, index) => {
  if (record.status === 'failed') {
    return 'table-row-error'
  } else if (record.status === 'timeout') {
    return 'table-row-warning'
  }
  return ''
}

const showProbeDetail = (record) => {
  emit('show-probe-detail', record)
}
</script>

<style scoped>
.table-row-error {
  background-color: #fff2f0;
}

.table-row-warning {
  background-color: #fffbe6;
}
</style>