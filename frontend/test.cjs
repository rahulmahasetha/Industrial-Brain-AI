const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:5173/copilot', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  const content = await page.content();
  if (content.includes('New Chat') || content.includes('AI Copilot')) {
    console.log('SUCCESS: Page rendered successfully. Content contains expected text.');
  } else {
    console.log('FAIL: Page is blank or missing expected content. HTML:', content.substring(0, 500));
  }
  await browser.close();
})();
