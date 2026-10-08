const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const svg = fs.readFileSync(path.join(root, 'resources', 'app.svg'), 'utf8');
  const output = path.join(root, 'tools', 'icon-pngs');
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ deviceScaleFactor: 1 });
    for (const size of [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]) {
      await page.setViewportSize({ width: size, height: size });
      await page.setContent(`<style>html,body{margin:0;width:100%;height:100%;overflow:hidden}svg{display:block;width:100%;height:100%}</style>${svg}`);
      await page.screenshot({ path: path.join(output, `${size}.png`), omitBackground: true });
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
