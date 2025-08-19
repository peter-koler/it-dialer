import { ref } from 'vue'

/**
 * 图表渲染管理 composable
 */
export function useCharts() {
  const probeDetailChart = ref(null)

  // 渲染延迟图表（时间序列）
  const renderLatencyChart = (results) => {
    const chartDom = document.getElementById('latency-chart')
    if (!chartDom) return
    
    const myChart = echarts.init(chartDom)
    
    // 按创建时间排序
    results.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    
    // 准备时间序列数据
    const timeData = results.map(result => {
      // 格式化时间显示
      const date = new Date(result.created_at)
      return date.toLocaleTimeString('zh-CN', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    })
    
    // 准备延迟数据
    const rttMinData = []
    const rttAvgData = []
    const rttMaxData = []
    
    results.forEach(result => {
      try {
        const details = typeof result.details === 'string' 
          ? JSON.parse(result.details) 
          : result.details
        
        rttMinData.push(details.rtt_min || 0)
        rttAvgData.push(details.rtt_avg || 0)
        rttMaxData.push(details.rtt_max || 0)
      } catch (e) {
        // 解析失败时使用默认值
        rttMinData.push(0)
        rttAvgData.push(0)
        rttMaxData.push(0)
      }
    })

    const option = {
      title: {
        text: '延迟时间序列图',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['最小延迟', '平均延迟', '最大延迟'],
        top: '10%'
      },
      xAxis: {
        type: 'category',
        data: timeData
      },
      yAxis: {
        type: 'value',
        name: '延迟 (ms)'
      },
      series: [
        {
          name: '最小延迟',
          type: 'line',
          data: rttMinData,
          smooth: true
        },
        {
          name: '平均延迟',
          type: 'line',
          data: rttAvgData,
          smooth: true
        },
        {
          name: '最大延迟',
          type: 'line',
          data: rttMaxData,
          smooth: true
        }
      ]
    }

    myChart.setOption(option)
  }

  // 渲染TCP任务详情图表
  const renderTcpCharts = (results) => {
    // 按创建时间排序
    results.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    
    // 准备时间序列数据
    const timeData = results.map(result => {
      // 格式化时间显示
      const date = new Date(result.created_at);
      return date.toLocaleTimeString('zh-CN', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    });
    
    // 准备连通性数据
    const connectedData = results.map(result => {
      try {
        const details = typeof result.details === 'string' 
          ? JSON.parse(result.details) 
          : result.details;
        return details.connected ? 1 : 0;
      } catch (e) {
        return 0;
      }
    });
    
    // 准备响应时间数据 (转换为毫秒)
    const responseTimeData = results.map(result => {
      try {
        const details = typeof result.details === 'string' 
          ? JSON.parse(result.details) 
          : result.details;
        // TCP插件返回的是秒，转换为毫秒
        return details.execution_time ? details.execution_time * 1000 : 0;
      } catch (e) {
        return 0;
      }
    });
    
    // 准备状态和返回码数据
    const statusData = results.map(result => {
      try {
        const details = typeof result.details === 'string' 
          ? JSON.parse(result.details) 
          : result.details;
        return details.return_code || 0;
      } catch (e) {
        return -1; // 表示解析失败
      }
    });
    
    // 渲染连通性图表
    const connectedChartDom = document.getElementById('tcp-connected-chart');
    if (connectedChartDom) {
      const connectedChart = echarts.init(connectedChartDom);
      const connectedOption = {
        title: {
          text: 'TCP连通性',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            const param = params[0];
            return `${param.name}<br/>${param.seriesName}: ${param.value === 1 ? '连通' : '未连通'}`;
          }
        },
        xAxis: {
          type: 'category',
          data: timeData
        },
        yAxis: {
          type: 'value',
          name: '连通状态',
          axisLabel: {
            formatter: function(value) {
              return value === 1 ? '连通' : '未连通';
            }
          }
        },
        series: [{
          name: '连通性',
          type: 'line',
          step: 'middle',
          data: connectedData,
          markLine: {
            silent: true,
            data: [{
              yAxis: 1,
              lineStyle: {
                color: '#52c41a'
              },
              label: {
                show: false
              }
            }, {
              yAxis: 0,
              lineStyle: {
                color: '#f5222d'
              },
              label: {
                show: false
              }
            }]
          }
        }]
      };
      connectedChart.setOption(connectedOption);
    }
    
    // 渲染响应时间图表
    const responseTimeChartDom = document.getElementById('tcp-response-time-chart');
    if (responseTimeChartDom) {
      const responseTimeChart = echarts.init(responseTimeChartDom);
      const responseTimeOption = {
        title: {
          text: '响应时间',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: timeData
        },
        yAxis: {
          type: 'value',
          name: '响应时间 (毫秒)'
        },
        series: [{
          name: '响应时间',
          type: 'line',
          data: responseTimeData,
          smooth: true
        }]
      };
      responseTimeChart.setOption(responseTimeOption);
    }
    
    // 渲染状态码图表
    const statusChartDom = document.getElementById('tcp-status-chart');
    if (statusChartDom) {
      const statusChart = echarts.init(statusChartDom);
      const statusOption = {
        title: {
          text: '连接返回码',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: timeData
        },
        yAxis: {
          type: 'value',
          name: '返回码'
        },
        series: [{
          name: '返回码',
          type: 'line',
          data: statusData,
          step: 'middle'
        }]
      };
      statusChart.setOption(statusOption);
    }
  }

  // 渲染拨测点详情图表
  const renderProbeDetailChart = (record, selectedTask) => {
    if (!probeDetailChart.value) return
    
    const chart = echarts.init(probeDetailChart.value)
    
    let option = {}
    
    try {
      const details = typeof record.details === 'string' 
        ? JSON.parse(record.details) 
        : record.details
      
      if (selectedTask.task.type === 'ping' && details) {
        option = {
          title: {
            text: 'Ping详情',
            textStyle: {
              fontSize: 14
            }
          },
          tooltip: {},
          radar: {
            indicator: [
              { name: '最小延迟\n(ms)', max: 100 },
              { name: '平均延迟\n(ms)', max: 100 },
              { name: '最大延迟\n(ms)', max: 100 },
              { name: '丢包率\n(%)', max: 100 }
            ]
          },
          series: [{
            type: 'radar',
            data: [
              {
                value: [
                  details.rtt_min || 0,
                  details.rtt_avg || 0,
                  details.rtt_max || 0,
                  details.packet_loss || 0
                ],
                name: '性能指标'
              }
            ]
          }]
        }
      } else if (selectedTask.task.type === 'tcp' && details) {
        option = {
          title: {
            text: 'TCP详情',
            textStyle: {
              fontSize: 14
            }
          },
          tooltip: {
            trigger: 'axis'
          },
          xAxis: {
            type: 'category',
            data: ['连接状态', '响应时间']
          },
          yAxis: {},
          series: [{
            type: 'bar',
            data: [
              {
                value: details.connected ? 1 : 0,
                itemStyle: {
                  color: details.connected ? '#52c41a' : '#ff4d4f'
                }
              },
              {
                value: details.execution_time ? (details.execution_time * 1000).toFixed(2) : 0
              }
            ]
          }]
        }
      } else {
        option = {
          title: {
            text: '无图表数据',
            left: 'center',
            top: 'center'
          }
        }
      }
    } catch (e) {
      option = {
        title: {
          text: '数据解析失败',
          left: 'center',
          top: 'center'
        }
      }
    }
    
    chart.setOption(option)
  }

  return {
    probeDetailChart,
    renderLatencyChart,
    renderTcpCharts,
    renderProbeDetailChart
  }
}