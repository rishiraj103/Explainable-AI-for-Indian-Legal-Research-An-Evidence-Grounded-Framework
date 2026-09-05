# Week 16 minimal researcher demo

From the repository root, run:

```powershell
python scripts/serve_week16_demo.py
```

Open http://127.0.0.1:8000/demo/ and stop with Ctrl+C. No npm install, model weights, PostgreSQL, or pipeline execution is needed.

This is the frozen plan's minimal researcher-facing interface: a single-user local demo, not a production system. It has no accounts, arbitrary-query retrieval, or deployment infrastructure.

All seven Week 13 examples are included: 2008_1629, 1980_105, 1980_133, 1981_55, 1985_40, 1997_792, and 2013_35. Select a case and switch between structured and unstructured presentations.

The browser reads `artifacts/week13_review_packet.md` for the frozen excerpt, authorities, passages, conclusion, and uncertainty. The final `artifacts/week11_temporal_prerank_evaluation.json` has citation checks and outcome flags but does not contain the full answer text. `artifacts/week13_rq3_ablation_parity.json` supplies the independent packet citation-ID mapping. No older pre-fix answer is substituted and no review ratings are shown. Before displaying anything, the page checks both presentations' ordered citation IDs and reporter citations against the evaluation, and checks passage parity across formats. Original text, including OCR imperfections, is preserved.

The launcher serves only the three artifacts above and the demo HTML/CSS/modules on loopback. It does not expose the workspace, credentials, models, or database. Run `node demo/verify.mjs` to verify all seven examples offline.

## Verification

Verified all seven cases in both formats in headless Microsoft Edge: 14 rendered displays, 35/35 ordered citation IDs and reporter citations per format, and unchanged verbatim passages. The structured view exposes all five sections. Desktop and 390-pixel mobile layout checks pass, with no browser script errors. A screenshot is saved at `artifacts/week16_demo.png`.

Optional browser verification (Playwright is a development-only tool, not required to run the demo):

```powershell
# In a separate terminal, keep the demo running on port 8016:
python scripts/serve_week16_demo.py --port 8016
# Then, in another terminal at the repository root:
$demoTools = Join-Path $env:TEMP 'legal-xai-demo-browser-tools'
npm install --prefix $demoTools playwright --no-audit --no-fund
$env:DEMO_PLAYWRIGHT_MODULE = Join-Path $demoTools 'node_modules/playwright/index.mjs'
node demo/verify-browser.mjs
```

This verification uses an installed Microsoft Edge browser and checks the actual rendered passages and citations against the packet/evaluation. It also checks that paths outside the demo allowlist return 404.
