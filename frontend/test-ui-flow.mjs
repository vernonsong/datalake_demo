import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 100 
  });
  const page = await browser.newPage({
    viewport: { width: 1400, height: 900 }
  });
  
  console.log('正在打开前端页面...');
  await page.goto('http://localhost:5176/');
  
  // 等待页面加载
  await page.waitForTimeout(2000);
  
  // 截图 - 初始状态
  await page.screenshot({ 
    path: 'screenshot-1-initial.png',
    fullPage: true 
  });
  console.log('✅ 截图 1：初始状态');
  
  // 查找输入框并输入文本
  const input = page.locator('textarea[placeholder*="输入消息"]');
  await input.click();
  await input.fill('测试消息');
  console.log('✅ 已输入测试消息');
  
  await page.waitForTimeout(1000);
  
  // 截图 - 输入后
  await page.screenshot({ 
    path: 'screenshot-2-typed.png',
    fullPage: true 
  });
  console.log('✅ 截图 2：输入消息后');
  
  // 查找发送按钮并点击
  const sendButton = page.locator('button[aria-label*="发送"], button:has-text("发送")');
  await sendButton.click();
  console.log('✅ 已点击发送');
  
  // 等待响应
  await page.waitForTimeout(5000);
  
  // 截图 - 发送后
  await page.screenshot({ 
    path: 'screenshot-3-sent.png',
    fullPage: true 
  });
  console.log('✅ 截图 3：发送消息后');
  
  // 获取控制台日志
  const logs = await page.evaluate(() => {
    return window.consoleLogs || [];
  });
  console.log('控制台日志:', logs);
  
  console.log('\n所有截图已保存到：frontend/ 目录');
  
  // 等待 5 秒后关闭
  await new Promise(resolve => setTimeout(resolve, 5000));
  await browser.close();
})();
