# E2 training and checkpoint-selection audit

Saved best checkpoint: `artifacts/e2_training_checkpoints/checkpoint-939`. The final test evaluation was produced after loading that checkpoint, whose validation accuracy was `0.5727`.

## Validation history

| Epoch | Accuracy | Macro F1 | Loss |
| ---: | ---: | ---: | ---: |
| 1.00 | 0.5005 | 0.3354 | 0.7238 |
| 2.00 | 0.5585 | 0.5087 | 0.7225 |
| 2.99 | 0.5727 | 0.5588 | 0.7183 |

## Training-loss observation

The first logged training loss was `0.6833` and the final logged training loss was `0.5928` (-13.24%). Intermediate minibatch losses fluctuate, but the logged training loss declines and validation accuracy improves at each saved epoch; there is no majority-class-collapse or incorrect-checkpoint indication in this audit.

## Test confusion matrix

Rows are true labels and columns predicted labels, ordered `[0, 1]`: `[[552, 197], [450, 304]]`. Both predicted classes occur (`1002` label-0 and `501` label-1 predictions), so the result is not an all-majority-class collapse.
