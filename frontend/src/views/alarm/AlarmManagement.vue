<template>
  <div class="alarm-management">
    <a-page-header title="拨测告警管理">
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
              v-model:value="filterForm.level" 
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
              v-model:value="filterForm.status" 
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
              v-model:value="filterForm.taskName" 
              placeholder="输入任务名称" 
              style="width: 200px"
              allowClear
            />
          </a-form-item>
          
          <a-form-item label="任务类型">
            <a-select 
              v-model:value="filterForm.taskType" 
              placeholder="选择任务类型" 
              style="width: 120px"
              allowClear
            >
              <a-select-option value="http">HTTP</a-select-option>
              <a-select-option value="ping">Ping</a-select-option>
              <a-select-option value="tcp">TCP</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="时间范围">
            <a-range-picker 
              v-model:value="filterForm.timeRange" 
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
          :data-source="alarmList"
          :loading="loading"
          :pagination="pagination"
          :row-selection="rowSelection"
          @change="handleTableChange"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'task_type'">
              <a-tag :color="getTaskTypeColor(record.task_type)">
                {{ getTaskTypeText(record.task_type) }}
              </a-tag>
            </template>
            
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
            
            <template v-if="column.dataIndex === 'created_at'">
              {{ formatTime(record.created_at) }}
            </template>
            
            <template v-if="column.dataIndex === 'message'">
              <a-tooltip :title="record.message">
                <span class="content-ellipsis">{{ record.message }}</span>
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
      title="拨测快照详情"
      width="1000px"
      :footer="null"
    >
      <div v-if="currentSnapshot">
        <!-- 基本信息 -->
        <a-card size="small" title="基本信息" class="mb-16">
          <a-descriptions :column="3" size="small">
            <a-descriptions-item label="任务名称">
              {{ currentSnapshot.task_name }}
            </a-descriptions-item>
            <a-descriptions-item label="任务类型">
              <a-tag :color="getTaskTypeColor(currentSnapshot.task_type)">
                {{ getTaskTypeText(currentSnapshot.task_type) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="告警级别">
              <a-tag :color="getLevelColor(currentSnapshot.level)">
                {{ getLevelText(currentSnapshot.level) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="拨测点">
              {{ currentSnapshot.probe_point || 'N/A' }}
            </a-descriptions-item>
            <a-descriptions-item label="触发时间">
              {{ formatTime(currentSnapshot.created_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="告警状态">
              <a-tag :color="getStatusColor(currentSnapshot.status)">
                {{ getStatusText(currentSnapshot.status) }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
        
        <!-- 快照详情 -->
        <SnapshotViewer 
          :task-type="currentSnapshot.task_type" 
          :snapshot-data="getSnapshotData(currentSnapshot)"
        />
      </div>
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
import dayjs from 'dayjs'
import { getAlerts, updateAlertStatus, deleteAlerts } from '@/api/alerts'
import SnapshotViewer from '@/components/SnapshotViewer.vue'

// 响应式数据
const loading = ref(false)
const showBatchActions = ref(false)
const snapshotModalVisible = ref(false)
const assignModalVisible = ref(false)
const selectedRowKeys = ref([])
const currentSnapshot = ref(null)
const currentAlert = ref(null)
const alarmList = ref([])

// 筛选表单
const filterForm = reactive({
  level: undefined,
  status: undefined,
  taskName: '',
  taskType: undefined,
  timeRange: []
})

// 转派表单
const assignForm = reactive({
  assignee: '',
  note: ''
})

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
    dataIndex: 'task_name',
    width: 150,
    ellipsis: true
  },
  {
    title: '任务类型',
    dataIndex: 'task_type',
    width: 100,
    filters: [
      { text: 'HTTP', value: 'http' },
      { text: 'Ping', value: 'ping' },
      { text: 'TCP', value: 'tcp' }
    ]
  },
  {
    title: '触发时间',
    dataIndex: 'created_at',
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
    dataIndex: 'message',
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

// 加载告警数据
const loadAlerts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      per_page: pagination.pageSize,
      alert_level: filterForm.level,
      status: filterForm.status,
      task_name: filterForm.taskName,
      task_type: filterForm.taskType
    }
    
    // 处理时间范围参数
    if (filterForm.timeRange && filterForm.timeRange.length === 2) {
      params.start_time = filterForm.timeRange[0].toISOString()
      params.end_time = filterForm.timeRange[1].toISOString()
    }
    
    const response = await getAlerts(params, '/alerts')
    if (response.data.code === 0) {
      // 根据实际API响应结构，告警数据在response.data.alerts或response.data.list中
      const alerts = response.data.alerts || response.data.list || []
      alarmList.value = alerts.map(alert => ({
        id: alert.id,
        task_name: alert.task_name || alert.taskName,
        task_type: alert.task_type || 'unknown',
        alarm_type: alert.alert_type,
        level: alert.alert_level || alert.level,
        status: alert.status,
        message: alert.content || alert.title || alert.message,
        created_at: alert.created_at,
        resolved_at: alert.resolved_at,
        snapshot: alert.snapshot_data || alert.snapshot
      }))
      pagination.total = response.data.pagination?.total || 0
    } else {
      message.error(response.message || '获取告警数据失败')
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
  Object.assign(filterForm, {
    level: undefined,
    status: undefined,
    taskName: '',
    taskType: undefined,
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
  currentSnapshot.value = record
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
      message.error(response.message || '操作失败')
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
      message.error(response.message || '删除失败')
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
      message.error(response.message || '批量操作失败')
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
      message.error(response.message || '批量操作失败')
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
      message.error(response.message || '批量删除失败')
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
      message.error(response.message || '转派失败')
    }
  } catch (error) {
    message.error('转派失败: ' + error.message)
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

// 获取任务类型颜色
const getTaskTypeColor = (type) => {
  const colors = {
    http: 'blue',
    ping: 'green',
    tcp: 'purple',
    unknown: 'gray'
  }
  return colors[type] || 'default'
}

// 获取任务类型文本
const getTaskTypeText = (type) => {
  const texts = {
    http: 'HTTP',
    ping: 'Ping',
    tcp: 'TCP',
    unknown: '未知'
  }
  return texts[type] || type
}

// 获取告警类型文本
const getAlarmTypeText = (type) => {
  const texts = {
    status: '状态告警',
    response_code: '返回代码告警',
    response_time: '响应时间告警',
    dns_ip: 'DNS IP告警',
    packet_loss: '丢包率告警',
    execution_time: '执行时间告警'
  }
  return texts[type] || type
}

// 获取快照数据
const getSnapshotData = (record) => {
  // 如果有真实快照数据且不为空，处理并返回
  if (record.snapshot && typeof record.snapshot === 'object' && Object.keys(record.snapshot).length > 0) {
    // 检查是否有result_data.details结构
    if (record.snapshot.result_data && record.snapshot.result_data.details) {
      const details = record.snapshot.result_data.details
      // 根据任务类型格式化数据
      if (record.task_type === 'tcp') {
        return {
          target: `${details.host}:${details.port}`,
          host: details.host,
          port: details.port,
          connected: details.connected,
          execution_time: details.execution_time,
          return_code: details.return_code,
          message: details.message
        }
      } else if (record.task_type === 'ping') {
        return {
          host: details.host || details.target,
          ip: details.ip,
          target: details.target || details.host,
          packet_size: details.packet_size,
          count: details.count,
          success_count: details.success_count,
          packet_loss: details.packet_loss,
          avg_time: details.avg_time,
          max_time: details.max_time,
          min_time: details.min_time,
          stddev: details.stddev,
          error: details.error || details.message,
          output: details.output
        }
      }
    }
    return record.snapshot
  }
  
  // 否则根据任务类型生成模拟快照数据
  const taskType = record.task_type || 'http'
  
  switch (taskType) {
    case 'http':
      return {
        url: 'https://example.com/api/test',
        method: 'GET',
        response_code: 500,
        response_time: 5000,
        dns_time: 50,
        connect_time: 200,
        ssl_time: 300,
        ttfb: 4500,
        error: '服务器内部错误：连接超时',
        response_headers: {
          'Content-Type': 'application/json',
          'Server': 'nginx/1.18.0',
          'Connection': 'close'
        },
        response_body: '{"error": "Internal Server Error", "code": 500}'
      }
    
    case 'ping':
      return {
        host: 'example.com',
        ip: '93.184.216.34',
        packet_size: 64,
        count: 4,
        success_count: 1,
        packet_loss: 75,
        avg_time: 250,
        max_time: 300,
        min_time: 200,
        stddev: 50,
        error: '网络不可达，丢包率过高',
        output: 'PING example.com (93.184.216.34): 64 data bytes\nRequest timeout for icmp_seq 0\nRequest timeout for icmp_seq 1\nRequest timeout for icmp_seq 2\n64 bytes from 93.184.216.34: icmp_seq=3 ttl=56 time=200.123 ms\n\n--- example.com ping statistics ---\n4 packets transmitted, 1 received, 75% packet loss\nround-trip min/avg/max/stddev = 200.123/200.123/200.123/0.000 ms'
      }
    
    case 'tcp':
      return {
        target: 'example.com:8080',
        host: 'example.com',
        port: 8080,
        connected: false,
        execution_time: 0.005,
        return_code: 61,
        message: '连接失败，返回码: 61 (Connection refused)'
      }
    
    case 'api':
      return {
        api_name: '用户登录API测试',
        total_steps: 3,
        success_steps: 1,
        total_time: 2500,
        error: '第2步执行失败：用户认证失败',
        steps: [
          {
            name: '获取登录页面',
            success: true,
            response_time: 200,
            status_code: 200
          },
          {
            name: '提交登录信息',
            success: false,
            response_time: 1500,
            status_code: 401,
            error: '用户名或密码错误'
          },
          {
            name: '获取用户信息',
            success: false,
            response_time: 0,
            error: '由于前一步失败，此步骤未执行'
          }
        ]
      }
    
    default:
      return {
        error: '未知任务类型',
        raw_data: record
      }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.alarm-management {
  padding: 24px;
  background: #f0f2f5;
  min-height: 100vh;
}

.page-header {
  background: #fff;
  margin-bottom: 16px;
  border-radius: 6px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-section {
  background: #fff;
  padding: 24px;
  margin-bottom: 16px;
  border-radius: 6px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
}

.filter-form {
  display: flex;
  gap: 16px;
  align-items: end;
  flex-wrap: wrap;
}

.filter-form .ant-form-item {
  margin-bottom: 0;
}

.batch-actions {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  padding: 12px 16px;
  margin-bottom: 16px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.batch-info {
  color: #1890ff;
  font-weight: 500;
}

.batch-buttons {
  display: flex;
  gap: 8px;
}

.table-section {
  background: #fff;
  padding: 24px;
  border-radius: 6px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
}

.table-section .ant-table {
  margin-top: 16px;
}

.level-tag {
  font-weight: 500;
}

.status-tag {
  font-weight: 500;
}

.message-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-dropdown {
  cursor: pointer;
}

.detail-modal .ant-descriptions-item-label {
  font-weight: 600;
  color: #262626;
}

.detail-modal .ant-descriptions-item-content {
  color: #595959;
}

.assign-modal .ant-form-item-label {
  font-weight: 600;
}

.mb-16 {
  margin-bottom: 16px;
}

.content-ellipsis {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.snapshot-modal {
  .ant-modal-body {
    max-height: 60vh;
    overflow-y: auto;
  }
  
  pre {
    background: #f6f8fa;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 16px;
    font-size: 12px;
    line-height: 1.45;
    overflow-x: auto;
  }
}

:deep(.ant-modal-header) {
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-modal-title) {
  font-weight: 600;
  color: #262626;
}

:deep(.ant-card-head) {
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-card-head-title) {
  font-weight: 600;
  color: #262626;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  background-color: #fafafa;
  color: #595959;
}

:deep(.ant-descriptions-item-content) {
  color: #262626;
}

:deep(.ant-table-thead > tr > th) {
  background: #fafafa;
  font-weight: 600;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background: #f5f5f5;
}
</style>