<template>
  <div class="api-task-edit">
    <a-page-header
      title="编辑API拨测任务"
      @back="goBack"
    >
      <template #extra>
        <a-space>
          <a-button @click="goBack">取消</a-button>
          <a-button type="primary" @click="saveTask" :loading="saving">保存任务</a-button>
        </a-space>
      </template>
    </a-page-header>
    
    <div class="content-container">
      <a-spin :spinning="loading">
        <a-row :gutter="24">
          <a-col :span="24">
            <!-- 基本信息 -->
            <a-card title="基本信息" size="small" style="margin-bottom: 16px;">
              <a-form layout="vertical">
                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="任务名称" required>
                      <a-input v-model:value="formData.name" placeholder="请输入任务名称" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="目标地址" required>
                      <a-input v-model:value="formData.target" placeholder="请输入目标地址" />
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-row :gutter="16">
                  <a-col :span="8">
                    <a-form-item label="执行间隔(秒)" required>
                      <a-input-number 
                        v-model:value="formData.interval" 
                        :min="1" 
                        :max="3600" 
                        style="width: 100%"
                        placeholder="执行间隔"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="8">
                    <a-form-item label="探测节点" required>
                      <a-select 
                        v-model:value="formData.agent_ids" 
                        mode="multiple" 
                        placeholder="请选择探测节点"
                        :options="nodeOptions"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="8">
                    <a-form-item label="任务状态">
                      <a-switch 
                        v-model:checked="formData.enabled" 
                        checked-children="启用" 
                        un-checked-children="禁用"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="任务状态告警配置">
                      <a-checkbox-group v-model:value="formData.statusAlertConfig" style="width: 100%">
                        <a-checkbox value="failed">失败时告警</a-checkbox>
                        <a-checkbox value="success">成功时告警</a-checkbox>
                      </a-checkbox-group>
                      <div v-if="formData.statusAlertConfig && formData.statusAlertConfig.length > 0" style="margin-top: 8px;">
                        <a-form-item label="状态告警级别" :label-col="{span: 8}" :wrapper-col="{span: 16}" style="margin-bottom: 0;">
                          <a-select v-model:value="formData.statusAlertLevel" placeholder="选择告警级别" style="width: 120px;">
                            <a-select-option value="severe">严重</a-select-option>
                            <a-select-option value="warning">警告</a-select-option>
                            <a-select-option value="info">信息</a-select-option>
                          </a-select>
                        </a-form-item>
                      </div>
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="超时告警配置">
                      <a-input-group compact>
                        <a-checkbox v-model:checked="formData.timeoutAlertEnabled" style="margin-right: 8px;">启用超时告警</a-checkbox>
                        <a-input-number 
                          v-model:value="formData.timeoutThreshold" 
                          :min="1" 
                          :max="60000" 
                          :disabled="!formData.timeoutAlertEnabled"
                          placeholder="超时阈值(毫秒)"
                          style="width: 150px;"
                        />
                      </a-input-group>
                      <div v-if="formData.timeoutAlertEnabled" style="margin-top: 8px;">
                        <a-form-item label="超时告警级别" :label-col="{span: 8}" :wrapper-col="{span: 16}" style="margin-bottom: 0;">
                          <a-select v-model:value="formData.timeoutAlertLevel" placeholder="选择告警级别" style="width: 120px;">
                            <a-select-option value="severe">严重</a-select-option>
                            <a-select-option value="warning">警告</a-select-option>
                            <a-select-option value="info">信息</a-select-option>
                          </a-select>
                        </a-form-item>
                      </div>
                    </a-form-item>
                  </a-col>
                </a-row>
              </a-form>
            </a-card>
            

            
            <!-- API步骤配置 -->
            <ApiStepsManager v-model="formData.steps" />
          </a-col>
        </a-row>
      </a-spin>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { ArrowLeftOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'
import ApiStepsManager from '@/components/ApiStepsManager.vue'

const router = useRouter()
const route = useRoute()
const taskId = route.params.id

const loading = ref(false)
const saving = ref(false)
const nodeOptions = ref([])

// 表单数据
const formData = ref({
  name: '',
  type: 'api',
  target: '',
  interval: 60,
  agent_ids: [],
  enabled: true,
  variables: [],
  authentication: {
    type: 'none',
    username: '',
    password: '',
    token: '',
    location: 'header',
    keyName: '',
    keyValue: '',
    accessToken: '',
    tokenType: 'Bearer',
    headers: []
  },
  steps: [],
  // 新增告警配置字段
  statusAlertConfig: [], // 任务状态告警配置，可选值：['failed', 'success']
  statusAlertLevel: 'warning', // 状态告警级别，默认为警告
  timeoutAlertEnabled: false, // 是否启用超时告警
  timeoutThreshold: 5000, // 超时阈值，单位毫秒
  timeoutAlertLevel: 'warning' // 超时告警级别，默认为警告
})

// 返回上一页
const goBack = () => {
  router.back()
}

// 获取节点选项
const fetchNodeOptions = async () => {
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

// 获取任务详情
const fetchTaskDetail = async () => {
  if (!taskId) {
    message.error('任务ID不存在')
    router.back()
    return
  }
  
  loading.value = true
  try {
    const response = await request.get(`/tasks/${taskId}`)
    // 后端返回的数据结构是 {code: 0, data: task.to_dict(), message: 'ok'}
    const task = response.data
    
    // 解析config字段中的API配置
    const config = task.config || {}
    
    // 填充表单数据
    formData.value = {
      name: task.name || '',
      type: 'api',
      target: task.target || '',
      interval: task.interval || 60,
      agent_ids: task.agent_ids || [],
      enabled: task.enabled !== false,
      variables: config.variables || [],
      authentication: config.authentication || {
        type: 'none',
        username: '',
        password: '',
        token: '',
        location: 'header',
        keyName: '',
        keyValue: '',
        accessToken: '',
        tokenType: 'Bearer',
        headers: []
      },
      steps: config.steps || [],
      // 加载告警配置数据
      statusAlertConfig: config.statusAlertConfig || [],
      timeoutAlertEnabled: config.timeoutAlertEnabled || false,
      timeoutThreshold: config.timeoutThreshold || 5000
    }
  } catch (error) {
    console.error('获取任务详情失败:', error)
    message.error('获取任务详情失败')
    router.back()
  } finally {
    loading.value = false
  }
}

// 保存任务
const saveTask = async () => {
  // 基本验证
  if (!formData.value.name.trim()) {
    message.error('请输入任务名称')
    return
  }
  
  if (!formData.value.target.trim()) {
    message.error('请输入目标地址')
    return
  }
  
  // 验证节点选择
  if (formData.value.agent_ids.includes('no-nodes-available')) {
    message.error('请选择有效的探测节点，当前节点服务不可用')
    return
  }
  
  if (!formData.value.agent_ids.length) {
    message.error('请选择至少一个探测节点')
    return
  }
  
  if (!formData.value.steps.length) {
    message.error('请至少添加一个API步骤')
    return
  }
  
  // 验证步骤配置
  for (let i = 0; i < formData.value.steps.length; i++) {
    const step = formData.value.steps[i]
    if (!step.name.trim()) {
      message.error(`第${i + 1}个步骤缺少名称`)
      return
    }
    if (!step.request.url.trim()) {
      message.error(`第${i + 1}个步骤缺少请求URL`)
      return
    }
  }
  
  saving.value = true
  try {
    // 构建符合后端期望的数据结构
    const taskData = {
      name: formData.value.name,
      type: formData.value.type,
      target: formData.value.target,
      interval: formData.value.interval,
      enabled: formData.value.enabled,
      agent_ids: formData.value.agent_ids,
      config: {
        steps: formData.value.steps,
        variables: formData.value.variables,
        authentication: formData.value.authentication,
        // 包含告警配置数据
        statusAlertConfig: formData.value.statusAlertConfig,
        timeoutAlertEnabled: formData.value.timeoutAlertEnabled,
        timeoutThreshold: formData.value.timeoutThreshold
      }
    }
    
    const response = await request.put(`/tasks/${taskId}`, taskData)
    if (response.code === 0) {
      message.success('任务更新成功')
      router.push('/probe-config/task')
    } else {
      message.error(response.message || '任务更新失败')
    }
  } catch (error) {
    console.error('更新任务失败:', error)
    message.error('更新任务失败: ' + (error.response?.data?.message || error.message))
  } finally {
    saving.value = false
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchNodeOptions()
  fetchTaskDetail()
})
</script>

<style scoped>
.api-task-edit {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.content-container {
  flex: 1;
  padding: 0 24px 24px;
  overflow-y: auto;
}

:deep(.ant-page-header) {
  background: white;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-card-head) {
  min-height: 40px;
}

:deep(.ant-card-head-title) {
  padding: 8px 0;
  font-size: 14px;
}

:deep(.ant-card-body) {
  padding: 16px;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}

:deep(.ant-tabs-content-holder) {
  padding-top: 16px;
}
</style>