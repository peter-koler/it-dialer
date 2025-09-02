<template>
  <div class="audit-logs">
    <a-card title="审计日志查询" :bordered="false">
      <!-- 搜索表单 -->
      <div class="search-form">
        <a-form
          :model="searchForm"
          layout="inline"
          @finish="handleSearch"
        >
          <a-form-item label="操作类型">
            <a-select
              v-model:value="searchForm.action"
              placeholder="请选择操作类型"
              style="width: 150px"
              allowClear
            >
              <a-select-option
                v-for="action in actionOptions"
                :key="action.value"
                :value="action.value"
              >
                {{ action.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="资源类型">
            <a-select
              v-model:value="searchForm.resource_type"
              placeholder="请选择资源类型"
              style="width: 120px"
              allowClear
            >
              <a-select-option
                v-for="type in resourceTypeOptions"
                :key="type.value"
                :value="type.value"
              >
                {{ type.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="操作用户" v-if="userOptions.length > 0">
            <a-select
              v-model:value="searchForm.user_id"
              placeholder="请选择用户"
              style="width: 150px"
              allowClear
              show-search
              :filter-option="filterUserOption"
            >
              <a-select-option
                v-for="user in userOptions"
                :key="user.id"
                :value="user.id"
              >
                {{ user.username }}
              </a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="租户" v-if="isSuperAdmin && tenantOptions.length > 0">
            <a-select
              v-model:value="searchForm.tenant_id"
              placeholder="请选择租户"
              style="width: 150px"
              allowClear
            >
              <a-select-option
                v-for="tenant in tenantOptions"
                :key="tenant.id"
                :value="tenant.id"
              >
                {{ tenant.name }}
              </a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="时间范围">
            <a-range-picker
              v-model:value="searchForm.dateRange"
              style="width: 240px"
              :placeholder="['开始时间', '结束时间']"
              format="YYYY-MM-DD"
            />
          </a-form-item>
          
          <a-form-item>
            <a-button type="primary" html-type="submit" :loading="loading">
              查询
            </a-button>
            <a-button style="margin-left: 8px" @click="handleReset">
              重置
            </a-button>
          </a-form-item>
        </a-form>
      </div>
      
      <!-- 审计日志表格 -->
      <a-table
        :columns="columns"
        :data-source="auditLogs"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-tag :color="getActionColor(record.action)">
              {{ getActionLabel(record.action) }}
            </a-tag>
          </template>
          
          <template v-else-if="column.key === 'resource_type'">
            <a-tag color="blue">
              {{ getResourceTypeLabel(record.resource_type) }}
            </a-tag>
          </template>
          
          <template v-else-if="column.key === 'operator_name'">
            <span v-if="record.operator_name">{{ record.operator_name }}</span>
            <span v-else style="color: #999">系统操作</span>
          </template>
          
          <template v-else-if="column.key === 'target_user_name'">
            <span v-if="record.target_user_name">{{ record.target_user_name }}</span>
            <span v-else>-</span>
          </template>
          
          <template v-else-if="column.key === 'tenant_name'">
            <span v-if="record.tenant_name">{{ record.tenant_name }}</span>
            <span v-else>-</span>
          </template>
          
          <template v-else-if="column.key === 'created_at'">
            {{ formatDateTime(record.created_at) }}
          </template>
          
          <template v-else-if="column.key === 'operation'">
            <a-button type="link" size="small" @click="showDetail(record)">
              查看详情
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      title="审计日志详情"
      :footer="null"
      width="800px"
    >
      <div v-if="currentLog">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="日志ID">
            {{ currentLog.id }}
          </a-descriptions-item>
          <a-descriptions-item label="操作类型">
            <a-tag :color="getActionColor(currentLog.action)">
              {{ getActionLabel(currentLog.action) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="资源类型">
            <a-tag color="blue">
              {{ getResourceTypeLabel(currentLog.resource_type) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="资源ID">
            {{ currentLog.resource_id || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="操作者">
            {{ currentLog.operator_name || '系统操作' }}
          </a-descriptions-item>
          <a-descriptions-item label="目标用户">
            {{ currentLog.target_user_name || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="租户" v-if="isSuperAdmin">
            {{ currentLog.tenant_name || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="IP地址">
            {{ currentLog.ip_address || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="操作时间" :span="2">
            {{ formatDateTime(currentLog.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="用户代理" :span="2">
            <div style="word-break: break-all; max-height: 60px; overflow-y: auto;">
              {{ currentLog.user_agent || '-' }}
            </div>
          </a-descriptions-item>
          <a-descriptions-item label="操作详情" :span="2" v-if="currentLog.details">
            <pre style="background: #f5f5f5; padding: 8px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{{ formatDetails(currentLog.details) }}</pre>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import api from '@/api'
import dayjs from 'dayjs'

const userStore = useUserStore()
const isSuperAdmin = computed(() => userStore.isSuperAdmin)

// 响应式数据
const loading = ref(false)
const auditLogs = ref([])
const actionOptions = ref([])
const resourceTypeOptions = ref([])
const userOptions = ref([])
const tenantOptions = ref([])
const detailVisible = ref(false)
const currentLog = ref(null)

// 搜索表单
const searchForm = reactive({
  action: undefined,
  resource_type: undefined,
  user_id: undefined,
  tenant_id: undefined,
  dateRange: undefined
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
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 80
  },
  {
    title: '操作类型',
    dataIndex: 'action',
    key: 'action',
    width: 120
  },
  {
    title: '资源类型',
    dataIndex: 'resource_type',
    key: 'resource_type',
    width: 100
  },
  {
    title: '操作者',
    dataIndex: 'operator_name',
    key: 'operator_name',
    width: 120
  },
  {
    title: '目标用户',
    dataIndex: 'target_user_name',
    key: 'target_user_name',
    width: 120
  },
  {
    title: '租户',
    dataIndex: 'tenant_name',
    key: 'tenant_name',
    width: 120,
    customRender: ({ record }) => record.tenant_name || '-'
  },
  {
    title: 'IP地址',
    dataIndex: 'ip_address',
    key: 'ip_address',
    width: 130
  },
  {
    title: '操作时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 160
  },
  {
    title: '操作',
    key: 'operation',
    width: 80,
    fixed: 'right'
  }
]

// 如果不是超级管理员，隐藏租户列
if (!isSuperAdmin.value) {
  const tenantColumnIndex = columns.findIndex(col => col.key === 'tenant_name')
  if (tenantColumnIndex > -1) {
    columns.splice(tenantColumnIndex, 1)
  }
}

// 获取审计日志列表
const fetchAuditLogs = async () => {
  try {
    loading.value = true
    
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchForm
    }
    
    // 处理日期范围
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_date = searchForm.dateRange[0].format('YYYY-MM-DD')
      params.end_date = searchForm.dateRange[1].format('YYYY-MM-DD')
    }
    delete params.dateRange
    
   // console.log('🔍 [AuditLogs] 开始获取审计日志，请求参数:', params)
    
    const response = await api.auditLogs.getAuditLogs(params)
    
  //  console.log('📥 [AuditLogs] 获取审计日志响应:', response)
    
    if (response.code === 0) {
  //    console.log('✅ [AuditLogs] 审计日志获取成功，数据条数:', response.data?.list?.length || 0)
      auditLogs.value = response.data.list
      pagination.total = response.data.total
    } else {
   //   console.error('❌ [AuditLogs] 审计日志获取失败，错误信息:', response.message)
      message.error(response.message || '获取审计日志失败')
    }
  } catch (error) {
 //   console.error('💥 [AuditLogs] 获取审计日志异常:', error)
   console.error('💥 [AuditLogs] 错误详情:', {
      message: error.message,
      stack: error.stack,
      response: error.response
    })
    message.error('获取审计日志失败')
  } finally {
    loading.value = false
  }
}

// 获取操作类型选项
const fetchActionOptions = async () => {
  try {
    //console.log('🔍 [AuditLogs] 开始获取操作类型选项')
    const response = await api.auditLogs.getActionOptions()
   // console.log('📥 [AuditLogs] 操作类型选项响应:', response)
    if (response.code === 0) {
    //  console.log('✅ [AuditLogs] 操作类型选项获取成功，数量:', response.data?.length || 0)
      actionOptions.value = response.data
    } else {
    //  console.error('❌ [AuditLogs] 操作类型选项获取失败:', response.message)
    }
  } catch (error) {
   // console.error('💥 [AuditLogs] 获取操作类型选项异常:', error)
  }
}

// 获取资源类型选项
const fetchResourceTypeOptions = async () => {
  try {
  //  console.log('🔍 [AuditLogs] 开始获取资源类型选项')
    const response = await api.auditLogs.getResourceTypeOptions()
  //  console.log('📥 [AuditLogs] 资源类型选项响应:', response)
    if (response.code === 0) {
   //   console.log('✅ [AuditLogs] 资源类型选项获取成功，数量:', response.data?.length || 0)
      resourceTypeOptions.value = response.data
    } else {
    //  console.error('❌ [AuditLogs] 资源类型选项获取失败:', response.message)
    }
  } catch (error) {
  //  console.error('💥 [AuditLogs] 获取资源类型选项异常:', error)
  }
}

// 获取用户选项
const fetchUserOptions = async () => {
  try {
  //  console.log('🔍 [AuditLogs] 开始获取用户选项')
    const response = await api.auditLogs.getUserOptions()
   // console.log('📥 [AuditLogs] 用户选项响应:', response)
    if (response.code === 0) {
   //   console.log('✅ [AuditLogs] 用户选项获取成功，数量:', response.data?.length || 0)
      userOptions.value = response.data
    } else {
    //  console.error('❌ [AuditLogs] 用户选项获取失败:', response.message)
    }
  } catch (error) {
  //  console.error('💥 [AuditLogs] 获取用户选项异常:', error)
  }
}

// 获取租户选项（仅超级管理员）
const fetchTenantOptions = async () => {
  if (!isSuperAdmin.value) {
    console.log('🚫 [AuditLogs] 非超级管理员，跳过获取租户选项')
    return
  }
  
  try {
  //  console.log('🔍 [AuditLogs] 开始获取租户选项')
    const response = await api.auditLogs.getTenantOptions()
  //  console.log('📥 [AuditLogs] 租户选项响应:', response)
    if (response.code === 0) {
   //   console.log('✅ [AuditLogs] 租户选项获取成功，数量:', response.data?.length || 0)
      tenantOptions.value = response.data
    } else {
   //   console.error('❌ [AuditLogs] 租户选项获取失败:', response.message)
    }
  } catch (error) {
 //   console.error('💥 [AuditLogs] 获取租户选项异常:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  fetchAuditLogs()
}

// 重置搜索
const handleReset = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = undefined
  })
  pagination.current = 1
  fetchAuditLogs()
}

// 表格变化处理
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchAuditLogs()
}

// 显示详情
const showDetail = (record) => {
  currentLog.value = record
  detailVisible.value = true
}

// 获取操作类型颜色
const getActionColor = (action) => {
  const colorMap = {
    'create_user': 'green',
    'update_user': 'blue',
    'delete_user': 'red',
    'activate_user': 'green',
    'deactivate_user': 'orange',
    'reset_password': 'purple',
    'create_tenant': 'green',
    'update_tenant': 'blue',
    'delete_tenant': 'red',
    'add_user_to_tenant': 'cyan',
    'remove_user_from_tenant': 'orange',
    'update_user_role': 'blue',
    'update_system_config': 'purple',
    'login_success': 'green',
    'login_failed': 'red',
    'logout': 'default'
  }
  return colorMap[action] || 'default'
}

// 获取操作类型标签
const getActionLabel = (action) => {
  const option = actionOptions.value.find(opt => opt.value === action)
  return option ? option.label : action
}

// 获取资源类型标签
const getResourceTypeLabel = (resourceType) => {
  const option = resourceTypeOptions.value.find(opt => opt.value === resourceType)
  return option ? option.label : resourceType
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// 格式化详情
const formatDetails = (details) => {
  if (!details) return ''
  try {
    return JSON.stringify(JSON.parse(details), null, 2)
  } catch {
    return details
  }
}

// 用户选项过滤
const filterUserOption = (input, option) => {
  return option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

// 组件挂载时初始化数据
onMounted(async () => {
  await Promise.all([
    fetchActionOptions(),
    fetchResourceTypeOptions(),
    fetchUserOptions(),
    fetchTenantOptions()
  ])
  fetchAuditLogs()
})
</script>

<style scoped>
.audit-logs {
  padding: 24px;
}

.search-form {
  margin-bottom: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.search-form .ant-form-item {
  margin-bottom: 8px;
}
</style>