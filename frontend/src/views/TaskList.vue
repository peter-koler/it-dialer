<script setup>
import { ref, onMounted } from 'vue'
import EnhancedChinaMap from '@/components/EnhancedChinaMap/EnhancedChinaMap.vue'

// 导入配置
import { columns, detailColumns, probeDetailColumns } from './TaskList/config/tableColumns.js'

// 导入 composables
import { useTaskData } from './TaskList/composables/useTaskData.js'
import { useMapData } from './TaskList/composables/useMapData.js'
import { useCharts } from './TaskList/composables/useCharts.js'
import { useModals } from './TaskList/composables/useModals.js'

// 使用 composables
const {
  aggregatedResults,
  loading,
  pagination,
  searchParams,
  formatDate,
  formatDetails,
  getRowClassName,
  fetchResults,
  handleSearch,
  handleStatusChange,
  handleTableChange
} = useTaskData()

const {
  mapData,
  mapLevel,
  selectedMapCode,
  generateMapData,
  handleRegionClick,
  handleLevelChange,
  resetMapState
} = useMapData()

const {
  probeDetailChart,
  renderLatencyChart,
  renderTcpCharts,
  renderProbeDetailChart
} = useCharts()

const {
  detailModalVisible,
  probeDetailVisible,
  selectedTask,
  selectedProbe,
  probeDetails,
  showDetails,
  showProbeDetail,
  handleDetailModalCancel,
  handleProbeDetailCancel
} = useModals()

// 地图引用
const chinaMapRef = ref(null)

// 包装显示详情方法
const handleShowDetails = (record) => {
  showDetails(record, {
    generateMapData,
    resetMapState,
    renderLatencyChart,
    renderTcpCharts,
    chinaMapRef,
    mapData
  })
}

// 包装显示拨测点详情方法
const handleShowProbeDetail = (record) => {
  showProbeDetail(record, {
    renderProbeDetailChart
  })
}

// 包装详情模态框取消方法
const handleDetailCancel = () => {
  handleDetailModalCancel({ resetMapState })
}

// 组件挂载时获取数据
onMounted(() => {
  fetchResults()
})
</script>

<template>
  <div>
    <a-card title="任务结果列表">
      <!-- 搜索栏 -->
      <a-row :gutter="16" style="margin-bottom: 16px;">
        <a-col :span="6">
          <a-input-search 
            v-model:value="searchParams.keyword" 
            placeholder="搜索任务名称" 
            enter-button 
            @search="handleSearch" 
          />
        </a-col>
        <a-col :span="6">
          <a-select 
            v-model:value="searchParams.status" 
            placeholder="选择状态" 
            style="width: 100%" 
            allow-clear
            @change="handleStatusChange"
          >
            <a-select-option value="success">成功</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
            <a-select-option value="timeout">超时</a-select-option>
          </a-select>
        </a-col>
      </a-row>
      
      <a-table
        :dataSource="aggregatedResults"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        :rowKey="(record) => record.id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'status'">
            <a-tag :color="record.status === 'success' ? 'green' : record.status === 'failed' ? 'red' : 'orange'">
              {{ record.status === 'success' ? '成功' : record.status === 'failed' ? '失败' : '超时' }}
            </a-tag>
          </template>
          <template v-else-if="column.dataIndex === 'response_time'">
            {{ record.response_time ? record.response_time.toFixed(2) + ' ms' : '-' }}
          </template>
          <template v-else-if="column.dataIndex === 'details'">
            <a-button type="link" @click="handleShowDetails(record)">查看详情</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 详情模态框 -->
    <a-modal
      v-model:visible="detailModalVisible"
      title="任务详情"
      width="90%"
      @cancel="handleDetailCancel"
      :footer="null"
    >
      <div v-if="selectedTask">
        <a-row :gutter="16">
          <!-- 左侧：中国地图 -->
          <a-col :span="12">
            <div class="map-container">
              <EnhancedChinaMap
                ref="chinaMapRef"
                :data="mapData"
                :level="mapLevel"
                :selectedCode="selectedMapCode"
                @regionClick="handleRegionClick"
                @levelChange="handleLevelChange"
              />
            </div>
          </a-col>
          
          <!-- 右侧：拨测点列表 -->
          <a-col :span="12">
            <div class="probe-list-container">
              <h4>拨测点列表</h4>
              <a-table
                :dataSource="aggregatedResults"
                :columns="detailColumns"
                :pagination="false"
                size="small"
                :rowKey="(record) => record.id"
                :rowClassName="getRowClassName"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.dataIndex === 'location'">
                    {{ record.location }}
                  </template>
                  <template v-else-if="column.dataIndex === 'time'">
                    {{ formatDate(record.created_at) }}
                  </template>
                  <template v-else-if="column.dataIndex === 'responseTime'">
                    {{ record.response_time ? record.response_time.toFixed(2) + ' ms' : '-' }}
                  </template>
                  <template v-else-if="column.dataIndex === 'status'">
                    <a-tag :color="record.status === 'success' ? 'green' : record.status === 'failed' ? 'red' : 'orange'">
                      {{ record.status === 'success' ? '成功' : record.status === 'failed' ? '失败' : '超时' }}
                    </a-tag>
                  </template>
                  <template v-else-if="column.dataIndex === 'actions'">
                    <a-button type="link" size="small" @click="handleShowProbeDetail(record)">详情</a-button>
                  </template>
                </template>
              </a-table>
            </div>
          </a-col>
        </a-row>
        
        <!-- 图表区域 -->
        <a-row style="margin-top: 16px;">
          <a-col :span="24">
            <div v-if="selectedTask.task.type === 'ping'">
              <div id="latency-chart" class="chart-container"></div>
            </div>
            <div v-else-if="selectedTask.task.type === 'tcp'">
              <a-row :gutter="16">
                <a-col :span="8">
                  <div id="tcp-connected-chart" class="chart-container"></div>
                </a-col>
                <a-col :span="8">
                  <div id="tcp-response-time-chart" class="chart-container"></div>
                </a-col>
                <a-col :span="8">
                  <div id="tcp-status-chart" class="chart-container"></div>
                </a-col>
              </a-row>
            </div>
          </a-col>
        </a-row>
      </div>
    </a-modal>

    <!-- 拨测点详情模态框 -->
    <a-modal
      v-model:visible="probeDetailVisible"
      :title="`拨测点详情 - ${selectedProbe?.location || ''}`"
      width="80%"
      @cancel="handleProbeDetailCancel"
      :footer="null"
    >
      <div v-if="selectedProbe">
        <a-row :gutter="16">
          <a-col :span="12">
            <h4>基本信息</h4>
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="位置">{{ selectedProbe.location }}</a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="selectedProbe.status === 'success' ? 'green' : selectedProbe.status === 'failed' ? 'red' : 'orange'">
                  {{ selectedProbe.status === 'success' ? '成功' : selectedProbe.status === 'failed' ? '失败' : '超时' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="响应时间">{{ selectedProbe.response_time ? selectedProbe.response_time.toFixed(2) + ' ms' : '-' }}</a-descriptions-item>
              <a-descriptions-item label="创建时间">{{ formatDate(selectedProbe.created_at) }}</a-descriptions-item>
            </a-descriptions>
          </a-col>
          <a-col :span="12">
            <h4>性能图表</h4>
            <div ref="probeDetailChart" class="chart-container"></div>
          </a-col>
        </a-row>
        
        <a-row style="margin-top: 16px;">
          <a-col :span="24">
            <h4>历史记录</h4>
            <a-table
              :dataSource="probeDetails[selectedProbe.agent_area] || []"
              :columns="probeDetailColumns"
              :pagination="{ pageSize: 10 }"
              size="small"
              :rowKey="(record) => record.id"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'time'">
                  {{ formatDate(record.created_at) }}
                </template>
                <template v-else-if="column.dataIndex === 'responseTime'">
                  {{ record.response_time ? record.response_time.toFixed(2) + ' ms' : '-' }}
                </template>
                <template v-else-if="column.dataIndex === 'status'">
                  <a-tag :color="record.status === 'success' ? 'green' : record.status === 'failed' ? 'red' : 'orange'">
                    {{ record.status === 'success' ? '成功' : record.status === 'failed' ? '失败' : '超时' }}
                  </a-tag>
                </template>
              </template>
            </a-table>
          </a-col>
        </a-row>
        
        <a-row style="margin-top: 16px;">
          <a-col :span="24">
            <h4>原始数据</h4>
            <pre style="background: #f5f5f5; padding: 12px; border-radius: 4px; max-height: 200px; overflow-y: auto;">{{ formatDetails(selectedProbe.details) }}</pre>
          </a-col>
        </a-row>
      </div>
    </a-modal>
  </div>
</template>

<style scoped>
@import './TaskList/styles/TaskList.css';
</style>
