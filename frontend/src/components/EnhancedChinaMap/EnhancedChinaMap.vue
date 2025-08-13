/**
 * 获取省份代码
 * @param {string} provinceName - 省份名称
 * @returns {string} 省份代码
 */
export function getProvinceCodeByName(provinceName) {
  // 这里应该根据实际数据结构和逻辑来实现
  // 以下为示例数据和逻辑
  const provinceCodeMap = {
    '北京市': '110000',
    '天津市': '120000',
    '河北省': '130000',
    // ...其他省份
  };
  return provinceCodeMap[provinceName] || '';
}
<template>
  <div class="map-wrapper">
    <div class="map-header" v-if="showHeader">
      <button v-if="currentLevel !== 'country'" @click="goBack" class="back-button">
        ← 返回上一级
      </button>
      <span class="map-title">{{ mapTitle }}</span>
    </div>
    <div ref="mapContainer" :class="['echarts-map', `level-${currentLevel}`]" :style="{ height }"></div>
    <div v-if="loadError" class="error-message">
      地图加载失败: {{ loadError }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getNameByCode, loadMapData, getProvinceCodeByName } from './mapUtils.js'
import { getProbeCount as getProbeCountUtil } from './mapStyling.js'
import { handleGoBack } from './mapInteractions.js'

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
const geoJson = ref(null)
const loadError = ref(null)

// 计算属性
const mapTitle = computed(() => {
  return getNameByCode(currentCode.value) || '全国'
})

// 获取区域的探针数量
const getProbeCount = (regionCode) => {
  // 首先尝试直接匹配区域名称
  const directMatch = props.mapData.find(item => item.name === regionCode)
  if (directMatch) {
    return directMatch.value
  }
  
  // 如果没有直接匹配，对于省份，尝试汇总其下属城市的数量
  // 定义所有省份与其城市的映射关系
  const provinceToCitiesMap = {
    '北京市': ['北京市'],
    '天津市': ['天津市'],
    '上海市': ['上海市'],
    '重庆市': ['重庆市'],
    '河北省': ['石家庄市', '唐山市', '秦皇岛市', '邯郸市', '邢台市', '保定市', '张家口市', '承德市', '沧州市', '廊坊市', '衡水市'],
    '山西省': ['太原市', '大同市', '阳泉市', '长治市', '晋城市', '朔州市', '晋中市', '运城市', '忻州市', '临汾市', '吕梁市'],
    '内蒙古自治区': ['呼和浩特市', '包头市', '乌海市', '赤峰市', '通辽市', '鄂尔多斯市', '呼伦贝尔市', '巴彦淖尔市', '乌兰察布市', '兴安盟', '锡林郭勒盟', '阿拉善盟'],
    '辽宁省': ['沈阳市', '大连市', '鞍山市', '抚顺市', '本溪市', '丹东市', '锦州市', '营口市', '阜新市', '辽阳市', '盘锦市', '铁岭市', '朝阳市', '葫芦岛市'],
    '吉林省': ['长春市', '吉林市', '四平市', '辽源市', '通化市', '白山市', '松原市', '白城市', '延边朝鲜族自治州'],
    '黑龙江省': ['哈尔滨市', '齐齐哈尔市', '鸡西市', '鹤岗市', '双鸭山市', '大庆市', '伊春市', '佳木斯市', '七台河市', '牡丹江市', '黑河市', '绥化市', '大兴安岭地区'],
    '江苏省': ['南京市', '无锡市', '徐州市', '常州市', '苏州市', '南通市', '连云港市', '淮安市', '盐城市', '扬州市', '镇江市', '泰州市', '宿迁市'],
    '浙江省': ['杭州市', '宁波市', '温州市', '嘉兴市', '湖州市', '绍兴市', '金华市', '衢州市', '舟山市', '台州市', '丽水市'],
    '安徽省': ['合肥市', '芜湖市', '蚌埠市', '淮南市', '马鞍山市', '淮北市', '铜陵市', '安庆市', '黄山市', '滁州市', '阜阳市', '宿州市', '六安市', '亳州市', '池州市', '宣城市'],
    '福建省': ['福州市', '厦门市', '莆田市', '三明市', '泉州市', '漳州市', '南平市', '龙岩市', '宁德市'],
    '江西省': ['南昌市', '景德镇市', '萍乡市', '九江市', '新余市', '鹰潭市', '赣州市', '吉安市', '宜春市', '抚州市', '上饶市'],
    '山东省': ['济南市', '青岛市', '淄博市', '枣庄市', '东营市', '烟台市', '潍坊市', '济宁市', '泰安市', '威海市', '日照市', '临沂市', '德州市', '聊城市', '滨州市', '菏泽市'],
    '河南省': ['郑州市', '开封市', '洛阳市', '平顶山市', '安阳市', '鹤壁市', '新乡市', '焦作市', '濮阳市', '许昌市', '漯河市', '三门峡市', '南阳市', '商丘市', '信阳市', '周口市', '驻马店市'],
    '湖北省': ['武汉市', '黄石市', '十堰市', '宜昌市', '襄阳市', '鄂州市', '荆门市', '孝感市', '荆州市', '黄冈市', '咸宁市', '随州市', '恩施土家族苗族自治州'],
    '湖南省': ['长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界市', '益阳市', '郴州市', '永州市', '怀化市', '娄底市', '湘西土家族苗族自治州'],
    '广东省': ['广州市', '深圳市', '珠海市', '汕头市', '佛山市', '韶关市', '湛江市', '肇庆市', '江门市', '茂名市', '惠州市', '梅州市', '汕尾市', '河源市', '阳江市', '清远市', '东莞市', '中山市', '潮州市', '揭阳市', '云浮市'],
    '广西壮族自治区': ['南宁市', '柳州市', '桂林市', '梧州市', '北海市', '防城港市', '钦州市', '贵港市', '玉林市', '百色市', '贺州市', '河池市', '来宾市', '崇左市'],
    '海南省': ['海口市', '三亚市', '三沙市', '儋州市'],
    '四川省': ['成都市', '自贡市', '攀枝花市', '泸州市', '德阳市', '绵阳市', '广元市', '遂宁市', '内江市', '乐山市', '南充市', '眉山市', '宜宾市', '广安市', '达州市', '雅安市', '巴中市', '资阳市', '阿坝藏族羌族自治州', '甘孜藏族自治州', '凉山彝族自治州'],
    '贵州省': ['贵阳市', '六盘水市', '遵义市', '安顺市', '毕节市', '铜仁市', '黔西南布依族苗族自治州', '黔东南苗族侗族自治州', '黔南布依族苗族自治州'],
    '云南省': ['昆明市', '曲靖市', '玉溪市', '保山市', '昭通市', '丽江市', '普洱市', '临沧市', '楚雄彝族自治州', '红河哈尼族彝族自治州', '文山壮族苗族自治州', '西双版纳傣族自治州', '大理白族自治州', '德宏傣族景颇族自治州', '怒江傈僳族自治州', '迪庆藏族自治州'],
    '西藏自治区': ['拉萨市', '日喀则市', '昌都市', '林芝市', '山南市', '那曲市', '阿里地区'],
    '陕西省': ['西安市', '铜川市', '宝鸡市', '咸阳市', '渭南市', '延安市', '汉中市', '榆林市', '安康市', '商洛市'],
    '甘肃省': ['兰州市', '嘉峪关市', '金昌市', '白银市', '天水市', '武威市', '张掖市', '平凉市', '酒泉市', '庆阳市', '定西市', '陇南市', '临夏回族自治州', '甘南藏族自治州'],
    '青海省': ['西宁市', '海东市', '海北藏族自治州', '黄南藏族自治州', '海南藏族自治州', '果洛藏族自治州', '玉树藏族自治州', '海西蒙古族藏族自治州'],
    '宁夏回族自治区': ['银川市', '石嘴山市', '吴忠市', '固原市', '中卫市'],
    '新疆维吾尔自治区': ['乌鲁木齐市', '克拉玛依市', '吐鲁番市', '哈密市', '昌吉回族自治州', '博尔塔拉蒙古自治州', '巴音郭楞蒙古自治州', '阿克苏地区', '克孜勒苏柯尔克孜自治州', '喀什地区', '和田地区', '伊犁哈萨克自治州', '塔城地区', '阿勒泰地区'],
    '台湾省': ['台北市', '新北市', '桃园市', '台中市', '台南市', '高雄市'],
    '香港特别行政区': ['香港特别行政区'],
    '澳门特别行政区': ['澳门特别行政区']
  }
  
  // 如果是省份，汇总其下属城市的监测点数量
  if (provinceToCitiesMap[regionCode]) {
    let totalCount = 0
    provinceToCitiesMap[regionCode].forEach(city => {
      const cityData = props.mapData.find(item => item.name === city)
      if (cityData) {
        totalCount += cityData.value
      }
    })
    return totalCount
  }
  
  // 默认返回0
  return 0
}

// 获取区域颜色
const getColorForRegion = (regionCode) => {
  const value = getProbeCount(regionCode)
  
  if (value > 10) return '#800026'
  if (value > 8) return '#BD0026'
  if (value > 6) return '#E31A1C'
  if (value > 4) return '#FC4E2A'
  if (value > 2) return '#FD8D3C'
  if (value > 1) return '#FEB24C'
  if (value > 0) return '#FED976'
  return '#4A90E2' // 默认蓝色
}

// 构建GeoJSON文件路径
const buildGeoJsonPath = (code, level) => {
  if (level === 'country') {
    return `/100000.geoJson`
  } else if (level === 'province') {
    return `/100000/${code}.geoJson`
  } else if (level === 'city') {
    const provinceCode = code.substring(0, 2) + '0000'
    return `/100000/${provinceCode}/${code}.geoJson`
  }
  return `/100000.geoJson`
}

// 加载GeoJSON数据
const loadGeoJsonData = async (code, level) => {
  const path = buildGeoJsonPath(code, level)
  try {
    const response = await fetch(path)
    if (!response.ok) {
      throw new Error(`Failed to load GeoJSON data: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Error loading GeoJSON data:', error)
    throw error
  }
}

// 初始化地图
const initMap = async () => {
  if (!mapContainer.value) return

  try {
    // 清除现有地图实例
    if (mapInstance.value) {
      echarts.dispose(mapInstance.value)
    }

    // 创建新地图实例
    mapInstance.value = echarts.init(mapContainer.value)
    
    // 加载初始地图数据
    const initialMapData = await loadGeoJsonData(currentCode.value, currentLevel.value)
    geoJson.value = initialMapData
    updateMap(initialMapData, currentLevel.value, currentCode.value)
    
    loadError.value = null
  } catch (error) {
    console.error('Failed to initialize map:', error)
    loadError.value = error.message
  }
}

// 更新地图
const updateMap = (data, level, code) => {
  if (!mapInstance.value) return

  try {
    // 更新状态
    currentLevel.value = level
    currentCode.value = code
    emit('update:level', level)
    emit('update:selectedCode', code)

    // 注册地图数据 - 使用正确的注册方式
    echarts.registerMap('MAP_' + code, data)

    // 配置地图选项
    const option = {
      tooltip: {
        trigger: 'item',
        showDelay: 0,
        transitionDuration: 0.2,
        formatter: (params) => {
          const regionName = params.name
          const probeCount = getProbeCount(regionName)
          return `${regionName}：监测点 ${probeCount} 个`
        },
        backgroundColor: 'rgba(30, 144, 255, 0.8)', // 蓝色背景
        borderColor: '#1E90FF',
        borderRadius: 4,
        textStyle: {
          color: '#fff',
          fontSize: 12
        },
        padding: [8, 12]
      },
      series: [
        {
          name: '中国地图',
          type: 'map',
          map: 'MAP_' + code,  // 使用注册时的名称
          selectedMode: 'single',
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: false
            }
          },
          itemStyle: {
            areaColor: '#4A90E2', // 直接设置默认颜色为蓝色
            borderColor: '#fff',
            borderWidth: 0.5
          },
          data: data.features.map(feature => {
            const regionName = feature.properties.name
            // 尝试从GeoJSON属性中获取区域代码，如果没有则使用区域名称
            const regionCode = feature.properties.adcode || feature.properties.code || regionName
            return {
              name: regionName,
              value: getProbeCount(regionName),
              code: regionCode
            }
          })
        }
      ]
    }

    // 渲染地图
    mapInstance.value.setOption(option, true)
    
    // 添加点击事件
    mapInstance.value.on('click', (params) => {
      handleRegionClick(params)
    })
  } catch (error) {
    console.error('Failed to update map:', error)
    loadError.value = error.message
  }
}

// 处理区域点击事件
const handleRegionClick = async (params) => {
  if (currentLevel.value === 'country') {
    // 从全国地图进入省级地图
    try {
      // 从GeoJSON属性中获取省份代码
      const provinceCode = params.data.code || getProvinceCodeByName(params.name)
      if (provinceCode && provinceCode !== '100000') {
        const provinceData = await loadGeoJsonData(provinceCode, 'province')
        updateMap(provinceData, 'province', provinceCode)
      }
    } catch (error) {
      console.error('Error handling region click:', error)
    }
  } else if (currentLevel.value === 'province') {
    // 从省级地图进入市级地图
    try {
      // 从GeoJSON属性中获取城市代码
      const cityCode = params.data.code
      if (cityCode && cityCode !== currentCode.value) {
        const cityData = await loadGeoJsonData(cityCode, 'city')
        updateMap(cityData, 'city', cityCode)
      }
    } catch (error) {
      console.error('Error handling city click:', error)
    }
  }
}

// 返回上一级
const goBack = () => {
  if (currentLevel.value === 'city') {
    // 从市级返回省级
    const provinceCode = currentCode.value.substring(0, 2) + '0000'
    loadGeoJsonData(provinceCode, 'province').then(provinceData => {
      updateMap(provinceData, 'province', provinceCode)
    })
  } else if (currentLevel.value === 'province') {
    // 从省级返回全国
    loadGeoJsonData('100000', 'country').then(countryData => {
      updateMap(countryData, 'country', '100000')
    })
  }
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
  if (mapInstance.value && geoJson.value) {
    updateMap(geoJson.value, currentLevel.value, currentCode.value)
  }
})

// 组件挂载时初始化地图
onMounted(() => {
  nextTick(() => {
    initMap()
    
    // 监听窗口大小变化
    window.addEventListener('resize', handleResize)
  })
})

// 组件卸载时清理地图
onUnmounted(() => {
  if (mapInstance.value) {
    echarts.dispose(mapInstance.value)
  }
  
  // 移除事件监听器
  window.removeEventListener('resize', handleResize)
})

// 处理窗口大小变化
const handleResize = () => {
  if (mapInstance.value) {
    mapInstance.value.resize()
  }
}

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

.echarts-map {
  width: 100%;
  background-color: rgb(22, 77, 58);
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