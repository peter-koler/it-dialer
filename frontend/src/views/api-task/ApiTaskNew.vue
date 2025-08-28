<template>
  <div class="api-task-new">
    <a-card title="新增API拨测任务">
      <template #extra>
        <a-space>
          <a-button @click="goBack">返回</a-button>
          <a-button type="primary" @click="handleSave" :loading="saving">保存</a-button>
        </a-space>
      </template>
      
      <a-form
        :model="formState"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 20 }"
        ref="formRef"
        @finish="handleSubmit"
      >
        <!-- 基本信息 -->
        <a-card title="基本信息" size="small" style="margin-bottom: 16px;">
          <a-form-item
            label="任务名称"
            name="name"
            :rules="[{ required: true, message: '请输入任务名称' }]"
          >
            <a-input v-model:value="formState.name" placeholder="请输入任务名称" />
          </a-form-item>
          
          <a-form-item
            label="目标地址"
            name="target"
            :rules="[{ required: true, message: '请输入目标地址' }]"
          >
            <a-input v-model:value="formState.target" placeholder="请输入目标地址" />
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
              style="width: 200px;"
            />
          </a-form-item>
          
          <a-form-item
            label="拨测节点"
            name="agentIds"
          >
            <a-select
              v-model:value="formState.agentIds"
              mode="multiple"
              placeholder="请选择拨测节点"
              :options="nodeOptions"
              allowClear
              showSearch
              style="width: 100%;"
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
          
          <a-form-item label="任务状态告警配置" name="statusAlertConfig">
            <a-checkbox-group v-model:value="formState.statusAlertConfig" style="width: 100%">
              <a-checkbox value="failed">失败时告警</a-checkbox>
              <a-checkbox value="success">成功时告警</a-checkbox>
            </a-checkbox-group>
            <div v-if="formState.statusAlertConfig && formState.statusAlertConfig.length > 0" style="margin-top: 8px;">
              <a-form-item label="状态告警级别" :label-col="{span: 6}" :wrapper-col="{span: 18}" style="margin-bottom: 0;">
                <a-select v-model:value="formState.statusAlertLevel" placeholder="选择告警级别" style="width: 120px;">
                  <a-select-option value="severe">严重</a-select-option>
                  <a-select-option value="warning">警告</a-select-option>
                  <a-select-option value="info">信息</a-select-option>
                </a-select>
              </a-form-item>
            </div>
          </a-form-item>
          
          <a-form-item label="超时告警配置" name="timeoutAlert">
            <a-input-group compact>
              <a-checkbox v-model:checked="formState.timeoutAlertEnabled" style="margin-right: 8px;">启用超时告警</a-checkbox>
              <a-input-number 
                v-model:value="formState.timeoutThreshold" 
                :min="1" 
                :max="60000" 
                :disabled="!formState.timeoutAlertEnabled"
                placeholder="超时阈值(毫秒)"
                style="width: 200px;"
              />
            </a-input-group>
            <div v-if="formState.timeoutAlertEnabled" style="margin-top: 8px;">
              <a-form-item label="超时告警级别" :label-col="{span: 6}" :wrapper-col="{span: 18}" style="margin-bottom: 0;">
                <a-select v-model:value="formState.timeoutAlertLevel" placeholder="选择告警级别" style="width: 120px;">
                  <a-select-option value="severe">严重</a-select-option>
                  <a-select-option value="warning">警告</a-select-option>
                  <a-select-option value="info">信息</a-select-option>
                </a-select>
              </a-form-item>
            </div>
          </a-form-item>
        </a-card>
        

        
        <!-- API步骤配置 -->
        <ApiStepsManager v-model="formState.apiSteps" />
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ArrowLeftOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'
import { createTask } from '@/api/task'
import ApiStepsManager from '@/components/ApiStepsManager.vue'

const router = useRouter()
const formRef = ref()
const saving = ref(false)

// 节点选项
const nodeOptions = ref([])

// 表单数据
const formState = reactive({
  name: '',
  type: 'api',
  target: '',
  interval: 60,
  agentIds: [],
  enabled: true,
  apiSteps: [],
  initialVariables: [],
  authentications: [],
  // 新增告警配置字段
  statusAlertConfig: [], // 任务状态告警配置，可选值：['failed', 'success']
  statusAlertLevel: 'warning', // 状态告警级别，默认为警告
  timeoutAlertEnabled: false, // 是否启用超时告警
  timeoutThreshold: 5000, // 超时阈值，单位毫秒
  timeoutAlertLevel: 'warning' // 超时告警级别，默认为警告
})

// 返回列表页
const goBack = () => {
  router.push('/probe-config/task')
}

// 获取节点列表
const fetchNodes = async () => {
  try {
    const response = await request.get('/nodes')
    // 后端返回的数据结构是 {code: 0, data: {list: [...], total: ...}}
    const nodeList = response.data?.list || []
    nodeOptions.value = nodeList.map(node => ({
      label: `${node.hostname || node.agent_id} (${node.agent_area || ''})`,
      value: node.agent_id
    }))
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

// 保存任务
const handleSave = async () => {
  try {
    await formRef.value.validateFields()
    
    // 验证节点选择
    if (formState.agentIds.includes('no-nodes-available')) {
      message.error('请选择有效的探测节点，当前节点服务不可用')
      return
    }
    
    if (!formState.agentIds.length) {
      message.error('请选择至少一个探测节点')
      return
    }
    
    saving.value = true
    
    // 转换字段名和结构以匹配后端API期望的格式
    const taskData = {
      name: formState.name,
      type: formState.type,
      target: formState.target,
      interval: formState.interval,
      enabled: formState.enabled,
      agent_ids: formState.agentIds, // 将agentIds转换为agent_ids
      config: {
        steps: formState.apiSteps,
        initialVariables: formState.initialVariables,
        authentications: formState.authentications,
        // 包含告警配置数据
        statusAlertConfig: formState.statusAlertConfig,
        timeoutAlertEnabled: formState.timeoutAlertEnabled,
        timeoutThreshold: formState.timeoutThreshold
      }
    }
    
    const response = await createTask(taskData)
    if (response.code === 0) {
      message.success('任务创建成功')
      router.push('/probe-task')
    } else {
      message.error('任务创建失败: ' + (response.message || '未知错误'))
    }
  } catch (error) {
    if (error.errorFields) {
      message.error('请检查表单填写是否正确')
    } else {
      message.error('任务创建失败: ' + error.message)
    }
  } finally {
    saving.value = false
  }
}

// 表单提交
const handleSubmit = (values) => {
  handleSave()
}

// 组件挂载时获取数据
onMounted(() => {
  fetchNodes()
})
</script>

<style scoped>
.api-task-new {
  padding: 16px;
}

.node-tip {
  color: #666;
  font-size: 12px;
  margin-top: 4px;
}
</style>