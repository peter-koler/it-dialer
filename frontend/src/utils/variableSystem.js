/**
 * API拨测变量系统
 * 支持动态提取HTTP响应数据，并在多个请求之间传递数据和状态
 */

/**
 * 变量管理器类
 */
export class VariableManager {
  constructor(initialVariables = []) {
    this.variables = new Map()
    
    // 初始化变量
    initialVariables.forEach(variable => {
      if (variable.name && variable.value !== undefined) {
        this.variables.set(variable.name, variable.value)
      }
    })
  }

  /**
   * 设置变量值
   * @param {string} name 变量名（包含$符号）
   * @param {any} value 变量值
   */
  setVariable(name, value) {
    if (!name.startsWith('$')) {
      name = '$' + name
    }
    this.variables.set(name, value)
  }

  /**
   * 获取变量值
   * @param {string} name 变量名（包含$符号）
   * @returns {any} 变量值
   */
  getVariable(name) {
    if (!name.startsWith('$')) {
      name = '$' + name
    }
    return this.variables.get(name)
  }

  /**
   * 获取所有变量
   * @returns {Object} 所有变量的键值对
   */
  getAllVariables() {
    return Object.fromEntries(this.variables)
  }

  /**
   * 检查变量是否存在
   * @param {string} name 变量名
   * @returns {boolean} 是否存在
   */
  hasVariable(name) {
    if (!name.startsWith('$')) {
      name = '$' + name
    }
    return this.variables.has(name)
  }

  /**
   * 删除变量
   * @param {string} name 变量名
   */
  deleteVariable(name) {
    if (!name.startsWith('$')) {
      name = '$' + name
    }
    this.variables.delete(name)
  }

  /**
   * 清空所有变量
   */
  clear() {
    this.variables.clear()
  }

  /**
   * 替换字符串中的变量
   * @param {string} text 包含变量的文本
   * @returns {string} 替换后的文本
   */
  replaceVariables(text) {
    if (typeof text !== 'string') {
      return text
    }

    let result = text
    
    // 使用正则表达式匹配变量模式 $variableName
    const variablePattern = /\$([a-zA-Z][a-zA-Z0-9]*)/g
    
    result = result.replace(variablePattern, (match, variableName) => {
      const fullVariableName = '$' + variableName
      if (this.variables.has(fullVariableName)) {
        const value = this.variables.get(fullVariableName)
        return value !== null && value !== undefined ? String(value) : match
      }
      return match // 如果变量不存在，保持原样
    })

    return result
  }

  /**
   * 替换对象中的所有变量
   * @param {any} obj 要处理的对象
   * @returns {any} 处理后的对象
   */
  replaceVariablesInObject(obj) {
    if (typeof obj === 'string') {
      return this.replaceVariables(obj)
    }
    
    if (Array.isArray(obj)) {
      return obj.map(item => this.replaceVariablesInObject(item))
    }
    
    if (obj && typeof obj === 'object') {
      const result = {}
      for (const [key, value] of Object.entries(obj)) {
        result[key] = this.replaceVariablesInObject(value)
      }
      return result
    }
    
    return obj
  }
}

/**
 * 数据提取器类
 * 用于从HTTP响应中提取数据
 */
export class DataExtractor {
  /**
   * 从响应中提取数据
   * @param {Object} response HTTP响应对象
   * @param {string} source 数据源类型
   * @param {string} expression 提取表达式
   * @returns {any} 提取的数据
   */
  static extractData(response, source, expression) {
    try {
      switch (source) {
        case 'status':
          return response.status
          
        case 'body':
          return this.extractFromBody(response.data, expression)
          
        case 'header':
        case 'headers':
          return this.extractFromHeaders(response.headers, expression)
          
        case 'cookie':
          return this.extractFromCookies(response.headers, expression)
          
        case 'url':
          return response.config?.url || ''
          
        case 'time':
          return response.duration || 0
          
        case 'size':
          return this.calculateResponseSize(response)
          
        default:
          console.warn(`未知的数据源类型: ${source}`)
          return null
      }
    } catch (error) {
      console.error(`数据提取失败: ${error.message}`, { source, expression })
      return null
    }
  }

  /**
   * 从响应体中提取数据
   * @param {any} body 响应体
   * @param {string} expression JSONPath或正则表达式
   * @returns {any} 提取的数据
   */
  static extractFromBody(body, expression) {
    if (!expression) {
      return body
    }

    // 如果是JSONPath表达式（以$开头）
    if (expression.startsWith('$.')) {
      return this.extractWithJsonPath(body, expression)
    }
    
    // 如果是正则表达式（以/开头和结尾）
    if (expression.startsWith('/') && expression.endsWith('/')) {
      const regex = new RegExp(expression.slice(1, -1))
      const bodyStr = typeof body === 'string' ? body : JSON.stringify(body)
      const match = bodyStr.match(regex)
      return match ? match[1] || match[0] : null
    }
    
    // 简单属性访问
    if (typeof body === 'object' && body !== null) {
      return this.getNestedProperty(body, expression)
    }
    
    return null
  }

  /**
   * 从响应头中提取数据
   * @param {Object} headers 响应头对象
   * @param {string} expression 头部名称
   * @returns {string} 头部值
   */
  static extractFromHeaders(headers, expression) {
    if (!headers || !expression) {
      return null
    }
    
    // 不区分大小写查找头部
    const lowerExpression = expression.toLowerCase()
    for (const [key, value] of Object.entries(headers)) {
      if (key.toLowerCase() === lowerExpression) {
        return value
      }
    }
    
    return null
  }

  /**
   * 从Cookie中提取数据
   * @param {Object} headers 响应头对象
   * @param {string} expression Cookie名称
   * @returns {string} Cookie值
   */
  static extractFromCookies(headers, expression) {
    const setCookieHeader = headers['set-cookie'] || headers['Set-Cookie']
    if (!setCookieHeader || !expression) {
      return null
    }
    
    const cookies = Array.isArray(setCookieHeader) ? setCookieHeader : [setCookieHeader]
    
    for (const cookie of cookies) {
      const match = cookie.match(new RegExp(`${expression}=([^;]+)`))
      if (match) {
        return match[1]
      }
    }
    
    return null
  }

  /**
   * 使用JSONPath提取数据
   * @param {any} data 数据对象
   * @param {string} path JSONPath表达式
   * @returns {any} 提取的数据
   */
  static extractWithJsonPath(data, path) {
    try {
      // 简化的JSONPath实现
      const parts = path.replace(/^\$\./, '').split('.')
      let result = data
      
      for (const part of parts) {
        if (result === null || result === undefined) {
          return null
        }
        
        // 处理数组索引
        if (part.includes('[') && part.includes(']')) {
          const [prop, indexStr] = part.split('[')
          const index = parseInt(indexStr.replace(']', ''))
          
          if (prop) {
            result = result[prop]
          }
          
          if (Array.isArray(result) && !isNaN(index)) {
            result = result[index]
          }
        } else {
          result = result[part]
        }
      }
      
      return result
    } catch (error) {
      console.error('JSONPath提取失败:', error)
      return null
    }
  }

  /**
   * 获取嵌套属性
   * @param {Object} obj 对象
   * @param {string} path 属性路径（用.分隔）
   * @returns {any} 属性值
   */
  static getNestedProperty(obj, path) {
    return path.split('.').reduce((current, prop) => {
      return current && current[prop] !== undefined ? current[prop] : null
    }, obj)
  }

  /**
   * 计算响应大小
   * @param {Object} response 响应对象
   * @returns {number} 响应大小（字节）
   */
  static calculateResponseSize(response) {
    try {
      const contentLength = response.headers['content-length'] || response.headers['Content-Length']
      if (contentLength) {
        return parseInt(contentLength)
      }
      
      // 如果没有Content-Length头，估算大小
      const bodyStr = typeof response.data === 'string' 
        ? response.data 
        : JSON.stringify(response.data)
      
      return new Blob([bodyStr]).size
    } catch (error) {
      return 0
    }
  }
}

/**
 * 断言验证器类
 */
export class AssertionValidator {
  /**
   * 验证断言
   * @param {any} actualValue 实际值
   * @param {string} operator 操作符
   * @param {any} expectedValue 期望值
   * @returns {Object} 验证结果
   */
  static validate(actualValue, operator, expectedValue) {
    try {
      let result = false
      let message = ''
      
      switch (operator) {
        case 'equals':
          result = String(actualValue) === String(expectedValue)
          message = result ? '值相等' : `期望 ${expectedValue}，实际 ${actualValue}`
          break
          
        case 'not_equals':
          result = String(actualValue) !== String(expectedValue)
          message = result ? '值不相等' : `期望不等于 ${expectedValue}，但实际值相等`
          break
          
        case 'contains':
          result = String(actualValue).includes(String(expectedValue))
          message = result ? '包含指定值' : `${actualValue} 不包含 ${expectedValue}`
          break
          
        case 'not_contains':
          result = !String(actualValue).includes(String(expectedValue))
          message = result ? '不包含指定值' : `${actualValue} 包含了不应该包含的 ${expectedValue}`
          break
          
        case 'greater_than':
          const numActual = Number(actualValue)
          const numExpected = Number(expectedValue)
          result = !isNaN(numActual) && !isNaN(numExpected) && numActual > numExpected
          message = result ? '大于期望值' : `${actualValue} 不大于 ${expectedValue}`
          break
          
        case 'less_than':
          const numActual2 = Number(actualValue)
          const numExpected2 = Number(expectedValue)
          result = !isNaN(numActual2) && !isNaN(numExpected2) && numActual2 < numExpected2
          message = result ? '小于期望值' : `${actualValue} 不小于 ${expectedValue}`
          break
          
        case 'regex':
          const regex = new RegExp(expectedValue)
          result = regex.test(String(actualValue))
          message = result ? '匹配正则表达式' : `${actualValue} 不匹配正则 ${expectedValue}`
          break
          
        case 'exists':
          result = actualValue !== null && actualValue !== undefined
          message = result ? '值存在' : '值不存在'
          break
          
        case 'not_exists':
          result = actualValue === null || actualValue === undefined
          message = result ? '值不存在' : '值存在但期望不存在'
          break
          
        default:
          result = false
          message = `未知的操作符: ${operator}`
      }
      
      return {
        success: result,
        message,
        actualValue,
        expectedValue,
        operator
      }
    } catch (error) {
      return {
        success: false,
        message: `断言验证失败: ${error.message}`,
        actualValue,
        expectedValue,
        operator
      }
    }
  }
}

/**
 * API步骤执行器
 */
export class ApiStepExecutor {
  constructor(variableManager) {
    this.variableManager = variableManager
  }

  /**
   * 执行API步骤
   * @param {Object} step 步骤配置
   * @param {Function} httpClient HTTP客户端函数
   * @returns {Object} 执行结果
   */
  async executeStep(step, httpClient) {
    const startTime = Date.now()
    const stepResult = {
      stepId: step.step_id,
      stepName: step.name,
      success: false,
      request: null,
      response: null,
      variables: {},
      assertions: [],
      duration: 0,
      error: null
    }

    try {
      // 1. 准备请求数据，替换变量
      const requestConfig = this.prepareRequest(step)
      stepResult.request = requestConfig

      // 2. 执行HTTP请求
      const response = await httpClient(requestConfig)
      stepResult.response = {
        status: response.status,
        headers: response.headers,
        data: response.data,
        duration: Date.now() - startTime
      }

      // 3. 提取变量
      const extractedVariables = this.extractVariables(step, response)
      stepResult.variables = extractedVariables

      // 4. 执行断言
      const assertionResults = this.executeAssertions(step, response)
      stepResult.assertions = assertionResults

      // 5. 判断步骤是否成功
      stepResult.success = assertionResults.every(assertion => assertion.success)
      stepResult.duration = Date.now() - startTime

      return stepResult
    } catch (error) {
      stepResult.error = error.message
      stepResult.duration = Date.now() - startTime
      return stepResult
    }
  }

  /**
   * 准备请求配置
   * @param {Object} step 步骤配置
   * @returns {Object} 请求配置
   */
  prepareRequest(step) {
    const config = {
      method: step.request.method,
      url: this.variableManager.replaceVariables(step.request.url),
      headers: this.variableManager.replaceVariablesInObject(step.request.headers),
      data: step.request.body ? this.variableManager.replaceVariables(step.request.body) : undefined
    }

    // 处理URL参数
    if (step.urlParameters && step.urlParameters.length > 0) {
      const params = {}
      step.urlParameters.forEach(param => {
        if (param.key && param.value) {
          params[param.key] = this.variableManager.replaceVariables(param.value)
        }
      })
      config.params = params
    }

    return config
  }

  /**
   * 提取变量
   * @param {Object} step 步骤配置
   * @param {Object} response HTTP响应
   * @returns {Object} 提取的变量
   */
  extractVariables(step, response) {
    const extractedVariables = {}

    if (step.variables && step.variables.length > 0) {
      step.variables.forEach(variable => {
        if (variable.name && variable.source) {
          const value = DataExtractor.extractData(response, variable.source, variable.expression)
          if (value !== null) {
            this.variableManager.setVariable(variable.name, value)
            extractedVariables[variable.name] = value
          }
        }
      })
    }

    return extractedVariables
  }

  /**
   * 执行断言
   * @param {Object} step 步骤配置
   * @param {Object} response HTTP响应
   * @returns {Array} 断言结果
   */
  executeAssertions(step, response) {
    const assertionResults = []

    if (step.assertions && step.assertions.length > 0) {
      step.assertions.forEach(assertion => {
        const actualValue = DataExtractor.extractData(response, assertion.source, assertion.expression)
        const expectedValue = this.variableManager.replaceVariables(assertion.expected)
        
        const result = AssertionValidator.validate(actualValue, assertion.operator, expectedValue)
        assertionResults.push({
          ...result,
          assertion: {
            source: assertion.source,
            expression: assertion.expression,
            operator: assertion.operator,
            expected: assertion.expected
          }
        })
      })
    }

    return assertionResults
  }
}

// 导出默认实例
export default {
  VariableManager,
  DataExtractor,
  AssertionValidator,
  ApiStepExecutor
}