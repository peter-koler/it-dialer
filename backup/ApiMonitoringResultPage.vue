<template>
  <div class="api-monitoring-result">
    <a-card title="API拨测结果" :bordered="false">
      <!-- 任务基本信息 -->
      <a-descriptions :column="{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }" bordered>
        <a-descriptions-item label="任务名称">{{ taskInfo.name || '-' }}</a-descriptions-item>
        <a-descriptions-item label="目标URL">{{ taskInfo.target || '-' }}</a-descriptions-item>
        <a-descriptions-item label="执行次数">{{ totalExecutions || 0 }}</a-descriptions-item>
        <a-descriptions-item label="平均响应时间">{{ avgResponseTime ? `${avgResponseTime.toFixed(2)} ms` : '-' }}</a-descriptions-item>
        <a-descriptions-item label="任务类型">API拨测</a-descriptions-item>
        <a-descriptions-item label="最新状态">
          <StatusTag :status="latestStatus" />
        </a-descriptions-item>
      </a-descriptions>

      <!-- 地图展示 -->
      <div class="map-container">
        <EnhancedChinaMap
          :map-data="mapData"
          :level="mapLevel"
          :selected-code="selectedMapCode"
          height="400px"
          @region-click="handleRegionClick"
          @update:level="handleLevelChange"
          @update:selected-code="handleCodeChange"
        />
      </div>

      <!-- 拨测点详情列表 -->
      <a-card title="拨测点详情列表" style="margin-top: 20px;">
        <a-table
          :dataSource="aggregatedProbeList"
          :columns="aggregatedProbeColumns"
          :pagination="{ pageSize: 10 }"
          :loading="loading"
          rowKey="location"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'">
              <StatusTag :status="record.status" />
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <a-button type="link" @click="showAggregatedProbeDetail(record)">查看API拨测点详情</a-button>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-card>

    <!-- 聚合拨测点详情弹窗 -->
    <a-modal
      v-model:open="aggregatedProbeModalVisible"
      title="拨测点详情"
      width="70%"
      :footer="null"
      @cancel="handleAggregatedModalCancel"
    >
      <a-table
        :dataSource="selectedProbeGroup"
        :columns="probeColumns"
        :pagination="{ pageSize: 5 }"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'status'">
            <StatusTag :status="record.status" />
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <a-button type="link" @click="viewApiTaskResult(record)">查看API详情</a-button>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- 单次拨测结果弹窗已移除，现在直接跳转到新页面 -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getTask, getTaskResults } from '@/api/task'
import StatusTag from '../task-detail/StatusTag.vue'
import EnhancedChinaMap from '@/components/EnhancedChinaMap/EnhancedChinaMap.vue'
// 已移除对旧ApiTaskResultModal的引用
import pinyinToChinese from '@/utils/pinyinToChinese.js'

// 路由参数
const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.id)

// 响应式状态
const loading = ref(false)
const taskInfo = ref({})
const probeList = ref([])
const resultModalVisible = ref(false)
const selectedProbe = ref(null)
const aggregatedProbeModalVisible = ref(false)
const selectedProbeGroup = ref([])

// 地图相关数据
const mapData = ref([])
const mapLevel = ref('country')
const selectedMapCode = ref('')

// 聚合拨测点表格列定义
const aggregatedProbeColumns = [
  {
    title: '位置',
    dataIndex: 'location',
    key: 'location',
  },
  {
    title: '拨测点数量',
    dataIndex: 'agentCount',
    key: 'agentCount',
  },
  {
    title: '成功率',
    dataIndex: 'successRate',
    key: 'successRate',
    render: (rate) => `${(rate * 100).toFixed(2)}%`,
  },
  {
    title: '最新状态',
    dataIndex: 'status',
    key: 'status',
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'action',
  },
]

// 拨测点表格列定义
const probeColumns = [
  {
    title: '位置',
    dataIndex: 'location',
    key: 'location',
  },
  {
    title: '时间',
    dataIndex: 'created_at',
    key: 'created_at',
    render: (text) => formatDate(text)
  },
  {
    title: '响应时间',
    dataIndex: 'response_time',
    key: 'response_time',
    render: (text) => text ? `${text} ms` : '-'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'action',
  }
]

// 计算属性
const totalExecutions = computed(() => probeList.value.length)

const avgResponseTime = computed(() => {
  const validTimes = probeList.value
    .map(item => item.response_time)
    .filter(time => time !== undefined && time !== null && time > 0)
  
  if (validTimes.length === 0) return 0
  return validTimes.reduce((sum, time) => sum + time, 0) / validTimes.length
})

const aggregatedProbeList = computed(() => {
  const groupedByLocation = probeList.value.reduce((acc, probe) => {
    if (!acc[probe.location]) {
      acc[probe.location] = []
    }
    acc[probe.location].push(probe)
    return acc
  }, {})

  return Object.keys(groupedByLocation).map(location => {
    const probes = groupedByLocation[location]
    const successCount = probes.filter(p => p.status === 'success').length
    const latestProbe = probes.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
    const agentIds = new Set(probes.map(p => p.agent_id).filter(id => id))

    return {
      location,
      agentCount: agentIds.size,
      successRate: probes.length > 0 ? successCount / probes.length : 0,
      status: latestProbe.status,
      probes,
    }
  })
})

const latestStatus = computed(() => {
  if (probeList.value.length === 0) return 'unknown'
  return probeList.value[0].status || 'unknown'
})

// 方法
const fetchTaskInfo = async () => {
  if (!taskId.value) return
  
  try {
    const response = await getTask(taskId.value)
    if (response.code === 0) {
      taskInfo.value = response.data
    } else {
      message.error(response.message || '获取任务信息失败')
    }
  } catch (error) {
    console.error('获取任务信息失败:', error)
    message.error('获取任务信息失败')
  }
}

const fetchTaskResults = async () => {
  if (!taskId.value) return
  
  loading.value = true
  try {
    const params = {
      task_id: taskId.value,
      page: 1,
      size: 1000,
      sort: 'created_at',
      order: 'desc'
    }
    
    const response = await getTaskResults(params)
    if (response.code === 0) {
      // 处理API拨测结果数据
      const results = response.data.list.map(item => {
        // 将拼音地区名转换为中文
        const locationName = pinyinToChinese[item.agent_area] || item.agent_area || '未知地区'
        
        return {
          ...item,
          location: locationName,
          id: item.id || `${item.agent_area}-${item.created_at}`
        }
      })
      
      probeList.value = results
      
      // 生成地图数据
      mapData.value = generateMapData(results)
    } else {
      message.error(response.message || '获取任务结果失败')
    }
  } catch (error) {
    console.error('获取任务结果失败:', error)
    message.error('获取任务结果失败')
  } finally {
    loading.value = false
  }
}

// 生成地图数据
const generateMapData = (results) => {
  if (!results || !Array.isArray(results)) {
    return []
  }

  // 统计各地区的拨测点数量和状态
  const regionData = {}

  results.forEach(result => {
    const agentArea = result.agent_area
    const agentId = result.agent_id

    if (agentArea) {
      // 将拼音地区名转换为中文
      const locationName = pinyinToChinese[agentArea] || agentArea

      if (!regionData[locationName]) {
        regionData[locationName] = {
          agents: new Set(),
          success: 0,
          fail: 0,
          count: 0
        }
      }

      if (agentId) {
        regionData[locationName].agents.add(agentId)
      }
      regionData[locationName].count++

      // 统计成功/失败数量
      if (result.status === 'success') {
        regionData[locationName].success++
      } else {
        regionData[locationName].fail++
      }
    }
  })

  // 转换为地图组件需要的格式
  return Object.keys(regionData).map(regionName => {
    const data = regionData[regionName]
    const successRate = data.count > 0 ? (data.success / data.count) : 0

    return {
      name: regionName,
      value: data.agents.size,
      successRate: successRate,
      success: data.success,
      fail: data.fail
    }
  })
}

// 格式化时间
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 处理地图区域点击
const handleRegionClick = (params) => {
  console.log('区域点击:', params)
  // 可以根据点击的区域筛选拨测点列表
}

// 处理地图层级变化
const handleLevelChange = (level) => {
  mapLevel.value = level
}

// 处理地图选中区域变化
const handleCodeChange = (code) => {
  selectedMapCode.value = code
}

// 显示聚合拨测点详情
const showAggregatedProbeDetail = (record) => {
  selectedProbeGroup.value = record.probes
  aggregatedProbeModalVisible.value = true
}

// 关闭聚合拨测点详情弹窗
const handleAggregatedModalCancel = () => {
  aggregatedProbeModalVisible.value = false
}

// 显示结果详情
const showResultDetail = (record) => {
  selectedProbe.value = record
  resultModalVisible.value = true
}

// 查看API任务结果详情
const viewApiTaskResult = (record) => {
  // 跳转到新的API任务结果页面
  router.push({
    name: 'ApiTaskResult',
    params: { id: record.id }
  })
}

// 处理弹窗关闭
const handleModalCancel = () => {
  resultModalVisible.value = false
}

// 监听路由参数变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    fetchTaskInfo()
    fetchTaskResults()
  }
}, { immediate: true })

// 组件挂载时获取数据
onMounted(() => {
  if (taskId.value) {
    fetchTaskInfo()
    fetchTaskResults()
  }
})
</script>

<style scoped>
.api-monitoring-result {
  padding: 20px;
}

.map-container {
  margin-top: 20px;
  border: 1px solid #f0f0f0;
  border-radius: 2px;
}
</style>