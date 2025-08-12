<template>
  <a-modal
    v-model:open="isVisible"
    :title="'任务详情 - ' + (selectedTask?.task?.name || '')"
    width="90%"
    @cancel="handleCancel"
    :footer="null"
    :destroyOnClose="true"
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
      
      <a-row :gutter="16" style="margin-top: 20px;">
        <!-- 左侧地图区域 -->
        <a-col :span="14">
          <a-card class="map-container">
            <EnhancedChinaMap 
              ref="chinaMapRef"
              :mapData="mapData"
              :level="mapLevel"
              :selectedCode="selectedMapCode"
              @region-click="handleRegionClick"
              @level-change="handleLevelChange"
              height="500px"
            />
          </a-card>
        </a-col>
        
        <!-- 右侧拨测点列表 -->
        <a-col :span="10">
          <a-card title="拨测点详情列表" class="probe-list-container">
            <ProbeList 
              :results="selectedTask.results"
              @show-probe-detail="showProbeDetail"
            />
          </a-card>
        </a-col>
      </a-row>
      
      <!-- 图表展示区域 -->
      <TaskCharts 
        :task-type="selectedTask.task.type"
        :results="selectedTask.results"
      />
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import EnhancedChinaMap from '@/components/EnhancedChinaMap/EnhancedChinaMap.vue'
import StatusTag from './StatusTag.vue'
import ProbeList from './ProbeList.vue'
import TaskCharts from './TaskCharts.vue'

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

const emit = defineEmits(['update:open', 'cancel', 'region-click', 'level-change'])

const chinaMapRef = ref(null)
const isVisible = ref(props.open)

// 监听props.open的变化
watch(() => props.open, (newVal) => {
  isVisible.value = newVal
})

const handleCancel = () => {
  isVisible.value = false
  emit('update:open', false)
  emit('cancel')
}

const handleRegionClick = (regionInfo) => {
  emit('region-click', regionInfo)
}

const handleLevelChange = (levelInfo) => {
  emit('level-change', levelInfo)
}

const showProbeDetail = (record) => {
  emit('show-probe-detail', record)
}
</script>

<style scoped>
.map-container,
.probe-list-container {
  height: 100%;
}
</style>