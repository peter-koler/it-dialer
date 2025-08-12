<template>
  <div class="map-wrapper">
    <div class="map-header" v-if="showHeader">
      <button v-if="currentLevel !== 'country'" @click="goBack" class="back-button">
        ← 返回上一级
      </button>
      <span class="map-title">{{ mapTitle }}</span>
    </div>
    <div ref="mapContainer" :class="['leaflet-map', `level-${currentLevel}`]" :style="{ height }"></div>
    <div v-if="loadError" class="error-message">
      地图加载失败: {{ loadError }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getNameByCode, loadMapData } from './mapUtils.js'
import { getColorForRegion, createOnEachFeature, getProbeCount, highlightFeature, resetHighlight } from './mapStyling.js'
import { handleRegionClick, handleGoBack } from './mapInteractions.js'

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
const map = ref(null)
const geoJsonLayer = ref(null)
const loadError = ref(null)

// 计算属性
const currentLevel = computed(() => props.level)
const currentSelectedCode = computed(() => props.selectedCode)
const mapType = computed(() => {
  if (currentLevel.value === 'country') return '100000'
  if (currentLevel.value === 'province') return currentSelectedCode.value
  if (currentLevel.value === 'city') return currentSelectedCode.value
  return '100000'
})

const mapTitle = computed(() => {
  if (currentLevel.value === 'country') return '全国'
  const name = getNameByCode(currentSelectedCode.value)
  return name || currentSelectedCode.value
})

// 更新地图
const updateMap = async () => {
  try {
    loadError.value = null
    console.log(`Updating map for type: ${mapType.value}`) // 调试用
    
    // 确保地图实例存在
    if (!map.value) {
      await initMap()
    }

    // 加载地图数据
    const geoJson = await loadMapData(mapType.value)
    if (!geoJson) {
      loadError.value = `无法加载地图数据: ${mapType.value}`
      console.error(loadError.value)
      return
    }

    // 清除现有图层
    if (geoJsonLayer.value) {
      map.value.removeLayer(geoJsonLayer.value)
    }

    // 创建回调函数
    const callbacks = {
      highlightFeature,
      resetHighlight: (e) => resetHighlight(e, geoJsonLayer),
      onRegionClick: (e) => handleRegionClick(e, props, currentLevel, currentSelectedCode, emit, updateMap),
      getProbeCount: (regionName) => getProbeCount(regionName, props.mapData)
    }

    // 创建新的GeoJSON图层
    geoJsonLayer.value = L.geoJSON(geoJson, {
      style: function (feature) {
        return {
          fillColor: getColorForRegion(feature.properties.name, props.mapData),
          weight: 2,
          opacity: 1,
          color: 'white',
          dashArray: '3',
          fillOpacity: 0.7
        };
      },
      onEachFeature: createOnEachFeature(props.mapData, callbacks)
    }).addTo(map.value)

    // 调整地图视图以适应GeoJSON边界
    try {
      const bounds = geoJsonLayer.value.getBounds()
      if (bounds.isValid()) {
        // 添加一些padding确保地图不会紧贴边缘
        map.value.fitBounds(bounds, { padding: [50, 50] })
      }
    } catch (boundsError) {
      console.warn('调整地图视图失败:', boundsError)
      // 如果获取边界失败，使用默认视图
      map.value.setView([35.8617, 104.1954], 4)
    }
  } catch (error) {
    loadError.value = error.message
    console.error('更新地图时出错:', error)
    // 尝试重置地图视图
    if (map.value) {
      map.value.setView([35.8617, 104.1954], 4)
    }
  } finally {
    // 确保在加载完成后移除加载状态
    // 这里可以添加加载完成的回调或事件
  }
}

// 返回上一级
const goBack = () => {
  handleGoBack(currentLevel, currentSelectedCode, emit, updateMap)
}

// 初始化地图
const initMap = async () => {
  try {
    console.log('Initializing map...') // 调试用
    
    // 确保容器已挂载
    if (!mapContainer.value) {
      console.error('Map container not found')
      return
    }

    // 如果地图已存在，先清理
    if (map.value) {
      map.value.remove()
      map.value = null
    }

    // 初始化地图 - 使用默认的OpenStreetMap图层
    map.value = L.map(mapContainer.value).setView([35.8617, 104.1954], 4)
    
    // 添加OpenStreetMap瓦片图层
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map.value)

    console.log('Map initialized successfully') // 调试用
    
    // 加载GeoJSON数据并更新地图
    await updateMap()
  } catch (error) {
    loadError.value = error.message
    console.error('初始化地图时出错:', error)
  }
}

// 监听属性变化
watch(() => [props.level, props.selectedCode], () => {
  console.log('Map props changed, updating map') // 调试用
  updateMap()
})

watch(() => props.mapData, (newData) => {
  console.log('Map data changed:', newData) // 调试用
  if (geoJsonLayer.value && map.value) {
    // 更新现有图层的样式以反映新的数据
    geoJsonLayer.value.eachLayer(layer => {
      const style = {
        fillColor: getColorForRegion(layer.feature.properties.name, props.mapData),
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
      }
      layer.setStyle(style)
    })
  }
}, { deep: true })

// 生命周期钩子
onMounted(async () => {
  console.log('EnhancedChinaMap mounted, initializing map') // 调试用
  // 延迟初始化地图，确保DOM完全渲染
  await nextTick()
  await initMap()
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})

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
  background-color: #f5f5f5;
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

.leaflet-map {
  width: 100%;
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