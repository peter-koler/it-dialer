// 区域代码到名称的映射
export const CODE_TO_NAME = {
  '110000': '北京市',
  '120000': '天津市',
  '130000': '河北省',
  '310000': '上海市',
  // 添加更多区域代码和名称
}

// 区域名称到代码的映射
export const NAME_TO_CODE = Object.entries(CODE_TO_NAME).reduce((acc, [code, name]) => {
  acc[name] = code
  return acc
}, {})

// 缓存已加载的地图数据
const mapDataCache = new Map()

/**
 * 根据区域代码获取区域名称
 * @param {string} code - 区域代码
 * @returns {string} 区域名称
 */
export function getNameByCode(code) {
  return CODE_TO_NAME[code] || ''
}

/**
 * 根据区域名称获取区域代码
 * @param {string} name - 区域名称
 * @returns {string} 区域代码
 */
export function getCodeByName(name) {
  return NAME_TO_CODE[name] || ''
}

/**
 * 获取GeoJSON文件路径
 * @param {string} code - 区域代码
 * @returns {string} GeoJSON文件路径
 */
export function getGeoJsonPath(code) {
  // 这里假设GeoJSON文件存储在public目录下
  // 文件命名格式为: 区域代码.geoJson
  return `/public/${code}.geoJson`
}

/**
 * 加载GeoJSON数据
 * @param {string} code - 区域代码
 * @returns {Promise<Object>} GeoJSON数据
 */
export async function loadGeoJsonData(code) {
  // 检查缓存
  if (mapDataCache.has(code)) {
    return mapDataCache.get(code)
  }
  
  try {
    const response = await fetch(getGeoJsonPath(code))
    if (!response.ok) {
      throw new Error(`无法加载GeoJSON数据: ${response.status} ${response.statusText}`)
    }
    const geoJsonData = await response.json()
    // 缓存数据
    mapDataCache.set(code, geoJsonData)
    return geoJsonData
  } catch (error) {
    console.error(`加载GeoJSON数据时出错 (${code}):`, error)
    throw error
  }
}

/**
 * 获取区域中心点坐标
 * @param {Object} geoJson - GeoJSON数据
 * @returns {Array<number>} 中心点坐标 [经度, 纬度]
 */
export function getRegionCenter(geoJson) {
  // 简化的中心点计算 - 实际应用中可能需要更复杂的算法
  if (geoJson.features && geoJson.features.length > 0) {
    const coordinates = geoJson.features[0].geometry.coordinates[0]
    if (coordinates && coordinates.length > 0) {
      // 计算所有坐标的平均值作为中心点
      const sum = coordinates.reduce((acc, coord) => {
        acc[0] += coord[0]
        acc[1] += coord[1]
        return acc
      }, [0, 0])
      
      return [sum[0] / coordinates.length, sum[1] / coordinates.length]
    }
  }
  return [104.1954, 35.8617] // 默认为中国中心点
}

/**
 * 加载地图数据
 * @param {string} mapType - 地图类型（区域代码）
 * @returns {Promise<Object|null>} GeoJSON数据
 */
export async function loadMapData(mapType) {
  // 检查缓存
  if (mapDataCache.has(mapType)) {
    console.log(`Loading map data from cache for type: ${mapType}`) // 调试用
    return mapDataCache.get(mapType)
  }

  try {
    console.log(`Fetching map data for type: ${mapType}`) // 调试用
    
    // 构建GeoJSON文件路径
    let geoJsonPath
    
    if (mapType === '100000') {
      // 全国地图
      geoJsonPath = '/100000.geoJson'
    } else if (mapType.length === 6 && mapType.endsWith('0000') && mapType !== '100000') {
      // 省级地图
      geoJsonPath = `/${mapType}.geoJson`
    } else if (mapType.length === 6 && !mapType.endsWith('0000')) {
      // 市级地图
      const provinceCode = mapType.substring(0, 2) + '0000'
      geoJsonPath = `/${provinceCode}/${mapType}.geoJson`
    }
    
    if (!geoJsonPath) {
      throw new Error(`Invalid map type: ${mapType}`)
    }
    
    // 发起请求获取GeoJSON数据
    const response = await fetch(geoJsonPath)
    
    if (!response.ok) {
      throw new Error(`Failed to load map data: ${response.status} ${response.statusText}`)
    }
    
    const geoJson = await response.json()
    console.log(`Successfully loaded map data for type: ${mapType}`) // 调试用
    
    // 缓存数据
    mapDataCache.set(mapType, geoJson)
    
    return geoJson
  } catch (error) {
    console.error(`Error loading map data for type ${mapType}:`, error)
    return null
  }
}

/**
 * 获取子区域列表
 * @param {string} parentCode - 父级区域代码
 * @returns {Array} 子区域列表
 */
export function getChildRegions(parentCode) {
  // 这里应该根据父级区域代码获取子区域列表
  // 实际项目中可能需要从服务器获取或使用本地数据
  return []
}

export default {
  getNameByCode,
  getCodeByName,
  loadMapData,
  getChildRegions
}

// 根据省份名称获取省份编码
export const getProvinceCodeByName = (name) => {
  // 将首字母大写转换为小写
  const normalizedName = name.charAt(0).toLowerCase() + name.slice(1)
  return regionCodes[normalizedName] || null
}