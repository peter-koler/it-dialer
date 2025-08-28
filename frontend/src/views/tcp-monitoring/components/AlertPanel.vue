<template>
  <a-row :gutter="[16, 16]" class="alert-section">
    <a-col :span="24">
      <a-card title="任务告警" :bordered="false">
        <a-table
          :dataSource="alertList"
          :columns="alertColumns"
          :loading="alertLoading"
          :pagination="{
            current: alertPagination.current,
            pageSize: alertPagination.pageSize,
            total: alertPagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条/共 ${total} 条`
          }"
          @change="handleAlertTableChange"
          rowKey="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'alertLevel'">
              <a-tag 
                :color="getAlertLevelColor(record.alertLevel)"
              >
                {{ getAlertLevelText(record.alertLevel) }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'triggerTime'">
              {{ dayjs(record.triggerTime).format('YYYY-MM-DD HH:mm:ss') }}
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <a-button type="link" @click="viewSnapshot(record)">查看快照</a-button>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-col>
  </a-row>
  
  <!-- 快照查看弹窗 -->
  <a-modal
    v-model:open="snapshotModalVisible"
    title="TCP连接快照"
    width="80%"
    :footer="null"
  >
    <AlertSnapshot 
      v-if="currentSnapshot" 
      :snapshot="currentSnapshot"
    />
  </a-modal>
</template>

<script setup>
import { ref, reactive, defineProps, defineEmits, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getAlerts } from '@/api/alerts'
import AlertSnapshot from '../../alert-management/components/AlertSnapshot.vue'
import pinyinToChinese from '@/utils/pinyinToChinese'

const props = defineProps({
  taskId: {
    type: [String, Number],
    required: true
  },
  timeRange: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['alertTableChange'])

// 告警相关状态
const alertList = ref([])
const alertLoading = ref(false)
const alertPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

// 快照模态框相关状态
const snapshotModalVisible = ref(false)
const currentSnapshot = ref(null)

// 告警表格列定义
const alertColumns = [
  { title: '任务名称', dataIndex: 'taskName', key: 'taskName' },
  { title: '拨测点', dataIndex: 'probeName', key: 'probeName',
    customRender: ({ text }) => {
      const chineseName = pinyinToChinese[text] || text;
      return chineseName;
    }
  },
  { title: '触发时间', dataIndex: 'triggerTime', key: 'triggerTime' },
  { title: '告警级别', dataIndex: 'alertLevel', key: 'alertLevel' },
  { title: '告警内容', dataIndex: 'alertContent', key: 'alertContent' },
  { title: '操作', dataIndex: 'action', key: 'action' }
]

// 获取告警级别颜色
const getAlertLevelColor = (level) => {
  const colorMap = {
    'critical': 'red',
    'warning': 'orange', 
    'info': 'blue'
  }
  return colorMap[level] || 'default'
}

// 获取告警级别文本
const getAlertLevelText = (level) => {
  const textMap = {
    'critical': '严重',
    'warning': '警告',
    'info': '信息'
  }
  return textMap[level] || level
}

// 获取告警数据
const fetchAlerts = async (startTime = null, endTime = null) => {
  alertLoading.value = true
  try {
    const params = {
      page: alertPagination.current,
      per_page: alertPagination.pageSize
    }
    
    // 如果有时间筛选条件，添加到参数中
    if (startTime && endTime) {
      params.start_time = startTime
      params.end_time = endTime
    }
    
    const response = await getAlerts(params)
    if (response.data.code === 0) {
      // 过滤当前任务的告警
      const allAlerts = response.data.alerts || []
      const taskAlerts = allAlerts.filter(alert => alert.task_id == props.taskId)
      
      alertList.value = taskAlerts.map(alert => ({
        id: alert.id,
        taskName: alert.taskName || alert.task_name,
        probeName: alert.agent_area || alert.agent_id || '未知拨测点',
        triggerTime: alert.triggerTime || alert.created_at,
        alertLevel: alert.alert_level,
        alertContent: alert.content,
        snapshot: alert.snapshot_data
      }))
      
      // 更新分页信息
      alertPagination.total = taskAlerts.length
    } else {
      message.error(response.message || '获取告警数据失败')
      alertList.value = []
      alertPagination.total = 0
    }
    
  } catch (error) {
    console.error('获取告警数据失败:', error)
    message.error('获取告警数据失败: ' + (error.message || '未知错误'))
    alertList.value = []
    alertPagination.total = 0
  } finally {
    alertLoading.value = false
  }
}

// 处理告警表格变化
const handleAlertTableChange = (pagination) => {
  alertPagination.current = pagination.current
  alertPagination.pageSize = pagination.pageSize
  
  // 重新获取数据
  if (props.timeRange && props.timeRange.length === 2) {
    fetchAlerts(props.timeRange[0].format('YYYY-MM-DD HH:mm:ss'), props.timeRange[1].format('YYYY-MM-DD HH:mm:ss'))
  } else {
    fetchAlerts()
  }
  
  emit('alertTableChange', pagination)
}

// 查看快照
const viewSnapshot = (record) => {
  if (record.snapshot) {
    currentSnapshot.value = record.snapshot
    snapshotModalVisible.value = true
  } else {
    message.info('该告警暂无快照数据')
  }
}

// 暴露方法给父组件
defineExpose({
  fetchAlerts
})

// 监听时间范围变化
watch(() => props.timeRange, (newTimeRange) => {
  if (newTimeRange && newTimeRange.length === 2) {
    const startTime = newTimeRange[0].format('YYYY-MM-DD HH:mm:ss')
    const endTime = newTimeRange[1].format('YYYY-MM-DD HH:mm:ss')
    fetchAlerts(startTime, endTime)
  } else {
    fetchAlerts()
  }
}, { deep: true })

// 组件挂载时获取数据
onMounted(() => {
  fetchAlerts()
})
</script>

<style scoped>
.alert-section {
  margin-top: 16px;
}
</style>