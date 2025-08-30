<template>
  <div class="system-variable-manager">
    <a-card title="系统变量管理">
      <template #extra>
        <a-button type="primary" @click="showCreateModal">
          <template #icon>
            <plus-outlined />
          </template>
          新增变量
        </a-button>
      </template>
      
      <!-- 搜索区域 -->
      <a-form layout="inline" class="search-form">
        <a-form-item label="关键词">
          <a-input v-model:value="searchParams.keyword" placeholder="变量名/描述" allowClear />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSearch">
            <template #icon>
              <search-outlined />
            </template>
            搜索
          </a-button>
          <a-button style="margin-left: 8px" @click="resetSearch">
            <template #icon>
              <reload-outlined />
            </template>
            重置
          </a-button>
        </a-form-item>
      </a-form>
      
      <!-- 变量表格 -->
      <a-table
        :dataSource="variables"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" @click="editVariable(record)">
                <template #icon>
                  <edit-outlined />
                </template>
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个变量吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="deleteVariable(record)"
              >
                <a-button type="link" danger>
                  <template #icon>
                    <delete-outlined />
                  </template>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 变量编辑模态框 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingVariable ? '编辑变量' : '新增变量'"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      :confirm-loading="confirmLoading"
    >
      <a-form
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
        ref="formRef"
      >
        <a-form-item
          label="变量名"
          name="name"
          :rules="[
            { required: true, message: '请输入变量名' },
            { validator: validateVariableName }
          ]"
        >
          <a-input 
            v-model:value="formState.name" 
            placeholder="请输入变量名 (必须以$public_开头)" 
            :disabled="!!editingVariable"
          />
        </a-form-item>
        
        <a-form-item
          label="变量值"
          name="value"
          :rules="[{ required: true, message: '请输入变量值' }]"
        >
          <a-input v-model:value="formState.value" placeholder="请输入变量值" />
        </a-form-item>
        
        <a-form-item
          label="描述"
          name="description"
        >
          <a-textarea 
            v-model:value="formState.description" 
            placeholder="请输入变量描述" 
            :auto-size="{ minRows: 2, maxRows: 6 }" 
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
  PlusOutlined, 
  SearchOutlined, 
  ReloadOutlined, 
  EditOutlined, 
  DeleteOutlined 
} from '@ant-design/icons-vue'
import request from '@/utils/request'
import { getSystemVariables, createSystemVariable, updateSystemVariable, deleteSystemVariable } from '@/api/systemVariables'

// 数据相关
const variables = ref([])
const loading = ref(false)
const confirmLoading = ref(false)

// 分页相关
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  pageSizeOptions: ['10', '20', '50', '100']
})

// 搜索参数
const searchParams = reactive({
  keyword: ''
})

// 表格列定义
const columns = [
  {
    title: '变量名',
    dataIndex: 'name',
    key: 'name',
    ellipsis: true
  },
  {
    title: '变量值',
    dataIndex: 'value',
    key: 'value',
    ellipsis: true
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    ellipsis: true
  },
  {
    title: '操作',
    key: 'action',
    width: 150
  }
]

// 模态框相关
const modalVisible = ref(false)
const editingVariable = ref(null)
const formRef = ref()
const formState = reactive({
  name: '',
  value: '',
  description: ''
})

// 获取变量列表
const fetchVariables = async () => {
  try {
    loading.value = true
    const response = await getSystemVariables({
      page: pagination.current,
      size: pagination.pageSize,
      keyword: searchParams.keyword
    })
    
    variables.value = response.data.list
    pagination.total = response.data.total
  } catch (error) {
    console.error('获取系统变量失败:', error)
    message.error('获取系统变量失败: ' + (error.message || error))
  } finally {
    loading.value = false
  }
}

// 处理表格变化
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchVariables()
}

// 处理搜索
const handleSearch = () => {
  pagination.current = 1
  fetchVariables()
}

// 重置搜索
const resetSearch = () => {
  searchParams.keyword = ''
  pagination.current = 1
  fetchVariables()
}

// 显示创建模态框
const showCreateModal = () => {
  editingVariable.value = null
  formState.name = '$public_'
  formState.value = ''
  formState.description = ''
  modalVisible.value = true
}

// 编辑变量
const editVariable = (record) => {
  editingVariable.value = record
  formState.name = record.name
  formState.value = record.value
  formState.description = record.description || ''
  modalVisible.value = true
}

// 删除变量
const deleteVariable = async (record) => {
  try {
    await deleteSystemVariable(record.id)
    message.success('变量删除成功')
    fetchVariables()
  } catch (error) {
    console.error('变量删除失败:', error)
    message.error('变量删除失败: ' + (error.message || error))
  }
}

// 验证变量名
const validateVariableName = async (rule, value) => {
  if (!value) return Promise.resolve()
  
  if (!value.startsWith('$')) {
    return Promise.reject('变量名必须以$开头')
  }
  
  if (value.length < 2) { // $ 长度为1，至少还需要1个字符
    return Promise.reject('变量名长度不足')
  }
  
  // 如果是编辑模式且变量名没有变化，则不需要检查重复
  if (editingVariable.value && editingVariable.value.name === value) {
    return Promise.resolve()
  }
  
  // 检查变量名是否重复
  try {
    const response = await getSystemVariables({
      keyword: value
    })
    
    const variables = response.data.list
    if (variables && variables.length > 0) {
      return Promise.reject('变量名已存在')
    }
    return Promise.resolve()
  } catch (error) {
    return Promise.reject('检查变量名失败: ' + (error.message || error))
  }
}

// 处理模态框确认
const handleModalOk = async () => {
  try {
    await formRef.value.validateFields()
    confirmLoading.value = true
    
    // 构造请求数据
    const requestData = {
      name: formState.name,
      value: formState.value,
      description: formState.description
    }
    
    // 发送请求
    if (editingVariable.value) {
      // 更新变量
      await request.put(`/system-variables/${editingVariable.value.id}`, requestData)
    } else {
      // 创建变量
      await request.post('/system-variables', requestData)
    }
    
    message.success(editingVariable.value ? '变量更新成功' : '变量创建成功')
    modalVisible.value = false
    fetchVariables() // 刷新变量列表
  } catch (error) {
    if (error.errorFields) {
      // 表单验证错误
      return
    }
    message.error(editingVariable.value ? '变量更新失败: ' + error.message : '变量创建失败: ' + error.message)
  } finally {
    confirmLoading.value = false
  }
}

// 处理模态框取消
const handleModalCancel = () => {
  modalVisible.value = false
}

// 组件挂载时获取变量列表
onMounted(() => {
  fetchVariables()
})
</script>

<style scoped>
.system-variable-manager {
  padding: 24px;
}

.search-form {
  margin-bottom: 24px;
}
</style>