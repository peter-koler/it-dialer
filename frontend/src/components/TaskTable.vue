<template>
  <a-table
    :dataSource="tasks"
    :columns="columns"
    :loading="loading"
    :pagination="pagination"
    @change="handleTableChange"
    :rowKey="(record) => record.id"
  >
    <template #bodyCell="{ column, record }">
      <template v-if="column.dataIndex === 'type'">
        <a-tag v-if="record.type === 'ping'" color="blue">Ping</a-tag>
        <a-tag v-else-if="record.type === 'tcp'" color="cyan">TCP</a-tag>
        <a-tag v-else-if="record.type === 'http'" color="purple">HTTP</a-tag>
        <a-tag v-else-if="record.type === 'api'" color="purple">API</a-tag>
        <a-tag v-else color="green">{{ record.type }}</a-tag>
      </template>
      
      <template v-else-if="column.dataIndex === 'latest_status'">
        <a-tag v-if="record.latest_status === 'success'" color="green">成功</a-tag>
        <a-tag v-else-if="record.latest_status === 'failed'" color="red">失败</a-tag>
        <a-tag v-else-if="record.latest_status === 'timeout'" color="orange">超时</a-tag>
        <a-tag v-else-if="record.latest_status">{{ record.latest_status }}</a-tag>
        <span v-else>-</span>
      </template>
      
      <template v-else-if="column.dataIndex === 'execution_count'">
        {{ record.execution_count || 0 }}
      </template>
      
      <template v-else-if="column.dataIndex === 'avg_response_time'">
        <span v-if="record.avg_response_time">{{ record.avg_response_time }} ms</span>
        <span v-else>-</span>
      </template>
      
      <template v-else-if="column.dataIndex === 'enabled'">
        <a-switch 
          v-model:checked="record.enabled" 
          @change="updateTaskStatus(record)"
          checked-children="启用" 
          un-checked-children="禁用"
        />
      </template>
      
      <template v-else-if="column.dataIndex === 'action'">
        <a-space>
          <a-button type="link" size="small" @click="editTask(record)">编辑</a-button>
          <a-popconfirm
            title="确定删除此任务吗？"
            ok-text="确定"
            cancel-text="取消"
            @confirm="deleteTask(record)"
          >
            <a-button type="link" size="small" danger>删除</a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </template>
  </a-table>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'

const props = defineProps({
  tasks: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['updateTaskStatus', 'editTask', 'deleteTask', 'tableChange'])

// 表格列定义
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    width: 80
  },
  {
    title: '任务名称',
    dataIndex: 'name'
  },
  {
    title: '任务类型',
    dataIndex: 'type'
  },
  {
    title: '目标地址',
    dataIndex: 'target'
  },
  {
    title: '执行间隔(秒)',
    dataIndex: 'interval'
  },
  {
    title: '最新状态',
    dataIndex: 'latest_status',
    width: 100
  },
  {
    title: '执行次数',
    dataIndex: 'execution_count',
    width: 100
  },
  {
    title: '平均响应时间',
    dataIndex: 'avg_response_time',
    width: 120
  },
  {
    title: '状态',
    dataIndex: 'enabled',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'created_at'
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 150
  }
]

// 更新任务状态
const updateTaskStatus = async (record) => {
  emit('updateTaskStatus', record)
}

// 编辑任务
const editTask = (record) => {
  emit('editTask', record)
}

// 删除任务
const deleteTask = async (record) => {
  emit('deleteTask', record)
}

// 处理表格变化
const handleTableChange = (pager) => {
  emit('tableChange', pager)
}
</script>