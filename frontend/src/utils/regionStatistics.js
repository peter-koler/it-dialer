import pinyinToChinese from './pinyinToChinese'
import regionCodes from './regionCodes'

// 拼音到省份的映射关系
const pinyinToProvince = {
  // 直辖市
  'beijing': '北京市',
  'tianjin': '天津市', 
  'shanghai': '上海市',
  'chongqing': '重庆市',
  
  // 省份城市映射
  'shijiazhuang': '河北省',
  'tangshan': '河北省',
  'qinhuangdao': '河北省',
  'handan': '河北省',
  'xingtai': '河北省',
  'baoding': '河北省',
  'zhangjiakou': '河北省',
  'chengde': '河北省',
  'cangzhou': '河北省',
  'langfang': '河北省',
  'hengshui': '河北省',
  
  'taiyuan': '山西省',
  'datong': '山西省',
  'yangquan': '山西省',
  'changzhi': '山西省',
  'jincheng': '山西省',
  'shuozhou': '山西省',
  'jinzhong': '山西省',
  'yuncheng': '山西省',
  'xinzhou': '山西省',
  'linfen': '山西省',
  'lvliang': '山西省',
  
  'hohhot': '内蒙古自治区',
  'baotou': '内蒙古自治区',
  'wuhai': '内蒙古自治区',
  'chifeng': '内蒙古自治区',
  'tongliao': '内蒙古自治区',
  'ordos': '内蒙古自治区',
  'hulunbuir': '内蒙古自治区',
  'bayannur': '内蒙古自治区',
  'ulanqab': '内蒙古自治区',
  'xingan': '内蒙古自治区',
  'xilingol': '内蒙古自治区',
  'alxa': '内蒙古自治区',
  
  'shenyang': '辽宁省',
  'dalian': '辽宁省',
  'anshan': '辽宁省',
  'fushun': '辽宁省',
  'benxi': '辽宁省',
  'dandong': '辽宁省',
  'jinzhou': '辽宁省',
  'yingkou': '辽宁省',
  'fuxin': '辽宁省',
  'liaoyang': '辽宁省',
  'panjin': '辽宁省',
  'tieling': '辽宁省',
  'chaoyang': '辽宁省',
  'huludao': '辽宁省',
  
  'changchun': '吉林省',
  'jilin': '吉林省',
  'siping': '吉林省',
  'liaoyuan': '吉林省',
  'tonghua': '吉林省',
  'baishan': '吉林省',
  'songyuan': '吉林省',
  'baicheng': '吉林省',
  'yanbian': '吉林省',
  
  'haerbin': '黑龙江省',
  'qiqihar': '黑龙江省',
  'jixi': '黑龙江省',
  'hegang': '黑龙江省',
  'shuangyashan': '黑龙江省',
  'daqing': '黑龙江省',
  'yichun': '黑龙江省',
  'jiamusi': '黑龙江省',
  'qitaihe': '黑龙江省',
  'mudanjiang': '黑龙江省',
  'heihe': '黑龙江省',
  'suihua': '黑龙江省',
  'daxinganling': '黑龙江省',
  
  'nanjing': '江苏省',
  'wuxi': '江苏省',
  'xuzhou': '江苏省',
  'changzhou': '江苏省',
  'suzhou': '江苏省',
  'nantong': '江苏省',
  'lianyungang': '江苏省',
  'huaian': '江苏省',
  'yancheng': '江苏省',
  'yangzhou': '江苏省',
  'zhenjiang': '江苏省',
  'taizhou': '江苏省',
  'suqian': '江苏省',
  
  'hangzhou': '浙江省',
  'ningbo': '浙江省',
  'wenzhou': '浙江省',
  'jiaxing': '浙江省',
  'huzhou': '浙江省',
  'shaoxing': '浙江省',
  'jinhua': '浙江省',
  'quzhou': '浙江省',
  'zhoushan': '浙江省',
  'taizhouzj': '浙江省',
  'lishui': '浙江省',
  
  'hefei': '安徽省',
  'wuhu': '安徽省',
  'bengbu': '安徽省',
  'huainan': '安徽省',
  'maanshan': '安徽省',
  'huaibei': '安徽省',
  'tongling': '安徽省',
  'anqing': '安徽省',
  'huangshan': '安徽省',
  'chuzhou': '安徽省',
  'fuyang': '安徽省',
  'suzhouah': '安徽省',
  'liuan': '安徽省',
  'haozhou': '安徽省',
  'chizhou': '安徽省',
  'xuancheng': '安徽省',
  
  'fuzhou': '福建省',
  'xiamen': '福建省',
  'putian': '福建省',
  'sanming': '福建省',
  'quanzhou': '福建省',
  'zhangzhou': '福建省',
  'nanping': '福建省',
  'longyan': '福建省',
  'ningde': '福建省',
  
  'nanchang': '江西省',
  'jingdezhen': '江西省',
  'pingxiang': '江西省',
  'jiujiang': '江西省',
  'xinyu': '江西省',
  'yingtan': '江西省',
  'ganzhou': '江西省',
  'jian': '江西省',
  'yi': '江西省',
  'fuzhoujx': '江西省',
  'shangrao': '江西省',
  
  'jinan': '山东省',
  'qingdao': '山东省',
  'zibo': '山东省',
  'zaozhuang': '山东省',
  'dongying': '山东省',
  'yantai': '山东省',
  'weifang': '山东省',
  'jining': '山东省',
  'taian': '山东省',
  'weihai': '山东省',
  'rizhao': '山东省',
  'laiwu': '山东省',
  'linyi': '山东省',
  'dezhou': '山东省',
  'liaocheng': '山东省',
  'binzhou': '山东省',
  'heze': '山东省',
  
  'zhengzhou': '河南省',
  'kaifeng': '河南省',
  'luoyang': '河南省',
  'pingdingshan': '河南省',
  'anyang': '河南省',
  'hebi': '河南省',
  'xinxiang': '河南省',
  'jiaozuo': '河南省',
  'puyang': '河南省',
  'xuchang': '河南省',
  'luohe': '河南省',
  'sanmenxia': '河南省',
  'nanyang': '河南省',
  'shangqiu': '河南省',
  'xinyang': '河南省',
  'zhoukou': '河南省',
  'zhumadian': '河南省',
  'jiyuan': '河南省',
  
  'wuhan': '湖北省',
  'huangshi': '湖北省',
  'shiyan': '湖北省',
  'yichang': '湖北省',
  'xiangyang': '湖北省',
  'ezhou': '湖北省',
  'jingmen': '湖北省',
  'xiaogan': '湖北省',
  'jingzhou': '湖北省',
  'huanggang': '湖北省',
  'xianning': '湖北省',
  'suizhou': '湖北省',
  'enshi': '湖北省',
  'xiantao': '湖北省',
  'qianjiang': '湖北省',
  'tianmen': '湖北省',
  'shennongjia': '湖北省',
  
  'changsha': '湖南省',
  'zhuzhou': '湖南省',
  'xiangtan': '湖南省',
  'hengyang': '湖南省',
  'shaoyang': '湖南省',
  'yueyang': '湖南省',
  'changde': '湖南省',
  'zhangjiajie': '湖南省',
  'yiyang': '湖南省',
  'loudi': '湖南省',
  'chenzhou': '湖南省',
  'yongzhou': '湖南省',
  'huaihua': '湖南省',
  'xiangxi': '湖南省',
  
  'guangzhou': '广东省',
  'shaoguan': '广东省',
  'shenzhen': '广东省',
  'zhuhai': '广东省',
  'shantou': '广东省',
  'foshan': '广东省',
  'jiangmen': '广东省',
  'zhanjiang': '广东省',
  'maoming': '广东省',
  'zhaoqing': '广东省',
  'huizhou': '广东省',
  'meizhou': '广东省',
  'shanwei': '广东省',
  'heyuan': '广东省',
  'yangjiang': '广东省',
  'qingyuan': '广东省',
  'dongguan': '广东省',
  'zhongshan': '广东省',
  'chaozhou': '广东省',
  'jieyang': '广东省',
  'yunfu': '广东省',
  
  'nanning': '广西壮族自治区',
  'liuzhou': '广西壮族自治区',
  'guilin': '广西壮族自治区',
  'wuzhou': '广西壮族自治区',
  'beihai': '广西壮族自治区',
  'fangchenggang': '广西壮族自治区',
  'qinzhou': '广西壮族自治区',
  'guigang': '广西壮族自治区',
  'yulin': '广西壮族自治区',
  'baise': '广西壮族自治区',
  'hezhou': '广西壮族自治区',
  'hechi': '广西壮族自治区',
  'laibin': '广西壮族自治区',
  'chongzuo': '广西壮族自治区',
  
  'haikou': '海南省',
  'sanya': '海南省',
  'sansha': '海南省',
  'danzhou': '海南省',
  
  'chengdu': '四川省',
  'zigong': '四川省',
  'panzhihua': '四川省',
  'luzhou': '四川省',
  'deyang': '四川省',
  'mianyang': '四川省',
  'guangyuan': '四川省',
  'suining': '四川省',
  'neijiang': '四川省',
  'leshan': '四川省',
  'nanchong': '四川省',
  'meishan': '四川省',
  'yibin': '四川省',
  'guangan': '四川省',
  'dazhou': '四川省',
  'yaan': '四川省',
  'bazhong': '四川省',
  'ziyang': '四川省',
  'aba': '四川省',
  'ganzi': '四川省',
  'liangshan': '四川省',
  
  'guiyang': '贵州省',
  'liupanshui': '贵州省',
  'zunyi': '贵州省',
  'anshun': '贵州省',
  'bijie': '贵州省',
  'tongren': '贵州省',
  'qingdongnan': '贵州省',
  'qiannan': '贵州省',
  'qiannanbu': '贵州省',
  
  'kunming': '云南省',
  'qujing': '云南省',
  'yuxi': '云南省',
  'baoshan': '云南省',
  'zhaotong': '云南省',
  'lijiang': '云南省',
  'puer': '云南省',
  'lincang': '云南省',
  'chuxiong': '云南省',
  'honghe': '云南省',
  'wenshan': '云南省',
  'xishuangbanna': '云南省',
  'dali': '云南省',
  'dehong': '云南省',
  'nujiang': '云南省',
  'diqing': '云南省',
  
  'lasa': '西藏自治区',
  'rikaze': '西藏自治区',
  'qamdo': '西藏自治区',
  'nyingchi': '西藏自治区',
  'shannan': '西藏自治区',
  'nagqu': '西藏自治区',
  'ngari': '西藏自治区',
  
  'xian': '陕西省',
  'tongchuan': '陕西省',
  'baoji': '陕西省',
  'xianyang': '陕西省',
  'weinan': '陕西省',
  'yanan': '陕西省',
  'hanzhong': '陕西省',
  'yulin': '陕西省',
  'ankang': '陕西省',
  'shangluo': '陕西省',
  
  'lanzhou': '甘肃省',
  'jiayuguan': '甘肃省',
  'jinchang': '甘肃省',
  'baiyin': '甘肃省',
  'tianshui': '甘肃省',
  'wuwei': '甘肃省',
  'zhangye': '甘肃省',
  'pingliang': '甘肃省',
  'jiuquan': '甘肃省',
  'qingyang': '甘肃省',
  'dingxi': '甘肃省',
  'longnan': '甘肃省',
  'linxia': '甘肃省',
  'gannan': '甘肃省',
  
  'xining': '青海省',
  'haidong': '青海省',
  'haibei': '青海省',
  'huangnan': '青海省',
  'hainan': '青海省',
  'guoluo': '青海省',
  'yushu': '青海省',
  'haixi': '青海省',
  
  'yinchuan': '宁夏回族自治区',
  'shizuishan': '宁夏回族自治区',
  'wuzhong': '宁夏回族自治区',
  'guyuan': '宁夏回族自治区',
  'zhongwei': '宁夏回族自治区',
  
  'urumqi': '新疆维吾尔自治区',
  'kelamayi': '新疆维吾尔自治区',
  'turpan': '新疆维吾尔自治区',
  'hami': '新疆维吾尔自治区',
  'changji': '新疆维吾尔自治区',
  'boertala': '新疆维吾尔自治区',
  'bayinguoleng': '新疆维吾尔自治区',
  'akesu': '新疆维吾尔自治区',
  'kezilesu': '新疆维吾尔自治区',
  'kashen': '新疆维吾尔自治区',
  'hetian': '新疆维吾尔自治区',
  'yili': '新疆维吾尔自治区',
  'tacheng': '新疆维吾尔自治区',
  'aletai': '新疆维吾尔自治区'
}

/**
 * 根据拼音location获取对应的省份
 * @param {string} pinyinLocation - 拼音位置名称
 * @returns {string} 省份名称
 */
export function getProvinceByPinyin(pinyinLocation) {
  // 首先检查是否是直辖市
  if (['beijing', 'tianjin', 'shanghai', 'chongqing'].includes(pinyinLocation)) {
    return pinyinToChinese[pinyinLocation] || pinyinLocation
  }
  
  // 检查城市到省份的映射
  return pinyinToProvince[pinyinLocation] || pinyinLocation
}

/**
 * 根据拼音location获取对应的城市名称
 * @param {string} pinyinLocation - 拼音位置名称
 * @returns {string} 城市名称
 */
export function getCityByPinyin(pinyinLocation) {
  return pinyinToChinese[pinyinLocation] || pinyinLocation
}

/**
 * 统计拨测点按省份分组
 * @param {Array} probeData - 拨测点数据数组
 * @returns {Object} 按省份分组的统计结果
 */
export function statisticsByProvince(probeData) {
  const provinceStats = {}
  
  probeData.forEach(probe => {
    // 使用agent_area字段进行统计，如果没有则使用location
    const locationForStats = probe.agent_area || probe.location
    const province = getProvinceByPinyin(locationForStats)
    
    if (!provinceStats[province]) {
      provinceStats[province] = {
        name: province,
        count: 0,
        cities: {},
        probes: [],
        uniqueLocations: new Set() // 用于去重统计唯一拨测点
      }
    }
    
    // 添加唯一位置到Set中进行去重
    provinceStats[province].uniqueLocations.add(locationForStats)
    provinceStats[province].probes.push(probe)
    
    // 统计城市（也需要去重）
    
    const city = getCityByPinyin(locationForStats)
    if (!provinceStats[province].cities[city]) {
      provinceStats[province].cities[city] = {
        name: city,
        count: 0,
        probes: [],
        uniqueLocations: new Set()
      }
    }
    provinceStats[province].cities[city].uniqueLocations.add(locationForStats)
    provinceStats[province].cities[city].probes.push(probe)
  })
  
  // 将Set的大小作为实际的拨测点数量
  Object.values(provinceStats).forEach(province => {
    province.count = province.uniqueLocations.size
    Object.values(province.cities).forEach(city => {
      city.count = city.uniqueLocations.size
    })
    // 清理Set对象，避免序列化问题
    delete province.uniqueLocations
    Object.values(province.cities).forEach(city => {
      delete city.uniqueLocations
    })
  })
  
  return provinceStats
}

/**
 * 统计拨测点按城市分组
 * @param {Array} probeData - 拨测点数据数组
 * @param {string} province - 省份名称
 * @returns {Object} 按城市分组的统计结果
 */
export function statisticsByCity(probeData, province) {
  const cityStats = {}
  
  probeData.forEach(probe => {
    // 使用agent_area字段进行统计，如果没有则使用location
    const locationForStats = probe.agent_area || probe.location
    const probeProvince = getProvinceByPinyin(locationForStats)
    if (probeProvince !== province) return
    
    const city = getCityByPinyin(locationForStats)
    
    if (!cityStats[city]) {
      cityStats[city] = {
        name: city,
        count: 0,
        probes: [],
        uniqueLocations: new Set()
      }
    }
    
    cityStats[city].uniqueLocations.add(locationForStats)
    cityStats[city].probes.push(probe)
  })
  
  // 将Set的大小作为实际的拨测点数量
  Object.values(cityStats).forEach(city => {
    city.count = city.uniqueLocations.size
    // 清理Set对象，避免序列化问题
    delete city.uniqueLocations
  })
  
  return cityStats
}

export default {
  getProvinceByPinyin,
  getCityByPinyin,
  statisticsByProvince,
  statisticsByCity
}