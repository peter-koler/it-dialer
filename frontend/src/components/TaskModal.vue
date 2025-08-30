<template>
  <a-modal
    v-model:open="modalVisible"
    :title="editingTask ? '编辑任务' : '新增任务'"
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
        label="任务名称"
        name="name"
        :rules="[{ required: true, message: '请输入任务名称' }]"
      >
        <a-input v-model:value="formState.name" placeholder="请输入任务名称" />
      </a-form-item>
      
      <a-form-item
        label="任务类型"
        name="type"
        :rules="[{ required: true, message: '请选择任务类型' }]"
      >
        <a-select v-model:value="formState.type" placeholder="请选择任务类型" @change="handleTypeChange">
          <a-select-option value="ping">Ping</a-select-option>
          <a-select-option value="tcp">TCP</a-select-option>
          <a-select-option value="http">HTTP</a-select-option>
        </a-select>
      </a-form-item>
      
      <a-form-item
        label="目标地址"
        name="target"
        :rules="[{ required: true, message: '请输入目标地址' }]"
      >
        <a-input v-model:value="formState.target" placeholder="请输入目标地址" />
      </a-form-item>
      
      <!-- TCP端口输入框 (仅在选择TCP类型时显示) -->
      <a-form-item
        v-if="formState.type === 'tcp'"
        label="端口"
        name="port"
        :rules="[{ required: true, message: '请输入端口号' }]"
      >
        <a-input-number 
          v-model:value="formState.port" 
          :min="1" 
          :max="65535" 
          placeholder="请输入端口号"
          style="width: 100%"
        />
      </a-form-item>
      
      <a-form-item
        label="执行间隔(秒)"
        name="interval"
        :rules="[{ required: true, message: '请输入执行间隔' }]"
      >
        <a-input-number 
          v-model:value="formState.interval" 
          :min="10" 
          :max="3600" 
          placeholder="请输入执行间隔(秒)"
        />
      </a-form-item>
      
      <a-form-item label="状态" name="enabled">
        <a-switch 
          v-model:checked="formState.enabled" 
          checked-children="启用" 
          un-checked-children="禁用"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  editingTask: {
    type: Object,
    default: null
  },
  confirmLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'ok', 'cancel'])

// 使用计算属性来绑定modalVisible
const modalVisible = computed({
  get() {
    return props.visible
  },
  set(value) {
    emit('update:visible', value)
  }
})

const formRef = ref()
const formState = reactive({
  name: '',
  type: 'ping',
  target: '',
  port: null,
  interval: 60,
  enabled: true
})

// 监听模态框可见性变化
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    // 重置表单
    formState.name = ''
    formState.type = 'ping'
    formState.target = ''
    formState.port = null
    formState.interval = 60
    formState.enabled = true
  } else {
    // 如果是编辑模式，填充表单
    if (props.editingTask) {
      formState.name = props.editingTask.name
      formState.type = props.editingTask.type
      formState.target = props.editingTask.target
      formState.interval = props.editingTask.interval
      formState.enabled = props.editingTask.enabled
      
      // 如果是TCP任务，解析端口信息
      if (props.editingTask.type === 'tcp') {
        // 尝试从目标地址中提取端口
        const parts = props.editingTask.target.split(':')
        if (parts.length === 2) {
          formState.target = parts[0]
          formState.port = parseInt(parts[1])
        } else {
          formState.port = 80 // 默认端口
        }
      }
    }
  }
})

// 处理任务类型变更
const handleTypeChange = (value) => {
  formState.type = value
  // 如果切换到TCP类型，设置默认端口
  if (value === 'tcp' && !formState.port) {
    formState.port = 80
  }
  // 如果切换到其他类型，清空端口
  else if (value !== 'tcp') {
    formState.port = null
  }
}

// 处理模态框确认
const handleModalOk = async () => {
  try {
    await formRef.value.validateFields()
    
    // 构造请求数据
    let requestData = {
      name: formState.name,
      type: formState.type,
      interval: formState.interval,
      enabled: formState.enabled
    }
    
    // 根据任务类型设置目标地址
    if (formState.type === 'tcp') {
      // TCP任务需要组合目标地址和端口
      requestData.target = `${formState.target}:${formState.port}`
      requestData.config = JSON.stringify({
        timeout: 5
      })
    } else {
      // 其他任务类型直接使用目标地址
      requestData.target = formState.target
      if (formState.type === 'ping') {
        requestData.config = JSON.stringify({
          count: 4
        })
      }
    }
    
    emit('ok', requestData)
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 处理模态框取消
const handleModalCancel = () => {
  emit('cancel')
}
</script>