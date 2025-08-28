<template>
  <a-modal
    v-model:open="isVisible"
    :title="'任务详情 - ' + (selectedTask?.task?.name || '')"
    width="90%"
    @cancel="handleCancel"
    :footer="null"
    :destroyOnClose="true"
    :z-index="1000"
  >
    <div v-if="selectedTask">
      <a-descriptions bordered size="small" :column="{ xs: 1, sm: 1, md: 2, lg: 3 }">
        <a-descriptions-item label="任务名称">
          {{ selectedTask.task.name }}
        </a-descriptions-item>
        <a-descriptions-item label="任务目标">
          {{ selectedTask.task.target }}
        </a-descriptions-item>
        <a-descriptions-item label="任务类型">
          {{ selectedTask.task.type }}
        </a-descriptions-item>
        <a-descriptions-item label="执行次数">
          {{ selectedTask.count }}
        </a-descriptions-item>
        <a-descriptions-item label="平均响应时间">
          <span v-if="selectedTask.avgResponseTime">{{ selectedTask.avgResponseTime.toFixed(2) }} ms</span>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="最新状态">
          <StatusTag :status="selectedTask.latestStatus" />
        </a-descriptions-item>
      </a-descriptions>
      
      <!-- 添加时间选择控件和刷新按钮 - 仅对ping和tcp类型显示 -->
      <div v-if="selectedTask.task.type !== 'api'" style="margin: 16px 0; display: flex; justify-content: space-between; align-items: center;">
        <TimeRangePicker 
          v-model="selectedTimeRange" 
          @change="handleTimeRangeChange" 
        />
        <a-button type="primary" @click="refreshData">刷新</a-button>
      </div>
      <!-- API任务类型的刷新按钮 -->
      <div v-else style="margin: 16px 0; display: flex; justify-content: flex-end; align-items: center;">
        <a-button type="primary" @click="refreshData">刷新</a-button>
      </div>
      
      <a-row :gutter="16" style="margin-top: 20px;">
        <!-- 左侧地图区域 - 仅对ping和tcp类型显示 -->
      <template v-if="selectedTask.task.type !== 'api'">
        <a-col :span="14">
          <a-card class="map-container">
            <a-spin :spinning="probeDataLoading">
              <EnhancedChinaMap 
                ref="chinaMapRef"
                :mapData="mapData"
                :level="mapLevel"
                :selectedCode="selectedMapCode"
                @region-click="handleRegionClick"
                @level-change="handleLevelChange"
                height="500px"
              />
            </a-spin>
          </a-card>
        </a-col>
        
        <!-- 右侧拨测点列表 -->
        <a-col :span="10">
          <a-card title="拨测点详情列表" class="probe-list-container">
            <ProbeList 
              :results="filteredResults"
              @show-probe-detail="showProbeDetail"
            />
          </a-card>
        </a-col>
      </template>
      </a-row>
      
      <!-- 图表展示区域 -->
      <TaskCharts 
        :task-type="selectedTask.task.type"
        :results="filteredResults"
      />
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import EnhancedChinaMap from '@/components/EnhancedChinaMap/EnhancedChinaMap.vue'
import StatusTag from './StatusTag.vue'
import ProbeList from './ProbeList.vue'
import TaskCharts from './TaskCharts.vue'
import TimeRangePicker from './TimeRangePicker.vue'
import { useProbeData } from './useProbeData'
import { getTaskResults } from '@/api/task'

const props = defineProps({
  open: {
    type: Boolean,
    required: true
  },
  selectedTask: {
    type: Object,
    default: null
  },
  mapData: {
    type: Array,
    default: () => []
  },
  mapLevel: {
    type: String,
    default: 'country'
  },
  selectedMapCode: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:open', 'cancel', 'region-click', 'level-change', 'show-probe-detail'])

const chinaMapRef = ref(null)
const isVisible = ref(props.open)
const selectedTimeRange = ref([])
const filteredResults = ref([])

// 使用组合式函数获取探针数据
const {
  loading: probeDataLoading,
  tableData,
  chartData,
  fetchProbeData
} = useProbeData(
  computed(() => props.selectedTask?.task?.id),
  computed(() => {
    if (selectedTimeRange.value && selectedTimeRange.value.length === 2) {
      return {
        start: selectedTimeRange.value[0],
        end: selectedTimeRange.value[1]
      }
    }
    return null
  })
)

// 计算属性 - 地图数据
const mapData = computed(() => {
  return chartData.value.length > 0 ? chartData.value : props.mapData
})

// 监听时间范围变化
watch(selectedTimeRange, (newRange) => {
  if (newRange && newRange.length === 2) {
    // 检查时间跨度是否超过30天
    const startDate = dayjs(newRange[0])
    const endDate = dayjs(newRange[1])
    const diffDays = endDate.diff(startDate, 'day')
    
    if (diffDays > 30) {
      message.warning('请选择 30 天内范围')
      return
    }
    
    // 获取探针数据
    fetchProbeData()
  }
}, { deep: true })

// 处理时间范围变化
const handleTimeRangeChange = (timeRange) => {
  selectedTimeRange.value = [timeRange.start, timeRange.end]
}

// 刷新数据
const refreshData = () => {
  if (selectedTimeRange.value && selectedTimeRange.value.length === 2) {
    fetchProbeData()
  }
}

// 监听props.open的变化
watch(() => props.open, (newVal) => {
  isVisible.value = newVal
  if (newVal) {
    // 初始化时间范围为1小时，使用本地时间格式
    const now = dayjs()
    const oneHourAgo = now.subtract(1, 'hour')
    selectedTimeRange.value = [oneHourAgo.format(), now.format()]
    
    // 获取初始数据
    fetchProbeData()
  }
})

// 监听选中的任务变化
watch(() => props.selectedTask, (newTask) => {
  if (newTask) {
    // 初始化时间范围为1小时，使用本地时间格式
    const now = dayjs()
    const oneHourAgo = now.subtract(1, 'hour')
    selectedTimeRange.value = [oneHourAgo.format(), now.format()]
    
    // 获取初始数据
    fetchProbeData()
  }
})

// 监听tableData变化并更新filteredResults
watch(tableData, (newData) => {
  filteredResults.value = [...newData] // 创建新数组确保引用变化
}, { immediate: true, deep: true })

// 处理取消
const handleCancel = () => {
  emit('cancel')
}

// 处理区域点击
const handleRegionClick = (regionInfo) => {
  emit('region-click', regionInfo)
}

// 处理层级变化
const handleLevelChange = (levelInfo) => {
  emit('level-change', levelInfo)
}

// 显示拨测点详情
const showProbeDetail = async (record) => {
  emit('show-probe-detail', record)
}
</script>

<style scoped>
.map-container {
  height: 100%;
}

.probe-list-container {
  height: 100%;
}
</style>