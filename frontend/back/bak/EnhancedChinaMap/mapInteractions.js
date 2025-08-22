import { loadMapData, getNameByCode, getProvinceCodeByName } from './mapUtils.js'
import { getColorForRegion, createOnEachFeature } from './mapStyling.js'

// 处理区域点击事件
export async function handleRegionClick(feature, layer, mapInstance, currentLevel, currentCode, updateMap) {
  console.log('Region clicked:', feature)
  
  // 如果当前是全国地图，点击进入省级地图
  if (currentLevel === 'country') {
    try {
      // 从feature properties中获取省级代码
      const provinceCode = feature.properties?.adcode || feature.properties?.id
      if (provinceCode && provinceCode !== '100000') {
        console.log(`Loading province map for ${feature.properties.name} (${provinceCode})`)
        const provinceData = await loadMapData(provinceCode, 'province')
        updateMap(provinceData, 'province', provinceCode, feature.properties.name)
      } else {
        console.warn(`Province code not found for: ${feature.properties?.name}`)
      }
    } catch (error) {
      console.error('Error handling region click:', error)
    }
  }
  // 如果当前是省级地图，点击进入市级地图
  else if (currentLevel === 'province') {
    try {
      // 从feature properties中获取市级代码
      const cityCode = feature.properties?.adcode || feature.properties?.id
      if (cityCode && cityCode !== currentCode) {
        console.log(`Loading city map for ${feature.properties.name} (${cityCode})`)
        const cityData = await loadMapData(cityCode, 'city')
        updateMap(cityData, 'city', cityCode, feature.properties.name)
      } else {
        console.warn(`City code not found for: ${feature.properties?.name}`)
      }
    } catch (error) {
      console.error('Error handling city click:', error)
    }
  }
}

// 处理返回上一级
export function handleGoBack(mapInstance, currentLevel, currentCode, initMap, updateMap) {
  if (currentLevel === 'city') {
    // 从市级返回省级
    const provinceCode = currentCode.substring(0, 2) + '0000';
    loadMapData(provinceCode, 'province').then(provinceData => {
      const provinceName = getNameByCode(provinceCode)
      updateMap(provinceData, 'province', provinceCode, provinceName)
    })
  } else if (currentLevel === 'province') {
    // 从省级返回全国
    loadMapData('100000', 'country').then(countryData => {
      updateMap(countryData, 'country', '100000', '全国')
    })
  }
}