// 为区域获取颜色
export const getColorForRegion = (regionName, mapData, getRegionAlertLevel) => {
  // 优先根据告警级别确定颜色
  if (getRegionAlertLevel) {
    const alertLevel = getRegionAlertLevel(regionName)
    if (alertLevel === 'critical') return '#ff4d4f' // 严重告警 - 红色
    if (alertLevel === 'warning') return '#faad14'  // 警告告警 - 黄色
    if (alertLevel === 'info') return '#1890ff'     // 信息告警 - 深蓝色
  }
  
  // 如果没有告警，根据拨测点数量确定颜色
  const regionData = mapData.find(item => item.name === regionName)
  const value = regionData ? regionData.value : 0
  
  if (value > 10) return '#800026'
  if (value > 8) return '#BD0026'
  if (value > 6) return '#E31A1C'
  if (value > 4) return '#FC4E2A'
  if (value > 2) return '#FD8D3C'
  if (value > 1) return '#FEB24C'
  if (value > 0) return '#FED976'
  return '#FFEDA0'
}

// 为每个要素添加交互
export const createOnEachFeature = (mapData, callbacks) => {
  const { highlightFeature, resetHighlight, onRegionClick, getProbeCount } = callbacks
  
  return (feature, layer) => {
    // 添加弹出框
    layer.bindPopup(`<b>${feature.properties.name}</b><br>拨测点数量: ${getProbeCount(feature.properties.name)}`)

    // 添加事件监听器
    layer.on({
      mouseover: highlightFeature,
      mouseout: resetHighlight,
      click: onRegionClick
    })
  }
}

// 获取区域的拨测点数量
export const getProbeCount = (regionName, mapData) => {
  const regionData = mapData.find(item => item.name === regionName)
  return regionData ? regionData.value : 0
}

// 高亮要素
export const highlightFeature = (e) => {
  const layer = e.target

  layer.setStyle({
    weight: 5,
    color: '#666',
    dashArray: '',
    fillOpacity: 0.7
  })

  layer.bringToFront()
}

// 重置高亮
export const resetHighlight = (e, geoJsonLayer) => {
  if (geoJsonLayer.value) {
    geoJsonLayer.value.resetStyle(e.target)
  }
}