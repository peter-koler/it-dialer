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
          <a-button 
            :type="autoRefresh ? 'default' : 'dashed'" 
            @click="toggleAutoRefresh" 
            style="margin-left: 8px;"
          >
            {{ autoRefresh ? '停止自动刷新' : '开启自动刷新' }}
          </a-button>
        </div>
      </template>
      
      <!-- 搜索和过滤区域 -->
      <div class="search-filter-section">
        <a-row :gutter="16" style="margin-bottom: 16px;">
          <a-col :span="8">
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索 Agent ID 或 IP 地址"
              allow-clear
              @search="handleSearch"
              @change="handleSearchChange"
            />
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="filterArea"
              placeholder="选择区域"
              allow-clear
              style="width: 100%"
              @change="handleAreaFilter"
            >
              <a-select-option v-for="area in areaOptions" :key="area" :value="area">
                {{ area }}
              </a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="filterStatus"
              placeholder="选择状态"
              allow-clear
              style="width: 100%"
              @change="handleStatusFilter"
            >
              <a-select-option value="online">运行中</a-select-option>
              <a-select-option value="offline">下线</a-select-option>
              <a-select-option value="timeout">超时</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-button @click="resetFilters">重置筛选</a-button>
          </a-col>
        </a-row>
      </div>
      
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
          <template v-else-if="column.key === 'thread_pool'">
             <div v-if="record.thread_pool && record.thread_pool.max_workers">
               {{ record.thread_pool.active_threads || 0 }}/{{ record.thread_pool.max_workers || 0 }}
             </div>
             <div v-else>
               暂无数据
             </div>
           </template>
          <template v-else-if="column.key === 'task_status'">
             <div v-if="record.task_status && record.task_status.total_tasks">
               总计: {{ record.task_status.total_tasks || 0 }}
             </div>
             <div v-else>
               暂无任务
             </div>
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
import { defineComponent, ref, onMounted, onUnmounted, computed } from 'vue'
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
    
    // 搜索和过滤状态
    const searchKeyword = ref('')
    const filterArea = ref(undefined)
    const filterStatus = ref(undefined)
    const areaOptions = ref([])
    
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
          title: '线程池状态',
          key: 'thread_pool',
          width: 200
        },
        {
          title: '任务统计',
          key: 'task_status',
          width: 150
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
          // 添加搜索和过滤参数
          keyword: searchKeyword.value || undefined,
          area: filterArea.value || undefined,
          status: filterStatus.value || undefined,
          ...params
        }
        
        const res = await getNodeList(query)
        
        if (res.code === 0) {
          nodes.value = res.data.list
          pagination.value.total = res.data.total
          
          // 更新区域选项
          updateAreaOptions(res.data.list)
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
    
    // 更新区域选项
    const updateAreaOptions = (nodeList) => {
      const areas = [...new Set(nodeList.map(node => node.agent_area).filter(Boolean))]
      areaOptions.value = areas.sort()
    }
    
    // 自动刷新功能
    const autoRefresh = ref(true)
    const refreshInterval = ref(null)
    
    const startAutoRefresh = () => {
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
      }
      if (autoRefresh.value) {
        refreshInterval.value = setInterval(() => {
          fetchNodes()
        }, 30000) // 每30秒刷新一次
      }
    }
    
    const stopAutoRefresh = () => {
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
        refreshInterval.value = null
      }
    }
    
    const toggleAutoRefresh = () => {
      autoRefresh.value = !autoRefresh.value
      if (autoRefresh.value) {
        startAutoRefresh()
      } else {
        stopAutoRefresh()
      }
    }
    
    // 处理表格分页、排序等变化
    const handleTableChange = (pag) => {
      pagination.value.current = pag.current
      pagination.value.pageSize = pag.pageSize
      fetchNodes()
    }
    
    // 搜索处理
    const handleSearch = () => {
      pagination.value.current = 1 // 重置到第一页
      fetchNodes()
    }
    
    const handleSearchChange = (e) => {
      if (!e.target.value) {
        // 如果搜索框被清空，立即刷新
        pagination.value.current = 1
        fetchNodes()
      }
    }
    
    // 区域过滤处理
    const handleAreaFilter = () => {
      pagination.value.current = 1
      fetchNodes()
    }
    
    // 状态过滤处理
    const handleStatusFilter = () => {
      pagination.value.current = 1
      fetchNodes()
    }
    
    // 重置筛选
    const resetFilters = () => {
      searchKeyword.value = ''
      filterArea.value = undefined
      filterStatus.value = undefined
      pagination.value.current = 1
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
      startAutoRefresh()
    })
    
    // 组件卸载时清理定时器
    onUnmounted(() => {
      stopAutoRefresh()
    })
    
    return {
      nodes,
      loading,
      pagination,
      columns,
      canOperateNodes,
      autoRefresh,
      // 搜索和过滤相关
      searchKeyword,
      filterArea,
      filterStatus,
      areaOptions,
      handleSearch,
      handleSearchChange,
      handleAreaFilter,
      handleStatusFilter,
      resetFilters,
      // 原有方法
      fetchNodes,
      handleTableChange,
      toggleNodeStatus,
      deleteNode,
      toggleAutoRefresh,
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

.search-filter-section {
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
  margin-bottom: 16px;
}

.search-filter-section .ant-input-search {
  border-radius: 6px;
}

.search-filter-section .ant-select {
  border-radius: 6px;
}

.search-filter-section .ant-btn {
  border-radius: 6px;
}
</style>