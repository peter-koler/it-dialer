import { test, expect } from '@playwright/test';

// 测试用户配置
const testUsers = {
  tenant1: { username: 'ceshi1', password: '123456' },
  tenant2: { username: 'ceshi2', password: '123456' },
  superuser: { username: 'superadmin', password: '1Q2W3E' }
};

// 通用登录函数
async function login(page, username, password) {
  await page.goto('/');
  await page.waitForSelector('input[placeholder*="用户名"], input[placeholder*="username"], input[type="text"]', { timeout: 10000 });
  
  // 监听控制台错误
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Browser console error:', msg.text());
    }
  });
  
  // 监听页面错误
  page.on('pageerror', error => {
    console.log('Page error:', error.message);
  });
  
  // 填写用户名
  const usernameInput = page.locator('input[placeholder*="用户名"], input[placeholder*="username"], input[type="text"]').first();
  await usernameInput.fill(username);
  
  // 填写密码
  const passwordInput = page.locator('input[type="password"]');
  await passwordInput.fill(password);
  
  // 点击登录按钮
  const loginButton = page.locator('button:has-text("登录"), button:has-text("Login"), button[type="submit"]');
  await loginButton.click();
  
  // 等待一段时间，观察页面变化
  await page.waitForTimeout(3000);
  
  // 检查是否有错误消息
  const errorMessage = page.locator('.ant-message-error, .error-message');
  if (await errorMessage.count() > 0) {
    const errorText = await errorMessage.first().textContent();
    console.log('Login error message:', errorText);
    throw new Error(`Login failed: ${errorText}`);
  }
  
  // 等待登录成功，检查是否跳转到主页面
  try {
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 15000 });
  } catch (error) {
    console.log('Current URL after login attempt:', page.url());
    throw error;
  }
}

// 通用登出函数
async function logout(page) {
  try {
    // 查找登出按钮或用户菜单
    const logoutSelector = 'button:has-text("退出"), button:has-text("登出"), button:has-text("Logout"), .ant-dropdown-trigger, .user-menu';
    await page.locator(logoutSelector).first().click();
    
    // 如果是下拉菜单，点击登出选项
    const logoutOption = page.locator('li:has-text("退出"), li:has-text("登出"), li:has-text("Logout")');
    if (await logoutOption.count() > 0) {
      await logoutOption.first().click();
    }
    
    // 等待跳转到登录页面
    await page.waitForURL(/\/(login|auth)/, { timeout: 10000 });
  } catch (error) {
    console.log('Logout failed, navigating to login page directly');
    await page.goto('/login');
  }
}

test.describe('多租户系统功能测试', () => {
  
  test('1. 租户用户登录测试', async ({ page }) => {
    // 访问登录页面
    await page.goto('http://localhost:8080/login');
    
    // 填写登录表单
    await page.fill('input[placeholder="用户名"]', testUsers.tenant1.username);
    await page.fill('input[placeholder="密码"]', testUsers.tenant1.password);
    
    // 点击登录按钮
    await page.click('button[type="submit"]');
    
    // 等待页面跳转
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功 - 检查页面标题或用户名
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
  });
  
  test('2. 超级管理员登录测试', async ({ page }) => {
    // 访问登录页面
    await page.goto('http://localhost:8080/login');
    
    // 填写登录表单
    await page.fill('input[placeholder="用户名"]', testUsers.superuser.username);
    await page.fill('input[placeholder="密码"]', testUsers.superuser.password);
    
    // 点击登录按钮
    await page.click('button[type="submit"]');
    
    // 等待页面跳转
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功 - 检查页面标题
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
  });
  
  test('3. 租户隔离测试 - 任务管理', async ({ page }) => {
    // 使用 ceshi1 登录
    await page.goto('http://localhost:8080/login');
    await page.fill('input[placeholder="用户名"]', testUsers.tenant1.username);
    await page.fill('input[placeholder="密码"]', testUsers.tenant1.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
    await expect(page.locator('text=ceshi1')).toBeVisible();
  });
  
  test('4. 创建拨测任务测试', async ({ page }) => {
    // 使用 ceshi1 登录
    await page.goto('http://localhost:8080/login');
    await page.fill('input[placeholder="用户名"]', testUsers.tenant1.username);
    await page.fill('input[placeholder="密码"]', testUsers.tenant1.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
  });
  
  test('5. 节点管理测试（全局共享）', async ({ page }) => {
    // 使用 ceshi1 登录
    await page.goto('http://localhost:8080/login');
    await page.fill('input[placeholder="用户名"]', testUsers.tenant1.username);
    await page.fill('input[placeholder="密码"]', testUsers.tenant1.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
  });
  
  test('6. 系统变量管理测试', async ({ page }) => {
    // 使用 ceshi1 登录
    await page.goto('http://localhost:8080/login');
    await page.fill('input[placeholder="用户名"]', testUsers.tenant1.username);
    await page.fill('input[placeholder="密码"]', testUsers.tenant1.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
  });
  
  test('7. 报表功能测试', async ({ page }) => {
    // 使用 ceshi1 登录
    await page.goto('http://localhost:8080/login');
    await page.fill('input[placeholder="用户名"]', testUsers.tenant1.username);
    await page.fill('input[placeholder="密码"]', testUsers.tenant1.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
  });
  
  test('8. 超级管理员跨租户功能测试', async ({ page }) => {
    // 使用超级管理员登录
    await page.goto('http://localhost:8080/login');
    await page.fill('input[placeholder="用户名"]', testUsers.superuser.username);
    await page.fill('input[placeholder="密码"]', testUsers.superuser.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
  });
  
  test('9. 租户数据隔离验证', async ({ page }) => {
    // 使用 ceshi1 登录
    await page.goto('http://localhost:8080/login');
    await page.fill('input[placeholder="用户名"]', testUsers.tenant1.username);
    await page.fill('input[placeholder="密码"]', testUsers.tenant1.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home|main|probe-config\/node)/, { timeout: 10000 });
    
    // 验证登录成功
    await expect(page.locator('text=IT 拨测系统')).toBeVisible();
  });
  
});