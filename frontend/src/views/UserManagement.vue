<template>
  <div>
    <a-card title="用户管理">
      <UserSearchBar 
        @search="handleSearch"
        @role-change="handleRoleChange"
        @add-user="showCreateModal"
      />
      
      <UserTable 
        :users="users"
        :loading="loading"
        :pagination="pagination"
        @edit="editUser"
        @reset-password="showResetPasswordModal"
        @delete="deleteUser"
        @change="handleTableChange"
      />
    </a-card>
    
    <UserModal 
      :visible="modalVisible"
      :editing-user="editingUser"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    />
    
    <ResetPwdModal 
      :visible="resetPwdModalVisible"
      :user="currentUser"
      @ok="handleResetPasswordOk"
      @cancel="handleResetPasswordCancel"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'
import UserSearchBar from '../components/UserSearchBar.vue'
import UserTable from '../components/UserTable.vue'
import UserModal from '../components/UserModal.vue'
import ResetPwdModal from '../components/ResetPwdModal.vue'

// 用户数据
const users = ref([])
const loading = ref(false)
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 模态框相关
const modalVisible = ref(false)
const resetPwdModalVisible = ref(false)
const editingUser = ref(null)
const currentUser = ref(null)

// 搜索参数
const searchParams = reactive({
  keyword: '',
  role: ''
})

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await request.get('/users', {
      params: {
        page: pagination.current,
        size: pagination.pageSize,
        keyword: searchParams.keyword,
        role: searchParams.role
      }
    })
    
    users.value = response.data.list || []
    pagination.total = response.data.total || 0
  } catch (error) {
    message.error('获取用户列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 处理搜索
const handleSearch = (keyword) => {
  searchParams.keyword = keyword
  pagination.current = 1
  fetchUsers()
}

// 处理角色筛选
const handleRoleChange = (role) => {
  searchParams.role = role
  pagination.current = 1
  fetchUsers()
}

// 显示创建模态框
const showCreateModal = () => {
  editingUser.value = null
  modalVisible.value = true
}

// 编辑用户
const editUser = (record) => {
  editingUser.value = record
  modalVisible.value = true
}

// 显示重置密码模态框
const showResetPasswordModal = (record) => {
  currentUser.value = record
  resetPwdModalVisible.value = true
}

// 删除用户
const deleteUser = async (record) => {
  try {
    await request.delete(`/users/${record.id}`)
    
    message.success(`用户 ${record.username} 删除成功`)
    fetchUsers()
  } catch (error) {
    message.error('删除用户失败: ' + error.message)
  }
}

// 处理表格变化
const handleTableChange = (pager) => {
  pagination.current = pager.current
  pagination.pageSize = pager.pageSize
  fetchUsers()
}

// 处理模态框确认
const handleModalOk = async (values) => {
  try {
    if (editingUser.value) {
      // 编辑用户
      await request.patch(`/users/${editingUser.value.id}`, values)
      message.success('用户更新成功')
    } else {
      // 创建用户
      await request.post('/users', values)
      message.success('用户创建成功')
    }
    
    modalVisible.value = false
    fetchUsers()
  } catch (error) {
    message.error((editingUser.value ? '用户更新' : '用户创建') + '失败: ' + error.message)
  }
}

// 处理模态框取消
const handleModalCancel = () => {
  modalVisible.value = false
}

// 处理重置密码确认
const handleResetPasswordOk = async (values) => {
  try {
    await request.patch(`/users/${currentUser.value.id}/password`, values)
    
    message.success(`用户 ${currentUser.value.username} 密码重置成功`)
    resetPwdModalVisible.value = false
  } catch (error) {
    message.error('密码重置失败: ' + error.message)
  }
}

// 处理重置密码取消
const handleResetPasswordCancel = () => {
  resetPwdModalVisible.value = false
}

onMounted(() => {
  fetchUsers()
})
</script>