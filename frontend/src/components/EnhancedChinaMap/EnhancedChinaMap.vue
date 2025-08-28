/**
 * 获取省份代码
 * @param {string} provinceName - 省份名称
 * @returns {string} 省份代码
 */
export function getProvinceCodeByName(provinceName) {
  // 这里应该根据实际数据结构和逻辑来实现
  // 以下为示例数据和逻辑
  const provinceCodeMap = {
    '北京市': '110000',
    '天津市': '120000',
    '河北省': '130000',
    // ...其他省份
  };
  return provinceCodeMap[provinceName] || '';
}
<template>
  <div class="map-wrapper">
    <div class="map-header" v-if="showHeader">
      <button v-if="currentLevel !== 'country'" @click="goBack" class="back-button">
        ← 返回上一级
      </button>
      <span class="map-title">{{ mapTitle }}</span>
    </div>
    <div ref="mapContainer" :class="['echarts-map', `level-${currentLevel}`]" :style="{ height }"></div>
    <div v-if="loadError" class="error-message">
      地图加载失败: {{ loadError }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getNameByCode, loadMapData, getProvinceCodeByName } from './mapUtils.js'
import { getProbeCount as getProbeCountUtil } from './mapStyling.js'
import { handleGoBack } from './mapInteractions.js'

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
  // 告警数据按区域统计
  alertsByRegion: {
    type: Object,
    default: () => ({})
  },
  // 获取区域告警级别的函数
  getRegionAlertLevel: {
    type: Function,
    default: () => () => null
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
const emit = defineEmits(['regionClick', 'update:level', 'update:selectedCode'])

// 响应式数据
const mapContainer = ref(null)
const mapInstance = ref(null)
const currentLevel = ref(props.level)
const currentCode = ref(props.selectedCode)
const geoJson = ref(null)
const loadError = ref(null)

// 计算属性
const mapTitle = computed(() => {
  return getNameByCode(currentCode.value) || '全国'
})

// 获取区域的探针数量
const getProbeCount = (regionCode) => {
  //console.log('getProbeCount: 查找区域', regionCode)
  //console.log('getProbeCount: mapData结构', props.mapData)
  
  // 首先尝试直接匹配省份名称
  const provinceMatch = props.mapData.find(item => item.name === regionCode)
  if (provinceMatch) {
   // console.log('getProbeCount: 找到省份匹配', provinceMatch)
    return provinceMatch.value || 0
  }
  
  // 如果没有直接匹配省份，尝试在所有省份的城市中查找
  for (const province of props.mapData) {
    if (province.cities && province.cities[regionCode]) {
      const cityData = province.cities[regionCode]
    //  console.log('getProbeCount: 找到城市匹配', regionCode, cityData)
      return cityData.value || 0
    }
  }
  
  //console.log('getProbeCount: 未找到匹配，返回0', regionCode)
  // 默认返回0
  return 0
}

// 获取区域颜色
const getColorForRegion = (regionCode) => {
  // 优先根据告警级别确定颜色
  if (props.getRegionAlertLevel) {
    let alertLevel = null
    
    if (currentLevel.value === 'country' || currentLevel.value === 'province') {
      // 全国地图和省级地图：直接使用区域名称查询告警
      alertLevel = props.getRegionAlertLevel(regionCode)
    } else if (currentLevel.value === 'city') {
      // 市级地图：先尝试直接使用城市名称查询告警
      alertLevel = props.getRegionAlertLevel(regionCode)
      
      // 如果城市没有直接的告警数据，则查询所属省份的告警
      if (!alertLevel) {
        const provinceCode = currentCode.value.substring(0, 2) + '0000'
        const provinceName = getNameByCode(provinceCode)
        if (provinceName) {
          alertLevel = props.getRegionAlertLevel(provinceName)
        }
      }
    }
    
    if (alertLevel === 'critical') return '#ff4d4f' // 严重告警 - 红色
    if (alertLevel === 'warning') return '#faad14'  // 警告告警 - 黄色
    if (alertLevel === 'info') return '#1890ff'     // 信息告警 - 深蓝色
  }
  
  // 如果没有告警，根据拨测点数量确定颜色
  const value = getProbeCount(regionCode)
  
  if (value > 10) return '#800026'
  if (value > 8) return '#BD0026'
  if (value > 6) return '#E31A1C'
  if (value > 4) return '#FC4E2A'
  if (value > 2) return '#FD8D3C'
  if (value > 1) return '#FEB24C'
  if (value > 0) return '#FED976'
  return '#4A90E2' // 默认蓝色
}

// 构建GeoJSON文件路径
const buildGeoJsonPath = (code, level) => {
  if (level === 'country') {
    return `/100000.geoJson`
  } else if (level === 'province') {
    return `/100000/${code}.geoJson`
  } else if (level === 'city') {
    const provinceCode = code.substring(0, 2) + '0000'
    return `/100000/${provinceCode}/${code}.geoJson`
  }
  return `/100000.geoJson`
}

// 加载GeoJSON数据
const loadGeoJsonData = async (code, level) => {
  const path = buildGeoJsonPath(code, level)
  try {
    const response = await fetch(path)
    if (!response.ok) {
      throw new Error(`Failed to load GeoJSON data: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Error loading GeoJSON data:', error)
    throw error
  }
}

// 初始化地图
const initMap = async () => {
  if (!mapContainer.value) return

  try {
    // 清除现有地图实例
    if (mapInstance.value) {
      echarts.dispose(mapInstance.value)
    }

    // 创建新地图实例
    mapInstance.value = echarts.init(mapContainer.value)
    
    // 加载初始地图数据
    const initialMapData = await loadGeoJsonData(currentCode.value, currentLevel.value)
    geoJson.value = initialMapData
    updateMap(initialMapData, currentLevel.value, currentCode.value)
    
    loadError.value = null
  } catch (error) {
    console.error('Failed to initialize map:', error)
    loadError.value = error.message
  }
}

// 更新地图
const updateMap = (data, level, code) => {
  if (!mapInstance.value) return

  try {
    // 更新状态
    currentLevel.value = level
    currentCode.value = code
    emit('update:level', level)
    emit('update:selectedCode', code)

    // 注册地图数据 - 使用正确的注册方式
    echarts.registerMap('MAP_' + code, data)

    // 配置地图选项
    const option = {
      tooltip: {
        trigger: 'item',
        showDelay: 0,
        transitionDuration: 0.2,
        formatter: (params) => {
          const regionName = params.name
          const probeCount = getProbeCount(regionName)
          let tooltip = `${regionName}：监测点 ${probeCount} 个`
          
          // 添加告警信息
          if (props.getRegionAlertLevel) {
            const alertLevel = props.getRegionAlertLevel(regionName)
            if (alertLevel) {
              const alertText = alertLevel === 'critical' ? '严重告警' : 
                               alertLevel === 'warning' ? '警告告警' : '信息告警'
              tooltip += `<br/>告警状态：${alertText}`
            }
          }
          
          return tooltip
        },
        backgroundColor: 'rgba(30, 144, 255, 0.8)', // 蓝色背景
        borderColor: '#1E90FF',
        borderRadius: 4,
        textStyle: {
          color: '#fff',
          fontSize: 12
        },
        padding: [8, 12]
      },
      series: [
        {
          name: '中国地图',
          type: 'map',
          map: 'MAP_' + code,  // 使用注册时的名称
          selectedMode: 'single',
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: false
            }
          },
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 0.5
          },
          data: data.features.map(feature => {
            const regionName = feature.properties.name
            // 尝试从GeoJSON属性中获取区域代码，如果没有则使用区域名称
            const regionCode = feature.properties.adcode || feature.properties.code || regionName
            return {
              name: regionName,
              value: getProbeCount(regionName),
              code: regionCode,
              itemStyle: {
                areaColor: getColorForRegion(regionName)
              }
            }
          })
        }
      ]
    }

    // 渲染地图
    mapInstance.value.setOption(option, true)
    
    // 添加点击事件
    mapInstance.value.on('click', (params) => {
      handleRegionClick(params)
    })
  } catch (error) {
    console.error('Failed to update map:', error)
    loadError.value = error.message
  }
}

// 处理区域点击事件
const handleRegionClick = async (params) => {
  if (currentLevel.value === 'country') {
    // 从全国地图进入省级地图
    try {
      // 从GeoJSON属性中获取省份代码
      const provinceCode = params.data.code || getProvinceCodeByName(params.name)
      if (provinceCode && provinceCode !== '100000') {
        const provinceData = await loadGeoJsonData(provinceCode, 'province')
        updateMap(provinceData, 'province', provinceCode)
      }
    } catch (error) {
      console.error('Error handling region click:', error)
    }
  } else if (currentLevel.value === 'province') {
    // 从省级地图进入市级地图
    try {
      // 从GeoJSON属性中获取城市代码
      const cityCode = params.data.code
      if (cityCode && cityCode !== currentCode.value) {
        const cityData = await loadGeoJsonData(cityCode, 'city')
        updateMap(cityData, 'city', cityCode)
      }
    } catch (error) {
      console.error('Error handling city click:', error)
    }
  }
}

// 返回上一级
const goBack = () => {
  if (currentLevel.value === 'city') {
    // 从市级返回省级
    const provinceCode = currentCode.value.substring(0, 2) + '0000'
    loadGeoJsonData(provinceCode, 'province').then(provinceData => {
      updateMap(provinceData, 'province', provinceCode)
    })
  } else if (currentLevel.value === 'province') {
    // 从省级返回全国
    loadGeoJsonData('100000', 'country').then(countryData => {
      updateMap(countryData, 'country', '100000')
    })
  }
}

// 监听属性变化
watch(() => props.level, (newLevel) => {
  currentLevel.value = newLevel
})

watch(() => props.selectedCode, (newCode) => {
  currentCode.value = newCode
})

watch(() => props.mapData, () => {
  // 重新加载地图数据以反映新的探针数据
  if (mapInstance.value && geoJson.value) {
    updateMap(geoJson.value, currentLevel.value, currentCode.value)
  }
})

// 组件挂载时初始化地图
onMounted(() => {
  nextTick(() => {
    initMap()
    
    // 监听窗口大小变化
    window.addEventListener('resize', handleResize)
  })
})

// 组件卸载时清理地图
onUnmounted(() => {
  if (mapInstance.value) {
    echarts.dispose(mapInstance.value)
  }
  
  // 移除事件监听器
  window.removeEventListener('resize', handleResize)
})

// 处理窗口大小变化
const handleResize = () => {
  if (mapInstance.value) {
    mapInstance.value.resize()
  }
}

// 暴露方法给父组件
defineExpose({
  updateMap,
  initMap
})
</script>

<style scoped>
.map-wrapper {
  position: relative;
}

.map-header {
  display: flex;
  align-items: center;
  padding: 10px;
  background-color:#f5f5f5;
}

.back-button {
  margin-right: 10px;
  padding: 5px 10px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.back-button:hover {
  background-color: #40a9ff;
}

.map-title {
  font-size: 16px;
  font-weight: bold;
}

.echarts-map {
  width: 100%;
  background-color: rgb(22, 77, 58);
}

.error-message {
  color: red;
  padding: 10px;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  margin-top: 10px;
}
</style>