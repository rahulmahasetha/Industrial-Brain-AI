import puppeteer from 'puppeteer';
(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  // Simulate print dimensions - A4 at 96dpi
  await page.setViewport({ width: 794, height: 1123 });
  await page.emulateMediaType('print');
  await page.goto('file:///Users/rahulmahaseth/Desktop/Industrial Brain AI/docs/Project_Report.html', { waitUntil: 'networkidle0', timeout: 30000 });
  await page.screenshot({ path: '/Users/rahulmahaseth/Desktop/Industrial Brain AI/frontend/report_cover_preview.png', fullPage: false });
  await browser.close();
  console.log('Done');
})();
