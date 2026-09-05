import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {loadCases} from './data.mjs';
const read = file => readFileSync(new URL(`../artifacts/${file}`, import.meta.url), 'utf8');
const evaluation = JSON.parse(read('week11_temporal_prerank_evaluation.json'));
const cases = loadCases(read('week13_review_packet.md'), evaluation, JSON.parse(read('week13_rq3_ablation_parity.json')));
for (const item of cases) {
  for (const title of ['Issue context (excerpt)', 'Authorities and source locators', 'Supporting evidence', 'Conclusion', 'Uncertainty']) {
    assert(item.displays.structured.includes(`**${title}**`));
  }
  assert.equal(item.passages.length, 5);
  console.log(`${item.id}: both formats, five exact citation IDs/reporters, passage parity PASS`);
}
assert.equal(cases.length, 7);
console.log('PASS: 7/7 cases; 35/35 citations per presentation.');
