# E2 correction manifest

## Discarded: 256-token cap, 99.2% truncated

The original prefix-only E2 result is retained for traceability but is not the accepted E2 result. Test accuracy: **0.5695**; macro F1: **0.5575**.

## Corrected: chunk-and-pool

The accepted E2 run uses overlapping 512-token windows (50-token overlap) and mean-pooled logits before softmax. All 1503/1503 eligible test documents are covered. Test accuracy: **0.5968**; macro F1: **0.5924**. Majority-vote comparison: accuracy **0.6015**, macro F1 **0.5937**.
