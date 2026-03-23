const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 100 
  });
  const page = await browser.newPage({
    viewport: { width: 1400, height: 900 }
  });
  
  await page.goto('http://localhost:5176/');
  
  // 截图
  await page.screenshot({ 
    path: 'frontend-screenshot.png',
    fullPage: true 
  });
  
  console.log('✅ 截图已保存到：frontend-screenshot.png');
  
  // 等待 10 秒后关闭
  await new Promise(resolve => setTimeout(resolve, 10000));
  await browser.close();
})();
