<template>
  <div class="map-wrapper">
    <div class="map-header" v-if="showHeader">
      <button v-if="currentLevel !== 'country'" @click="goBack" class="back-button">
        ← 返回上一级
      </button>
      <span class="map-title">{{ mapTitle }}</span>
    </div>
    <div ref="mapContainer" :class="['leaflet-map', `level-${currentLevel}`]" :style="{ height }"></div>
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
const currentLevel = ref(props.level)
const currentSelectedCode = ref(props.selectedCode)
const geoJsonLayer = ref(null)

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

// 监听数据变化
watch(() => props.mapData, () => {
  updateMap()
}, { deep: true })

// 监听层级变化
watch(() => props.level, (newLevel) => {
  currentLevel.value = newLevel
  updateMap()
})

// 监听选中区域变化
watch(() => props.selectedCode, (newCode) => {
  currentSelectedCode.value = newCode
  updateMap()
})

// 更新地图
const updateMap = async () => {
  if (!map.value) return

  let mapType = '100000'
  if (currentLevel.value === 'province' && currentSelectedCode.value) {
    mapType = currentSelectedCode.value
  } else if (currentLevel.value === 'city' && currentSelectedCode.value) {
    mapType = currentSelectedCode.value
  }

  // 加载地图数据
  const geoJson = await loadMapData(mapType)
  if (!geoJson) return

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
  map.value.fitBounds(geoJsonLayer.value.getBounds())
}

// 返回上一级
const goBack = () => {
  handleGoBack(currentLevel, currentSelectedCode, emit, updateMap)
}

// 初始化地图
const initMap = async () => {
  if (!mapContainer.value) return

  // 创建地图实例
  map.value = L.map(mapContainer.value).setView([35.8617, 104.1954], 4)

  // 添加基础瓦片图层
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map.value)

  // 加载初始地图数据
  await updateMap()
}

// 组件挂载
onMounted(async () => {
  await nextTick()
  initMap()
})

// 组件卸载
onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})

// 暴露方法给父组件
defineExpose({
  goBack,
  updateMap
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
  background: none;
  border: none;
  color: #1890ff;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
}

.back-button:hover {
  color: #40a9ff;
}

.map-title {
  flex: 1;
  text-align: center;
  font-weight: bold;
  font-size: 16px;
}

.leaflet-map {
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
<template>
  <div class="map-wrapper">
    <div class="map-header" v-if="showHeader">
      <button v-if="currentLevel !== 'country'" @click="goBack" class="back-button">
        ← 返回上一级
      </button>
      <span class="map-title">{{ mapTitle }}</span>
    </div>
    <div ref="mapContainer" :class="['leaflet-map', `level-${currentLevel}`]" :style="{ height }"></div>
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
const currentLevel = ref(props.level)
const currentSelectedCode = ref(props.selectedCode)
const geoJsonLayer = ref(null)

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

// 监听数据变化
watch(() => props.mapData, () => {
  updateMap()
}, { deep: true })

// 监听层级变化
watch(() => props.level, (newLevel) => {
  currentLevel.value = newLevel
  updateMap()
})

// 监听选中区域变化
watch(() => props.selectedCode, (newCode) => {
  currentSelectedCode.value = newCode
  updateMap()
})

// 更新地图
const updateMap = async () => {
  if (!map.value) return

  let mapType = '100000'
  if (currentLevel.value === 'province' && currentSelectedCode.value) {
    mapType = currentSelectedCode.value
  } else if (currentLevel.value === 'city' && currentSelectedCode.value) {
    mapType = currentSelectedCode.value
  }

  // 加载地图数据
  const geoJson = await loadMapData(mapType)
  if (!geoJson) return

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
  map.value.fitBounds(geoJsonLayer.value.getBounds())
}

// 返回上一级
const goBack = () => {
  handleGoBack(currentLevel, currentSelectedCode, emit, updateMap)
}

// 初始化地图
const initMap = async () => {
  if (!mapContainer.value) return

  // 创建地图实例
  map.value = L.map(mapContainer.value).setView([35.8617, 104.1954], 4)

  // 添加基础瓦片图层
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map.value)

  // 加载初始地图数据
  await updateMap()
}

// 组件挂载
onMounted(async () => {
  await nextTick()
  initMap()
})

// 组件卸载
onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})

// 暴露方法给父组件
defineExpose({
  goBack,
  updateMap
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
  background: none;
  border: none;
  color: #1890ff;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
}

.back-button:hover {
  color: #40a9ff;
}

.map-title {
  flex: 1;
  text-align: center;
  font-weight: bold;
  font-size: 16px;
}

.leaflet-map {
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