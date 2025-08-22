<template>
  <a-modal
    v-model:visible="modalVisible"
    :title="editingTask ? '编辑任务' : '新增任务'"
    @ok="handleModalOk"
    @cancel="handleModalCancel"
    :confirm-loading="confirmLoading"
    width="600px"
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
      
      <a-form-item
        label="拨测节点"
        name="agentIds"
        :rules="[{ required: false }]"
      >
        <a-select
          v-model:value="formState.agentIds"
          mode="multiple"
          placeholder="请选择拨测节点"
          :options="nodeOptions"
          :filter-option="filterNodeOption"
          allowClear
          showSearch
        >
        </a-select>
        <div class="node-tip">如不选择节点，则所有节点都会执行该任务</div>
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
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'

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

// 节点选项
const nodeOptions = ref([])

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
  agentIds: [],
  enabled: true
})

// 过滤节点选项
const filterNodeOption = (input, option) => {
  return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

// 获取节点列表
const fetchNodes = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/v1/nodes')
    const data = await response.json()
    
    if (data.code === 0) {
      nodeOptions.value = data.data.list
        .filter(node => node.status === 'online') // 只显示在线节点
        .map(node => ({
          label: `${node.name} (${node.agent_id})`,
          value: node.agent_id
        }))
    }
  } catch (error) {
    console.error('获取节点列表失败:', error)
    // 优雅降级：不显示错误提示，提供默认选项
      nodeOptions.value = [{
        label: '暂无可用节点 (请检查节点服务状态)',
        value: 'no-nodes-available',
        disabled: true
      }]
  }
}

// 监听模态框可见性变化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    // 获取节点列表
    fetchNodes()
    
    // 如果是编辑模式，填充表单
    if (props.editingTask) {
      formState.name = props.editingTask.name
      formState.type = props.editingTask.type
      formState.target = props.editingTask.target
      formState.interval = props.editingTask.interval
      formState.enabled = props.editingTask.enabled
      formState.agentIds = props.editingTask.agent_ids || []
      
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
    } else {
      // 新增任务时重置表单
      formState.name = ''
      formState.type = 'ping'
      formState.target = ''
      formState.port = null
      formState.interval = 60
      formState.agentIds = []
      formState.enabled = true
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
      enabled: formState.enabled,
      agent_ids: formState.agentIds
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

// 组件挂载时获取节点列表
onMounted(() => {
  fetchNodes()
})
</script>

<style scoped>
.node-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>