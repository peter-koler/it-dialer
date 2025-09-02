<template>
  <div>
    <a-table
      :columns="columns"
      :data-source="users"
      :loading="loading"
      :pagination="pagination"
      :row-key="record => record.id"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'index'">
          {{ (pagination.current - 1) * pagination.pageSize + users.indexOf(record) + 1 }}
        </template>
        <template v-else-if="column.dataIndex === 'role'">
          <a-tag :color="record.role === 'admin' ? 'red' : 'blue'">
            {{ record.role === 'admin' ? '管理员' : '查看者' }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'status'">
          <a-switch
            :checked="record.status === 1"
            checked-children="启用"
            un-checked-children="禁用"
            @change="onStatusChange(record, $event)"
          />
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="onEdit(record)">编辑</a-button>
            <a-button type="link" size="small" @click="onResetPassword(record)">重置密码</a-button>
            <a-popconfirm
              :title="`确定删除用户 ${record.username}？`"
              @confirm="onDelete(record)"
            >
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'

const props = defineProps({
  users: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['edit', 'reset-password', 'delete', 'change'])

// 表格列定义
const columns = [
  {
    title: '序号',
    dataIndex: 'index',
    key: 'index'
  },
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    sorter: true
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    sorter: true
  },
  {
    title: '角色',
    dataIndex: 'role',
    key: 'role'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status'
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    sorter: true
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'action'
  }
]

const handleTableChange = (pagination, filters, sorter) => {
  emit('change', pagination, filters, sorter)
}

const onEdit = (record) => {
  emit('edit', record)
}

const onResetPassword = (record) => {
  emit('reset-password', record)
}

const onDelete = (record) => {
  emit('delete', record)
}

const onStatusChange = async (record, checked) => {
  try {
    const newStatus = checked ? 1 : 0
    // 调用API更新用户状态
    await request.patch(`/users/${record.id}`, { status: newStatus })
    // 更新本地数据
    record.status = newStatus
    message.success(`用户 ${record.username} 状态已更新`)
  } catch (error) {
    message.error('状态更新失败: ' + error.message)
  }
}
</script>