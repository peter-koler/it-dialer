<template>
  <a-modal
    v-model:open="modalVisible"
    :title="editingTask ? '编辑任务' : '新增任务'"
    @ok="handleModalOk"
    @cancel="handleModalCancel"
    :confirm-loading="confirmLoading"
    width="1200px"
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

      <!-- 告警配置 -->
      <a-form-item v-if="formState.type === 'http' || formState.type === 'ping' || formState.type === 'tcp'" :wrapper-col="{ span: 24 }">
        <a-collapse v-model:activeKey="activeKey" accordion>
          <a-collapse-panel key="1" header="告警配置">
            <a-form-item label="启用告警" :label-col="{ span: 3 }" :wrapper-col="{ span: 21 }">
              <a-switch v-model:checked="formState.alarmConfig.enabled" />
            </a-form-item>

            <div v-if="formState.alarmConfig.enabled">
              <!-- HTTP任务的告警配置 -->
              <template v-if="formState.type === 'http'">
                <!-- 状态告警 -->
                <a-card title="状态告警" size="small" style="margin-bottom: 16px;">
                  <template #extra>
                    <a-switch v-model:checked="formState.alarmConfig.rules.status.enabled" size="small" />
                  </template>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="触发条件">
                        当 webstatus 为
                        <a-select v-model:value="formState.alarmConfig.rules.status.condition" :disabled="!formState.alarmConfig.rules.status.enabled" style="width: 100px; margin-left: 8px;">
                          <a-select-option value="异常">异常</a-select-option>
                          <a-select-option value="正常">正常</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="告警级别">
                        <a-select v-model:value="formState.alarmConfig.rules.status.level" :disabled="!formState.alarmConfig.rules.status.enabled" style="width: 120px;">
                          <a-select-option value="notice">通知</a-select-option>
                          <a-select-option value="warning">警告</a-select-option>
                          <a-select-option value="critical">严重</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>
              </template>
              
              <!-- Ping任务的告警配置 -->
              <template v-if="formState.type === 'ping'">
                <!-- Ping状态告警 -->
                <a-card title="Ping状态告警" size="small" style="margin-bottom: 16px;">
                  <template #extra>
                    <a-switch v-model:checked="formState.alarmConfig.rules.status.enabled" size="small" />
                  </template>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="触发条件">
                        当 Ping状态 为
                        <a-select v-model:value="formState.alarmConfig.rules.status.condition" :disabled="!formState.alarmConfig.rules.status.enabled" style="width: 100px; margin-left: 8px;">
                          <a-select-option value="异常">异常</a-select-option>
                          <a-select-option value="正常">正常</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="告警级别">
                        <a-select v-model:value="formState.alarmConfig.rules.status.level" :disabled="!formState.alarmConfig.rules.status.enabled" style="width: 120px;">
                          <a-select-option value="notice">通知</a-select-option>
                          <a-select-option value="warning">警告</a-select-option>
                          <a-select-option value="critical">严重</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>
                
                <!-- 丢包率告警 -->
                <a-card title="丢包率告警" size="small" style="margin-bottom: 16px;">
                  <template #extra>
                    <a-switch v-model:checked="formState.alarmConfig.rules.packet_loss.enabled" size="small" />
                  </template>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="触发条件">
                        当丢包率
                        <a-select v-model:value="formState.alarmConfig.rules.packet_loss.condition" :disabled="!formState.alarmConfig.rules.packet_loss.enabled" style="width: 100px; margin: 0 8px;">
                          <a-select-option value="gt">大于</a-select-option>
                          <a-select-option value="gte">大于等于</a-select-option>
                          <a-select-option value="eq">等于</a-select-option>
                        </a-select>
                        <a-input-number v-model:value="formState.alarmConfig.rules.packet_loss.value" :disabled="!formState.alarmConfig.rules.packet_loss.enabled" style="width: 100px;" :min="0" :max="100" addon-after="%" />
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="告警级别">
                        <a-select v-model:value="formState.alarmConfig.rules.packet_loss.level" :disabled="!formState.alarmConfig.rules.packet_loss.enabled" style="width: 120px;">
                          <a-select-option value="notice">通知</a-select-option>
                          <a-select-option value="warning">警告</a-select-option>
                          <a-select-option value="critical">严重</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>
                
                <!-- 执行时间告警 -->
              <a-card title="执行时间告警" size="small">
                <template #extra>
                  <a-switch v-model:checked="formState.alarmConfig.rules.execution_time.enabled" size="small" />
                </template>
                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="触发条件">
                      当执行时间
                      <a-select v-model:value="formState.alarmConfig.rules.execution_time.condition" :disabled="!formState.alarmConfig.rules.execution_time.enabled" style="width: 100px; margin: 0 8px;">
                        <a-select-option value="gt">大于</a-select-option>
                        <a-select-option value="gte">大于等于</a-select-option>
                        <a-select-option value="lt">小于</a-select-option>
                        <a-select-option value="lte">小于等于</a-select-option>
                      </a-select>
                      <a-input-number v-model:value="formState.alarmConfig.rules.execution_time.value" :disabled="!formState.alarmConfig.rules.execution_time.enabled" style="width: 100px;" :min="0" addon-after="ms" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="告警级别">
                      <a-select v-model:value="formState.alarmConfig.rules.execution_time.level" :disabled="!formState.alarmConfig.rules.execution_time.enabled" style="width: 120px;">
                        <a-select-option value="notice">通知</a-select-option>
                        <a-select-option value="warning">警告</a-select-option>
                        <a-select-option value="critical">严重</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>
              </a-card>
              </template>
              
              <!-- TCP任务的告警配置 -->
              <template v-if="formState.type === 'tcp'">
                <!-- TCP状态告警 -->
                <a-card title="TCP状态告警" size="small" style="margin-bottom: 16px;">
                  <template #extra>
                    <a-switch v-model:checked="formState.alarmConfig.rules.status.enabled" size="small" />
                  </template>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="触发条件">
                        当 TCP状态 为
                        <a-select v-model:value="formState.alarmConfig.rules.status.condition" :disabled="!formState.alarmConfig.rules.status.enabled" style="width: 100px; margin-left: 8px;">
                          <a-select-option value="异常">异常</a-select-option>
                          <a-select-option value="正常">正常</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="告警级别">
                        <a-select v-model:value="formState.alarmConfig.rules.status.level" :disabled="!formState.alarmConfig.rules.status.enabled" style="width: 120px;">
                          <a-select-option value="notice">通知</a-select-option>
                          <a-select-option value="warning">警告</a-select-option>
                          <a-select-option value="critical">严重</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>
                
                <!-- 执行时间告警 -->
                <a-card title="执行时间告警" size="small">
                  <template #extra>
                    <a-switch v-model:checked="formState.alarmConfig.rules.execution_time.enabled" size="small" />
                  </template>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="触发条件">
                        当执行时间
                        <a-select v-model:value="formState.alarmConfig.rules.execution_time.condition" :disabled="!formState.alarmConfig.rules.execution_time.enabled" style="width: 100px; margin: 0 8px;">
                          <a-select-option value="gt">大于</a-select-option>
                          <a-select-option value="gte">大于等于</a-select-option>
                          <a-select-option value="lt">小于</a-select-option>
                          <a-select-option value="lte">小于等于</a-select-option>
                        </a-select>
                        <a-input-number v-model:value="formState.alarmConfig.rules.execution_time.value" :disabled="!formState.alarmConfig.rules.execution_time.enabled" style="width: 100px;" :min="0" addon-after="ms" />
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="告警级别">
                        <a-select v-model:value="formState.alarmConfig.rules.execution_time.level" :disabled="!formState.alarmConfig.rules.execution_time.enabled" style="width: 120px;">
                          <a-select-option value="notice">通知</a-select-option>
                          <a-select-option value="warning">警告</a-select-option>
                          <a-select-option value="critical">严重</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>
              </template>

              <!-- HTTP任务特有的告警配置 -->
              <template v-if="formState.type === 'http'">
                <!-- 返回代码告警 -->
                <a-card title="返回代码告警" size="small" style="margin-bottom: 16px;">
                  <template #extra>
                    <a-switch v-model:checked="formState.alarmConfig.rules.response_code.enabled" size="small" />
                  </template>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="触发条件">
                        当返回代码
                        <a-select v-model:value="formState.alarmConfig.rules.response_code.condition" :disabled="!formState.alarmConfig.rules.response_code.enabled" style="width: 100px; margin: 0 8px;">
                          <a-select-option value="eq">等于</a-select-option>
                          <a-select-option value="neq">不等于</a-select-option>
                          <a-select-option value="gt">大于</a-select-option>
                        </a-select>
                        <a-input-number v-model:value="formState.alarmConfig.rules.response_code.value" :disabled="!formState.alarmConfig.rules.response_code.enabled" style="width: 100px;" />
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="告警级别">
                        <a-select v-model:value="formState.alarmConfig.rules.response_code.level" :disabled="!formState.alarmConfig.rules.response_code.enabled" style="width: 120px;">
                          <a-select-option value="notice">通知</a-select-option>
                          <a-select-option value="warning">警告</a-select-option>
                          <a-select-option value="critical">严重</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>

                <!-- 响应时间告警 -->
                <a-card title="响应时间告警" size="small" style="margin-bottom: 16px;">
                  <template #extra>
                    <a-switch v-model:checked="formState.alarmConfig.rules.response_time.enabled" size="small" />
                  </template>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="触发条件">
                        当响应时间
                        <a-select v-model:value="formState.alarmConfig.rules.response_time.condition" :disabled="!formState.alarmConfig.rules.response_time.enabled" style="width: 100px; margin: 0 8px;">
                          <a-select-option value="gt">大于</a-select-option>
                          <a-select-option value="lt">小于</a-select-option>
                          <a-select-option value="eq">等于</a-select-option>
                        </a-select>
                        <a-input-number v-model:value="formState.alarmConfig.rules.response_time.value" :disabled="!formState.alarmConfig.rules.response_time.enabled" style="width: 100px;" addon-after="ms" />
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="告警级别">
                        <a-select v-model:value="formState.alarmConfig.rules.response_time.level" :disabled="!formState.alarmConfig.rules.response_time.enabled" style="width: 120px;">
                          <a-select-option value="notice">通知</a-select-option>
                          <a-select-option value="warning">警告</a-select-option>
                          <a-select-option value="critical">严重</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>

                <!-- DNS IP 告警 -->
                <a-card title="DNS IP 告警" size="small">
                  <template #extra>
                    <a-switch v-model:checked="formState.alarmConfig.rules.dns_ip.enabled" size="small" />
                  </template>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="触发条件">
                        当 DNS IP 不在期望列表中
                      </a-form-item>
                      <a-select
                        mode="tags"
                        style="width: 100%"
                        placeholder="输入期望的IP地址，按回车确认"
                        v-model:value="formState.alarmConfig.rules.dns_ip.expected_ips"
                        :disabled="!formState.alarmConfig.rules.dns_ip.enabled"
                      >
                      </a-select>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="告警级别">
                        <a-select v-model:value="formState.alarmConfig.rules.dns_ip.level" :disabled="!formState.alarmConfig.rules.dns_ip.enabled" style="width: 120px;">
                          <a-select-option value="notice">通知</a-select-option>
                          <a-select-option value="warning">警告</a-select-option>
                          <a-select-option value="critical">严重</a-select-option>
                        </a-select>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </a-card>
              </template>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </a-form-item>
    </a-form>
  </a-modal>
  

</template>

<script setup>
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, UpOutlined, DownOutlined, SettingOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'


const props = defineProps({
  open: {
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

const emit = defineEmits(['update:open', 'ok', 'cancel'])

// 节点选项
const nodeOptions = ref([])

// 使用计算属性来绑定modalVisible
const modalVisible = computed({
  get() {
    return props.open
  },
  set(value) {
    emit('update:open', value)
  }
})

const formRef = ref()

// 响应式数据
const formState = reactive({
  name: '',
  type: 'ping',
  target: '',
  port: null,
  interval: 60,
  agentIds: [],
  enabled: true,
  alarmConfig: {
    enabled: false,
    rules: {
      status: { enabled: false, condition: '异常', level: 'warning' },
      packet_loss: { enabled: false, condition: 'gt', value: 10, level: 'warning' },
      execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
    }
  }
})

const activeKey = ref('1');



// 过滤节点选项
const filterNodeOption = (input, option) => {
  return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

// 获取节点列表
const fetchNodes = async () => {
  try {
    const response = await request.get('/nodes')
    
    // 确保response.data和response.data.list存在
    if (response && response.data && response.data.list) {
      nodeOptions.value = response.data.list
        .filter(node => node.status === 'online') // 只显示在线节点
        .map(node => ({
          label: `${node.name} (${node.agent_id})`,
          value: node.agent_id
        }))
    } else {
      // 数据格式不正确时的处理
      nodeOptions.value = [{
        label: '暂无可用节点 (数据格式错误)',
        value: 'no-nodes-available',
        disabled: true
      }]
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
watch(() => props.open, (newVal) => {
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
      
      // 填充告警配置
      if (props.editingTask.alarm_config) {
        formState.alarmConfig = JSON.parse(JSON.stringify(props.editingTask.alarm_config))
      } else {
        // 如果没有，则重置为默认值
        if (props.editingTask.type === 'ping') {
          formState.alarmConfig = {
            enabled: false,
            rules: {
              status: { enabled: false, condition: '异常', level: 'warning' },
              packet_loss: { enabled: false, condition: 'gt', value: 10, level: 'warning' },
              execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
            }
          }
        } else if (props.editingTask.type === 'tcp') {
          formState.alarmConfig = {
            enabled: false,
            rules: {
              status: { enabled: false, condition: '异常', level: 'warning' },
              execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
            }
          }
        } else {
          formState.alarmConfig = {
            enabled: false,
            rules: {
              status: { enabled: false, condition: '异常', level: 'warning' },
              response_code: { enabled: false, condition: 'eq', value: 404, level: 'warning' },
              response_time: { enabled: false, condition: 'gt', value: 1000, level: 'warning' },
              dns_ip: { enabled: false, expected_ips: [], level: 'warning' },
              packet_loss: { enabled: false, condition: 'gt', value: 10, level: 'warning' },
              execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
            }
          }
        }
      }

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
      // 重置告警配置 - 根据任务类型设置不同的默认配置
      if (formState.type === 'ping') {
        formState.alarmConfig = {
          enabled: false,
          rules: {
            status: { enabled: false, condition: '异常', level: 'warning' },
            packet_loss: { enabled: false, condition: 'gt', value: 10, level: 'warning' },
            execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
          }
        }
      } else if (formState.type === 'tcp') {
        formState.alarmConfig = {
          enabled: false,
          rules: {
            status: { enabled: false, condition: '异常', level: 'warning' },
            execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
          }
        }
      } else {
        formState.alarmConfig = {
          enabled: false,
          rules: {
            status: { enabled: false, condition: '异常', level: 'warning' },
            response_code: { enabled: false, condition: 'eq', value: 404, level: 'warning' },
            response_time: { enabled: false, condition: 'gt', value: 1000, level: 'warning' },
            dns_ip: { enabled: false, expected_ips: [], level: 'warning' },
            packet_loss: { enabled: false, condition: 'gt', value: 10, level: 'warning' },
            execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
          }
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
  
  // 根据任务类型重置告警配置
  if (value === 'ping') {
    formState.alarmConfig = {
      enabled: false,
      rules: {
        status: { enabled: false, condition: '异常', level: 'warning' },
        packet_loss: { enabled: false, condition: 'gt', value: 10, level: 'warning' },
        execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
      }
    }
  } else {
    formState.alarmConfig = {
      enabled: false,
      rules: {
        status: { enabled: false, condition: '异常', level: 'warning' },
        response_code: { enabled: false, condition: 'eq', value: 404, level: 'warning' },
        response_time: { enabled: false, condition: 'gt', value: 1000, level: 'warning' },
        dns_ip: { enabled: false, expected_ips: [], level: 'warning' },
        packet_loss: { enabled: false, condition: 'gt', value: 10, level: 'warning' },
        execution_time: { enabled: false, condition: 'gt', value: 5000, level: 'warning' }
      }
    }
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
    
    // 根据任务类型设置目标地址和配置
    if (formState.type === 'http') {
      requestData.target = formState.target
      requestData.alarm_config = JSON.parse(JSON.stringify(formState.alarmConfig))
    } else if (formState.type === 'tcp') {
      // TCP任务需要组合目标地址和端口
      requestData.target = `${formState.target}:${formState.port}`
      requestData.config = JSON.stringify({
        timeout: 5
      })
      // TCP任务的告警配置
      requestData.alarm_config = JSON.parse(JSON.stringify(formState.alarmConfig))
    } else {
      // 其他任务类型直接使用目标地址
      requestData.target = formState.target
      if (formState.type === 'ping') {
        requestData.config = JSON.stringify({
          count: 4
        })
        // ping任务的告警配置
        requestData.alarm_config = JSON.parse(JSON.stringify(formState.alarmConfig))
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