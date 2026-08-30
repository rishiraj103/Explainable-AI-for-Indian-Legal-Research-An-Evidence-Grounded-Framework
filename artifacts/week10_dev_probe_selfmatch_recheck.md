# Week 10 Dev-Probe Self-Match Recheck

| Dev case | Before k=100 / k=500 | After k=100 / k=500 | Result |
| --- | --- | --- | --- |
| `1980_104` | rank 58 / rank 58 | rank 58 / rank 58 | unchanged |
| `1982_186` | absent / rank 260 | absent / rank 260 | unchanged |
| `1984_62` | absent / absent | rank 40 / rank 40 | newly retrieved |
| `1986_70` | absent / absent | absent / absent | unchanged |
| `1988_238` | absent / absent | rank 64 / rank 64 | newly retrieved |
| `1990_651` | rank 92 / rank 92 | rank 92 / rank 92 | unchanged |
| `1992_137` | absent / absent | rank 67 / rank 67 | newly retrieved |
| `1992_464` | rank 69 / rank 69 | rank 69 / rank 69 | unchanged |
| `1993_66` | absent / absent | absent / absent | unchanged |

The pre-fix broad lexical-mismatch conclusion is withdrawn: the self-match rule was a material contributor. The corrected configuration retrieves 6/9 expected authorities at k=100 and 7/9 at k=500; newly retrieved after the repair are 1984_62, 1988_238, 1992_137. Only the remaining absent cases are residual retrieval failures, not evidence for a corpus-wide lexical-mismatch claim.
