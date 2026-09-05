// Optional browser check. Supply an installed Playwright module path; no demo
// runtime dependency is required. Start serve_week16_demo.py --port 8016 first.
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {loadCases} from './data.mjs';
const {chromium} = await import(pathToFileURL(process.env.DEMO_PLAYWRIGHT_MODULE).href);
const read = file => readFileSync(new URL(`../artifacts/${file}`, import.meta.url), 'utf8');
const cases = loadCases(read('week13_review_packet.md'), JSON.parse(read('week11_temporal_prerank_evaluation.json')), JSON.parse(read('week13_rq3_ablation_parity.json')));
const browser = await chromium.launch({channel: 'msedge', headless: true});
try {
  const page = await browser.newPage({viewport: {width: 1280, height: 900}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:8016/demo/');
  await page.waitForFunction(() => !document.querySelector('#case').disabled);
  for (const item of cases) {
    await page.selectOption('#case', item.id);
    for (const format of ['structured', 'unstructured']) {
      await page.selectOption('#format', format);
      const text = await page.locator('#brief').textContent();
      const ids = await page.locator('#brief li').allTextContents();
      assert.deepEqual(ids.map(line => /citation ID `([^`]+)`/.exec(line)[1]), item.citationIds);
      for (const passage of item.passages) assert(text.includes(passage), `${item.id}: passage changed in DOM`);
      if (format === 'structured') assert.equal(await page.locator('#brief h3').count(), 5);
    }
    console.log(`${item.id}: rendered citations and verbatim passages PASS (both formats)`);
  }
  assert.deepEqual(errors, []);
  await page.selectOption('#case', '2008_1629');
  await page.selectOption('#format', 'structured');
  await page.screenshot({path: 'artifacts/week16_demo.png', fullPage: true});
  await page.setViewportSize({width: 390, height: 844});
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  for (const path of ['/.env', '/config/reproducibility_freeze.json']) {
    assert.equal((await page.request.get(`http://127.0.0.1:8016${path}`)).status(), 404);
  }
  console.log('PASS: 14 browser displays, desktop/mobile layout, no script errors, scoped file serving.');
} finally {
  await browser.close();
}
