// 测试401错误处理的脚本
// 在浏览器控制台中运行此脚本

// 1. 设置无效token
localStorage.setItem('access_token', 'invalid_token_test');
console.log('已设置无效token:', localStorage.getItem('access_token'));

// 2. 导入axios实例（需要在浏览器环境中）
// 这个脚本需要在前端应用的控制台中运行

// 3. 发送请求测试401处理
fetch('http://localhost:5001/api/v1/nodes', {
  headers: {
    'Authorization': 'Bearer invalid_token_test',
    'Content-Type': 'application/json'
  }
})
.then(response => {
  console.log('响应状态:', response.status);
  if (response.status === 401) {
    console.log('收到401错误');
    // 手动触发清理和跳转逻辑
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('current_tenant');
    console.log('已清除认证信息');
    
    if (window.location.pathname !== '/login') {
      console.log('准备跳转到登录页面');
      window.location.href = '/login';
    }
  }
  return response.json();
})
.then(data => {
  console.log('响应数据:', data);
})
.catch(error => {
  console.error('请求错误:', error);
});

// 使用说明：
// 1. 在浏览器中打开 http://localhost:8080
// 2. 打开开发者工具的控制台
// 3. 复制粘贴上面的代码并执行
// 4. 观察控制台输出和页面跳转行为