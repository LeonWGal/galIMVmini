const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const variants = path.join(root, 'resources', 'lobe-variants');
  const output = path.join(root, 'tools', 'variant-pngs');
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ deviceScaleFactor: 1 });
    for (const file of fs.readdirSync(variants).filter(name => /^simple-.*\.svg$/i.test(name))) {
      const slug = file.replace(/^simple-/, '').replace(/\.svg$/i, '');
      const svg = fs.readFileSync(path.join(variants, file), 'utf8');
      const folder = path.join(output, slug);
      fs.mkdirSync(folder, { recursive: true });
      for (const size of [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]) {
        await page.setViewportSize({ width: size, height: size });
        await page.setContent(`<style>html,body{margin:0;width:100%;height:100%;overflow:hidden}svg{display:block;width:100%;height:100%}</style>${svg}`);
        await page.screenshot({ path: path.join(folder, `${size}.png`), omitBackground: true });
      }
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
