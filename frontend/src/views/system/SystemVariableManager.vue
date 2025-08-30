import request from '@/utils/request'

/**
 * 获取系统变量列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export const getSystemVariables = (params) => {
  return request.get('/system/variables', { params })
}

/**
 * 创建系统变量
 * @param {Object} data - 变量数据
 * @returns {Promise}
 */
export const createSystemVariable = (data) => {
  return request.post('/system/variables', data)
}

/**
 * 更新系统变量
 * @param {string|number} id - 变量ID
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export const updateSystemVariable = (id, data) => {
  return request.put(`/system/variables/${id}`, data)
}

/**
 * 删除系统变量
 * @param {string|number} id - 变量ID
 * @returns {Promise}
 */
export const deleteSystemVariable = (id) => {
  return request.delete(`/system/variables/${id}`)
}
<template>
  <div class="system-variable-manager">
    <a-card title="系统变量管理" :bordered="false">
      <template #extra>
        <a-button type="primary" @click="showAddModal">
          <template #icon>
            <plus-outlined />
          </template>
          添加变量
        </a-button>
      </template>

      <!-- 变量列表 -->
      <a-table
        :columns="columns"
        :data-source="variables"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <span>{{ record.name }}</span>
          </template>
          <template v-else-if="column.key === 'value'">
            <span>{{ maskValue(record.value, record.is_secret) }}</span>
          </template>
          <template v-else-if="column.key === 'is_secret'">
            <a-tag :color="record.is_secret ? 'red' : 'green'">
              {{ record.is_secret ? '是' : '否' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            <span>{{ formatDate(record.created_at) }}</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a @click="showEditModal(record)">编辑</a>
              <a-divider type="vertical" />
              <a-popconfirm
                title="确定要删除这个变量吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="deleteVariable(record.id)"
              >
                <a class="danger-link">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>

      <!-- 添加/编辑变量的模态框 -->
      <a-modal
        v-model:open="modalVisible"
        :title="modalTitle"
        @ok="handleModalOk"
        @cancel="handleModalCancel"
        :confirm-loading="modalLoading"
      >
        <a-form
          :model="formState"
          :rules="rules"
          ref="formRef"
          :label-col="{ span: 6 }"
          :wrapper-col="{ span: 16 }"
        >
          <a-form-item label="变量名称" name="name">
            <a-input v-model:value="formState.name" placeholder="请输入变量名称，以$public_开头" />
          </a-form-item>
          <a-form-item label="变量值" name="value">
            <a-textarea v-model:value="formState.value" placeholder="请输入变量值" :rows="4" />
          </a-form-item>
          <a-form-item label="是否保密" name="is_secret">
            <a-switch v-model:checked="formState.is_secret" />
          </a-form-item>
          <a-form-item label="描述" name="description">
            <a-textarea v-model:value="formState.description" placeholder="请输入变量描述" :rows="2" />
          </a-form-item>
        </a-form>
      </a-modal>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { getSystemVariables, createSystemVariable, updateSystemVariable, deleteSystemVariable } from '@/api/systemVariables'

// 表格列定义
const columns = [
  {
    title: '变量名称',
    dataIndex: 'name',
    key: 'name',
    sorter: true,
    width: '25%'
  },
  {
    title: '变量值',
    dataIndex: 'value',
    key: 'value',
    width: '30%'
  },
  {
    title: '是否保密',
    dataIndex: 'is_secret',
    key: 'is_secret',
    width: '10%',
    filters: [
      { text: '是', value: true },
      { text: '否', value: false }
    ]
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    sorter: true,
    width: '15%'
  },
  {
    title: '操作',
    key: 'action',
    width: '20%'
  }
]

// 状态定义
const variables = ref([])
const loading = ref(false)
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条记录`
})

// 模态框状态
const modalVisible = ref(false)
const modalTitle = ref('添加系统变量')
const modalLoading = ref(false)
const formRef = ref(null)
const formState = reactive({
  id: null,
  name: '',
  value: '',
  is_secret: false,
  description: ''
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入变量名称', trigger: 'blur' },
    { pattern: /^\$public_[a-zA-Z0-9_]+$/, message: '变量名必须以$public_开头，只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  value: [
    { required: true, message: '请输入变量值', trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString()
}

// 掩码显示敏感值
const maskValue = (value, isSecret) => {
  if (!value) return ''
  if (isSecret) {
    return '******'
  }
  return value
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

// 获取变量列表
const fetchVariables = async (params = {}) => {
  try {
    loading.value = true
    
    // 构建查询参数
    const queryParams = {
      page: params.current || pagination.current,
      size: params.pageSize || pagination.pageSize,
      keyword: params.filters?.is_secret
    }

    // 添加排序参数
    if (params.sorter && params.sorter.field) {
      queryParams.sort_field = params.sorter.field
      queryParams.sort_order = params.sorter.order === 'ascend' ? 'asc' : 'desc'
    }

    const response = await getSystemVariables(queryParams)
    
    variables.value = response.list
    pagination.total = response.total
    pagination.current = queryParams.page
    pagination.pageSize = queryParams.size
    
  } catch (error) {
    console.error('获取系统变量失败:', error)
    message.error('获取系统变量失败: ' + (error.message || error))
  } finally {
    loading.value = false
  }
}

// 表格变化处理
const handleTableChange = (pag, filters, sorter) => {
  fetchVariables({
    current: pag.current,
    pageSize: pag.pageSize,
    filters: {
      is_secret: filters.is_secret && filters.is_secret.length > 0 ? filters.is_secret[0] : undefined
    },
    sorter: {
      field: sorter.field,
      order: sorter.order
    }
  })
}

// 显示添加模态框
const showAddModal = () => {
  modalTitle.value = '添加系统变量'
  formState.id = null
  formState.name = '$public_'
  formState.value = ''
  formState.is_secret = false
  formState.description = ''
  modalVisible.value = true
}

// 显示编辑模态框
const showEditModal = (record) => {
  modalTitle.value = '编辑系统变量'
  formState.id = record.id
  formState.name = record.name
  formState.value = record.value
  formState.is_secret = record.is_secret
  formState.description = record.description || ''
  modalVisible.value = true
}

// 处理模态框确认
const handleModalOk = () => {
  formRef.value.validate().then(() => {
    modalLoading.value = true
    
    // 根据是否有ID决定是创建还是更新
    const isUpdate = formState.id !== null
    const formData = {
      name: formState.name,
      value: formState.value,
      description: formState.description,
      is_secret: formState.is_secret
    }
    
    // 使用API服务进行操作
    const operation = isUpdate 
      ? updateSystemVariable(formState.id, formData)
      : createSystemVariable(formData)
    
    operation
      .then(() => {
        message.success(isUpdate ? '更新成功' : '添加成功')
        modalVisible.value = false
        fetchVariables() // 刷新列表
      })
      .catch(error => {
        console.error(isUpdate ? '更新系统变量失败:' : '添加系统变量失败:', error)
        message.error((isUpdate ? '更新' : '添加') + '系统变量失败: ' + (error.message || error))
      })
      .finally(() => {
        modalLoading.value = false
      })
  })
}

// 处理模态框取消
const handleModalCancel = () => {
  modalVisible.value = false
}

// 删除变量
const deleteVariable = async (id) => {
  try {
    await deleteSystemVariable(id)
    message.success('删除成功')
    fetchVariables() // 刷新列表
  } catch (error) {
    console.error('删除系统变量失败:', error)
    message.error('删除系统变量失败: ' + (error.message || error))
  }
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

.danger-link {
  color: #ff4d4f;
}

.danger-link:hover {
  color: #ff7875;
}
</style>