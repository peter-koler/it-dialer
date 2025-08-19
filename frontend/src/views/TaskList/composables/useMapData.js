import { ref } from 'vue'
import pinyinToChinese from '@/utils/pinyinToChinese.js'

/**
 * 地图数据管理 composable
 */
export function useMapData() {
  const mapData = ref([])
  const mapLevel = ref('country')
  const selectedMapCode = ref('')

  // 生成地图数据
  const generateMapData = (results) => {
    const locationMap = {}
    
    // 确保results是一个数组
    if (!Array.isArray(results)) {
      console.warn('generateMapData: results is not an array', results)
      return []
    }
    
    results.forEach(result => {
      // 使用agent_area作为位置标识，如果没有则尝试使用task.agent_ids
      let location = result.agent_area;
      if (!location && result.task && result.task.agent_ids && result.task.agent_ids.length > 0) {
        location = result.task.agent_ids[0];
      }
      
      // 如果仍然没有位置信息，则跳过
      if (!location) return;
      
      // 将拼音转换为中文
      const locationName = pinyinToChinese[location] || location
      
      if (!locationMap[locationName]) {
        locationMap[locationName] = {
          name: locationName,
          value: 0
        }
      }
      locationMap[locationName].value += 1
    })
    
    const mapDataArray = Object.values(locationMap)
    console.log('Generated map data:', mapDataArray) // 调试用
    return mapDataArray
  }

  // 处理地图区域点击
  const handleRegionClick = (regionInfo) => {
    console.log('点击了区域:', regionInfo)
    // 可以根据点击的区域筛选右侧表格数据
  }

  // 处理地图层级变化
  const handleLevelChange = (levelInfo) => {
    mapLevel.value = levelInfo.level
    selectedMapCode.value = levelInfo.code
    console.log('地图层级变化:', levelInfo)
  }

  // 重置地图状态
  const resetMapState = () => {
    mapLevel.value = 'country'
    selectedMapCode.value = ''
    mapData.value = []
  }

  return {
    mapData,
    mapLevel,
    selectedMapCode,
    generateMapData,
    handleRegionClick,
    handleLevelChange,
    resetMapState
  }
}