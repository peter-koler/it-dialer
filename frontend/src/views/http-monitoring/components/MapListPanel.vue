<template>
  <a-row :gutter="[16, 16]">
    <a-col :span="12">
      <a-card title="拨测地域分布" :bordered="false">
        <EnhancedChinaMap
          :map-data="props.mapData"
          :alerts-by-region="props.alertsByRegion"
          :get-region-alert-level="props.getRegionAlertLevel"
          :level="mapLevel"
          :selected-code="selectedMapCode"
          height="400px"
          @regionClick="handleRegionClick"
          @update:level="handleLevelChange"
          @update:selectedCode="handleCodeChange"
        />
      </a-card>
    </a-col>
    <a-col :span="12">
      <a-card title="拨测点详情列表" :bordered="false">
        <a-table
          :columns="columns"
          :data-source="props.data"
          :loading="loading"
          row-key="location"
          :pagination="{ pageSize: 10 }"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'">
              <a-tag :color="record.status === 'success' ? 'green' : 'red'">
                {{ record.status === 'success' ? '成功' : '失败' }}
              </a-tag>
            </template>
            <template v-if="column.dataIndex === 'action'">
              <a-button type="link" @click="goToProbeDetail(record)">查看监测点详情</a-button>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-col>
  </a-row>
  
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
          <a-tag :color="record.status === 'success' ? 'green' : 'red'">
            {{ record.status === 'success' ? '成功' : '失败' }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <a-button type="link" @click="showDetails(record)">查看HTTP详情</a-button>
        </template>
      </template>
    </a-table>
  </a-modal>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'
import EnhancedChinaMap from '@/components/EnhancedChinaMap/EnhancedChinaMap.vue'
import pinyinToChinese from '@/utils/pinyinToChinese'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  mapData: {
    type: Array,
    default: () => []
  },
  alertsByRegion: {
    type: Object,
    default: () => ({})
  },
  getRegionAlertLevel: {
    type: Function,
    default: () => () => null
  },

  loading: {
    type: Boolean,
    default: false
  },
  mapLevel: {
    type: String,
    default: 'country'
  },
  selectedMapCode: {
    type: String,
    default: '100000'
  }
})

const emit = defineEmits([
  'regionClick',
  'update:level',
  'update:selectedCode',
  'showAggregatedProbeDetail',
  'showDetails',
  'goToProbeDetail'
])

// 弹窗相关状态
const aggregatedProbeModalVisible = ref(false)
const selectedProbeGroup = ref([])

// 聚合拨测点表格列定义
const columns = [
  { title: '拨测点', dataIndex: 'location', key: 'location',
    customRender: ({ text }) => {
      const chineseName = pinyinToChinese[text] || text;
      return chineseName;
    }
  },
  { title: '拨测点数量', dataIndex: 'agentCount', key: 'agentCount' },
  { title: '成功率', dataIndex: 'successRate', key: 'successRate', 
    customRender: ({ text }) => `${(text * 100).toFixed(2)}%` },
  { title: '最新状态', dataIndex: 'status', key: 'status' },
  { title: '平均响应时间', dataIndex: 'avgResponseTime', key: 'avgResponseTime',
    customRender: ({ text }) => text ? `${text.toFixed(2)} ms` : '-' },
  { title: '操作', dataIndex: 'action', key: 'action' }
]

// 拨测点表格列定义
const probeColumns = [
  { title: '位置', dataIndex: 'location', key: 'location',
    customRender: ({ text }) => {
      const chineseName = pinyinToChinese[text] || text;
      return chineseName;
    }
  },
  { title: '时间', dataIndex: 'created_at', key: 'created_at',
    customRender: ({ text }) => formatDate(text) },
  { title: '响应时间', dataIndex: 'response_time', key: 'response_time',
    customRender: ({ text }) => text ? `${text} ms` : '-' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', dataIndex: 'action', key: 'action' }
]

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 处理地图区域点击
const handleRegionClick = (data) => {
  emit('regionClick', data)
}

// 处理地图级别变化
const handleLevelChange = (level) => {
  emit('update:level', level)
}

// 处理地图代码变化
const handleCodeChange = (code) => {
  emit('update:selectedCode', code)
}

// 显示聚合拨测点详情
const showAggregatedProbeDetail = (record) => {
  selectedProbeGroup.value = record.probes || []
  aggregatedProbeModalVisible.value = true
  emit('showAggregatedProbeDetail', record)
}

// 处理聚合弹窗取消
const handleAggregatedModalCancel = () => {
  aggregatedProbeModalVisible.value = false
  selectedProbeGroup.value = []
}

// 显示详情
const showDetails = (record) => {
  emit('showDetails', record)
}

// 跳转到拨测点详情页面
const goToProbeDetail = (record) => {
  emit('goToProbeDetail', record)
}
</script>

<style scoped>
/* 组件样式 */
</style>