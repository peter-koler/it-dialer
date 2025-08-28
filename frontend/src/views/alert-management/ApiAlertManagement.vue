<template>
  <div class="api-alert-management">
    <a-page-header title="API告警管理">
      <template #extra>
        <a-space>
          <a-button @click="refreshData">
            <template #icon><reload-outlined /></template>
            刷新
          </a-button>
          <a-button type="primary" @click="showBatchActions = !showBatchActions">
            <template #icon><setting-outlined /></template>
            批量操作
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="content-container">
      <!-- 筛选条件 -->
      <a-card size="small" style="margin-bottom: 16px;">
        <a-form layout="inline">
          <a-form-item label="告警级别">
            <a-select 
              v-model:value="filters.level" 
              placeholder="选择告警级别" 
              style="width: 120px"
              allowClear
            >
              <a-select-option value="critical">严重</a-select-option>
              <a-select-option value="warning">警告</a-select-option>
              <a-select-option value="info">信息</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="处理状态">
            <a-select 
              v-model:value="filters.status" 
              placeholder="选择处理状态" 
              style="width: 120px"
              allowClear
            >
              <a-select-option value="pending">待处理</a-select-option>
              <a-select-option value="processing">处理中</a-select-option>
              <a-select-option value="resolved">已解决</a-select-option>
              <a-select-option value="ignored">已忽略</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="任务名称">
            <a-input 
              v-model:value="filters.taskName" 
              placeholder="输入任务名称" 
              style="width: 200px"
              allowClear
            />
          </a-form-item>
          
          <a-form-item label="时间范围">
            <a-range-picker 
              v-model:value="filters.timeRange" 
              show-time
              format="YYYY-MM-DD HH:mm:ss"
            />
          </a-form-item>
          
          <a-form-item>
            <a-space>
              <a-button type="primary" @click="handleSearch">
                <template #icon><search-outlined /></template>
                搜索
              </a-button>
              <a-button @click="resetFilters">重置</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-card>

      <!-- 批量操作栏 -->
      <a-card v-if="showBatchActions" size="small" style="margin-bottom: 16px;">
        <a-space>
          <span>已选择 {{ selectedRowKeys.length }} 项</span>
          <a-button 
            type="primary" 
            :disabled="selectedRowKeys.length === 0"
            @click="batchMarkResolved"
          >
            批量标记已解决
          </a-button>
          <a-button 
            :disabled="selectedRowKeys.length === 0"
            @click="batchIgnore"
          >
            批量忽略
          </a-button>
          <a-button 
            danger
            :disabled="selectedRowKeys.length === 0"
            @click="batchDelete"
          >
            批量删除
          </a-button>
        </a-space>
      </a-card>

      <!-- 告警列表 -->
      <a-card>
        <a-table
          :columns="columns"
          :data-source="alertList"
          :loading="loading"
          :pagination="pagination"
          :row-selection="rowSelection"
          @change="handleTableChange"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'level'">
              <a-tag :color="getLevelColor(record.level)">
                {{ getLevelText(record.level) }}
              </a-tag>
            </template>
            
            <template v-if="column.dataIndex === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>
            
            <template v-if="column.dataIndex === 'triggerTime'">
              {{ formatTime(record.triggerTime) }}
            </template>
            
            <template v-if="column.dataIndex === 'content'">
              <a-tooltip :title="record.content">
                <span class="content-ellipsis">{{ record.content }}</span>
              </a-tooltip>
            </template>
            
            <template v-if="column.dataIndex === 'actions'">
              <a-space>
                <a-button 
                  type="link" 
                  size="small" 
                  @click="viewSnapshot(record)"
                >
                  查看快照
                </a-button>
                <a-dropdown>
                  <template #overlay>
                    <a-menu @click="({ key }) => handleAction(key, record)">
                      <a-menu-item key="resolve">标记已解决</a-menu-item>
                      <a-menu-item key="ignore">忽略</a-menu-item>
                      <a-menu-item key="assign">转派</a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="delete" danger>删除</a-menu-item>
                    </a-menu>
                  </template>
                  <a-button type="link" size="small">
                    更多 <down-outlined />
                  </a-button>
                </a-dropdown>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- 快照查看弹窗 -->
    <a-modal
      v-model:open="snapshotModalVisible"
      title="API执行快照"
      width="80%"
      :footer="null"
    >
      <AlertSnapshot 
        v-if="currentSnapshot" 
        :snapshot="currentSnapshot"
      />
    </a-modal>

    <!-- 转派弹窗 -->
    <a-modal
      v-model:open="assignModalVisible"
      title="转派告警"
      @ok="handleAssign"
    >
      <a-form layout="vertical">
        <a-form-item label="转派给">
          <a-select 
            v-model:value="assignForm.assignee" 
            placeholder="选择处理人员"
            style="width: 100%"
          >
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="dev-team">开发团队</a-select-option>
            <a-select-option value="ops-team">运维团队</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea 
            v-model:value="assignForm.note" 
            placeholder="请输入转派备注"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { 
  ReloadOutlined, 
  SettingOutlined, 
  SearchOutlined, 
  DownOutlined 
} from '@ant-design/icons-vue'
import AlertSnapshot from './components/AlertSnapshot.vue'
import { getAlerts, updateAlertStatus, deleteAlerts } from '@/api/alerts'

// 响应式数据
const loading = ref(false)
const showBatchActions = ref(false)
const snapshotModalVisible = ref(false)
const assignModalVisible = ref(false)
const selectedRowKeys = ref([])
const currentSnapshot = ref(null)
const currentAlert = ref(null)

// 筛选条件
const filters = reactive({
  level: undefined,
  status: undefined,
  taskName: '',
  timeRange: []
})

// 转派表单
const assignForm = reactive({
  assignee: '',
  note: ''
})

// 告警列表
const alertList = ref([])

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`
})

// 表格列配置
const columns = [
  {
    title: '任务名称',
    dataIndex: 'taskName',
    width: 150,
    ellipsis: true
  },
  {
    title: '触发时间',
    dataIndex: 'triggerTime',
    width: 160,
    sorter: true
  },
  {
    title: '告警级别',
    dataIndex: 'level',
    width: 100,
    filters: [
      { text: '严重', value: 'critical' },
      { text: '警告', value: 'warning' },
      { text: '信息', value: 'info' }
    ]
  },
  {
    title: '处理状态',
    dataIndex: 'status',
    width: 100,
    filters: [
      { text: '待处理', value: 'pending' },
      { text: '处理中', value: 'processing' },
      { text: '已解决', value: 'resolved' },
      { text: '已忽略', value: 'ignored' }
    ]
  },
  {
    title: '告警内容',
    dataIndex: 'content',
    ellipsis: true
  },
  {
    title: '操作',
    dataIndex: 'actions',
    width: 150,
    fixed: 'right'
  }
]

// 行选择配置
const rowSelection = {
  selectedRowKeys,
  onChange: (keys) => {
    selectedRowKeys.value = keys
  }
}

// 获取告警级别颜色
const getLevelColor = (level) => {
  const colors = {
    critical: 'red',
    warning: 'orange',
    info: 'blue'
  }
  return colors[level] || 'default'
}

// 获取告警级别文本
const getLevelText = (level) => {
  const texts = {
    critical: '严重',
    warning: '警告',
    info: '信息'
  }
  return texts[level] || level
}

// 获取状态颜色
const getStatusColor = (status) => {
  const colors = {
    pending: 'red',
    processing: 'orange',
    resolved: 'green',
    ignored: 'gray'
  }
  return colors[status] || 'default'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决',
    ignored: '已忽略'
  }
  return texts[status] || status
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 加载告警数据
const loadAlerts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      per_page: pagination.pageSize,
      alert_level: filters.level,
      status: filters.status,
      task_name: filters.taskName
    }
    
    // 处理时间范围参数
    if (filters.timeRange && filters.timeRange.length === 2) {
      params.start_time = filters.timeRange[0].toISOString()
      params.end_time = filters.timeRange[1].toISOString()
    }
    
    const response = await getAlerts(params, '/api-alerts')
    if (response.data.code === 0) {
      alertList.value = response.data.alerts || response.data.list || []
      pagination.total = response.data.total || 0
    } else {
      message.error(response.data.message || '获取告警数据失败')
    }
  } catch (error) {
    message.error('获取告警数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  loadAlerts()
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  loadAlerts()
}

// 重置筛选条件
const resetFilters = () => {
  Object.assign(filters, {
    level: undefined,
    status: undefined,
    taskName: '',
    timeRange: []
  })
  handleSearch()
}

// 表格变化处理
const handleTableChange = (pag, filters, sorter) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadAlerts()
}

// 查看快照
const viewSnapshot = (record) => {
  currentSnapshot.value = record.snapshot
  snapshotModalVisible.value = true
}

// 处理操作
const handleAction = async (action, record) => {
  currentAlert.value = record
  
  switch (action) {
    case 'resolve':
      await updateStatus(record.id, 'resolved')
      break
    case 'ignore':
      await updateStatus(record.id, 'ignored')
      break
    case 'assign':
      assignModalVisible.value = true
      break
    case 'delete':
      await deleteAlert(record.id)
      break
  }
}

// 更新状态
const updateStatus = async (id, status) => {
  try {
    const response = await updateAlertStatus(id, { status })
    if (response.data.code === 0) {
      message.success('操作成功')
      loadAlerts()
    } else {
      message.error(response.data.message || '操作失败')
    }
  } catch (error) {
    message.error('操作失败: ' + error.message)
  }
}

// 删除告警
const deleteAlert = async (id) => {
  try {
    const response = await deleteAlerts([id])
    if (response.data.code === 0) {
      message.success('删除成功')
      loadAlerts()
    } else {
      message.error(response.data.message || '删除失败')
    }
  } catch (error) {
    message.error('删除失败: ' + error.message)
  }
}

// 批量标记已解决
const batchMarkResolved = async () => {
  try {
    const response = await updateAlertStatus(selectedRowKeys.value, { status: 'resolved' })
    if (response.data.code === 0) {
      message.success('批量操作成功')
      selectedRowKeys.value = []
      loadAlerts()
    } else {
      message.error(response.data.message || '批量操作失败')
    }
  } catch (error) {
    message.error('批量操作失败: ' + error.message)
  }
}

// 批量忽略
const batchIgnore = async () => {
  try {
    const response = await updateAlertStatus(selectedRowKeys.value, { status: 'ignored' })
    if (response.data.code === 0) {
      message.success('批量操作成功')
      selectedRowKeys.value = []
      loadAlerts()
    } else {
      message.error(response.data.message || '批量操作失败')
    }
  } catch (error) {
    message.error('批量操作失败: ' + error.message)
  }
}

// 批量删除
const batchDelete = async () => {
  try {
    const response = await deleteAlerts(selectedRowKeys.value)
    if (response.data.code === 0) {
      message.success('批量删除成功')
      selectedRowKeys.value = []
      loadAlerts()
    } else {
      message.error(response.data.message || '批量删除失败')
    }
  } catch (error) {
    message.error('批量删除失败: ' + error.message)
  }
}

// 处理转派
const handleAssign = async () => {
  try {
    const response = await updateAlertStatus(currentAlert.value.id, {
      status: 'processing',
      assignee: assignForm.assignee,
      note: assignForm.note
    })
    
    if (response.data.code === 0) {
      message.success('转派成功')
      assignModalVisible.value = false
      Object.assign(assignForm, { assignee: '', note: '' })
      loadAlerts()
    } else {
      message.error(response.data.message || '转派失败')
    }
  } catch (error) {
    message.error('转派失败: ' + error.message)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.api-alert-management {
  padding: 16px;
}

.content-container {
  max-width: 1400px;
}

.content-ellipsis {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>