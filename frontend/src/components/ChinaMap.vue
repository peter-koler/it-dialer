<template>
  <div ref="mapContainer" class="echarts-map" :style="{ height: height }"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import 'echarts/map/js/china.js'

// 定义属性
const props = defineProps({
  height: {
    type: String,
    default: '600px'
  },
  // 地图数据
  mapData: {
    type: Array,
    default: () => []
  },
  // 当前层级: 'country', 'province', 'city'
  level: {
    type: String,
    default: 'country'
  },
  // 当前选中的区域编码
  selectedCode: {
    type: String,
    default: ''
  }
})

// 定义事件
const emit = defineEmits(['region-click', 'level-change'])

// 响应式数据
const mapContainer = ref(null)
const chart = ref(null)
const currentLevel = ref(props.level)
const currentSelectedCode = ref(props.selectedCode)

// 监听数据变化
watch(() => props.mapData, () => {
  updateChart()
})

// 监听层级变化
watch(() => props.level, (newLevel) => {
  currentLevel.value = newLevel
  updateChart()
})

// 监听选中区域变化
watch(() => props.selectedCode, (newCode) => {
  currentSelectedCode.value = newCode
  updateChart()
})

// 更新图表
const updateChart = () => {
  if (!chart.value || !mapContainer.value) return
  
  const option = generateOption()
  chart.value.setOption(option, true)
}

// 生成图表配置
const generateOption = () => {
  let title = '全国拨测点分布图'
  let mapType = 'china'
  
  if (currentLevel.value === 'province' && currentSelectedCode.value) {
    title = getCodeToName(currentSelectedCode.value) + '拨测点分布图'
    mapType = currentSelectedCode.value
  } else if (currentLevel.value === 'city' && currentSelectedCode.value) {
    title = getCodeToName(currentSelectedCode.value) + '拨测点分布图'
    mapType = currentSelectedCode.value
  }
  
  return {
    title: {
      text: title,
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `${params.name}<br/>${params.value || 0}个拨测点`
      }
    },
    visualMap: {
      min: 0,
      max: 50,
      inRange: {
        color: ['#d9f0a3', '#addd8e', '#78c679', '#41ab5d', '#238443', '#006837', '#004529']
      },
      textStyle: {
        color: '#000'
      },
      calculable: true
    },
    series: [
      {
        name: '拨测点数量',
        type: 'map',
        map: mapType,
        roam: true,
        zoom: 1.2,
        label: {
          show: true,
          color: '#000'
        },
        itemStyle: {
          areaColor: '#eee',
          borderColor: '#333'
        },
        emphasis: {
          label: {
            color: '#fff'
          },
          itemStyle: {
            areaColor: '#2a93fc'
          }
        },
        data: props.mapData
      }
    ]
  }
}

// 编码转名称（简化版）
const getCodeToName = (code) => {
  // 这里应该使用完整的编码到名称映射
  // 为简化，直接返回编码
  return code + ' '
}

// 处理地图点击事件
const handleMapClick = (params) => {
  if (!params.name) return
  
  emit('region-click', {
    name: params.name,
    value: params.value,
    level: currentLevel.value
  })
  
  // 根据当前层级决定是否需要下钻
  if (currentLevel.value === 'country') {
    // 从全国下钻到省份
    const provinceCode = getProvinceCodeByName(params.name)
    if (provinceCode) {
      currentLevel.value = 'province'
      currentSelectedCode.value = provinceCode
      emit('level-change', {
        level: 'province',
        code: provinceCode
      })
      loadProvinceMap(provinceCode)
    }
  } else if (currentLevel.value === 'province') {
    // 从省份下钻到城市
    const cityCode = getCityCodeByName(params.name, currentSelectedCode.value)
    if (cityCode) {
      currentLevel.value = 'city'
      currentSelectedCode.value = cityCode
      emit('level-change', {
        level: 'city',
        code: cityCode
      })
      loadCityMap(cityCode)
    }
  }
}

// 根据省份名称获取编码（简化版）
const getProvinceCodeByName = (name) => {
  const provinceMap = {
    '北京': '110000',
    '天津': '120000',
    '河北': '130000',
    '山西': '140000',
    '内蒙古': '150000',
    '辽宁': '210000',
    '吉林': '220000',
    '黑龙江': '230000',
    '上海': '310000',
    '江苏': '320000',
    '浙江': '330000',
    '安徽': '340000',
    '福建': '350000',
    '江西': '360000',
    '山东': '370000',
    '河南': '410000',
    '湖北': '420000',
    '湖南': '430000',
    '广东': '440000',
    '广西': '450000',
    '海南': '460000',
    '重庆': '500000',
    '四川': '510000',
    '贵州': '520000',
    '云南': '530000',
    '西藏': '540000',
    '陕西': '610000',
    '甘肃': '620000',
    '青海': '630000',
    '宁夏': '640000',
    '新疆': '650000',
    '台湾': '710000',
    '香港': '810000',
    '澳门': '820000'
  }
  return provinceMap[name] || ''
}

// 根据城市名称和省份编码获取城市编码（简化版）
const getCityCodeByName = (name, provinceCode) => {
  // 这里应该有完整的城市编码映射
  // 为简化，返回一个模拟的编码
  return provinceCode.substring(0, 2) + '0100'
}

// 加载省级地图
const loadProvinceMap = async (code) => {
  try {
    // 动态加载省级地图
    await import(`echarts/map/js/province/${code.substring(0, 2)}0000.js`)
    updateChart()
  } catch (error) {
    console.error('加载省级地图失败:', error)
  }
}

// 加载市级地图
const loadCityMap = async (code) => {
  try {
    // 动态加载市级地图
    await import(`echarts/map/js/city/${code}.js`)
    updateChart()
  } catch (error) {
    console.error('加载市级地图失败:', error)
  }
}

// 返回上一级
const goBack = () => {
  if (currentLevel.value === 'city') {
    // 从城市返回省份
    const provinceCode = currentSelectedCode.value.substring(0, 2) + '0000'
    currentLevel.value = 'province'
    currentSelectedCode.value = provinceCode
    emit('level-change', {
      level: 'province',
      code: provinceCode
    })
    updateChart()
  } else if (currentLevel.value === 'province') {
    // 从省份返回全国
    currentLevel.value = 'country'
    currentSelectedCode.value = ''
    emit('level-change', {
      level: 'country',
      code: ''
    })
    updateChart()
  }
}

// 初始化图表
const initChart = () => {
  if (!mapContainer.value) return
  
  // 销毁之前的实例
  if (chart.value) {
    chart.value.dispose()
  }
  
  chart.value = echarts.init(mapContainer.value)
  updateChart()
  
  // 监听点击事件
  chart.value.on('click', handleMapClick)
}

// 组件挂载
onMounted(() => {
  initChart()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    if (chart.value) {
      chart.value.resize()
    }
  })
})

// 组件卸载
onUnmounted(() => {
  if (chart.value) {
    chart.value.dispose()
  }
})

// 暴露方法给父组件
defineExpose({
  goBack
})
</script>

<style scoped>
.echarts-map {
  width: 100%;
}
</style>