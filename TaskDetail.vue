<template>
  <div class="task-detail-container">
    <a-row :gutter="16">
      <!-- 左侧地图区域 -->
      <a-col :span="14">
        <a-card title="拨测点分布图" class="map-container">
          <div ref="mapContainer" class="echarts-map"></div>
        </a-card>
      </a-col>
      
      <!-- 右侧拨测点列表 -->
      <a-col :span="10">
        <a-card title="拨测点列表" class="probe-list-container">
          <a-table 
            :dataSource="probeData" 
            :columns="columns"
            :pagination="pagination"
            @change="handleTableChange"
            :loading="loading"
            :rowKey="(record) => record.id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'location'">
                {{ record.province }}-{{ record.city }}
              </template>
              <template v-if="column.dataIndex === 'time'">
                {{ formatDate(record.created_at) }}
              </template>
              <template v-if="column.dataIndex === 'responseTime'">
                {{ record.response_time }} ms
              </template>
              <template v-if="column.dataIndex === 'actions'">
                <a-button type="link" @click="showDetail(record)">查看详情</a-button>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      title="拨测点详情"
      width="600px"
      :footer="null"
      @cancel="handleModalCancel"
    >
      <div v-if="selectedProbe">
        <a-descriptions bordered :column="1">
          <a-descriptions-item label="拨测点名称">
            {{ selectedProbe.task?.name }}
          </a-descriptions-item>
          <a-descriptions-item label="位置">
            {{ selectedProbe.province }}-{{ selectedProbe.city }}
          </a-descriptions-item>
          <a-descriptions-item label="时间">
            {{ formatDate(selectedProbe.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="响应时间">
            {{ selectedProbe.response_time }} ms
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(selectedProbe.status)">
              {{ selectedProbe.status }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
        
        <div ref="detailChartContainer" class="detail-chart-container"></div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import 'echarts/map/js/china.js'

// 定义响应式数据
const mapContainer = ref(null)
const detailChartContainer = ref(null)
const modalVisible = ref(false)
const selectedProbe = ref(null)
const mapChart = ref(null)
const detailChart = ref(null)

// 表格相关数据
const probeData = ref([])
const loading = ref(false)
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

// 表格列定义
const columns = [
  {
    title: '拨测点名称',
    dataIndex: ['task', 'name']
  },
  {
    title: '位置',
    dataIndex: 'location'
  },
  {
    title: '时间',
    dataIndex: 'time'
  },
  {
    title: '响应时间',
    dataIndex: 'responseTime',
    sorter: (a, b) => a.response_time - b.response_time
  },
  {
    title: '操作',
    dataIndex: 'actions'
  }
]

// 格式化时间
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 获取状态标签颜色
const getStatusColor = (status) => {
  switch (status) {
    case 'success':
      return 'green'
    case 'failed':
      return 'red'
    case 'timeout':
      return 'orange'
    default:
      return 'default'
  }
}

// 显示详情
const showDetail = (record) => {
  selectedProbe.value = record
  modalVisible.value = true
  
  // 等待DOM更新后渲染图表
  nextTick(() => {
    renderDetailChart(record)
  })
}

// 处理弹窗关闭
const handleModalCancel = () => {
  modalVisible.value = false
  selectedProbe.value = null
  
  // 销毁图表实例
  if (detailChart.value) {
    detailChart.value.dispose()
    detailChart.value = null
  }
}

// 渲染详情图表
const renderDetailChart = (record) => {
  if (!detailChartContainer.value) return
  
  // 销毁之前的图表实例
  if (detailChart.value) {
    detailChart.value.dispose()
  }
  
  detailChart.value = echarts.init(detailChartContainer.value)
  
  // 解析details数据
  let details = record.details
  if (typeof details === 'string') {
    try {
      details = JSON.parse(details)
    } catch (e) {
      console.error('解析details失败:', e)
    }
  }
  
  let option = {}
  
  // 根据任务类型渲染不同的图表
  if (record.task?.type === 'ping') {
    option = {
      title: {
        text: 'Ping延迟详情',
        left: 'center'
      },
      tooltip: {},
      xAxis: {
        type: 'category',
        data: ['最小延迟', '平均延迟', '最大延迟']
      },
      yAxis: {
        type: 'value',
        name: '延迟(ms)'
      },
      series: [{
        type: 'bar',
        data: [
          details?.rtt_min || 0,
          details?.rtt_avg || 0,
          details?.rtt_max || 0
        ]
      }]
    }
  } else if (record.task?.type === 'tcp') {
    option = {
      title: {
        text: 'TCP连接详情',
        left: 'center'
      },
      tooltip: {},
      xAxis: {
        type: 'category',
        data: ['连接状态']
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        type: 'bar',
        data: [{
          value: details?.connected ? 1 : 0,
          itemStyle: {
            color: details?.connected ? '#52c41a' : '#ff4d4f'
          }
        }]
      }]
    }
  } else {
    option = {
      title: {
        text: '暂无详细图表数据',
        left: 'center',
        top: 'center'
      }
    }
  }
  
  detailChart.value.setOption(option)
}

// 处理表格分页变化
const handleTableChange = (pager) => {
  pagination.value.current = pager.current
  pagination.value.pageSize = pager.pageSize
  // 这里应该重新获取数据
  fetchProbeData()
}

// 获取拨测点数据（模拟数据）
const fetchProbeData = async () => {
  loading.value = true
  try {
    // 模拟API调用
    // 实际应该根据任务ID获取相关结果数据
    // const response = await fetch(`/api/results?task_id=${taskId}`)
    
    // 模拟数据
    probeData.value = [
      {
        id: 1,
        task: {
          id: 1,
          name: '北京拨测点'
        },
        province: '北京市',
        city: '北京市',
        status: 'success',
        response_time: 45,
        created_at: new Date().toISOString(),
        details: {
          rtt_min: 40,
          rtt_avg: 45,
          rtt_max: 50
        }
      },
      {
        id: 2,
        task: {
          id: 1,
          name: '上海拨测点'
        },
        province: '上海市',
        city: '上海市',
        status: 'success',
        response_time: 62,
        created_at: new Date().toISOString(),
        details: {
          rtt_min: 58,
          rtt_avg: 62,
          rtt_max: 68
        }
      },
      {
        id: 3,
        task: {
          id: 1,
          name: '广州拨测点'
        },
        province: '广东省',
        city: '广州市',
        status: 'timeout',
        response_time: 1200,
        created_at: new Date().toISOString(),
        details: {
          rtt_min: 0,
          rtt_avg: 0,
          rtt_max: 0
        }
      }
    ]
    
    pagination.value.total = probeData.value.length
  } catch (error) {
    console.error('获取拨测点数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化地图
const initMap = () => {
  if (!mapContainer.value) return
  
  // 销毁之前的图表实例
  if (mapChart.value) {
    mapChart.value.dispose()
  }
  
  mapChart.value = echarts.init(mapContainer.value)
  
  const option = {
    title: {
      text: '全国拨测点分布图',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>{c}个拨测点'
    },
    toolbox: {
      show: true,
      orient: 'vertical',
      left: 'right',
      top: 'center',
      feature: {
        dataView: { readOnly: false },
        restore: {},
        saveAsImage: {}
      }
    },
    visualMap: {
      min: 0,
      max: 2500,
      text: ['High', 'Low'],
      realtime: false,
      calculable: true,
      inRange: {
        color: ['lightskyblue', 'yellow', 'orangered']
      }
    },
    series: [
      {
        name: '拨测点数量',
        type: 'map',
        map: 'china',
        roam: true,
        zoom: 1.2,
        label: {
          show: true
        },
        data: [
          { name: '北京', value: 10 },
          { name: '天津', value: 5 },
          { name: '上海', value: 8 },
          { name: '重庆', value: 3 },
          { name: '河北', value: 12 },
          { name: '河南', value: 9 },
          { name: '云南', value: 4 },
          { name: '辽宁', value: 7 },
          { name: '黑龙江', value: 6 },
          { name: '湖南', value: 11 },
          { name: '安徽', value: 8 },
          { name: '山东', value: 15 },
          { name: '新疆', value: 2 },
          { name: '江苏', value: 13 },
          { name: '浙江', value: 14 },
          { name: '江西', value: 9 },
          { name: '湖北', value: 11 },
          { name: '广西', value: 7 },
          { name: '甘肃', value: 4 },
          { name: '山西', value: 8 },
          { name: '内蒙古', value: 5 },
          { name: '陕西', value: 9 },
          { name: '吉林', value: 6 },
          { name: '福建', value: 10 },
          { name: '贵州', value: 5 },
          { name: '广东', value: 18 },
          { name: '青海', value: 2 },
          { name: '西藏', value: 1 },
          { name: '四川', value: 12 },
          { name: '宁夏', value: 3 },
          { name: '海南', value: 4 },
          { name: '台湾', value: 5 },
          { name: '香港', value: 6 },
          { name: '澳门', value: 3 }
        ]
      }
    ]
  }
  
  mapChart.value.setOption(option)
  
  // 监听地图点击事件
  mapChart.value.on('click', function (params) {
    console.log('点击了:', params.name)
    // 这里可以实现点击省份或城市后缩放展示相应区域的功能
  })
}

// 组件挂载后初始化
onMounted(() => {
  initMap()
  fetchProbeData()
  
  // 监听窗口大小变化，重置图表大小
  window.addEventListener('resize', () => {
    if (mapChart.value) {
      mapChart.value.resize()
    }
    if (detailChart.value) {
      detailChart.value.resize()
    }
  })
})
</script>

<style scoped>
.task-detail-container {
  padding: 16px;
}

.map-container,
.probe-list-container {
  height: 100%;
}

.echarts-map {
  width: 100%;
  height: 600px;
}

.detail-chart-container {
  width: 100%;
  height: 300px;
  margin-top: 20px;
}
</style>