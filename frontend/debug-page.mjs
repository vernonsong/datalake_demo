import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ 
    headless: true
  });
  const page = await browser.newPage({
    viewport: { width: 1400, height: 900 }
  });
  
  console.log('正在打开前端页面...');
  await page.goto('http://localhost:5176/');
  
  // 等待页面加载
  await page.waitForTimeout(3000);
  
  // 获取页面 HTML
  const html = await page.content();
  console.log('\n=== 页面 HTML 结构 ===\n');
  console.log(html.substring(0, 3000));
  
  // 查找所有输入框
  const inputs = await page.locator('input, textarea').all();
  console.log(`\n找到 ${inputs.length} 个输入框`);
  
  for (let i = 0; i < inputs.length; i++) {
    const placeholder = await inputs[i].getAttribute('placeholder');
    const type = await inputs[i].getAttribute('type');
    console.log(`输入框 ${i + 1}: type=${type}, placeholder=${placeholder}`);
  }
  
  // 查找所有按钮
  const buttons = await page.locator('button, [role="button"]').all();
  console.log(`\n找到 ${buttons.length} 个按钮`);
  
  for (let i = 0; i < buttons.length; i++) {
    const text = await buttons[i].textContent();
    const ariaLabel = await buttons[i].getAttribute('aria-label');
    console.log(`按钮 ${i + 1}: text="${text}", aria-label="${ariaLabel}"`);
  }
  
  await browser.close();
  console.log('\n✅ 测试完成');
})();
