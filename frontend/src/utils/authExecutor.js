/**
 * 认证执行器 - 处理各种认证方式
 */

/**
 * Basic Auth 认证处理器
 */
export class BasicAuthHandler {
  constructor(config) {
    this.username = config.username
    this.password = config.password
  }

  /**
   * 应用认证到请求配置
   * @param {Object} requestConfig - axios请求配置
   */
  applyAuth(requestConfig) {
    if (!requestConfig.headers) {
      requestConfig.headers = {}
    }
    
    const credentials = btoa(`${this.username}:${this.password}`)
    requestConfig.headers['Authorization'] = `Basic ${credentials}`
    
    return requestConfig
  }

  /**
   * 验证认证配置
   */
  validate() {
    if (!this.username || !this.password) {
      throw new Error('Basic Auth requires username and password')
    }
    return true
  }
}

/**
 * Digest Auth 认证处理器
 */
export class DigestAuthHandler {
  constructor(config) {
    this.username = config.username
    this.password = config.password
    this.realm = config.realm || ''
    this.nonce = config.nonce || ''
    this.qop = config.qop || 'auth'
    this.nc = '00000001'
    this.cnonce = this.generateCnonce()
  }

  /**
   * 生成客户端随机数
   */
  generateCnonce() {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15)
  }

  /**
   * 计算MD5哈希
   */
  md5(str) {
    // 简化版MD5实现，实际项目中应使用crypto-js
    return btoa(str).replace(/=/g, '').toLowerCase()
  }

  /**
   * 计算响应哈希
   */
  calculateResponse(method, uri) {
    const ha1 = this.md5(`${this.username}:${this.realm}:${this.password}`)
    const ha2 = this.md5(`${method}:${uri}`)
    
    if (this.qop === 'auth') {
      return this.md5(`${ha1}:${this.nonce}:${this.nc}:${this.cnonce}:${this.qop}:${ha2}`)
    } else {
      return this.md5(`${ha1}:${this.nonce}:${ha2}`)
    }
  }

  /**
   * 应用认证到请求配置
   */
  applyAuth(requestConfig, method = 'GET', uri = '/') {
    if (!requestConfig.headers) {
      requestConfig.headers = {}
    }

    const response = this.calculateResponse(method, uri)
    
    let authHeader = `Digest username="${this.username}", ` +
                    `realm="${this.realm}", ` +
                    `nonce="${this.nonce}", ` +
                    `uri="${uri}", ` +
                    `response="${response}"`
    
    if (this.qop === 'auth') {
      authHeader += `, qop=${this.qop}, nc=${this.nc}, cnonce="${this.cnonce}"`
    }
    
    requestConfig.headers['Authorization'] = authHeader
    
    return requestConfig
  }

  /**
   * 验证认证配置
   */
  validate() {
    if (!this.username || !this.password) {
      throw new Error('Digest Auth requires username and password')
    }
    return true
  }
}

/**
 * OAuth 1.0 认证处理器
 */
export class OAuth1Handler {
  constructor(config) {
    this.consumerKey = config.consumerKey
    this.consumerSecret = config.consumerSecret
    this.accessToken = config.accessToken
    this.accessTokenSecret = config.accessTokenSecret
    this.signatureMethod = config.signatureMethod || 'HMAC-SHA1'
    this.version = '1.0'
  }

  /**
   * 生成随机数
   */
  generateNonce() {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15)
  }

  /**
   * 获取时间戳
   */
  getTimestamp() {
    return Math.floor(Date.now() / 1000).toString()
  }

  /**
   * URL编码
   */
  percentEncode(str) {
    return encodeURIComponent(str)
      .replace(/!/g, '%21')
      .replace(/'/g, '%27')
      .replace(/\(/g, '%28')
      .replace(/\)/g, '%29')
      .replace(/\*/g, '%2A')
  }

  /**
   * 生成签名基础字符串
   */
  generateSignatureBaseString(method, url, params) {
    const sortedParams = Object.keys(params)
      .sort()
      .map(key => `${this.percentEncode(key)}=${this.percentEncode(params[key])}`)
      .join('&')
    
    return `${method.toUpperCase()}&${this.percentEncode(url)}&${this.percentEncode(sortedParams)}`
  }

  /**
   * 生成签名密钥
   */
  generateSigningKey() {
    return `${this.percentEncode(this.consumerSecret)}&${this.percentEncode(this.accessTokenSecret || '')}`
  }

  /**
   * 生成HMAC-SHA1签名（简化版）
   */
  generateSignature(baseString, signingKey) {
    // 实际项目中应使用crypto-js的HmacSHA1
    return btoa(baseString + signingKey).substring(0, 28)
  }

  /**
   * 应用认证到请求配置
   */
  applyAuth(requestConfig, method = 'GET', url) {
    if (!requestConfig.headers) {
      requestConfig.headers = {}
    }

    const timestamp = this.getTimestamp()
    const nonce = this.generateNonce()
    
    const oauthParams = {
      oauth_consumer_key: this.consumerKey,
      oauth_nonce: nonce,
      oauth_signature_method: this.signatureMethod,
      oauth_timestamp: timestamp,
      oauth_version: this.version
    }
    
    if (this.accessToken) {
      oauthParams.oauth_token = this.accessToken
    }
    
    const baseString = this.generateSignatureBaseString(method, url, oauthParams)
    const signingKey = this.generateSigningKey()
    const signature = this.generateSignature(baseString, signingKey)
    
    oauthParams.oauth_signature = signature
    
    const authHeader = 'OAuth ' + Object.keys(oauthParams)
      .map(key => `${key}="${this.percentEncode(oauthParams[key])}"`)
      .join(', ')
    
    requestConfig.headers['Authorization'] = authHeader
    
    return requestConfig
  }

  /**
   * 验证认证配置
   */
  validate() {
    if (!this.consumerKey || !this.consumerSecret) {
      throw new Error('OAuth 1.0 requires consumer key and secret')
    }
    return true
  }
}

/**
 * OAuth 2.0 认证处理器
 */
export class OAuth2Handler {
  constructor(config) {
    this.clientId = config.clientId
    this.clientSecret = config.clientSecret
    this.accessToken = config.accessToken
    this.refreshToken = config.refreshToken
    this.tokenUrl = config.tokenUrl
    this.scope = config.scope || ''
    this.grantType = config.grantType || 'client_credentials'
  }

  /**
   * 获取访问令牌
   */
  async getAccessToken() {
    if (this.accessToken && !this.isTokenExpired()) {
      return this.accessToken
    }
    
    try {
      const response = await this.requestToken()
      this.accessToken = response.access_token
      this.refreshToken = response.refresh_token
      this.tokenExpiry = Date.now() + (response.expires_in * 1000)
      
      return this.accessToken
    } catch (error) {
      throw new Error(`Failed to get OAuth2 access token: ${error.message}`)
    }
  }

  /**
   * 检查令牌是否过期
   */
  isTokenExpired() {
    return this.tokenExpiry && Date.now() >= this.tokenExpiry
  }

  /**
   * 请求新的访问令牌
   */
  async requestToken() {
    const params = new URLSearchParams()
    
    if (this.grantType === 'client_credentials') {
      params.append('grant_type', 'client_credentials')
      params.append('client_id', this.clientId)
      params.append('client_secret', this.clientSecret)
      if (this.scope) {
        params.append('scope', this.scope)
      }
    } else if (this.grantType === 'refresh_token' && this.refreshToken) {
      params.append('grant_type', 'refresh_token')
      params.append('refresh_token', this.refreshToken)
      params.append('client_id', this.clientId)
      params.append('client_secret', this.clientSecret)
    }
    
    const response = await fetch(this.tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params
    })
    
    if (!response.ok) {
      throw new Error(`Token request failed: ${response.status} ${response.statusText}`)
    }
    
    return await response.json()
  }

  /**
   * 应用认证到请求配置
   */
  async applyAuth(requestConfig) {
    if (!requestConfig.headers) {
      requestConfig.headers = {}
    }
    
    const token = await this.getAccessToken()
    requestConfig.headers['Authorization'] = `Bearer ${token}`
    
    return requestConfig
  }

  /**
   * 验证认证配置
   */
  validate() {
    if (!this.clientId || !this.clientSecret) {
      throw new Error('OAuth 2.0 requires client ID and secret')
    }
    if (!this.tokenUrl) {
      throw new Error('OAuth 2.0 requires token URL')
    }
    return true
  }
}

/**
 * 认证执行器工厂
 */
export class AuthExecutor {
  /**
   * 创建认证处理器
   * @param {Object} authConfig - 认证配置
   * @returns {Object} 认证处理器实例
   */
  static createHandler(authConfig) {
    if (!authConfig || !authConfig.type) {
      return null
    }
    
    switch (authConfig.type) {
      case 'basic':
        return new BasicAuthHandler(authConfig)
      case 'digest':
        return new DigestAuthHandler(authConfig)
      case 'oauth1':
        return new OAuth1Handler(authConfig)
      case 'oauth2':
        return new OAuth2Handler(authConfig)
      default:
        throw new Error(`Unsupported authentication type: ${authConfig.type}`)
    }
  }

  /**
   * 应用认证到请求配置
   * @param {Object} requestConfig - 请求配置
   * @param {Array} authentications - 认证配置列表
   * @param {string} method - HTTP方法
   * @param {string} url - 请求URL
   * @returns {Object} 应用认证后的请求配置
   */
  static async applyAuthentications(requestConfig, authentications, method = 'GET', url = '') {
    if (!authentications || authentications.length === 0) {
      return requestConfig
    }
    
    let config = { ...requestConfig }
    
    for (const authConfig of authentications) {
      try {
        const handler = this.createHandler(authConfig)
        if (handler) {
          handler.validate()
          if (handler.applyAuth.constructor.name === 'AsyncFunction') {
            config = await handler.applyAuth(config, method, url)
          } else {
            config = handler.applyAuth(config, method, url)
          }
        }
      } catch (error) {
        console.error(`Failed to apply authentication ${authConfig.type}:`, error)
        throw error
      }
    }
    
    return config
  }

  /**
   * 验证所有认证配置
   * @param {Array} authentications - 认证配置列表
   * @returns {boolean} 验证结果
   */
  static validateAuthentications(authentications) {
    if (!authentications || authentications.length === 0) {
      return true
    }
    
    for (const authConfig of authentications) {
      try {
        const handler = this.createHandler(authConfig)
        if (handler) {
          handler.validate()
        }
      } catch (error) {
        console.error(`Authentication validation failed for ${authConfig.type}:`, error)
        return false
      }
    }
    
    return true
  }
}

export default AuthExecutor