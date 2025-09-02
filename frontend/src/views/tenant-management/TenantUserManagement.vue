<template>
  <div class="tenant-user-management">
    <div class="page-header">
      <h2>租户用户管理</h2>
      <a-button type="primary" @click="showCreateModal">
        <PlusOutlined />
        添加用户
      </a-button>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input
            v-model:value="searchForm.keyword"
            placeholder="搜索用户名或邮箱"
            allow-clear
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="searchForm.role"
            placeholder="选择角色"
            allow-clear
          >
            <a-select-option value="">全部角色</a-select-option>
            <a-select-option value="user">普通用户</a-select-option>
            <a-select-option value="tenant_admin">租户管理员</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <SearchOutlined />
              搜索
            </a-button>
            <a-button @click="handleReset">
              重置
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </div>

    <!-- 用户列表 -->
    <a-table 
      :columns="columns" 
      :data-source="users" 
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="record.status === 1 ? 'green' : 'red'">
            {{ record.status === 1 ? '活跃' : '停用' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'role'">
          <a-tag :color="getRoleColor(record.role)">
            {{ getRoleText(record.role) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'created_at'">
          {{ formatDate(record.created_at) }}
        </template>
        <template v-else-if="column.key === 'joined_at'">
          {{ formatDate(record.joined_at) }}
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="showEditModal(record)">
              编辑
            </a-button>
            <a-popconfirm
              title="确定要移除该用户吗？"
              @confirm="handleRemoveUser(record)"
              :disabled="record.role === 'tenant_admin' && adminCount <= 1"
            >
              <a-button 
                type="link" 
                size="small" 
                danger
                :disabled="record.role === 'tenant_admin' && adminCount <= 1"
              >
                移除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 创建用户模态框 -->
    <a-modal
      v-model:open="createModalVisible"
      title="添加用户"
      @ok="handleCreateUser"
      @cancel="handleCreateCancel"
      :confirm-loading="createLoading"
    >
      <a-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        layout="vertical"
      >
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="createForm.username" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="createForm.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item label="密码" name="password">
          <a-input-password v-model:value="createForm.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item label="角色" name="role">
          <a-select v-model:value="createForm.role" placeholder="请选择角色">
            <a-select-option value="user">普通用户</a-select-option>
            <a-select-option value="tenant_admin">租户管理员</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑用户模态框 -->
    <a-modal
      v-model:open="editModalVisible"
      title="编辑用户"
      @ok="handleUpdateUser"
      @cancel="handleEditCancel"
      :confirm-loading="editLoading"
    >
      <a-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        layout="vertical"
      >
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="editForm.username" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="editForm.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item label="角色" name="role">
          <a-select 
            v-model:value="editForm.role" 
            placeholder="请选择角色"
            :disabled="editForm.role === 'tenant_admin' && adminCount <= 1"
          >
            <a-select-option value="user">普通用户</a-select-option>
            <a-select-option value="tenant_admin">租户管理员</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-select v-model:value="editForm.status" placeholder="请选择状态">
            <a-select-option :value="1">活跃</a-select-option>
            <a-select-option :value="0">停用</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="重置密码">
          <a-input-password 
            v-model:value="editForm.new_password" 
            placeholder="留空则不修改密码" 
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const users = ref([])
const createModalVisible = ref(false)
const editModalVisible = ref(false)
const createLoading = ref(false)
const editLoading = ref(false)
const createFormRef = ref()
const editFormRef = ref()

// 搜索表单
const searchForm = reactive({
  keyword: '',
  role: ''
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

// 创建表单
const createForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'user'
})

// 编辑表单
const editForm = reactive({
  id: null,
  username: '',
  email: '',
  role: '',
  status: '',
  new_password: ''
})

// 表单验证规则
const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const editRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 表格列配置
const columns = [
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username'
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email'
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
    key: 'created_at'
  },
  {
    title: '加入时间',
    dataIndex: 'joined_at',
    key: 'joined_at'
  },
  {
    title: '操作',
    key: 'action',
    width: 150
  }
]

// 计算管理员数量
const adminCount = computed(() => {
  return users.value.filter(user => user.role === 'tenant_admin').length
})

// 获取当前租户ID
const getCurrentTenantId = () => {
  return userStore.currentTenant?.tenant_id
}

// 加载用户列表
const loadUsers = async () => {
  const tenantId = getCurrentTenantId()
  if (!tenantId) {
    message.error('未找到当前租户信息')
    return
  }

  loading.value = true
  try {
    const params = {
      page: pagination.current,
      size: pagination.pageSize,
      keyword: searchForm.keyword,
      role: searchForm.role
    }

    const response = await request.get(`/tenants/${tenantId}/users`, { params })
    
    // 数据直接在 response.data 中，不需要嵌套的 data 属性
    const responseData = response.data || {}
    
    users.value = responseData.users || []
    pagination.total = responseData.pagination?.total || 0
  } catch (error) {
    console.error('加载用户列表失败:', error)
    message.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  loadUsers()
}

// 重置搜索
const handleReset = () => {
  searchForm.keyword = ''
  searchForm.role = ''
  pagination.current = 1
  loadUsers()
}

// 表格变化处理
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadUsers()
}

// 显示创建模态框
const showCreateModal = () => {
  createModalVisible.value = true
}

// 创建用户
const handleCreateUser = async () => {
  try {
    await createFormRef.value.validate()
    
    const tenantId = getCurrentTenantId()
    if (!tenantId) {
      message.error('未找到当前租户信息')
      return
    }

    createLoading.value = true
    
    await request.post(`/tenants/${tenantId}/users`, createForm)
    
    message.success('用户创建成功')
    createModalVisible.value = false
    resetCreateForm()
    loadUsers()
  } catch (error) {
    console.error('创建用户失败:', error)
    if (error.response?.data?.error) {
      message.error(error.response.data.error)
    } else {
      message.error('创建用户失败')
    }
  } finally {
    createLoading.value = false
  }
}

// 取消创建
const handleCreateCancel = () => {
  createModalVisible.value = false
  resetCreateForm()
}

// 重置创建表单
const resetCreateForm = () => {
  Object.assign(createForm, {
    username: '',
    email: '',
    password: '',
    role: 'user'
  })
  createFormRef.value?.resetFields()
}

// 显示编辑模态框
const showEditModal = (record) => {
  Object.assign(editForm, {
    id: record.id,
    username: record.username,
    email: record.email,
    role: record.role,
    status: record.status,
    new_password: ''
  })
  editModalVisible.value = true
}

// 更新用户
const handleUpdateUser = async () => {
  try {
    await editFormRef.value.validate()
    
    const tenantId = getCurrentTenantId()
    if (!tenantId) {
      message.error('未找到当前租户信息')
      return
    }

    editLoading.value = true
    
    const updateData = {
      username: editForm.username,
      email: editForm.email,
      role: editForm.role,
      status: editForm.status
    }
    
    // 如果提供了新密码，则包含在更新数据中
    if (editForm.new_password) {
      updateData.password = editForm.new_password
    }
    
    await request.put(`/tenants/${tenantId}/users/${editForm.id}`, updateData)
    
    message.success('用户更新成功')
    editModalVisible.value = false
    resetEditForm()
    loadUsers()
  } catch (error) {
    console.error('更新用户失败:', error)
    if (error.response?.data?.error) {
      message.error(error.response.data.error)
    } else {
      message.error('更新用户失败')
    }
  } finally {
    editLoading.value = false
  }
}

// 取消编辑
const handleEditCancel = () => {
  editModalVisible.value = false
  resetEditForm()
}

// 重置编辑表单
const resetEditForm = () => {
  Object.assign(editForm, {
    id: null,
    username: '',
    email: '',
    role: '',
    status: '',
    new_password: ''
  })
  editFormRef.value?.resetFields()
}

// 移除用户
const handleRemoveUser = async (record) => {
  const tenantId = getCurrentTenantId()
  if (!tenantId) {
    message.error('未找到当前租户信息')
    return
  }

  try {
    await request.delete(`/tenants/${tenantId}/users/${record.id}`)
    message.success('用户移除成功')
    loadUsers()
  } catch (error) {
    console.error('移除用户失败:', error)
    if (error.response?.data?.error) {
      message.error(error.response.data.error)
    } else {
      message.error('移除用户失败')
    }
  }
}

// 获取角色颜色
const getRoleColor = (role) => {
  const colors = {
    user: 'blue',
    tenant_admin: 'green'
  }
  return colors[role] || 'default'
}

// 获取角色文本
const getRoleText = (role) => {
  const texts = {
    user: '普通用户',
    tenant_admin: '租户管理员'
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
  loadUsers()
})
</script>

<style scoped>
.tenant-user-management {
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