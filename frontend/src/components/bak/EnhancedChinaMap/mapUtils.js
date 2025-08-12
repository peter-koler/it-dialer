import regionCodes from '@/utils/regionCodes'

/**
 * 根据区域代码获取区域名称
 * @param {string} code - 区域代码
 * @returns {string} 区域名称
 */
export function getNameByCode(code) {
  // 这应该从完整的映射表中获取，这里只是示例
  const codeMap = {
    '100000': '全国',
    '110000': '北京市',
    '120000': '天津市',
    '310000': '上海市',
    '440000': '广东省',
    '440100': '广州市',
    '440300': '深圳市'
    // 更多映射...
  }
  return codeMap[code] || code
}

/**
 * 根据省份名称获取省份代码
 * @param {string} name - 省份名称
 * @returns {string} 省份代码
 */
export function getProvinceCodeByName(name) {
  // 处理特殊名称
  const nameMapping = {
    '广东省': '440000',
    '北京市': '110000',
    '天津市': '120000',
    '上海市': '310000',
    '重庆市': '500000',
    '河北省': '130000',
    '山西省': '140000',
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
    '海南省': '460000',
    '四川省': '510000',
    '贵州省': '520000',
    '云南省': '530000',
    '陕西省': '610000',
    '甘肃省': '620000',
    '青海省': '630000',
    '台湾省': '710000',
    '内蒙古自治区': '150000',
    '广西壮族自治区': '450000',
    '西藏自治区': '540000',
    '宁夏回族自治区': '640000',
    '新疆维吾尔自治区': '650000',
    '香港特别行政区': '810000',
    '澳门特别行政区': '820000'
  }
  
  return nameMapping[name] || null
}

/**
 * 加载地图数据
 * @param {string} code - 区域代码
 * @param {'country'|'province'|'city'} level - 区域级别
 * @returns {Promise<Object>} 地图数据
 */
export async function loadMapData(code, level = 'country') {
  console.log('Fetching map data for code:', code, 'level:', level)
  
  let url
  if (level === 'country') {
    // 全国地图
    url = `/100000.geoJson`
  } else if (level === 'province') {
    // 省级地图 - 实际在 /100000/{code}.geoJson
    url = `/100000/${code}.geoJson`
  } else if (level === 'city') {
    // 市级地图 - 需要知道所属省份
    // 从code推断所属省份 (前两位数字 + "0000")
    const provinceCode = code.substring(0, 2) + '0000'
    url = `/100000/${provinceCode}/${code}.geoJson`
  }
  
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to load map data: ${response.status}`)
    }
    const data = await response.json()
    console.log('Successfully loaded map data for code:', code)
    return data
  } catch (error) {
    console.error('Failed to load map data for code:', code, error)
    throw error
  }
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
  getProvinceCodeByName,
  loadMapData,
  getChildRegions
}

