<template>
  <div>
    <a-card title="拨测任务">
      <template #extra>
        <a-space>
          <a-button type="primary" @click="showCreateModal">
            <template #icon>
              <PlusOutlined />
            </template>
            新增任务
          </a-button>
          <a-button type="primary" @click="createApiTask">
            <template #icon>
              <PlusOutlined />
            </template>
            新增API拨测任务
          </a-button>
        </a-space>
      </template>
      
      <!-- 任务筛选组件 -->
      <TaskFilter 
        :searchParams="searchParams" 
        @update:searchParams="handleSearchParamsUpdate"
        @search="handleSearch" 
        @reset="resetFilters" 
      />
      
      <!-- 任务表格组件 -->
      <TaskTable 
        :tasks="tasks"
        :loading="loading"
        :pagination="pagination"
        @updateTaskStatus="updateTaskStatus"
        @editTask="editTask"
        @deleteTask="deleteTask"
        @tableChange="handleTableChange"
      />
    </a-card>
    
    <!-- 任务模态框组件 -->
    <EnhancedTaskModal
      :open="modalVisible"
      :editing-task="editingTask"
      :confirm-loading="confirmLoading"
      @update:open="handleModalVisibleUpdate"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { createTask, updateTask } from '@/api/task'
import request from '@/utils/request'
import TaskFilter from '../../components/TaskFilter.vue'
import TaskTable from '../../components/TaskTable.vue'
import EnhancedTaskModal from '../../components/EnhancedTaskModal.vue'

// 路由
const router = useRouter()

// 数据相关
const tasks = ref([])
const loading = ref(false)
const confirmLoading = ref(false)

// 分页相关
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 搜索参数
const searchParams = reactive({
  keyword: '',
  type: undefined,
  status: undefined
})

// 模态框相关
const modalVisible = ref(false)
const editingTask = ref(null)

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    // 构建查询参数
    const params = {
      page: pagination.current,
      size: pagination.pageSize
    }
    
    // 添加搜索参数
    if (searchParams.keyword) {
      params.keyword = searchParams.keyword
    }
    if (searchParams.type) {
      params.type = searchParams.type
    }
    if (searchParams.status !== undefined) {
      // 将布尔值转换为字符串传递给后端
      params.enabled = searchParams.status
    }
    
    const response = await request.get('/tasks', { params })
    
    if (response.code === 0) {
      tasks.value = response.data.list
      pagination.total = response.data.total
    } else {
      message.error(response.message || '获取任务列表失败')
      tasks.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('获取任务列表失败:', error)
    message.error('获取任务列表失败: ' + error.message)
    // 确保在错误情况下tasks仍然是数组
    tasks.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 处理搜索参数更新
const handleSearchParamsUpdate = (newParams) => {
  Object.assign(searchParams, newParams)
}

// 显示创建模态框
const showCreateModal = () => {
  editingTask.value = null
  modalVisible.value = true
}

// 创建API拨测任务
const createApiTask = () => {
  router.push('/tasks/api/new')
}

// 处理模态框可见性更新
const handleModalVisibleUpdate = (visible) => {
  modalVisible.value = visible
}

// 处理模态框确认
const handleModalOk = async (requestData) => {
  try {
    confirmLoading.value = true
    
    // 发送请求
    let response
    if (editingTask.value) {
      // 更新任务
      response = await updateTask(editingTask.value.id, requestData)
    } else {
      // 创建任务
      response = await createTask(requestData)
    }
    
    if (response.code === 0) {
      message.success(editingTask.value ? '任务更新成功' : '任务创建成功')
      modalVisible.value = false
      fetchTasks() // 刷新任务列表
    } else {
      message.error(response.message || (editingTask.value ? '任务更新失败' : '任务创建失败'))
    }
  } catch (error) {
    console.error('保存任务失败:', error)
    message.error('保存任务失败: ' + (error.message || error))
  } finally {
    confirmLoading.value = false
  }
}

// 处理模态框取消
const handleModalCancel = () => {
  modalVisible.value = false
}

// 更新任务状态
const updateTaskStatus = async (record) => {
  try {
    const response = await request.put(`/tasks/${record.id}`, {
      ...record,
      enabled: record.enabled
    })
    
    if (response.code === 0) {
      message.success('任务状态更新成功')
    } else {
      message.error(response.message || '任务状态更新失败')
      // 恢复状态
      record.enabled = !record.enabled
    }
  } catch (error) {
    message.error('任务状态更新失败: ' + error.message)
    // 恢复状态
    record.enabled = !record.enabled
  }
}

// 编辑任务
const editTask = (task) => {
  if (task.type === 'api') {
    // API任务跳转到新的编辑页面
    router.push(`/tasks/api/edit/${task.id}`)
  } else {
    // 其他类型任务使用原有的模态框编辑
    editingTask.value = task
    modalVisible.value = true
  }
}

// 删除任务
const deleteTask = async (record) => {
  try {
    const response = await request.delete(`/tasks/${record.id}`)
    
    if (response.code === 0) {
      message.success('任务删除成功')
      fetchTasks()
    } else {
      message.error(response.message || '任务删除失败')
    }
  } catch (error) {
    message.error('任务删除失败: ' + error.message)
  }
}

// 处理表格变化
const handleTableChange = (pager) => {
  pagination.current = pager.current
  pagination.pageSize = pager.pageSize
  fetchTasks()
}

// 处理搜索
const handleSearch = () => {
  pagination.current = 1
  fetchTasks()
}

// 重置筛选
const resetFilters = () => {
  pagination.current = 1
  fetchTasks()
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTasks()
})
</script>