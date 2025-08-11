import regionCodes from '@/utils/regionCodes.js'

// 地图注册表
export const mapRegistry = new Map()

// 根据编码获取名称
export const getNameByCode = (code) => {
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
export const loadMapData = async (mapType) => {
  // 如果地图已经加载过，则直接返回
  if (mapRegistry.has(mapType)) {
    return mapRegistry.get(mapType)
  }

  try {
    let geoJsonUrl
    if (mapType === '100000') {
      // 全国地图
      geoJsonUrl = '/100000/100000.geoJson'
    } else if (mapType.length === 6 && mapType.endsWith('0000') && mapType !== '100000') {
      // 省级地图
      geoJsonUrl = `/100000/${mapType}.geoJson`
    } else if (mapType.length === 6 && !mapType.endsWith('0000')) {
      // 市级地图
      const provinceCode = mapType.substring(0, 2) + '0000'
      geoJsonUrl = `/100000/${provinceCode}/${mapType}.geoJson`
    }

    if (geoJsonUrl) {
      const response = await fetch(geoJsonUrl)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const geoJson = await response.json()
      mapRegistry.set(mapType, geoJson)
      return geoJson
    }
  } catch (error) {
    console.error(`加载地图数据失败 ${mapType}:`, error)
  }
  return null
}

// 根据省份名称获取省份编码
export const getProvinceCodeByName = (name) => {
  // 将首字母大写转换为小写
  const normalizedName = name.charAt(0).toLowerCase() + name.slice(1)
  return regionCodes[normalizedName] || null
}
import regionCodes from '@/utils/regionCodes.js'

// 地图注册表
export const mapRegistry = new Map()

// 根据编码获取名称
export const getNameByCode = (code) => {
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
export const loadMapData = async (mapType) => {
  // 如果地图已经加载过，则直接返回
  if (mapRegistry.has(mapType)) {
    return mapRegistry.get(mapType)
  }

  try {
    let geoJsonUrl
    if (mapType === '100000') {
      // 全国地图
      geoJsonUrl = '/100000/100000.geoJson'
    } else if (mapType.length === 6 && mapType.endsWith('0000') && mapType !== '100000') {
      // 省级地图
      geoJsonUrl = `/100000/${mapType}.geoJson`
    } else if (mapType.length === 6 && !mapType.endsWith('0000')) {
      // 市级地图
      const provinceCode = mapType.substring(0, 2) + '0000'
      geoJsonUrl = `/100000/${provinceCode}/${mapType}.geoJson`
    }

    if (geoJsonUrl) {
      const response = await fetch(geoJsonUrl)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const geoJson = await response.json()
      mapRegistry.set(mapType, geoJson)
      return geoJson
    }
  } catch (error) {
    console.error(`加载地图数据失败 ${mapType}:`, error)
  }
  return null
}

// 根据省份名称获取省份编码
export const getProvinceCodeByName = (name) => {
  // 将首字母大写转换为小写
  const normalizedName = name.charAt(0).toLowerCase() + name.slice(1)
  return regionCodes[normalizedName] || null
}