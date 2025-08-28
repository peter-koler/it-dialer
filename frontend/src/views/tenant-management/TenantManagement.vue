<template>
  <div class="tenant-management">
    <div class="page-header">
      <h2>租户管理</h2>
      <a-button type="primary" @click="showCreateModal">
        <PlusOutlined />
        创建租户
      </a-button>
    </div>

    <!-- 租户列表 -->
    <a-table 
      :columns="columns" 
      :data-source="tenants" 
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 'active' ? 'green' : 'red'">
            {{ record.status === 'active' ? '活跃' : '停用' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'subscription_level'">
          <a-tag :color="getSubscriptionColor(record.subscription_level)">
            {{ getSubscriptionText(record.subscription_level) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'created_at'">
          {{ formatDate(record.created_at) }}
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="showEditModal(record)">
              编辑
            </a-button>
            <a-button type="link" size="small" @click="showUsageModal(record)">
              使用统计
            </a-button>
            <a-popconfirm
              :title="`确定要${record.status === 'active' ? '停用' : '启用'}该租户吗？`"
              @confirm="toggleTenantStatus(record)"
            >
              <a-button type="link" size="small" :danger="record.status === 'active'">
                {{ record.status === 'active' ? '停用' : '启用' }}
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 创建/编辑租户模态框 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑租户' : '创建租户'"
      @ok="handleSubmit"
      @cancel="handleCancel"
      :confirm-loading="submitLoading"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="租户名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入租户名称" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formData.description" placeholder="请输入租户描述" :rows="3" />
        </a-form-item>
        <a-form-item label="订阅级别" name="subscription_level">
          <a-select 
            v-model:value="formData.subscription_level" 
            placeholder="请选择订阅级别"
            @change="handleSubscriptionLevelChange"
          >
            <a-select-option value="free">免费版</a-select-option>
            <a-select-option value="pro">专业版</a-select-option>
            <a-select-option value="enterprise">企业版</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="资源配额">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="最大任务数" name="max_tasks">
                <a-input-number 
                  v-model:value="formData.max_tasks" 
                  :min="1" 
                  :max="10000"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="最大节点数" name="max_nodes">
                <a-input-number 
                  v-model:value="formData.max_nodes" 
                  :min="1" 
                  :max="1000"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="最大告警数" name="max_alerts">
                <a-input-number 
                  v-model:value="formData.max_alerts" 
                  :min="1" 
                  :max="10000"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="最大变量数" name="max_variables">
                <a-input-number 
                  v-model:value="formData.max_variables" 
                  :min="1" 
                  :max="1000"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea 
            v-model:value="formData.description" 
            placeholder="请输入租户描述"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 使用统计模态框 -->
    <a-modal
      v-model:open="usageModalVisible"
      title="租户使用统计"
      :footer="null"
      width="800px"
    >
      <div v-if="currentTenantUsage">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="租户名称">
            {{ currentTenantUsage.tenant_name }}
          </a-descriptions-item>
          <a-descriptions-item label="订阅级别">
            <a-tag :color="getSubscriptionColor(currentTenantUsage.subscription_level)">
              {{ getSubscriptionText(currentTenantUsage.subscription_level) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="当前任务数">
            {{ currentTenantUsage.current_tasks }} / {{ currentTenantUsage.max_tasks }}
          </a-descriptions-item>
          <a-descriptions-item label="当前节点数">
            {{ currentTenantUsage.current_nodes }} / {{ currentTenantUsage.max_nodes }}
          </a-descriptions-item>
          <a-descriptions-item label="当前告警数">
            {{ currentTenantUsage.current_alerts }} / {{ currentTenantUsage.max_alerts }}
          </a-descriptions-item>
          <a-descriptions-item label="当前变量数">
            {{ currentTenantUsage.current_variables }} / {{ currentTenantUsage.max_variables }}
          </a-descriptions-item>
          <a-descriptions-item label="存储使用量">
            {{ formatBytes(currentTenantUsage.storage_used) }}
          </a-descriptions-item>
          <a-descriptions-item label="最后活跃时间">
            {{ formatDate(currentTenantUsage.last_active_at) }}
          </a-descriptions-item>
        </a-descriptions>
        
        <!-- 资源使用率图表 -->
        <div style="margin-top: 24px;">
          <h4>资源使用率</h4>
          <a-row :gutter="16">
            <a-col :span="6" v-for="(item, key) in getUsageStats()" :key="key">
              <a-card size="small">
                <a-statistic
                  :title="item.title"
                  :value="item.percentage"
                  suffix="%"
                  :value-style="{ color: item.color }"
                />
                <a-progress 
                  :percent="item.percentage" 
                  :stroke-color="item.color"
                  :show-info="false"
                  size="small"
                />
              </a-card>
            </a-col>
          </a-row>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

// 响应式数据
const loading = ref(false)
const tenants = ref([])
const modalVisible = ref(false)
const usageModalVisible = ref(false)
const submitLoading = ref(false)
const isEdit = ref(false)
const formRef = ref()
const currentTenantUsage = ref(null)

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条记录`
})

// 表单数据
const formData = reactive({
  name: '',
  subscription_level: 'free',
  max_tasks: 10,
  max_nodes: 5,
  max_alerts: 10,
  max_variables: 20,
  description: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入租户名称', trigger: 'blur' },
    { min: 2, max: 50, message: '租户名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  subscription_level: [
    { required: true, message: '请选择订阅级别', trigger: 'change' }
  ],
  max_tasks: [
    { required: true, message: '请输入最大任务数', trigger: 'blur' }
  ],
  max_nodes: [
    { required: true, message: '请输入最大节点数', trigger: 'blur' }
  ]
}

// 表格列配置
const columns = [
  {
    title: '租户ID',
    dataIndex: 'id',
    key: 'id',
    width: 80
  },
  {
    title: '租户名称',
    dataIndex: 'name',
    key: 'name',
    width: 150
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    width: 200
  },
  {
    title: '订阅级别',
    dataIndex: 'subscription_level',
    key: 'subscription_level',
    width: 120
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 150
  },
  {
    title: '操作',
    key: 'action',
    width: 200
  }
]

// 生命周期
onMounted(() => {
  fetchTenants()
})

// 获取租户列表
const fetchTenants = async () => {
  loading.value = true
  try {
    const response = await request.get('/tenants', {
      params: {
        page: pagination.current,
        size: pagination.pageSize
      }
    })
    tenants.value = response.tenants || []
    pagination.total = response.total || 0
  } catch (error) {
    message.error('获取租户列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 表格变化处理
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchTenants()
}

// 显示创建模态框
const showCreateModal = () => {
  isEdit.value = false
  resetForm()
  modalVisible.value = true
}

// 显示编辑模态框
const showEditModal = (record) => {
  isEdit.value = true
  Object.assign(formData, record)
  modalVisible.value = true
}

// 显示使用统计模态框
const showUsageModal = async (record) => {
  try {
    const response = await request.get(`/tenants/${record.id}/usage`)
    currentTenantUsage.value = response.data.data || response.data
    usageModalVisible.value = true
  } catch (error) {
    message.error('获取使用统计失败: ' + error.message)
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    if (isEdit.value) {
      await request.put(`/tenants/${formData.id}`, formData)
      message.success('租户更新成功')
    } else {
      await request.post('/tenants', formData)
      message.success('租户创建成功')
    }
    
    modalVisible.value = false
    fetchTenants()
  } catch (error) {
    if (error.errorFields) {
      // 表单验证错误
      return
    }
    message.error('操作失败: ' + error.message)
  } finally {
    submitLoading.value = false
  }
}

// 取消操作
const handleCancel = () => {
  modalVisible.value = false
  resetForm()
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    subscription_level: 'free',
    max_tasks: 10,
    max_nodes: 5,
    max_alerts: 10,
    max_variables: 20,
    description: ''
  })
  formRef.value?.resetFields()
}

// 订阅级别变化时自动调整默认限额
const handleSubscriptionLevelChange = (level) => {
  const quotaMap = {
    'free': { max_tasks: 10, max_nodes: 5, max_alerts: 10, max_variables: 20 },
    'pro': { max_tasks: 50, max_nodes: 20, max_alerts: 50, max_variables: 100 },
    'enterprise': { max_tasks: 200, max_nodes: 100, max_alerts: 200, max_variables: 500 }
  }
  
  const quota = quotaMap[level] || quotaMap['free']
  Object.assign(formData, quota)
}

// 切换租户状态
const toggleTenantStatus = async (record) => {
  try {
    const newStatus = record.status === 'active' ? 'inactive' : 'active'
    await request.patch(`/tenants/${record.id}/status`, { status: newStatus })
    message.success(`租户${newStatus === 'active' ? '启用' : '停用'}成功`)
    fetchTenants()
  } catch (error) {
    message.error('操作失败: ' + error.message)
  }
}

// 工具函数
const getSubscriptionColor = (level) => {
  const colorMap = {
    'free': 'blue',
    'pro': 'green',
    'enterprise': 'red'
  }
  return colorMap[level] || 'default'
}

const getSubscriptionText = (level) => {
  const textMap = {
    'free': '免费版',
    'pro': '专业版',
    'enterprise': '企业版'
  }
  return textMap[level] || level
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getUsageStats = () => {
  if (!currentTenantUsage.value) return {}
  
  const usage = currentTenantUsage.value
  return {
    tasks: {
      title: '任务使用率',
      percentage: Math.round((usage.current_tasks / usage.max_tasks) * 100),
      color: usage.current_tasks / usage.max_tasks > 0.8 ? '#ff4d4f' : '#52c41a'
    },
    nodes: {
      title: '节点使用率',
      percentage: Math.round((usage.current_nodes / usage.max_nodes) * 100),
      color: usage.current_nodes / usage.max_nodes > 0.8 ? '#ff4d4f' : '#52c41a'
    },
    alerts: {
      title: '告警使用率',
      percentage: Math.round((usage.current_alerts / usage.max_alerts) * 100),
      color: usage.current_alerts / usage.max_alerts > 0.8 ? '#ff4d4f' : '#52c41a'
    },
    variables: {
      title: '变量使用率',
      percentage: Math.round((usage.current_variables / usage.max_variables) * 100),
      color: usage.current_variables / usage.max_variables > 0.8 ? '#ff4d4f' : '#52c41a'
    }
  }
}
</script>

<style scoped>
.tenant-management {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
</style>