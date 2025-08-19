<template>
  <div class="api-variable-tracker">
    <div class="tracker-header">
      <h4>变量状态</h4>
      <a-space>
        <a-button size="small" @click="showHistory = !showHistory">
          <template #icon>
            <HistoryOutlined />
          </template>
          {{ showHistory ? '隐藏历史' : '显示历史' }}
        </a-button>
        <a-button size="small" @click="exportVariables">
          <template #icon>
            <ExportOutlined />
          </template>
          导出
        </a-button>
      </a-space>
    </div>
    
    <!-- 变量统计 -->
    <div class="variable-stats">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic
            title="总变量数"
            :value="totalVariables"
            :value-style="{ fontSize: '16px' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="已提取"
            :value="extractedVariables"
            :value-style="{ fontSize: '16px', color: '#52c41a' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="提取失败"
            :value="failedExtractions"
            :value-style="{ fontSize: '16px', color: '#ff4d4f' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="未使用"
            :value="unusedVariables"
            :value-style="{ fontSize: '16px', color: '#faad14' }"
          />
        </a-col>
      </a-row>
    </div>
    
    <a-divider />
    
    <!-- 变量搜索和过滤 -->
    <div class="variable-filters">
      <a-row :gutter="16" align="middle">
        <a-col :flex="1">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索变量名或值"
            allow-clear
            @search="handleSearch"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-input-search>
        </a-col>
        <a-col>
          <a-select
            v-model:value="filterStatus"
            placeholder="状态过滤"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="all">全部</a-select-option>
            <a-select-option value="extracted">已提取</a-select-option>
            <a-select-option value="failed">提取失败</a-select-option>
            <a-select-option value="unused">未使用</a-select-option>
          </a-select>
        </a-col>
        <a-col>
          <a-select
            v-model:value="filterType"
            placeholder="类型过滤"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="all">全部类型</a-select-option>
            <a-select-option value="string">字符串</a-select-option>
            <a-select-option value="number">数字</a-select-option>
            <a-select-option value="boolean">布尔值</a-select-option>
            <a-select-option value="object">对象</a-select-option>
            <a-select-option value="array">数组</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </div>
    
    <!-- 变量列表 -->
    <div class="variable-list">
      <a-table
        :dataSource="filteredVariables"
        :columns="variableColumns"
        :pagination="{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
        }"
        size="small"
        :scroll="{ x: 800 }"
        :expandable="{
          expandedRowKeys: expandedRows,
          onExpand: handleRowExpand,
          expandRowByClick: false
        }"
      >
        <!-- 变量名列 -->
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.dataIndex === 'name'">
            <div class="variable-name">
              <a-typography-text 
                :code="true" 
                :copyable="{ text: record.name }"
                :strong="true"
              >
                {{ record.name }}
              </a-typography-text>
              <a-tag 
                v-if="record.source" 
                size="small" 
                :color="getSourceColor(record.source)"
                style="margin-left: 8px"
              >
                {{ getSourceText(record.source) }}
              </a-tag>
            </div>
          </template>
          
          <!-- 当前值列 -->
          <template v-else-if="column.dataIndex === 'currentValue'">
            <div class="variable-value">
              <a-typography-text 
                :copyable="{ text: String(record.currentValue) }"
                :ellipsis="{ tooltip: true }"
                :type="getValueType(record.currentValue)"
              >
                {{ formatValue(record.currentValue) }}
              </a-typography-text>
              <a-tag 
                size="small" 
                :color="getTypeColor(record.valueType)"
                style="margin-left: 8px"
              >
                {{ record.valueType }}
              </a-tag>
            </div>
          </template>
          
          <!-- 状态列 -->
          <template v-else-if="column.dataIndex === 'status'">
            <a-tag :color="getStatusColor(record.status)" size="small">
              <template #icon>
                <CheckOutlined v-if="record.status === 'extracted'" />
                <CloseOutlined v-if="record.status === 'failed'" />
                <ExclamationOutlined v-if="record.status === 'unused'" />
              </template>
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          
          <!-- 提取步骤列 -->
          <template v-else-if="column.dataIndex === 'extractedAt'">
            <span v-if="record.extractedAt !== undefined">
              步骤 {{ record.extractedAt + 1 }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
          
          <!-- 使用次数列 -->
          <template v-else-if="column.dataIndex === 'usageCount'">
            <a-badge 
              :count="record.usageCount || 0" 
              :show-zero="true"
              :number-style="{ backgroundColor: record.usageCount > 0 ? '#52c41a' : '#d9d9d9' }"
            />
          </template>
          
          <!-- 操作列 -->
          <template v-else-if="column.dataIndex === 'actions'">
            <a-space size="small">
              <a-button 
                size="small" 
                type="text" 
                @click="viewVariableHistory(record)"
                :disabled="!showHistory"
              >
                <template #icon><HistoryOutlined /></template>
              </a-button>
              <a-button 
                size="small" 
                type="text" 
                @click="copyVariable(record)"
              >
                <template #icon><CopyOutlined /></template>
              </a-button>
            </a-space>
          </template>
        </template>
        
        <!-- 展开行内容 -->
        <template #expandedRowRender="{ record }">
          <div class="variable-details">
            <a-descriptions :column="2" size="small" bordered>
              <a-descriptions-item label="初始值" v-if="record.initialValue !== undefined">
                <a-typography-text 
                  :copyable="{ text: String(record.initialValue) }"
                  :code="typeof record.initialValue === 'object'"
                >
                  {{ formatValue(record.initialValue) }}
                </a-typography-text>
              </a-descriptions-item>
              
              <a-descriptions-item label="提取表达式" v-if="record.expression">
                <a-typography-text code>
                  {{ record.expression }}
                </a-typography-text>
              </a-descriptions-item>
              
              <a-descriptions-item label="提取来源" v-if="record.extractionSource">
                {{ getExtractionSourceText(record.extractionSource) }}
              </a-descriptions-item>
              
              <a-descriptions-item label="最后更新" v-if="record.lastUpdated">
                {{ formatTime(record.lastUpdated) }}
              </a-descriptions-item>
              
              <a-descriptions-item label="错误信息" v-if="record.error" :span="2">
                <a-alert :message="record.error" type="error" size="small" />
              </a-descriptions-item>
            </a-descriptions>
            
            <!-- 变量历史 -->
            <div v-if="showHistory && record.history && record.history.length > 0" class="variable-history">
              <a-divider orientation="left" style="margin: 16px 0 8px 0">
                <span style="font-size: 12px; color: #666">变化历史</span>
              </a-divider>
              
              <a-timeline size="small">
                <a-timeline-item
                  v-for="(historyItem, index) in record.history"
                  :key="index"
                  :color="historyItem.success ? 'green' : 'red'"
                >
                  <div class="history-item">
                    <div class="history-header">
                      <span class="history-step">步骤 {{ historyItem.stepIndex + 1 }}</span>
                      <span class="history-time">{{ formatTime(historyItem.timestamp) }}</span>
                    </div>
                    <div class="history-content">
                      <span class="history-label">值:</span>
                      <a-typography-text 
                        :code="typeof historyItem.value === 'object'"
                        :type="historyItem.success ? 'success' : 'danger'"
                      >
                        {{ formatValue(historyItem.value) }}
                      </a-typography-text>
                    </div>
                    <div v-if="historyItem.error" class="history-error">
                      <a-alert :message="historyItem.error" type="error" size="small" />
                    </div>
                  </div>
                </a-timeline-item>
              </a-timeline>
            </div>
          </div>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  HistoryOutlined,
  ExportOutlined,
  SearchOutlined,
  CheckOutlined,
  CloseOutlined,
  ExclamationOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'

const props = defineProps({
  variables: {
    type: Object,
    default: () => ({})
  },
  steps: {
    type: Array,
    default: () => []
  }
})

// 响应式数据
const showHistory = ref(false)
const searchText = ref('')
const filterStatus = ref('all')
const filterType = ref('all')
const expandedRows = ref([])

// 计算属性
const processedVariables = computed(() => {
  const variables = []
  
  // 处理最终变量状态
  Object.entries(props.variables || {}).forEach(([name, value]) => {
    const variable = {
      key: name,
      name,
      currentValue: value,
      valueType: getVariableType(value),
      status: 'extracted',
      extractedAt: undefined,
      usageCount: 0,
      initialValue: undefined,
      expression: '',
      extractionSource: '',
      lastUpdated: Date.now(),
      error: null,
      history: [],
      source: 'final'
    }
    
    // 从步骤中查找变量的提取信息
    props.steps.forEach((step, stepIndex) => {
      if (step.extractions) {
        step.extractions.forEach(extraction => {
          if (extraction.variable_name === name) {
            variable.extractedAt = stepIndex
            variable.expression = extraction.expression
            variable.extractionSource = extraction.source
            variable.status = extraction.success ? 'extracted' : 'failed'
            variable.error = extraction.message
            variable.source = 'extraction'
            
            // 添加到历史记录
            variable.history.push({
              stepIndex,
              timestamp: step.start_time || Date.now(),
              value: extraction.extracted_value,
              success: extraction.success,
              error: extraction.message
            })
          }
        })
      }
      
      // 检查变量使用情况（在请求中）
      if (step.request) {
        const requestStr = JSON.stringify(step.request)
        if (requestStr.includes(`{{${name}}}`) || requestStr.includes(`\${${name}}`)) {
          variable.usageCount++
        }
      }
    })
    
    // 如果没有找到提取信息，可能是预设变量
    if (variable.extractedAt === undefined) {
      variable.status = variable.usageCount > 0 ? 'extracted' : 'unused'
      variable.source = 'preset'
    }
    
    variables.push(variable)
  })
  
  // 查找提取失败的变量
  props.steps.forEach((step, stepIndex) => {
    if (step.extractions) {
      step.extractions.forEach(extraction => {
        if (!extraction.success && !variables.find(v => v.name === extraction.variable_name)) {
          variables.push({
            key: `failed-${extraction.variable_name}-${stepIndex}`,
            name: extraction.variable_name,
            currentValue: undefined,
            valueType: 'undefined',
            status: 'failed',
            extractedAt: stepIndex,
            usageCount: 0,
            initialValue: undefined,
            expression: extraction.expression,
            extractionSource: extraction.source,
            lastUpdated: step.start_time || Date.now(),
            error: extraction.message,
            history: [{
              stepIndex,
              timestamp: step.start_time || Date.now(),
              value: undefined,
              success: false,
              error: extraction.message
            }],
            source: 'extraction'
          })
        }
      })
    }
  })
  
  return variables
})

const filteredVariables = computed(() => {
  let filtered = processedVariables.value
  
  // 搜索过滤
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    filtered = filtered.filter(variable => 
      variable.name.toLowerCase().includes(search) ||
      String(variable.currentValue).toLowerCase().includes(search)
    )
  }
  
  // 状态过滤
  if (filterStatus.value && filterStatus.value !== 'all') {
    filtered = filtered.filter(variable => variable.status === filterStatus.value)
  }
  
  // 类型过滤
  if (filterType.value && filterType.value !== 'all') {
    filtered = filtered.filter(variable => variable.valueType === filterType.value)
  }
  
  return filtered
})

const totalVariables = computed(() => processedVariables.value.length)
const extractedVariables = computed(() => 
  processedVariables.value.filter(v => v.status === 'extracted').length
)
const failedExtractions = computed(() => 
  processedVariables.value.filter(v => v.status === 'failed').length
)
const unusedVariables = computed(() => 
  processedVariables.value.filter(v => v.status === 'unused').length
)

// 表格列定义
const variableColumns = [
  {
    title: '变量名',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    fixed: 'left'
  },
  {
    title: '当前值',
    dataIndex: 'currentValue',
    key: 'currentValue',
    width: 250,
    ellipsis: true
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    filters: [
      { text: '已提取', value: 'extracted' },
      { text: '提取失败', value: 'failed' },
      { text: '未使用', value: 'unused' }
    ]
  },
  {
    title: '提取步骤',
    dataIndex: 'extractedAt',
    key: 'extractedAt',
    width: 100,
    sorter: (a, b) => (a.extractedAt || -1) - (b.extractedAt || -1)
  },
  {
    title: '使用次数',
    dataIndex: 'usageCount',
    key: 'usageCount',
    width: 100,
    sorter: (a, b) => a.usageCount - b.usageCount
  },
  {
    title: '操作',
    dataIndex: 'actions',
    key: 'actions',
    width: 100,
    fixed: 'right'
  }
]

// 方法
const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const handleRowExpand = (expanded, record) => {
  if (expanded) {
    expandedRows.value.push(record.key)
  } else {
    const index = expandedRows.value.indexOf(record.key)
    if (index > -1) {
      expandedRows.value.splice(index, 1)
    }
  }
}

const viewVariableHistory = (record) => {
  // 展开行以显示历史
  if (!expandedRows.value.includes(record.key)) {
    expandedRows.value.push(record.key)
  }
}

const copyVariable = async (record) => {
  try {
    const text = `${record.name}: ${formatValue(record.currentValue)}`
    await navigator.clipboard.writeText(text)
    message.success('变量信息已复制到剪贴板')
  } catch (err) {
    message.error('复制失败')
  }
}

const exportVariables = () => {
  const data = filteredVariables.value.map(variable => ({
    变量名: variable.name,
    当前值: formatValue(variable.currentValue),
    类型: variable.valueType,
    状态: getStatusText(variable.status),
    提取步骤: variable.extractedAt !== undefined ? `步骤 ${variable.extractedAt + 1}` : '-',
    使用次数: variable.usageCount,
    提取表达式: variable.expression,
    错误信息: variable.error || '-'
  }))
  
  const csv = convertToCSV(data)
  downloadCSV(csv, `api-variables-${Date.now()}.csv`)
  message.success('变量数据已导出')
}

const getVariableType = (value) => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (Array.isArray(value)) return 'array'
  return typeof value
}

const getValueType = (value) => {
  if (value === null || value === undefined) return 'secondary'
  return 'default'
}

const getTypeColor = (type) => {
  const colors = {
    'string': 'blue',
    'number': 'green',
    'boolean': 'orange',
    'object': 'purple',
    'array': 'cyan',
    'null': 'default',
    'undefined': 'default'
  }
  return colors[type] || 'default'
}

const getStatusColor = (status) => {
  const colors = {
    'extracted': 'success',
    'failed': 'error',
    'unused': 'warning'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    'extracted': '已提取',
    'failed': '提取失败',
    'unused': '未使用'
  }
  return texts[status] || status
}

const getSourceColor = (source) => {
  const colors = {
    'extraction': 'blue',
    'preset': 'green',
    'final': 'purple'
  }
  return colors[source] || 'default'
}

const getSourceText = (source) => {
  const texts = {
    'extraction': '提取',
    'preset': '预设',
    'final': '最终'
  }
  return texts[source] || source
}

const getExtractionSourceText = (source) => {
  const sources = {
    'response_body': '响应体',
    'response_headers': '响应头',
    'status_code': '状态码'
  }
  return sources[source] || source
}

const formatValue = (value) => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

const convertToCSV = (data) => {
  if (!data.length) return ''
  
  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header]
        return typeof value === 'string' && value.includes(',') 
          ? `"${value.replace(/"/g, '""')}"` 
          : value
      }).join(',')
    )
  ].join('\n')
  
  return csvContent
}

const downloadCSV = (csv, filename) => {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.api-variable-tracker {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tracker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tracker-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.variable-stats {
  background: #fafafa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.variable-filters {
  margin-bottom: 16px;
}

.variable-list {
  flex: 1;
  overflow: hidden;
}

.variable-name {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.variable-value {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.text-muted {
  color: #999;
}

.variable-details {
  background: #fafafa;
  padding: 16px;
  border-radius: 6px;
  margin: 8px 0;
}

.variable-history {
  margin-top: 16px;
}

.history-item {
  font-size: 12px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.history-step {
  font-weight: 500;
}

.history-time {
  color: #999;
}

.history-content {
  margin-bottom: 4px;
}

.history-label {
  font-weight: 500;
  margin-right: 8px;
}

.history-error {
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .variable-filters .ant-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .variable-filters .ant-col {
    width: 100%;
  }
}
</style>