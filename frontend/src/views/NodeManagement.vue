<template>
  <div class="node-management">
    <a-card>
      <template #title>
        <div class="card-header">
          <span>节点管理</span>
          <a-button type="primary" @click="fetchNodes" style="margin-left: 12px;">
            <ReloadOutlined />
            刷新
          </a-button>
        </div>
      </template>
      
      <a-table 
        :dataSource="nodes" 
        :columns="columns" 
        :pagination="pagination"
        :loading="loading"
        rowKey="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'lastHeartbeat'">
            {{ formatDateTime(record.last_heartbeat) }}
          </template>
          <template v-else-if="column.key === 'createdAt'">
            {{ formatDateTime(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'action' && canOperateNodes">
            <a-space>
              <a-button 
                size="small" 
                :type="record.status === 'online' ? 'default' : 'primary'"
                @click="toggleNodeStatus(record)"
              >
                {{ record.status === 'online' ? '下线' : '上线' }}
              </a-button>
              <a-button size="small" type="primary" danger @click="deleteNode(record)">
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, computed } from 'vue'
import { 
  getNodeList, 
  updateNodeStatus, 
  deleteNode as deleteNodeAPI
} from '@/api/node'
import { 
  ReloadOutlined 
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'

export default defineComponent({
  name: 'NodeManagement',
  components: {
    ReloadOutlined
  },
  setup() {
    const userStore = useUserStore()
    const nodes = ref([])
    const loading = ref(false)
    const pagination = ref({
      current: 1,
      pageSize: 10,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true,
      showTotal: (total) => `共 ${total} 条记录`
    })
    
    // 权限控制
    const canOperateNodes = computed(() => userStore.isSuperAdmin)
    
    // 动态列配置，根据权限显示操作列
    const columns = computed(() => {
      const baseColumns = [
        {
          title: 'ID',
          dataIndex: 'id',
          width: 80
        },
        {
          title: 'Agent ID',
          dataIndex: 'agent_id'
        },
        {
          title: '区域',
          dataIndex: 'agent_area'
        },
        {
          title: 'IP地址',
          dataIndex: 'ip_address'
        },
        {
          title: '主机名',
          dataIndex: 'hostname'
        },
        {
          title: '状态',
          dataIndex: 'status',
          key: 'status'
        },
        {
          title: '最后心跳',
          dataIndex: 'last_heartbeat',
          key: 'lastHeartbeat'
        },
        {
          title: '创建时间',
          dataIndex: 'created_at',
          key: 'createdAt'
        }
      ]
      
      // 只有超级管理员才显示操作列
      if (canOperateNodes.value) {
        baseColumns.push({
          title: '操作',
          key: 'action',
          width: 200
        })
      }
      
      return baseColumns
    })
    
    // 获取节点列表
    const fetchNodes = async (params = {}) => {
      try {
        loading.value = true
        const query = {
          page: pagination.value.current,
          size: pagination.value.pageSize,
          ...params
        }
        
        const res = await getNodeList(query)
        
        if (res.code === 0) {
          nodes.value = res.data.list
          pagination.value.total = res.data.total
        } else {
          message.error(res.message || '获取节点列表失败')
        }
      } catch (err) {
        // 如果是登录过期错误，不显示错误消息，让axios拦截器处理跳转
        if (err.message === '登录已过期，请重新登录') {
          console.log('检测到登录过期，由axios拦截器处理跳转')
          return
        }
        message.error('获取节点列表失败: ' + err.message)
      } finally {
        loading.value = false
      }
    }
    
    // 处理表格分页、排序等变化
    const handleTableChange = (pag) => {
      pagination.value.current = pag.current
      pagination.value.pageSize = pag.pageSize
      fetchNodes()
    }
    
    // 切换节点状态
    const toggleNodeStatus = async (record) => {
      // 权限检查
      if (!canOperateNodes.value) {
        message.error('您没有权限执行此操作')
        return
      }
      
      try {
        const newStatus = record.status === 'online' ? 'offline' : 'online'
        const res = await updateNodeStatus({
          node_id: record.id,
          status: newStatus
        })
        
        if (res.code === 0) {
          message.success(`${record.agent_id} ${newStatus === 'online' ? '上线' : '下线'}成功`)
          fetchNodes()
        } else {
          message.error(res.message || '操作失败')
        }
      } catch (err) {
        message.error('操作失败: ' + err.message)
      }
    }
    
    // 删除节点
    const deleteNode = (record) => {
      // 权限检查
      if (!canOperateNodes.value) {
        message.error('您没有权限执行此操作')
        return
      }
      
      Modal.confirm({
        title: '确认删除',
        content: `确定要删除节点 ${record.agent_id} 吗？此操作不可恢复。`,
        okText: '确认',
        cancelText: '取消',
        onOk: async () => {
          try {
            const res = await deleteNodeAPI(record.id)
            if (res && res.code === 0) {
              message.success('删除成功')
              fetchNodes()
            } else {
              message.error(res?.message || '删除失败')
            }
          } catch (err) {
            console.error('删除节点失败:', err)
            message.error('删除失败: ' + (err.message || '未知错误'))
          }
        }
      })
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'online': '运行中',
        'offline': '下线',
        'timeout': '超时'
      }
      return statusMap[status] || status
    }
    
    // 获取状态颜色
    const getStatusColor = (status) => {
      const colorMap = {
        'online': 'green',
        'offline': 'red',
        'timeout': 'orange'
      }
      return colorMap[status] || 'default'
    }
    
    // 格式化日期时间
    const formatDateTime = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    // 初始化
    onMounted(() => {
      fetchNodes()
    })
    
    return {
      nodes,
      loading,
      pagination,
      columns,
      canOperateNodes,
      fetchNodes,
      handleTableChange,
      toggleNodeStatus,
      deleteNode,
      getStatusText,
      getStatusColor,
      formatDateTime
    }
  }
})
</script>

<style scoped>
.node-management {
  padding: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>