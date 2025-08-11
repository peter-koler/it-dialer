import { getProvinceCodeByName } from './mapUtils.js'

// 区域点击事件
export const handleRegionClick = (e, props, currentLevel, currentSelectedCode, emit, updateMap) => {
  const regionName = e.target.feature.properties.name
  const getProbeCount = (regionName) => {
    const regionData = props.mapData.find(item => item.name === regionName)
    return regionData ? regionData.value : 0
  }
  const probeCount = getProbeCount(regionName)
  
  emit('region-click', {
    name: regionName,
    value: probeCount,
    level: currentLevel.value
  })

  // 根据当前层级决定是否需要下钻
  if (currentLevel.value === 'country') {
    // 从全国下钻到省份
    const provinceCode = getProvinceCodeByName(regionName)
    if (provinceCode) {
      currentLevel.value = 'province'
      currentSelectedCode.value = provinceCode
      emit('level-change', {
        level: 'province',
        code: provinceCode
      })
      updateMap()
    }
  } else if (currentLevel.value === 'province') {
    // 省级层级只选择，不下钻
    // 可以在这里添加其他逻辑
  }
}

// 返回上一级
export const handleGoBack = (currentLevel, currentSelectedCode, emit, updateMap) => {
  if (currentLevel.value === 'city') {
    // 从城市返回省份
    currentLevel.value = 'province'
    emit('level-change', {
      level: 'province',
      code: currentSelectedCode.value.substring(0, 2) + '0000'
    })
    updateMap()
  } else if (currentLevel.value === 'province') {
    // 从省份返回全国
    currentLevel.value = 'country'
    currentSelectedCode.value = '100000'
    emit('level-change', {
      level: 'country',
      code: '100000'
    })
    updateMap()
  }
}