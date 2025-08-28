import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'
import 'ant-design-vue/dist/reset.css'
import './styles/index.css'

// 引入Ant Design Vue组件
import Antd from 'ant-design-vue'

// 引入ECharts相关组件
import ECharts from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
} from 'echarts/components'

// 注册ECharts组件
use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
])

// 创建Vue应用
const app = createApp(App)

// 注册全局组件
app.component('v-chart', ECharts)

// 配置国际化
const i18n = createI18n({
  legacy: false, // 使用Composition API模式
  locale: 'zh-CN',
  fallbackLocale: 'en-US',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

// 使用插件
app.use(pinia)
app.use(Antd)
app.use(router)
app.use(i18n)

// 挂载应用
app.mount('#app')