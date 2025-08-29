<template>
  <div class="api-task-new">
    <!-- API错误提示 -->
    <a-alert
      v-if="apiError.show"
      :message="apiError.message"
      :description="apiError.description"
      type="error"
      show-icon
      closable
      @close="apiError.show = false"
      style="margin-bottom: 16px;"
    />

    <!-- 资源限额显示 -->
    <a-card size="small" style="margin-bottom: 16px;" v-if="quotaInfo">
      <template #title>
        <a-space>
          <ApiOutlined />
          <span>任务资源限额</span>
        </a-space>
      </template>
      <template #extra>
        <a-button size="small" @click="refreshQuota" :loading="quotaLoading">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </template>
      
      <a-row :gutter="16">
        <a-col :span="12">
          <a-statistic
            title="当前任务数"
            :value="quotaInfo.current"
            :suffix="`/ ${quotaInfo.limit}`"
            :value-style="getQuotaValueStyle()"
          >
            <template #prefix>
              <ApiOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :span="12">
          <div style="margin-top: 8px;">
            <a-progress
              :percent="quotaInfo.usage_rate || 0"
              :status="getQuotaProgressStatus()"
              :stroke-color="getQuotaProgressColor()"
            />
            <div style="margin-top: 4px; font-size: 12px; color: #666;">
              使用率: {{ quotaInfo.usage_rate || 0 }}%
            </div>
          </div>
        </a-col>
      </a-row>
      
      <a-alert
        v-if="quotaInfo.usage_rate >= 90"
        message="任务数量即将达到限额，请谨慎创建新任务"
        type="warning"
        show-icon
        style="margin-top: 12px"
      />
     </a-card>
     
     <!-- 超限提示Modal -->
     <a-modal
       v-model:open="quotaModalVisible"
       title="资源限额超限提醒"
       :closable="false"
       :maskClosable="false"
       width="500px"
     >
       <template #footer>
         <a-space>
           <a-button @click="quotaModalVisible = false">取消</a-button>
           <a-button type="primary" @click="goToTenantManagement">管理限额</a-button>
         </a-space>
       </template>
       
       <div style="text-align: center; padding: 20px 0;">
         <a-result
           status="warning"
           title="任务数量已达限额"
           sub-title="当前租户的任务数量已达到限额，无法创建新任务。请联系管理员调整限额或删除不需要的任务。"
         >
           <template #icon>
             <ExclamationCircleOutlined style="color: #faad14;" />
           </template>
         </a-result>
         
         <a-descriptions :column="1" bordered size="small" style="margin-top: 16px;">
           <a-descriptions-item label="当前任务数">
             <a-tag color="orange">{{ quotaInfo?.current || 0 }}</a-tag>
           </a-descriptions-item>
           <a-descriptions-item label="限额">
             <a-tag color="red">{{ quotaInfo?.limit || 0 }}</a-tag>
           </a-descriptions-item>
           <a-descriptions-item label="使用率">
             <a-tag color="red">{{ quotaInfo?.usage_rate || 0 }}%</a-tag>
           </a-descriptions-item>
         </a-descriptions>
       </div>
     </a-modal>
     
     <a-card title="新增API拨测任务">
      <template #extra>
          <a-space>
            <a-button @click="goBack">返回</a-button>
            <a-button 
              type="primary" 
              @click="handleSave" 
              :loading="saving"
              :disabled="isQuotaExceeded"
            >
              保存
            </a-button>
            <a-tooltip v-if="isQuotaExceeded" title="任务数量已达限额，无法创建新任务">
              <ExclamationCircleOutlined style="color: #ff4d4f; margin-left: 8px;" />
            </a-tooltip>
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
import { ArrowLeftOutlined, ApiOutlined, ReloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'
import { createTask } from '@/api/task'
import ApiStepsManager from '@/components/ApiStepsManager.vue'

const router = useRouter()
const formRef = ref()
const saving = ref(false)

// 节点选项
const nodeOptions = ref([])

// 资源限额相关
const quotaInfo = ref(null)
const quotaLoading = ref(false)
const quotaModalVisible = ref(false)

// API错误提示相关
const apiError = reactive({
  show: false,
  message: '',
  description: ''
})

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
    // 显示API错误提示
    apiError.show = true
    apiError.message = '获取节点列表失败'
    apiError.description = '无法获取可用的探测节点，请检查网络连接或联系管理员'
    // 优雅降级：提供默认选项
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
    
    // 检查资源限额
    if (quotaInfo.value && quotaInfo.value.usage_rate >= 100) {
      showQuotaExceededModal()
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
      // 显示API错误提示
      apiError.show = true
      apiError.message = '任务创建失败'
      apiError.description = error.message || '创建任务时发生未知错误，请重试或联系管理员'
    }
  } finally {
    saving.value = false
  }
}

// 表单提交
const handleSubmit = (values) => {
  handleSave()
}

// 获取资源限额数据
const fetchQuotaData = async () => {
  quotaLoading.value = true
  try {
    // 获取当前用户的租户ID
    const userResponse = await request.get('/users/profile')
    const tenantId = userResponse.data.tenant_id
    
    if (!tenantId) {
      console.warn('未找到租户ID')
      return
    }
    
    // 获取租户资源使用情况
    const response = await request.get(`/v2/tenants/${tenantId}/usage`)
    if (response.code === 0 && response.data.usage_stats.tasks) {
      quotaInfo.value = response.data.usage_stats.tasks
    }
  } catch (error) {
    console.error('获取资源限额失败:', error)
    // 显示API错误提示
    apiError.show = true
    apiError.message = '获取资源限额失败'
    apiError.description = '无法获取当前租户的资源使用情况，请刷新页面重试'
  } finally {
    quotaLoading.value = false
  }
}

// 刷新资源限额
const refreshQuota = () => {
  fetchQuotaData()
}

// 获取限额数值样式
const getQuotaValueStyle = () => {
  if (!quotaInfo.value) return {}
  const usageRate = quotaInfo.value.usage_rate || 0
  if (usageRate >= 90) return { color: '#ff4d4f' }
  if (usageRate >= 75) return { color: '#faad14' }
  return { color: '#52c41a' }
}

// 获取进度条状态
const getQuotaProgressStatus = () => {
  if (!quotaInfo.value) return 'success'
  const usageRate = quotaInfo.value.usage_rate || 0
  if (usageRate >= 90) return 'exception'
  if (usageRate >= 75) return 'active'
  return 'success'
}

// 获取进度条颜色
const getQuotaProgressColor = () => {
  if (!quotaInfo.value) return '#52c41a'
  const usageRate = quotaInfo.value.usage_rate || 0
  if (usageRate >= 90) return '#ff4d4f'
  if (usageRate >= 75) return '#faad14'
  return '#52c41a'
}

// 显示超限Modal
const showQuotaExceededModal = () => {
  quotaModalVisible.value = true
}

// 跳转到租户管理页面
const goToTenantManagement = () => {
  quotaModalVisible.value = false
  router.push('/system/tenant')
}

// 组件挂载时获取数据
onMounted(() => {
  fetchNodes()
  fetchQuotaData()
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