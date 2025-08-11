<template>
  <div class="map-wrapper">
    <div class="map-header" v-if="showHeader">
      <a-button v-if="currentLevel !== 'country'" type="link" @click="goBack" class="back-button">
        <ArrowLeftOutlined /> 返回上一级
      </a-button>
      <span class="map-title">{{ mapTitle }}</span>
    </div>
    <div ref="mapContainer" :class="['echarts-map', `level-${currentLevel}`]" :style="{ height }"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ArrowLeftOutlined } from '@ant-design/icons-vue'
import regionCodes from '@/utils/regionCodes.js'

// 定义属性
const props = defineProps({
  height: {
    type: String,
    default: '500px'
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
    default: '100000'
  },
  // 是否显示头部
  showHeader: {
    type: Boolean,
    default: true
  }
})

// 定义事件
const emit = defineEmits(['region-click', 'level-change'])

// 响应式数据
const mapContainer = ref(null)
const chart = ref(null)
const currentLevel = ref(props.level)
const currentSelectedCode = ref(props.selectedCode)
const mapRegistry = new Set() // 记录已注册的地图

// 计算属性
const mapTitle = computed(() => {
  if (currentLevel.value === 'country') {
    return '全国拨测点分布图'
  } else if (currentLevel.value === 'province' && currentSelectedCode.value) {
    const provinceName = getNameByCode(currentSelectedCode.value)
    return `${provinceName}拨测点分布图`
  } else if (currentLevel.value === 'city' && currentSelectedCode.value) {
    const cityName = getNameByCode(currentSelectedCode.value)
    return `${cityName}拨测点分布图`
  }
  return '拨测点分布图'
})

// 根据编码获取名称
const getNameByCode = (code) => {
  // 反向查找regionCodes
  for (const [name, regionCode] of Object.entries(regionCodes)) {
    if (regionCode === code) {
      // 将拼音转换为首字母大写
      return name.charAt(0).toUpperCase() + name.slice(1)
    }
  }
  return code
}

// 加载地图数据
const loadMapData = async (mapType) => {
  // 如果地图已经注册过，则直接返回
  if (mapRegistry.has(mapType)) {
    return
  }

  try {
    let geoJsonUrl
    if (mapType === '100000') {
      // 全国地图
      geoJsonUrl = '/100000.geoJson'
    } else if (mapType.length === 6 && mapType.endsWith('0000') && mapType !== '100000') {
      // 省级地图
      geoJsonUrl = `/${mapType}.geoJson`
    } else if (mapType.length === 6 && !mapType.endsWith('0000')) {
      // 市级地图
      const provinceCode = mapType.substring(0, 2) + '0000'
      geoJsonUrl = `/${provinceCode}/${mapType}.geoJson`
    }

    if (geoJsonUrl) {
      const response = await fetch(geoJsonUrl)
      const geoJson = await response.json()
      echarts.registerMap(mapType, geoJson)
      mapRegistry.add(mapType)
    }
  } catch (error) {
    console.error(`加载地图数据失败 ${mapType}:`, error)
  }
}

// 监听数据变化
watch(() => props.mapData, () => {
  updateChart()
}, { deep: true })

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
const updateChart = async () => {
  if (!chart.value || !mapContainer.value) return

  let mapType = '100000'
  if (currentLevel.value === 'province' && currentSelectedCode.value) {
    mapType = currentSelectedCode.value
  } else if (currentLevel.value === 'city' && currentSelectedCode.value) {
    mapType = currentSelectedCode.value
  }

  // 确保地图数据已加载
  await loadMapData(mapType)

  nextTick(() => {
    const option = generateOption(mapType)
    chart.value.setOption(option, {
      replaceMerge: ['series'],
      transition: {
        duration: 300
      }
    })
  })
}

// 生成图表配置
const generateOption = (mapType) => {
  let title = '全国拨测点分布图'
  let zoom = 1.2

  if (currentLevel.value === 'province' && currentSelectedCode.value) {
    const provinceName = getNameByCode(currentSelectedCode.value)
    title = `${provinceName}拨测点分布图`
    zoom = 1.5
  } else if (currentLevel.value === 'city' && currentSelectedCode.value) {
    const cityName = getNameByCode(currentSelectedCode.value)
    title = `${cityName}拨测点分布图`
    zoom = 2
  }

  return {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.data && params.data.tooltip) {
          return params.data.tooltip
        }
        return `${params.name}<br/>${params.value || 0}个拨测点`
      }
    },
    visualMap: {
      min: 0,
      max: props.mapData.length > 0 ? Math.max(...props.mapData.map(item => item.value || 0)) : 10,
      inRange: {
        color: ['#d9f0a3', '#addd8e', '#78c679', '#41ab5d', '#238443', '#006837', '#004529']
      },
      textStyle: {
        color: '#333'
      },
      calculable: true,
      show: true
    },
    series: [
      {
        name: '拨测点数量',
        type: 'map',
        map: mapType,
        roam: false,
        zoom: zoom,
        label: {
          show: currentLevel.value === 'country',
          color: '#333',
          fontSize: 10
        },
        itemStyle: {
          areaColor: '#f0f0f0',
          borderColor: '#999',
          borderWidth: 0.5
        },
        emphasis: {
          label: {
            color: '#fff',
            fontSize: 12
          },
          itemStyle: {
            areaColor: '#2a93fc',
            borderColor: '#000',
            borderWidth: 1
          }
        },
        data: props.mapData,
        animationDurationUpdate: 300
      }
    ]
  }
}

// 处理地图点击事件
const handleMapClick = async (params) => {
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
        code: provinceCode,
        name: params.name
      })
      updateChart()
    }
  } else if (currentLevel.value === 'province') {
    // 从省份"选中"城市（不进行下钻）
    const cityCode = getCityCodeByName(params.name, currentSelectedCode.value)
    if (cityCode) {
      currentLevel.value = 'city'
      currentSelectedCode.value = cityCode
      emit('level-change', {
        level: 'city',
        code: cityCode,
        name: params.name
      })
      updateChart()
    }
  }
  // 城市级不进行下钻操作，仅选中
}

// 根据省份名称获取编码
const getProvinceCodeByName = (name) => {
  // 特殊处理直辖市
  if (['北京市', '天津市', '上海市', '重庆市'].includes(name)) {
    const directCities = {
      '北京市': '110000',
      '天津市': '120000',
      '上海市': '310000',
      '重庆市': '500000'
    }
    return directCities[name]
  }

  // 处理省/自治区/特别行政区
  const provinceMap = {
    '河北省': '130000',
    '山西省': '140000',
    '内蒙古自治区': '150000',
    '辽宁省': '210000',
    '吉林省': '220000',
    '黑龙江省': '230000',
    '江苏省': '320000',
    '浙江省': '330000',
    '安徽省': '340000',
    '福建省': '350000',
    '江西省': '360000',
    '山东省': '370000',
    '河南省': '410000',
    '湖北省': '420000',
    '湖南省': '430000',
    '广东省': '440000',
    '广西壮族自治区': '450000',
    '海南省': '460000',
    '四川省': '510000',
    '贵州省': '520000',
    '云南省': '530000',
    '西藏自治区': '540000',
    '陕西省': '610000',
    '甘肃省': '620000',
    '青海省': '630000',
    '宁夏回族自治区': '640000',
    '新疆维吾尔自治区': '650000',
    '台湾省': '710000',
    '香港特别行政区': '810000',
    '澳门特别行政区': '820000'
  }

  return provinceMap[name] || ''
}

// 根据城市名称和省份编码获取城市编码
const getCityCodeByName = (name, provinceCode) => {
  // 移除"市"字进行匹配
  const cleanName = name.replace('市', '')

  // 查找城市编码
  for (const [cityPinyin, code] of Object.entries(regionCodes)) {
    // 将拼音转换为中文城市名进行匹配
    const cityName = cityPinyin.charAt(0).toUpperCase() + cityPinyin.slice(1)
    if (cityName.includes(cleanName) && code.startsWith(provinceCode.substring(0, 2))) {
      return code
    }
  }

  return ''
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
    currentSelectedCode.value = '100000'
    emit('level-change', {
      level: 'country',
      code: '100000'
    })
    updateChart()
  }
}

// 初始化图表
const initChart = async () => {
  if (!mapContainer.value) return

  // 初始化ECharts实例
  chart.value = echarts.init(mapContainer.value)

  // 设置初始选项
  const option = generateOption('100000')
  chart.value.setOption(option)

  // 绑定点击事件
  chart.value.on('click', 'series.map', handleMapClick)

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

// 窗口大小变化处理
const handleResize = () => {
  if (chart.value) {
    chart.value.resize()
  }
}

// 组件挂载
onMounted(async () => {
  await nextTick()
  initChart()
})

// 组件卸载
onUnmounted(() => {
  if (chart.value) {
    chart.value.dispose()
  }
  window.removeEventListener('resize', handleResize)
})

// 暴露方法给父组件
defineExpose({
  goBack,
  updateChart
})
</script>

<style scoped>
.map-wrapper {
  width: 100%;
}

.map-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.back-button {
  padding: 0;
  height: auto;
}

.map-title {
  flex: 1;
  text-align: center;
  font-weight: bold;
  font-size: 16px;
}

.echarts-map {
  width: 100%;
}

.level-country {
  height: 500px;
}

.level-province {
  height: 500px;
}

.level-city {
  height: 500px;
}
</style>