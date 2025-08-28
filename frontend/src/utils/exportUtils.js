import { message } from 'ant-design-vue'
import { exportReport } from '@/api/reports'

/**
 * 通用报表导出工具
 */
export class ExportUtils {
  /**
   * 导出报表文件
   * @param {number} reportId - 报表ID
   * @param {Object} options - 导出选项
   * @param {string} options.format - 导出格式 ('excel' | 'pdf')
   * @param {string} options.start_date - 开始日期 (YYYY-MM-DD)
   * @param {string} options.end_date - 结束日期 (YYYY-MM-DD)
   * @param {Object} options.filters - 过滤条件
   * @param {string} options.filename - 自定义文件名（可选）
   */
  static async exportReportFile(reportId, options = {}) {
    const {
      format = 'excel',
      start_date,
      end_date,
      filters = {},
      filename
    } = options

    try {
      message.loading('正在生成报表文件...', 0)
      
      const response = await exportReport(reportId, {
        format,
        start_date,
        end_date,
        filters
      })

      // 从响应头获取文件名
      const contentDisposition = response.headers['content-disposition']
      let downloadFilename = filename
      
      if (!downloadFilename && contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
        if (filenameMatch) {
          downloadFilename = filenameMatch[1]
        }
      }
      
      if (!downloadFilename) {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')
        const extension = format === 'excel' ? 'xlsx' : 'pdf'
        downloadFilename = `report_${timestamp}.${extension}`
      }

      // 创建下载链接
      const blob = new Blob([response.data], {
        type: format === 'excel' 
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          : 'application/pdf'
      })
      
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = downloadFilename
      document.body.appendChild(link)
      link.click()
      
      // 清理
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      message.destroy()
      message.success('报表导出成功')
      
    } catch (error) {
      message.destroy()
      console.error('导出报表失败:', error)
      
      if (error.response?.status === 404) {
        message.error('没有找到符合条件的数据')
      } else if (error.response?.status === 500) {
        const errorMsg = error.response?.data?.message || '服务器内部错误'
        message.error(`导出失败: ${errorMsg}`)
      } else {
        message.error('导出报表失败，请稍后重试')
      }
    }
  }

  /**
   * 快速导出当前时间范围的报表
   * @param {string} reportType - 报表类型 ('tcp' | 'ping' | 'http' | 'api' | 'overview')
   * @param {string} format - 导出格式 ('excel' | 'pdf')
   * @param {string} timeRange - 时间范围 ('1h' | '1d' | '7d' | '30d')
   * @param {Object} filters - 额外的过滤条件
   */
  static async quickExport(reportType, format = 'excel', timeRange = '7d', filters = {}) {
    try {
      // 根据时间范围计算日期
      const endDate = new Date()
      const startDate = new Date()
      
      switch (timeRange) {
        case '1h':
          startDate.setHours(startDate.getHours() - 1)
          break
        case '1d':
          startDate.setDate(startDate.getDate() - 1)
          break
        case '7d':
          startDate.setDate(startDate.getDate() - 7)
          break
        case '30d':
          startDate.setDate(startDate.getDate() - 30)
          break
        default:
          startDate.setDate(startDate.getDate() - 7)
      }

      const start_date = startDate.toISOString().split('T')[0]
      const end_date = endDate.toISOString().split('T')[0]

      // 创建临时报表并导出
      const reportConfig = {
        name: `${reportType.toUpperCase()}报表_${timeRange}`,
        description: `${reportType.toUpperCase()}报表 - ${timeRange}时间范围`,
        report_type: reportType === 'overview' ? 'task_summary' : 'result_analysis',
        config: {
          task_type: reportType === 'overview' ? null : reportType,
          time_range: timeRange,
          ...filters
        }
      }

      // 这里需要先创建报表，然后导出
      // 为了简化，我们使用固定的报表ID，实际应用中应该动态创建
      const reportId = this.getReportIdByType(reportType)
      
      await this.exportReportFile(reportId, {
        format,
        start_date,
        end_date,
        filters: {
          task_type: reportType === 'overview' ? null : reportType,
          ...filters
        }
      })
      
    } catch (error) {
      console.error('快速导出失败:', error)
      message.error('快速导出失败，请稍后重试')
    }
  }

  /**
   * 根据报表类型获取报表ID（临时方案）
   * 实际应用中应该从后端获取或动态创建
   */
  static getReportIdByType(reportType) {
    const reportIdMap = {
      'overview': 1,
      'tcp': 2,
      'ping': 3,
      'http': 4,
      'api': 5
    }
    return reportIdMap[reportType] || 1
  }

  /**
   * 批量导出多个报表
   * @param {Array} exportTasks - 导出任务列表
   */
  static async batchExport(exportTasks) {
    if (!exportTasks || exportTasks.length === 0) {
      message.warning('没有要导出的报表')
      return
    }

    message.loading(`正在批量导出 ${exportTasks.length} 个报表...`, 0)
    
    const results = []
    
    for (let i = 0; i < exportTasks.length; i++) {
      const task = exportTasks[i]
      try {
        await this.exportReportFile(task.reportId, task.options)
        results.push({ success: true, task })
        
        // 添加延迟避免服务器压力过大
        if (i < exportTasks.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
      } catch (error) {
        results.push({ success: false, task, error })
      }
    }
    
    message.destroy()
    
    const successCount = results.filter(r => r.success).length
    const failCount = results.length - successCount
    
    if (failCount === 0) {
      message.success(`批量导出完成，共导出 ${successCount} 个报表`)
    } else {
      message.warning(`批量导出完成，成功 ${successCount} 个，失败 ${failCount} 个`)
    }
    
    return results
  }
}

// 导出默认实例
export default ExportUtils