<template>
  <a-card title="API步骤配置" size="small" style="margin-bottom: 16px;">
    <div class="api-steps-container">
      <div v-for="(step, index) in steps" :key="index" class="api-step-item">
        <a-card :title="`步骤 ${index + 1}: ${step.name || '未命名步骤'}`" size="small">
          <template #extra>
            <a-space>
              <a-button type="text" size="small" @click="moveStep(index, -1)" :disabled="index === 0">
                <template #icon><up-outlined /></template>
              </a-button>
              <a-button type="text" size="small" @click="moveStep(index, 1)" :disabled="index === steps.length - 1">
                <template #icon><down-outlined /></template>
              </a-button>
              <a-button type="text" size="small" danger @click="removeStep(index)">
                <template #icon><delete-outlined /></template>
              </a-button>
            </a-space>
          </template>
          
          <a-form layout="vertical">
            <a-form-item label="步骤名称" required>
              <a-input v-model:value="step.name" placeholder="请输入步骤名称" />
            </a-form-item>
            
            <a-form-item label="请求方法" required>
              <a-select v-model:value="step.request.method">
                <a-select-option value="GET">GET</a-select-option>
                <a-select-option value="POST">POST</a-select-option>
                <a-select-option value="PUT">PUT</a-select-option>
                <a-select-option value="DELETE">DELETE</a-select-option>
                <a-select-option value="HEAD">HEAD</a-select-option>
                <a-select-option value="OPTIONS">OPTIONS</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="请求URL" required>
              <a-input
                v-model:value="step.request.url"
                placeholder="请求URL（支持变量，如：https://api.example.com/users/$userId）"
                @blur="onUrlChange(index)"
              />
            </a-form-item>
            
            <a-collapse>
              <a-collapse-panel key="urlParams" header="URL参数">
                <div class="url-params-actions" style="margin-bottom: 12px;">
                  <a-space>
                    <a-button type="primary" size="small" @click="addUrlParameter(index)">
                      <template #icon><plus-outlined /></template>
                      添加URL参数
                    </a-button>
                    <a-button type="default" size="small" @click="parseUrlParameters(index)" :disabled="!hasUrlParameters(step.request.url)">
                      <template #icon><thunderbolt-outlined /></template>
                      参数自动解析
                    </a-button>
                  </a-space>
                </div>
                <div v-for="(param, paramIndex) in step.request.urlParameters" :key="paramIndex" class="url-param-item">
                  <a-input v-model:value="param.key" placeholder="参数名" style="width: 40%" @input="syncUrlParametersToParams(index)" />
                  <a-input v-model:value="param.value" placeholder="参数值" style="width: 50%" @input="syncUrlParametersToParams(index)" />
                  <a-button type="text" danger @click="removeUrlParameter(index, paramIndex)">
                    <template #icon><delete-outlined /></template>
                  </a-button>
                </div>
                <div v-if="step.request.urlParameters && step.request.urlParameters.length === 0" class="empty-params-hint">
                  <a-empty :image="false" description="暂无URL参数" />
                </div>
              </a-collapse-panel>
              
              <a-collapse-panel key="headers" header="请求头">
                <div v-for="(header, headerIndex) in step.request.headers" :key="headerIndex" class="header-item">
                  <a-input v-model:value="header.key" placeholder="Header名称" style="width: 40%" />
                  <a-input v-model:value="header.value" placeholder="Header值" style="width: 50%" />
                  <a-button type="text" danger @click="removeHeader(index, headerIndex)">
                    <template #icon><delete-outlined /></template>
                  </a-button>
                </div>
                <a-button type="dashed" block @click="addHeader(index)">
                  <template #icon><plus-outlined /></template>
                  添加请求头
                </a-button>
              </a-collapse-panel>
              
              <a-collapse-panel key="body" header="请求体" v-if="['POST', 'PUT'].includes(step.request.method)">
                <a-form-item label="Content-Type">
                  <a-select v-model:value="step.request.contentType" placeholder="请选择Content-Type">
                    <a-select-option value="application/json">application/json</a-select-option>
                    <a-select-option value="application/x-www-form-urlencoded">application/x-www-form-urlencoded</a-select-option>
                    <a-select-option value="text/plain">text/plain</a-select-option>
                  </a-select>
                </a-form-item>
                
                <a-form-item label="请求体内容">
                  <a-textarea 
                    v-model:value="step.request.body" 
                    placeholder="请输入请求体内容，支持使用$变量" 
                    :auto-size="{ minRows: 3, maxRows: 6 }" 
                  />
                </a-form-item>
              </a-collapse-panel>
              
              <a-collapse-panel key="variables" header="变量提取">
                <div v-for="(variable, varIndex) in step.variables" :key="varIndex" class="variable-item">
                  <a-input v-model:value="variable.name" placeholder="变量名称 (以$开头)" style="width: 30%" />
                  <a-select v-model:value="variable.source" style="width: 25%">
                    <a-select-option value="body">响应体</a-select-option>
                    <a-select-option value="headers">响应头</a-select-option>
                    <a-select-option value="status">状态码</a-select-option>
                    <a-select-option value="cookie">Cookie</a-select-option>
                    <a-select-option value="url">响应URL</a-select-option>
                  </a-select>
                  <a-input v-model:value="variable.expression" placeholder="提取表达式 (JSONPath或正则)" style="width: 35%" />
                  <a-button type="text" danger @click="removeVariable(index, varIndex)">
                    <template #icon><delete-outlined /></template>
                  </a-button>
                </div>
                <a-button type="dashed" block @click="addVariable(index)">
                  <template #icon><plus-outlined /></template>
                  添加变量提取
                </a-button>
              </a-collapse-panel>
              
              <a-collapse-panel key="assertions" header="断言验证">
                <div v-for="(assertion, assertIndex) in step.assertions" :key="assertIndex" class="assertion-item">
                  <div class="assertion-config">
                    <a-select v-model:value="assertion.source" style="width: 20%">
                      <a-select-option value="body">响应体</a-select-option>
                      <a-select-option value="headers">响应头</a-select-option>
                      <a-select-option value="status">状态码</a-select-option>
                      <a-select-option value="cookie">Cookie</a-select-option>
                      <a-select-option value="time">响应时间</a-select-option>
                      <a-select-option value="size">响应大小</a-select-option>
                    </a-select>
                    <a-input v-model:value="assertion.expression" placeholder="提取表达式" style="width: 25%" />
                    <a-select v-model:value="assertion.operator" style="width: 15%">
                      <a-select-option value="equals">等于</a-select-option>
                      <a-select-option value="not_equals">不等于</a-select-option>
                      <a-select-option value="contains">包含</a-select-option>
                      <a-select-option value="not_contains">不包含</a-select-option>
                      <a-select-option value="startsWith">开头是</a-select-option>
                      <a-select-option value="endsWith">结尾是</a-select-option>
                      <a-select-option value="greater_than">大于</a-select-option>
                      <a-select-option value="less_than">小于</a-select-option>
                      <a-select-option value="regex">匹配正则</a-select-option>
                      <a-select-option value="exists">存在</a-select-option>
                      <a-select-option value="not_exists">不存在</a-select-option>
                    </a-select>
                    <a-input v-model:value="assertion.expected" placeholder="期望值" style="width: 15%" />
                    <a-switch 
                      v-model:checked="assertion.enableAlert" 
                      size="small" 
                      style="margin-left: 8px"
                    />
                    <span style="margin-left: 4px; font-size: 12px; color: #666;">告警</span>
                    <a-button type="text" danger @click="removeAssertion(index, assertIndex)" style="margin-left: 8px">
                      <template #icon><delete-outlined /></template>
                    </a-button>
                  </div>
                  <div v-if="assertion.enableAlert" class="assertion-alert-config">
                    <a-form-item label="告警条件" :label-col="{span: 4}" :wrapper-col="{span: 20}">
                      <a-radio-group v-model:value="assertion.alertCondition" size="small">
                        <a-radio value="match">断言匹配时告警</a-radio>
                        <a-radio value="not_match">断言不匹配时告警</a-radio>
                      </a-radio-group>
                      <div class="form-help-text">选择在什么情况下触发告警</div>
                    </a-form-item>
                    <a-form-item label="断言告警级别" :label-col="{span: 4}" :wrapper-col="{span: 20}">
                      <a-select v-model:value="assertion.alertLevel" placeholder="选择告警级别" style="width: 120px;">
                        <a-select-option value="severe">严重</a-select-option>
                        <a-select-option value="warning">警告</a-select-option>
                        <a-select-option value="info">信息</a-select-option>
                      </a-select>
                    </a-form-item>
                  </div>
                </div>
                <a-button type="dashed" block @click="addAssertion(index)">
                  <template #icon><plus-outlined /></template>
                  添加断言
                </a-button>
              </a-collapse-panel>
              
              <a-collapse-panel key="alerts" header="告警配置">
                <a-form-item label="返回码告警">
                  <a-input 
                    v-model:value="step.alerts.allowedStatusCodes" 
                    placeholder="允许的返回码范围，例如：200、200,201,204 或 2xx" 
                  />
                  <div class="form-help-text">如果API返回码不在允许范围内，则触发告警</div>
                  <div v-if="step.alerts.allowedStatusCodes" style="margin-top: 8px;">
                    <a-form-item label="返回码告警级别" :label-col="{span: 8}" :wrapper-col="{span: 16}" style="margin-bottom: 0;">
                      <a-select v-model:value="step.alerts.statusCodeAlertLevel" placeholder="选择告警级别" style="width: 120px;">
                        <a-select-option value="severe">严重</a-select-option>
                        <a-select-option value="warning">警告</a-select-option>
                        <a-select-option value="info">信息</a-select-option>
                      </a-select>
                    </a-form-item>
                  </div>
                </a-form-item>
                
                <a-form-item label="耗时告警">
                  <a-input-number 
                    v-model:value="step.alerts.responseTimeThreshold" 
                    :min="0" 
                    :step="0.1" 
                    placeholder="响应时间阈值" 
                    style="width: 100%"
                    addon-after="秒"
                  />
                  <div class="form-help-text">如果API响应时间超过阈值，则触发告警</div>
                  <div v-if="step.alerts.responseTimeThreshold && step.alerts.responseTimeThreshold > 0" style="margin-top: 8px;">
                    <a-form-item label="耗时告警级别" :label-col="{span: 8}" :wrapper-col="{span: 16}" style="margin-bottom: 0;">
                      <a-select v-model:value="step.alerts.responseTimeAlertLevel" placeholder="选择告警级别" style="width: 120px;">
                        <a-select-option value="severe">严重</a-select-option>
                        <a-select-option value="warning">警告</a-select-option>
                        <a-select-option value="info">信息</a-select-option>
                      </a-select>
                    </a-form-item>
                  </div>
                </a-form-item>
              </a-collapse-panel>
            </a-collapse>
          </a-form>
        </a-card>
      </div>
      
      <a-button type="dashed" block @click="addStep" style="margin-top: 16px">
        <template #icon><plus-outlined /></template>
        添加步骤
      </a-button>
    </div>
  </a-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { PlusOutlined, DeleteOutlined, UpOutlined, DownOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const steps = ref([...props.modelValue])

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (JSON.stringify(newValue) !== JSON.stringify(steps.value)) {
    steps.value = [...newValue]
    // 确保所有步骤都有完整的结构
    ensureStepStructure()
  }
}, { deep: true })

// 监听steps变化并emit
watch(steps, (newValue) => {
  if (JSON.stringify(newValue) !== JSON.stringify(props.modelValue)) {
    emit('update:modelValue', newValue)
  }
}, { deep: true })

// 创建新步骤的默认结构
const createDefaultStep = () => ({
  step_id: `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  name: '',
  request: {
    method: 'GET',
    url: '',
    headers: [],
    urlParameters: [],
    params: [],
    body: '',
    contentType: 'application/json'
  },
  variables: [],
  assertions: [],
  alerts: {
    allowedStatusCodes: '200',
    statusCodeAlertLevel: 'warning',
    responseTimeThreshold: 5.0,
    responseTimeAlertLevel: 'warning'
  }
})

// 添加步骤
const addStep = () => {
  steps.value.push(createDefaultStep())
}

// 移除步骤
const removeStep = (index) => {
  steps.value.splice(index, 1)
}

// 移动步骤
const moveStep = (index, direction) => {
  const newIndex = index + direction
  if (newIndex >= 0 && newIndex < steps.value.length) {
    const temp = steps.value[index]
    steps.value[index] = steps.value[newIndex]
    steps.value[newIndex] = temp
  }
}

// 添加请求头
const addHeader = (stepIndex) => {
  if (!steps.value[stepIndex].request.headers) {
    steps.value[stepIndex].request.headers = []
  }
  steps.value[stepIndex].request.headers.push({ key: '', value: '' })
}

// 移除请求头
const removeHeader = (stepIndex, headerIndex) => {
  steps.value[stepIndex].request.headers.splice(headerIndex, 1)
}

// 添加变量提取
const addVariable = (stepIndex) => {
  if (!steps.value[stepIndex].variables) {
    steps.value[stepIndex].variables = []
  }
  steps.value[stepIndex].variables.push({
    name: '',
    source: 'body',
    expression: ''
  })
}

// 移除变量提取
const removeVariable = (stepIndex, varIndex) => {
  steps.value[stepIndex].variables.splice(varIndex, 1)
}

// 添加断言
const addAssertion = (stepIndex) => {
  if (!steps.value[stepIndex].assertions) {
    steps.value[stepIndex].assertions = []
  }
  steps.value[stepIndex].assertions.push({
    source: 'status',
    expression: '',
    operator: 'equals',
    expected: '',
    enableAlert: false,
    alertCondition: 'match',
    alertLevel: 'warning'
  })
}

// 移除断言
const removeAssertion = (stepIndex, assertIndex) => {
  steps.value[stepIndex].assertions.splice(assertIndex, 1)
}

// 添加URL参数
const addUrlParameter = (stepIndex) => {
  if (!steps.value[stepIndex].request.urlParameters) {
    steps.value[stepIndex].request.urlParameters = []
  }
  if (!steps.value[stepIndex].request.params) {
    steps.value[stepIndex].request.params = []
  }
  
  const newParam = { key: '', value: '' }
  steps.value[stepIndex].request.urlParameters.push(newParam)
  steps.value[stepIndex].request.params.push(newParam)
}

// 移除URL参数
const removeUrlParameter = (stepIndex, paramIndex) => {
  steps.value[stepIndex].request.urlParameters.splice(paramIndex, 1)
  if (steps.value[stepIndex].request.params) {
    steps.value[stepIndex].request.params.splice(paramIndex, 1)
  }
}

// 检查URL是否包含参数
const hasUrlParameters = (url) => {
  if (!url) return false
  return url.includes('?') && url.includes('=')
}

// 解析URL参数
const parseUrlParameters = (stepIndex) => {
  const url = steps.value[stepIndex].request.url
  if (!url || !hasUrlParameters(url)) return
  
  try {
    const urlObj = new URL(url)
    const params = []
    
    urlObj.searchParams.forEach((value, key) => {
      params.push({ key, value })
    })
    
    if (params.length > 0) {
      steps.value[stepIndex].request.urlParameters = params
      steps.value[stepIndex].request.params = params
      // 移除URL中的参数部分，保留基础URL
      steps.value[stepIndex].request.url = url.split('?')[0]
    }
  } catch (error) {
    console.warn('URL解析失败:', error)
  }
}

// URL变化时的处理
const onUrlChange = (stepIndex) => {
  // 可以在这里添加URL变化时的逻辑
}

// 同步URL参数到params字段
const syncUrlParametersToParams = (stepIndex) => {
  const step = steps.value[stepIndex]
  if (step.request.urlParameters) {
    step.request.params = [...step.request.urlParameters]
  }
}

// 确保所有步骤都有完整的结构
const ensureStepStructure = () => {
  steps.value.forEach(step => {
    // 确保有step_id
    if (!step.step_id) {
      step.step_id = `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    }
    
    // 确保有alerts对象
    if (!step.alerts) {
      step.alerts = {
        allowedStatusCodes: '200',
        responseTimeThreshold: 5.0
      }
    }
    
    // 确保alerts对象有所有必需的属性
    if (!step.alerts.allowedStatusCodes) {
      step.alerts.allowedStatusCodes = '200'
    }
    if (!step.alerts.responseTimeThreshold) {
      step.alerts.responseTimeThreshold = 5.0
    }
    
    // 确保有request对象
    if (!step.request) {
      step.request = {
        method: 'GET',
        url: '',
        headers: [],
        urlParameters: [],
        params: [],
        body: '',
        contentType: 'application/json'
      }
    }
    
    // 确保request对象有所有必需的属性
    if (!step.request.headers) step.request.headers = []
    if (!step.request.urlParameters) step.request.urlParameters = []
    if (!step.request.params) step.request.params = []
    if (!step.variables) step.variables = []
    if (!step.assertions) step.assertions = []
  })
}

// 初始化时确保所有步骤都有完整的结构
ensureStepStructure()

// 初始化时如果没有步骤，添加一个默认步骤
if (steps.value.length === 0) {
  addStep()
}
</script>

<style scoped>
.api-steps-container {
  width: 100%;
}

.api-step-item {
  margin-bottom: 16px;
}

.header-item,
.variable-item,
.assertion-item,
.url-param-item {
  margin-bottom: 12px;
}

.assertion-config {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.assertion-alert-config {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
  margin-top: 8px;
}

.header-item:last-child,
.variable-item:last-child,
.assertion-item:last-child,
.url-param-item:last-child {
  margin-bottom: 0;
}

.url-params-actions {
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
}

.empty-params-hint {
  text-align: center;
  padding: 20px 0;
  color: #999;
}

.form-help-text {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
  line-height: 1.4;
}
</style>