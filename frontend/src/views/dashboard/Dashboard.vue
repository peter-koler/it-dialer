<template>
  <div class="dashboard-container">
    <!-- 超级管理员视图 -->
    <template v-if="isSuperAdmin">
      <a-card title="全局租户统计概览" class="quota-overview-card">
        <template #extra>
          <a-button @click="refreshQuota" :loading="loading" size="small">
            <template #icon>
              <ReloadOutlined />
            </template>
            刷新
          </a-button>
        </template>
        
        <a-alert
          v-if="apiError"
          :message="apiError"
          type="error"
          show-icon
          closable
          @close="apiError = null"
          style="margin-bottom: 16px"
        />
        
        <!-- 全局汇总数据 -->
        <a-row :gutter="[16, 16]" v-if="quotaData && quotaData.stats">
          <a-col :xs="24" :sm="12" :lg="6">
            <a-card size="small" class="summary-card">
              <a-statistic
                title="租户总数"
                :value="quotaData.stats.total_tenants || 0"
                :value-style="{ color: '#1890ff' }"
              >
                <template #prefix>
                  <TeamOutlined />
                </template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <a-card size="small" class="summary-card">
              <a-statistic
                title="活跃租户"
                :value="quotaData.stats.active_tenants || 0"
                :value-style="{ color: '#52c41a' }"
              >
                <template #prefix>
                  <ApiOutlined />
                </template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <a-card size="small" class="summary-card">
              <a-statistic
                title="用户总数"
                :value="quotaData.stats.total_users || 0"
                :value-style="{ color: '#722ed1' }"
              >
                <template #prefix>
                  <TeamOutlined />
                </template>
              </a-statistic>
            </a-card>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <a-card size="small" class="summary-card">
              <a-statistic
                title="暂停租户"
                :value="quotaData.stats.suspended_tenants || 0"
                :value-style="{ color: '#fa8c16' }"
              >
                <template #prefix>
                  <AlertOutlined />
                </template>
              </a-statistic>
            </a-card>
          </a-col>
        </a-row>
        
        <a-empty v-else-if="!loading" description="暂无数据" />
        
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
        </div>
      </a-card>
    </template>
    
    <!-- 普通租户视图 -->
    <template v-else>
      <a-card :title="`资源限额概览 - ${quotaData?.tenant_info?.tenant_name || '当前租户'}`" class="quota-overview-card">
        <template #extra>
          <a-button @click="refreshQuota" :loading="loading" size="small">
            <template #icon>
              <ReloadOutlined />
            </template>
            刷新
          </a-button>
        </template>
        
        <a-alert
          v-if="apiError"
          :message="apiError"
          type="error"
          show-icon
          closable
          @close="apiError = null"
          style="margin-bottom: 16px"
        />
        
        <a-row :gutter="[16, 16]" v-if="quotaData && quotaData.usage_stats">
          <a-col :xs="24" :sm="12" :lg="6" v-for="(quota, key) in quotaData.usage_stats" :key="key">
            <a-card size="small" :class="getCardClass(quota)">
              <a-statistic
                :title="getResourceTitle(key)"
                :value="quota.current"
                :suffix="`/ ${quota.limit}`"
                :value-style="getValueStyle(quota)"
              >
                <template #prefix>
                  <component :is="getResourceIcon(key)" />
                </template>
              </a-statistic>
              
              <div class="quota-progress" style="margin-top: 8px;">
                <a-progress
                  :percent="quota.usage_rate || 0"
                  :status="getProgressStatus(quota)"
                  :stroke-color="getProgressColor(quota)"
                  size="small"
                />
              </div>
              
              <div class="quota-status" style="margin-top: 4px; font-size: 12px; color: #666;">
                使用率: {{ quota.usage_rate || 0 }}%
              </div>
            </a-card>
          </a-col>
        </a-row>
        
        <a-empty v-else-if="!loading" description="暂无数据" />
        
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
        </div>
      </a-card>
    </template>
    

    
    <!-- 任务配额使用详情 - 仅普通租户显示 -->
    <a-card title="任务配额使用详情" style="margin-top: 16px;" v-if="quotaData && !isSuperAdmin && quotaData.usage_stats">
      <template #extra>
        <a-button @click="refreshTaskList" :loading="taskListLoading" size="small">
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新任务列表
        </a-button>
      </template>
      
      <div class="task-quota-details">
        <!-- 配额概览 -->
        <div class="quota-summary" style="margin-bottom: 16px;">
          <a-alert
            :message="`当前已使用 ${quotaData.usage_stats.tasks?.current || 0} / ${quotaData.usage_stats.tasks?.limit || 0} 个任务配额`"
            :type="getQuotaAlertType(quotaData.usage_stats.tasks)"
            show-icon
            style="margin-bottom: 16px;"
          />
        </div>
        
        <!-- 任务列表 -->
        <a-table
          :columns="taskColumns"
          :data-source="taskList"
          :loading="taskListLoading"
          :pagination="{
            current: taskPagination.current,
            pageSize: taskPagination.pageSize,
            total: taskPagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }"
          @change="handleTaskTableChange"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'type'">
              <a-tag :color="getTaskTypeColor(record.type)">
                {{ getTaskTypeText(record.type) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="getTaskStatusColor(record.enabled)">
                {{ record.enabled ? '启用' : '禁用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'target'">
              <a-tooltip :title="record.target">
                <span class="target-text">{{ record.target }}</span>
              </a-tooltip>
            </template>
            <template v-else-if="column.key === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            <template v-else-if="column.key === 'interval'">
              {{ record.interval }}秒
            </template>
          </template>
        </a-table>
      </div>
    </a-card>
    
    <!-- 超级管理员详细统计 -->
    <a-card title="租户详细统计" style="margin-top: 16px;" v-if="quotaData && isSuperAdmin && quotaData.stats">
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :lg="8">
          <a-card size="small" title="订阅级别分布">
            <div v-if="quotaData.stats.subscription_distribution">
              <div v-for="(count, level) in quotaData.stats.subscription_distribution" :key="level" class="subscription-item">
                <span class="subscription-label">{{ level }}:</span>
                <span class="subscription-count">{{ count }} 个租户</span>
              </div>
            </div>
            <a-empty v-else size="small" description="暂无数据" />
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="8">
          <a-card size="small" title="租户状态分布">
            <div class="status-distribution">
              <div class="status-item">
                <span class="status-label active">活跃:</span>
                <span class="status-count">{{ quotaData.stats.tenant_stats?.active || 0 }}</span>
              </div>
              <div class="status-item">
                <span class="status-label inactive">非活跃:</span>
                <span class="status-count">{{ quotaData.stats.tenant_stats?.inactive || 0 }}</span>
              </div>
              <div class="status-item">
                <span class="status-label suspended">暂停:</span>
                <span class="status-count">{{ quotaData.stats.tenant_stats?.suspended || 0 }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="12" :lg="8">
          <a-card size="small" title="系统概览">
            <div class="system-overview">
              <div class="overview-item">
                <span class="overview-label">总租户数:</span>
                <span class="overview-value">{{ quotaData.stats.tenant_stats?.total || 0 }}</span>
              </div>
              <div class="overview-item">
                <span class="overview-label">总用户数:</span>
                <span class="overview-value">{{ quotaData.stats.total_users || 0 }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-card>
    
    <!-- 超级管理员租户配额分布表格 -->
    <a-card title="租户配额分布" style="margin-top: 16px;" v-if="isSuperAdmin && tenantList.length > 0">
      <a-table
        :columns="tenantColumns"
        :data-source="tenantList"
        :loading="tenantListLoading"
        :pagination="false"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'subscription_level'">
            <a-tag :color="getSubscriptionColor(record.subscription_level)">
              {{ getSubscriptionText(record.subscription_level) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getTenantStatusColor(record.status)">
              {{ getTenantStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'quotas'">
            <div class="quota-summary">
              <div class="quota-item" v-if="record.usage?.tasks">
                <span>任务: {{ record.usage.tasks.current || 0 }}/{{ record.usage.tasks.limit || record.max_tasks }}</span>
                <a-progress 
                  :percent="record.usage.tasks.usage_rate || 0" 
                  :status="getProgressStatus(record.usage.tasks)"
                  :stroke-color="getProgressColor(record.usage.tasks)"
                  size="small" 
                  style="margin-left: 8px; width: 60px;"
                />
              </div>
              <div class="quota-item" v-if="record.usage?.nodes">
                <span>节点: {{ record.usage.nodes.current || 0 }}/{{ record.usage.nodes.limit || record.max_nodes }}</span>
                <a-progress 
                  :percent="record.usage.nodes.usage_rate || 0" 
                  :status="getProgressStatus(record.usage.nodes)"
                  :stroke-color="getProgressColor(record.usage.nodes)"
                  size="small" 
                  style="margin-left: 8px; width: 60px;"
                />
              </div>
              <div class="quota-item" v-if="record.usage?.alerts">
                <span>告警: {{ record.usage.alerts.current || 0 }}/{{ record.usage.alerts.limit || record.max_alerts }}</span>
                <a-progress 
                  :percent="record.usage.alerts.usage_rate || 0" 
                  :status="getProgressStatus(record.usage.alerts)"
                  :stroke-color="getProgressColor(record.usage.alerts)"
                  size="small" 
                  style="margin-left: 8px; width: 60px;"
                />
              </div>
              <div class="quota-item" v-if="record.usage?.variables">
                <span>变量: {{ record.usage.variables.current || 0 }}/{{ record.usage.variables.limit || record.max_variables }}</span>
                <a-progress 
                  :percent="record.usage.variables.usage_rate || 0" 
                  :status="getProgressStatus(record.usage.variables)"
                  :stroke-color="getProgressColor(record.usage.variables)"
                  size="small" 
                  style="margin-left: 8px; width: 60px;"
                />
              </div>
            </div>
          </template>
        </template>
      </a-table>
    </a-card>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  PlusOutlined,
  SettingOutlined,
  BellOutlined,
  TeamOutlined,
  ApiOutlined,
  CloudServerOutlined,
  AlertOutlined
} from '@ant-design/icons-vue'
import request from '@/utils/request'
import { useUserStore } from '@/stores/user'

// 用户store
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const quotaData = ref(null)
const apiError = ref(null)

// 任务列表相关数据
const taskList = ref([])
const taskListLoading = ref(false)
const taskPagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

// 租户列表相关数据（超级管理员）
const tenantList = ref([])
const tenantListLoading = ref(false)

// 计算属性
const isSuperAdmin = computed(() => userStore.isSuperAdmin)
const currentTenantId = computed(() => userStore.tenantId)

// 租户列表表格列定义（超级管理员）
const tenantColumns = [
  {
    title: '租户名称',
    dataIndex: 'name',
    key: 'name',
    width: 150
  },
  {
    title: '订阅级别',
    dataIndex: 'subscription_level',
    key: 'subscription_level',
    width: 100
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 80
  },
  {
    title: '配额使用情况',
    key: 'quotas',
    width: 400
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 150
  }
]

// 任务列表表格列定义
const taskColumns = [
  {
    title: '任务名称',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    ellipsis: true
  },
  {
    title: '任务类型',
    dataIndex: 'type',
    key: 'type',
    width: 100
  },
  {
    title: '目标地址',
    dataIndex: 'target',
    key: 'target',
    width: 250,
    ellipsis: true
  },
  {
    title: '检测间隔',
    dataIndex: 'interval',
    key: 'interval',
    width: 100
  },
  {
    title: '状态',
    dataIndex: 'enabled',
    key: 'status',
    width: 80
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 150
  }
]

// 获取资源限额数据
const fetchQuotaData = async () => {
  loading.value = true
  apiError.value = null
  
  try {
    // 等待用户信息完全加载
    if (!userStore.user && userStore.token) {
      console.log('等待用户信息加载...')
      // 如果有token但没有用户信息，等待一段时间再重试
      await new Promise(resolve => setTimeout(resolve, 500))
      if (!userStore.user) {
        throw new Error('用户信息加载失败，请刷新页面重试')
      }
    }
    
    // 检查用户角色，优先判断是否为超级管理员
    if (isSuperAdmin.value || userStore.user?.tenant_role === 'super_admin') {
      // 超级管理员：获取所有租户的统计信息
      const response = await request.get('/tenants/stats')
      // v2 API返回格式：{code: 0, data: {...}, message: 'ok'}
      const statsData = response.data?.data || response.data || response
      
      // 映射后端数据结构到前端期望的格式
      quotaData.value = {
        type: 'super_admin',
        stats: {
          total_tenants: statsData.tenant_stats?.total || 0,
          active_tenants: statsData.tenant_stats?.active || 0,
          inactive_tenants: statsData.tenant_stats?.inactive || 0,
          suspended_tenants: statsData.tenant_stats?.suspended || 0,
          total_users: statsData.total_users || 0,
          subscription_distribution: statsData.subscription_distribution || {},
          tenant_stats: statsData.tenant_stats || {}
        },
        tenants_summary: statsData
      }
    } else {
      // 普通租户：获取当前租户的使用统计
      let tenantId = currentTenantId.value
      
      // 检查租户ID的有效性
      if (!tenantId || tenantId === 'all_tenants' || tenantId === 'undefined') {
        // 尝试从用户信息中获取租户ID
        tenantId = userStore.user?.tenant_id
        if (!tenantId) {
          // 如果用户有租户列表，使用第一个租户
          if (userStore.availableTenants && userStore.availableTenants.length > 0) {
            tenantId = userStore.availableTenants[0].tenant_id
          } else {
            throw new Error('未找到有效的租户信息，请联系管理员')
          }
        }
      }
      
      // 使用确定的租户ID获取数据
      const response = await request.get(`/tenants/${tenantId}/usage`)
      // v2 API返回格式：{code: 0, data: {...}, message: 'ok'}
      const responseData = response.data?.data || response.data || response
      quotaData.value = {
        type: 'tenant',
        usage_stats: responseData.usage_stats || responseData,
        tenant_info: {
          tenant_id: tenantId,
          tenant_name: responseData.tenant_name || userStore.user?.tenant_name || '当前租户'
        }
      }
    }
  } catch (error) {
    console.error('获取资源限额数据失败:', error)
    apiError.value = error.response?.data?.message || error.message || '获取资源限额数据失败'
    message.error(apiError.value)
  } finally {
    loading.value = false
  }
}

// 获取租户列表数据（超级管理员）
const fetchTenantList = async () => {
  if (!isSuperAdmin.value) return
  
  tenantListLoading.value = true
  try {
    // 使用v1版本的API获取包含配额使用信息的租户列表
    const response = await request.get('/v1/tenants')
    const responseData = response.data?.data || response.data || response
    let tenants = responseData.list || responseData.tenants || responseData || []
    
    // 为每个租户的配额信息添加usage_rate计算
    tenants = tenants.map(tenant => {
      if (tenant.usage) {
        const usage = { ...tenant.usage }
        // 计算每个配额类型的使用率
        Object.keys(usage).forEach(key => {
          if (usage[key] && usage[key].current !== undefined && usage[key].limit !== undefined) {
            usage[key].usage_rate = usage[key].limit > 0 ? (usage[key].current / usage[key].limit * 100) : 0
          }
        })
        return { ...tenant, usage }
      }
      return tenant
    })
    
    tenantList.value = tenants
  } catch (error) {
    console.error('获取租户列表失败:', error)
    message.error('获取租户列表失败')
  } finally {
    tenantListLoading.value = false
  }
}

// 获取任务列表数据
const fetchTaskList = async () => {
  if (isSuperAdmin.value) return // 超级管理员不显示任务列表
  
  taskListLoading.value = true
  try {
    const response = await request.get('/tasks', {
      params: {
        page: taskPagination.value.current,
        per_page: taskPagination.value.pageSize
      }
    })
    
    const responseData = response.data?.data || response.data || response
    taskList.value = responseData.list || responseData.tasks || []
    taskPagination.value.total = responseData.total || 0
  } catch (error) {
    console.error('获取任务列表失败:', error)
    message.error('获取任务列表失败')
  } finally {
    taskListLoading.value = false
  }
}

// 刷新数据
const refreshQuota = () => {
  fetchQuotaData()
  fetchTaskList()
}

// 刷新任务列表
const refreshTaskList = () => {
  fetchTaskList()
}

// 获取资源标题
const getResourceTitle = (key) => {
  const titles = {
    tasks: '拨测任务',
    nodes: '拨测节点',
    variables: '系统变量',
    alerts: '告警规则'
  }
  return titles[key] || key
}

// 获取资源图标
const getResourceIcon = (key) => {
  const icons = {
    tasks: ApiOutlined,
    nodes: CloudServerOutlined,
    variables: SettingOutlined,
    alerts: AlertOutlined
  }
  return icons[key] || ApiOutlined
}

// 获取卡片样式类
const getCardClass = (quota) => {
  const usageRate = quota.usage_rate || 0
  if (usageRate >= 90) return 'quota-card-danger'
  if (usageRate >= 75) return 'quota-card-warning'
  return 'quota-card-normal'
}

// 获取数值样式
const getValueStyle = (quota) => {
  const usageRate = quota.usage_rate || 0
  if (usageRate >= 90) return { color: '#ff4d4f' }
  if (usageRate >= 75) return { color: '#faad14' }
  return { color: '#52c41a' }
}

// 获取进度条状态
const getProgressStatus = (quota) => {
  const usageRate = quota.usage_rate || 0
  if (usageRate >= 90) return 'exception'
  if (usageRate >= 75) return 'active'
  return 'success'
}

// 获取进度条颜色
const getProgressColor = (quota) => {
  const usageRate = quota.usage_rate || 0
  if (usageRate >= 90) return '#ff4d4f'
  if (usageRate >= 75) return '#faad14'
  return '#52c41a'
}

// 获取配额警告类型
const getQuotaAlertType = (quota) => {
  if (!quota) return 'info'
  const usageRate = quota.usage_rate || 0
  if (usageRate >= 90) return 'error'
  if (usageRate >= 75) return 'warning'
  return 'success'
}

// 获取任务状态颜色
const getTaskStatusColor = (enabled) => {
  return enabled ? 'green' : 'red'
}

// 获取任务类型颜色
const getTaskTypeColor = (type) => {
  const colors = {
    'ping': 'blue',
    'tcp': 'green',
    'http': 'orange',
    'api': 'purple'
  }
  return colors[type] || 'default'
}

// 获取任务类型文本
const getTaskTypeText = (type) => {
  const texts = {
    'ping': 'PING',
    'tcp': 'TCP',
    'http': 'HTTP',
    'api': 'API'
  }
  return texts[type] || type.toUpperCase()
}

// 租户相关辅助方法
const getSubscriptionColor = (level) => {
  const colorMap = {
    'free': 'blue',
    'enterprise': 'gold',
    'premium': 'purple'
  }
  return colorMap[level] || 'default'
}

const getSubscriptionText = (level) => {
  const textMap = {
    'free': '免费版',
    'enterprise': '企业版',
    'premium': '高级版'
  }
  return textMap[level] || level
}

const getTenantStatusColor = (status) => {
  const colorMap = {
    'active': 'green',
    'inactive': 'red',
    'suspended': 'orange'
  }
  return colorMap[status] || 'default'
}

const getTenantStatusText = (status) => {
  const statusMap = {
    'active': '活跃',
    'inactive': '非活跃',
    'suspended': '暂停'
  }
  return statusMap[status] || status
}

// 配额相关辅助方法
const getResourceLabel = (key) => {
  const labelMap = {
    'tasks': '任务',
    'nodes': '节点',
    'alerts': '告警',
    'variables': '变量'
  }
  return labelMap[key] || key
}

const getQuotaStatusColor = (quota) => {
  const usageRate = quota.usage_rate || 0
  if (usageRate >= 90) return 'red'
  if (usageRate >= 70) return 'orange'
  if (usageRate >= 50) return 'yellow'
  return 'green'
}

const getQuotaStatusText = (quota) => {
  const usageRate = quota.usage_rate || 0
  if (usageRate >= 90) return '告警'
  if (usageRate >= 70) return '警告'
  if (usageRate >= 50) return '注意'
  return '正常'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 处理表格变化
const handleTaskTableChange = (pagination) => {
  taskPagination.value.current = pagination.current
  taskPagination.value.pageSize = pagination.pageSize
  fetchTaskList()
}

// 页面加载时获取数据
onMounted(async () => {
  // 确保userStore已初始化
  userStore.initializeUser()
  
  // 等待一个tick确保状态更新完成
  await new Promise(resolve => setTimeout(resolve, 100))
  
  fetchQuotaData()
  fetchTaskList()
  fetchTenantList()
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: calc(100vh - 64px);
}

.quota-overview-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.quota-card-normal {
  border-left: 4px solid #52c41a;
}

.quota-card-warning {
  border-left: 4px solid #faad14;
}

.quota-card-danger {
  border-left: 4px solid #ff4d4f;
}

.summary-card {
  border-left: 4px solid #1890ff;
  transition: all 0.3s ease;
}

.summary-card:hover {
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
  transform: translateY(-2px);
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.trend-chart {
  padding: 16px 0;
}

.trend-item {
  text-align: center;
  margin-bottom: 24px;
}

.trend-item h4 {
  margin-bottom: 16px;
  color: #333;
  font-weight: 500;
}

.quota-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quota-item {
  font-size: 12px;
  padding: 2px 6px;
  background: #f5f5f5;
  border-radius: 4px;
  display: inline-block;
  margin-right: 8px;
  margin-bottom: 4px;
}

/* 配额使用详细分析样式 */
.usage-chart {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.usage-item {
  text-align: center;
  flex: 1;
  min-width: 80px;
}

.usage-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.usage-text {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}

.quota-status-overview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  padding: 8px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: #fafafa;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.status-icon {
  font-size: 14px;
  color: #1890ff;
}

.status-name {
  font-weight: 500;
  flex: 1;
}

.status-details {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.subscription-info {
  text-align: center;
}

.subscription-level {
  margin-bottom: 16px;
}

.tenant-info {
  text-align: left;
}

.tenant-info p {
  margin: 4px 0;
  font-size: 13px;
}

.target-text {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

/* 超级管理员详细统计样式 */
.subscription-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.subscription-item:last-child {
  border-bottom: none;
}

.subscription-label {
  font-weight: 500;
  color: #666;
}

.subscription-count {
  color: #1890ff;
  font-weight: 600;
}

.status-distribution {
  padding: 8px 0;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-weight: 500;
}

.status-label.active {
  color: #52c41a;
}

.status-label.inactive {
  color: #d9d9d9;
}

.status-label.suspended {
  color: #fa8c16;
}

.status-count {
  font-weight: 600;
  font-size: 16px;
}

.system-overview {
  padding: 8px 0;
}

.overview-item {
  display: flex;
  justify-content: space-between;
}

/* 配额显示样式 */
.quota-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quota-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  white-space: nowrap;
}

.quota-item span {
  min-width: 80px;
  margin-right: 8px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.overview-item:last-child {
  border-bottom: none;
}

.overview-label {
  font-weight: 500;
  color: #666;
}

.overview-value {
  color: #722ed1;
  font-weight: 600;
  font-size: 16px;
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .trend-chart .ant-col {
    margin-bottom: 16px;
  }
  
  .subscription-item,
  .status-item,
  .overview-item {
    padding: 6px 0;
  }
}
</style>