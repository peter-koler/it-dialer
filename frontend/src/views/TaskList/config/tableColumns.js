// 表格列定义配置
export const columns = [
  {
    title: '任务ID',
    dataIndex: ['task', 'id'],
    width: 80
  },
  {
    title: '任务名称',
    dataIndex: ['task', 'name']
  },
  {
    title: '任务目标',
    dataIndex: ['task', 'target']
  },
  {
    title: '任务类型',
    dataIndex: ['task', 'type']
  },
  {
    title: '最新状态',
    dataIndex: 'status'
  },
  {
    title: '平均响应时间',
    dataIndex: 'response_time'
  },
  {
    title: '执行次数',
    dataIndex: 'count'
  },
  {
    title: '创建时间',
    dataIndex: 'latestCreatedAt'
  },
  {
    title: '操作',
    dataIndex: 'details',
    width: 100
  }
]

// 详情表格列定义
export const detailColumns = [
  {
    title: '位置',
    dataIndex: 'location'
  },
  {
    title: '时间',
    dataIndex: 'time'
  },
  {
    title: '响应时间',
    dataIndex: 'responseTime',
    sorter: (a, b) => (a.response_time || 0) - (b.response_time || 0)
  },
  {
    title: '状态',
    dataIndex: 'status'
  },
  {
    title: '操作',
    dataIndex: 'actions'
  }
]

// 拨测点详情表格列定义
export const probeDetailColumns = [
  {
    title: '时间',
    dataIndex: 'time'
  },
  {
    title: '响应时间',
    dataIndex: 'responseTime'
  },
  {
    title: '状态',
    dataIndex: 'status'
  }
]