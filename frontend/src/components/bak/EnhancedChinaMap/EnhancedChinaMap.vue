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
const emit = defineEmits(['regionClick', 'update:level', 'update:selectedCode'])

// 响应式数据
const mapContainer = ref(null)
const mapInstance = ref(null)
const currentLevel = ref(props.level)
const currentCode = ref(props.selectedCode)
const geoJsonLayer = ref(null)
const loadError = ref(null)

// 计算属性
const mapTitle = computed(() => {
  return getNameByCode(currentCode.value) || '全国'
})

// 初始化地图
const initMap = async () => {
  if (!mapContainer.value) return

  try {
    // 清除现有地图实例
    if (mapInstance.value) {
      mapInstance.value.remove()
    }

    // 创建新地图实例
    mapInstance.value = L.map(mapContainer.value).setView([35.8617, 104.1954], 4)
    
    // 添加地图瓦片图层
    //L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    // attribution: '© OpenStreetMap contributors'
    // }).addTo(mapInstance.value)

    // 加载初始地图数据
    const initialMapData = await loadMapData(currentCode.value, currentLevel.value)
    updateMap(initialMapData, currentLevel.value, currentCode.value, mapTitle.value)
    
    loadError.value = null
  } catch (error) {
    console.error('Failed to initialize map:', error)
    loadError.value = error.message
  }
}

// 更新地图
const updateMap = (data, level, code, name) => {
  if (!mapInstance.value) return

  try {
    // 更新状态
    currentLevel.value = level
    currentCode.value = code
    emit('update:level', level)
    emit('update:selectedCode', code)

    // 清除现有图层
    if (geoJsonLayer.value) {
      mapInstance.value.removeLayer(geoJsonLayer.value)
    }

    // 添加新的GeoJSON图层
    geoJsonLayer.value = L.geoJson(data, {
      style: (feature) => ({
        fillColor: getColorForRegion(feature, props.mapData),
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
      }),
      onEachFeature: (feature, layer) => {
        createOnEachFeature(feature, layer, props.mapData)
        
        // 保存原始样式
        const originalStyle = {
          fillColor: getColorForRegion(feature, props.mapData),
          weight: 2,
          opacity: 1,
          color: 'white',
          dashArray: '3',
          fillOpacity: 0.7
        };
        
        // 添加鼠标事件
        layer.on({
          mouseover: (e) => {
            const layer = e.target;
            
            // 高亮显示区域（蓝色）
            layer.setStyle({
              fillColor: '#3388ff',
              weight: 3,
              color: '#2074b6',
              fillOpacity: 0.9
            });
            
            // 显示信息框
            const regionCode = feature.properties.adcode || feature.properties.id;
            const probeCount = getProbeCount(feature.properties.name, props.mapData);
            const tooltipContent = `
              <div class="region-tooltip">
                <div class="region-name">${feature.properties.name}</div>
                <div class="probe-count">监测点总数: ${probeCount}</div>
              </div>
            `;
            
            layer.bindTooltip(tooltipContent, {
              permanent: false,
              direction: 'top',
              offset: [0, -10],
              className: 'region-tooltip-wrapper'
            }).openTooltip();
          },
          mouseout: (e) => {
            // 恢复原始样式
            layer.setStyle(originalStyle);
            
            // 关闭信息框
            e.target.closeTooltip();
          },
          click: (e) => {
            handleRegionClick(feature, layer, mapInstance.value, currentLevel.value, currentCode.value, updateMap)
          }
        })
      }
    }).addTo(mapInstance.value)

    // 调整视图以适应数据边界
    mapInstance.value.fitBounds(geoJsonLayer.value.getBounds())
  } catch (error) {
    console.error('Failed to update map:', error)
    loadError.value = error.message
  }
}

// 返回上一级
const goBack = () => {
  handleGoBack(mapInstance.value, currentLevel.value, currentCode.value, initMap, updateMap)
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
  if (mapInstance.value && geoJsonLayer.value) {
    // 重新初始化地图以更新数据
    initMap()
  }
})

// 组件挂载时初始化地图
onMounted(() => {
  nextTick(() => {
    initMap()
  })
})

// 组件卸载时清理地图
onUnmounted(() => {
  if (mapInstance.value) {
    mapInstance.value.remove()
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

.leaflet-map {
  width: 100%;
   background-color:rgb(22, 77, 58);
}

.error-message {
  color: red;
  padding: 10px;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  margin-top: 10px;
}

.region-label-text {
  color: white;
  font-size: 12px;
  font-weight: bold;
  text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
}

.region-tooltip-wrapper {
  background-color: rgba(0, 0, 0, 0.8);
  border-radius: 8px;
  box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  padding: 8px 12px;
  text-align: center;
  border: none;
  font-family: inherit;
}

.region-tooltip {
  color: white;
}

.region-name {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 4px;
}

.probe-count {
  font-size: 12px;
}
</style>