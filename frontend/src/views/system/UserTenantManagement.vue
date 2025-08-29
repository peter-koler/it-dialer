<template>
  <div class="user-tenant-management">
    <div class="page-header">
      <h2>用户租户关联管理</h2>
      <a-button type="primary" @click="showCreateModal">
        <PlusOutlined />
        添加关联
      </a-button>
    </div>

    <!-- 搜索筛选 -->
    <div class="search-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input
            v-model:value="searchForm.username"
            placeholder="搜索用户名"
            allow-clear
            @change="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="searchForm.tenant_id"
            placeholder="选择租户"
            allow-clear
            @change="handleSearch"
          >
            <a-select-option value="">全部租户</a-select-option>
            <a-select-option v-for="tenant in tenantOptions" :key="tenant.id" :value="tenant.id">
              {{ tenant.name }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="searchForm.role"
            placeholder="选择角色"
            allow-clear
            @change="handleSearch"
          >
            <a-select-option value="">全部角色</a-select-option>
            <a-select-option value="user">普通用户</a-select-option>
            <a-select-option value="tenant_admin">租户管理员</a-select-option>
            <a-select-option value="super_admin">超级管理员</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-button type="primary" @click="handleSearch">
            <SearchOutlined />
            搜索
          </a-button>
          <a-button style="margin-left: 8px" @click="resetSearch">
            重置
          </a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 关联列表 -->
    <a-table 
      :columns="columns" 
      :data-source="userTenants" 
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'role'">
          <a-tag :color="getRoleColor(record.role)">
            {{ getRoleText(record.role) }}
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
            <a-popconfirm
              title="确定要删除该关联吗？"
              @confirm="deleteUserTenant(record)"
            >
              <a-button type="link" size="small" danger>
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 添加/编辑关联模态框 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑用户租户关联' : '添加用户租户关联'"
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
        <a-form-item label="用户" name="user_id">
          <a-select
            v-model:value="formData.user_id"
            placeholder="请选择用户"
            show-search
            :filter-option="filterUserOption"
            @focus="loadUsers"
          >
            <a-select-option v-for="user in userOptions" :key="user.id" :value="user.id">
              {{ user.username }} ({{ user.email }})
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="租户" name="tenant_id">
          <a-select
            v-model:value="formData.tenant_id"
            placeholder="请选择租户"
            @focus="loadTenants"
          >
            <a-select-option v-for="tenant in tenantOptions" :key="tenant.id" :value="tenant.id">
              {{ tenant.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="角色" name="role">
          <a-select v-model:value="formData.role" placeholder="请选择角色">
            <a-select-option value="user">普通用户</a-select-option>
            <a-select-option value="tenant_admin">租户管理员</a-select-option>
            <a-select-option value="super_admin">超级管理员</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

// 响应式数据
const loading = ref(false)
const userTenants = ref([])
const tenantOptions = ref([])
const userOptions = ref([])
const modalVisible = ref(false)
const submitLoading = ref(false)
const isEdit = ref(false)
const formRef = ref()
const currentRecord = ref(null)

// 搜索表单
const searchForm = reactive({
  username: '',
  tenant_id: '',
  role: ''
})

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
  user_id: null,
  tenant_id: '',
  role: 'user'
})

// 表单验证规则
const formRules = {
  user_id: [
    { required: true, message: '请选择用户', trigger: 'change' }
  ],
  tenant_id: [
    { required: true, message: '请选择租户', trigger: 'change' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 表格列配置
const columns = [
  {
    title: '用户ID',
    dataIndex: 'user_id',
    key: 'user_id',
    width: 80
  },
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    width: 120
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    width: 200
  },
  {
    title: '租户名称',
    dataIndex: 'tenant_name',
    key: 'tenant_name',
    width: 150
  },
  {
    title: '角色',
    dataIndex: 'role',
    key: 'role',
    width: 120
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
    width: 150
  }
]

// 获取用户租户关联列表
const loadUserTenants = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchForm
    }
    
    const response = await request.get('/user-tenants', { params })
    userTenants.value = response.user_tenants || []
    pagination.total = response.total || 0
  } catch (error) {
    message.error('获取用户租户关联列表失败')
    console.error('Load user tenants error:', error)
  } finally {
    loading.value = false
  }
}

// 获取租户选项
const loadTenants = async () => {
  try {
    const response = await request.get('/v1/tenants')
    // 租户接口返回的数据结构直接包含tenants数组
    tenantOptions.value = response.tenants || []
  } catch (error) {
    message.error('获取租户列表失败')
    console.error('Load tenants error:', error)
  }
}

// 获取用户选项
const loadUsers = async () => {
  try {
    const response = await request.get('/users')
    if (response.code === 0) {
      userOptions.value = response.data.list || []
    } else {
      message.error(response.message || '获取用户列表失败')
    }
  } catch (error) {
    message.error('获取用户列表失败')
    console.error('Load users error:', error)
  }
}

// 显示创建模态框
const showCreateModal = () => {
  isEdit.value = false
  modalVisible.value = true
  resetForm()
  loadTenants()
  loadUsers()
}

// 显示编辑模态框
const showEditModal = (record) => {
  isEdit.value = true
  currentRecord.value = record
  modalVisible.value = true
  formData.user_id = record.user_id
  formData.tenant_id = record.tenant_id
  formData.role = record.role
  loadTenants()
  loadUsers()
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    user_id: null,
    tenant_id: '',
    role: 'user'
  })
  formRef.value?.resetFields()
}

// 处理表单提交
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    if (isEdit.value) {
      // 更新用户租户关联
      await request.put(`/tenants/${currentRecord.value.tenant_id}/users/${currentRecord.value.user_id}`, {
        user_id: formData.user_id,
        tenant_id: formData.tenant_id,
        role: formData.role
      })
      message.success('用户租户关联更新成功')
    } else {
      // 添加关联
      await request.post(`/tenants/${formData.tenant_id}/users`, {
        user_id: formData.user_id,
        role: formData.role
      })
      message.success('用户租户关联添加成功')
    }
    
    modalVisible.value = false
    loadUserTenants()
  } catch (error) {
    message.error(isEdit.value ? '更新用户角色失败' : '添加用户租户关联失败')
    console.error('Submit error:', error)
  } finally {
    submitLoading.value = false
  }
}

// 处理模态框取消
const handleCancel = () => {
  modalVisible.value = false
  resetForm()
}

// 删除用户租户关联
const deleteUserTenant = async (record) => {
  try {
    await request.delete(`/tenants/${record.tenant_id}/users/${record.user_id}`)
    message.success('删除用户租户关联成功')
    loadUserTenants()
  } catch (error) {
    message.error('删除用户租户关联失败')
    console.error('Delete user tenant error:', error)
  }
}

// 处理搜索
const handleSearch = () => {
  pagination.current = 1
  loadUserTenants()
}

// 重置搜索
const resetSearch = () => {
  Object.assign(searchForm, {
    username: '',
    tenant_id: '',
    role: ''
  })
  handleSearch()
}

// 处理表格变化
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadUserTenants()
}

// 用户选项过滤
const filterUserOption = (input, option) => {
  return option.children[0].children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

// 获取角色颜色
const getRoleColor = (role) => {
  const colors = {
    user: 'blue',
    tenant_admin: 'green',
    super_admin: 'purple'
  }
  return colors[role] || 'default'
}

// 获取角色文本
const getRoleText = (role) => {
  const texts = {
    user: '普通用户',
    tenant_admin: '租户管理员',
    super_admin: '超级管理员'
  }
  return texts[role] || role
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 组件挂载时加载数据
onMounted(() => {
  loadUserTenants()
  loadTenants()
})
</script>

<style scoped>
.user-tenant-management {
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

.search-section {
  background: #fafafa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}
</style>