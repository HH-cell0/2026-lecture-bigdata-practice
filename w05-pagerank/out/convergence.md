# Task 2 · Convergence

## Predictions (written before any run)

Basis: `bench.py` builds a graph with one 2-node spider trap (p01198 <-> p01199),
12 dead ends, ~5 out-links per node. My `pagerank` sends dead-end rank to every
node, so the trap is a closed set, and a 2-cycle has eigenvalue -1. So the
second eigenvalue of the full matrix is beta * 1 = beta, and the L1 change
should shrink by about beta per iteration: iterations ~ ln(tol) / ln(beta).

| beta | ln(1e-10)/ln(beta) | prediction |
|---|---|---|
| 0.5  | 23.03/0.693 = 33   | ~33 |
| 0.7  | 23.03/0.357 = 65   | ~65 |
| 0.85 | 23.03/0.163 = 142  | ~142 |
| 0.95 | 23.03/0.051 = 449  | ~449 |
| 0.99 | 23.03/0.010 = 2291 | hits the 500 cap, does not converge |

(Upper bounds if the first change is ~1; a smaller start means a few fewer.)

- **A4 iterations:** no change from 1,200 to 20,000 nodes (16.7x). The rate is
  beta * |lambda2| and the trap keeps |lambda2| = 1 at any size; n does not appear.
- **A4 time:** one iteration touches every node and every edge once, ~6n work,
  so per-iteration time and total time grow ~16.7x (a bit more if a 20,000-entry
  dict falls out of cache).
- **A5:** one extra digit costs ln(10)/-ln(0.85) = 2.303/0.163 = 14.2 iterations
  at beta 0.85, so 1e-6 should need ~4 x 14.2 = 57 fewer iterations than 1e-10.
- **A6:** as beta -> 1 less rank teleports out of the trap, so I expect
  p01198/p01199 to climb into the top 10 at 0.95 or 0.99.

## Measurements (this laptop, two passes)

`convergence.json` holds both passes: runs 1-8 are pass 1, runs 9-16 repeat them.
Iteration counts were identical in both passes; times are shown as pass1 / pass2.

| nodes | edges | beta | tol | iterations | seconds | ms / iteration |
|---|---|---|---|---|---|---|
| 1,200 | 5,877 | 0.5  | 1e-10 | 14 | 0.015 / 0.021 | 1.1 / 1.5 |
| 1,200 | 5,877 | 0.7  | 1e-10 | 17 | 0.018 / 0.020 | 1.1 / 1.2 |
| 1,200 | 5,877 | 0.85 | 1e-10 | 20 | 0.025 / 0.023 | 1.3 / 1.2 |
| 1,200 | 5,877 | 0.95 | 1e-10 | 23 | 0.027 / 0.024 | 1.2 / 1.0 |
| 1,200 | 5,877 | 0.99 | 1e-10 | 24 | 0.024 / 0.027 | 1.0 / 1.1 |
| 20,000 | 101,665 | 0.85 | 1e-10 | 21 | 0.495 / 0.504 | 23.6 / 24.0 |
| 20,000 | 101,665 | 0.95 | 1e-10 | 24 | 0.650 / 0.671 | 27.1 / 28.0 |
| 1,200 | 5,877 | 0.85 | 1e-6  | 12 | 0.016 / 0.015 | 1.3 / 1.3 |

Timing noise between passes: up to 40% on the 1,200-node runs (0.015 vs 0.021 s,
too short for the timer to measure well), 2-3% on the 20,000-node runs. Not
re-measured: plugging in would not help, because the noise comes from how short
the run is. The fix would be to repeat the same size many times and sum the times.
Check: the beta 0.99 run that stopped at 24 iterations is 1.6e-11 (L1) away from
a 5,000-iteration run, so stopping early did not cut convergence short.

## Why my predictions were wrong

I predicted 142 iterations at 0.85 and that 0.99 would hit the 500 cap. I got 20
and 24. Taking the graph apart (scratch diagnostic, not submitted):

- **The 2-node trap has 0 in-links** and gets identical inflow on both nodes, so
  p01198 - p01199 stays exactly 0.0: the period-2 eigenvalue -1 is never
  triggered. It keeps ~2/n of the rank (1.70e-3 at n=1,200) and never matters.
- **The real trap is p00000-p00009.** Preferential attachment only links to
  nodes that already exist, so the graph is a DAG pointing back at the first 10
  nodes, which link only to each other (only 1 edge outside them points to a
  later node; none of them is a dead end). They hold 75.8% of the rank at beta 0.85 and 98.1% at 0.99.
- **Starting uniform, the beta-rate part of the error starts at zero.** The update is
  r(k+1) = beta M' r(k) + (1-beta) v with v uniform and r(0) = v, so
  r(k) - r* = beta^k [M'^k v - (1-beta) sum_i beta^i M'^(i+k) v]. If M'^k v
  settles at rate rho, the bracket is O(rho^k) and the error is O((beta rho)^k).
  beta is only the worst case, reached when M'^k v never settles.
- Measured steady-state error ratio e(k+1)/e(k) (L1 vs a 3,000-iteration
  reference, k = 21-24): 0.3663 at beta 0.85 and 0.4269 at 0.99, so
  rho = 0.3663/0.85 = 0.4309 and 0.4269/0.99 = 0.4312 (0.4318 / 0.4316 at
  20,000 nodes): rho is the same for both betas, set by the graph (the
  10-node core), not by beta.

## A3 · Shape as beta -> 1

14, 17, 20, 23, 24: it grows, but more slowly toward 1, not blowing up. The rate
per iteration is beta x rho with rho = 0.431 for both betas, so as beta -> 1
it approaches 0.431 instead of 1, and the count heads toward a limit of
ln(1e-10/1.5)/ln(1/0.431) = 23.4/0.84 ~ 28. The bound ln(tol)/ln(beta) assumes
a part of the error with |lambda2| = 1, and this graph has none.
Most direct evidence: beta 0.999, 0.9999 and 0.99999 all stop at 24 iterations,
where ln(tol)/ln(beta) predicts 23,014 / 230,247 / 2,302,574. All three answers
are 2.0e-11 (L1) from a 5,000-iteration run; the later ~7e-15 per-step change is
rounding jitter (net drift 3e-14 from iteration 200 to 5,000).
28 is an upper bound computed from the steady-state ratio alone. The measured 24
falls below it because the first ~12 iterations shrink faster than the steady
state (the same transient as in A5).

## A4 · Size (1,200 -> 20,000 nodes, 16.7x; edges 17.3x)

- **Iterations: 20 -> 21 and 23 -> 24.** I predicted no change, and that was right but
  for the wrong reason (I thought the trap fixed the rate at beta). The rate comes
  from the 10-node core, which is the same at both sizes (same seed, same first
  nodes). The +1 is not structural: reverse BFS gives a maximum of 2 hops to the
  core at both sizes, and 14 nodes (12 dead ends + 2 trap) cannot reach it at
  both sizes. It is a parallel shift: at iterations 17-23 the 20,000-node L1
  error is 2.50-2.58x the 1,200-node error at every iteration (iter 20: 5.00e-11
  vs 1.98e-11), while the starting errors differ by only 1.014x. One iteration
  cuts the error 1/0.366 = 2.73x, so the gap is ln(2.5)/ln(2.73) = 0.92/1.00 ~ 1
  iteration, and the tol threshold falls inside that gap.
- **Time:** the reliable figures are the 20,000-node ones, steady to 2-3%
  between passes: 23.6 / 24.0 ms per iteration at 0.85, 27.1 / 28.0 at 0.95.
  Against the noisy 1,200-node figures (1.0-1.5 ms) that is about 18-20x per
  iteration for 17.3x the edges, so my linear-work prediction holds per
  iteration. The total-time ratios (x19.8 / x21.9 at 0.85) carry the
  1,200-node noise. The extra is not pinned down: the
  1,200-node times vary by up to 40%, too much to separate a cache effect from noise.

## A5 · Tolerance (1e-10 vs 1e-6 at beta 0.85)

20 vs 12: 8 iterations for 4 digits, **2 per digit**. Predicted 14.2 per digit
from ln(10)/-ln(0.85). Across the iterations that matter here (12 -> 20) the
L1 change shrinks by an average 0.336 per iteration, so
ln(10)/ln(1/0.336) = 2.303/1.091 = 2.11 per digit, x 4 = 8.4, which matches.
(The steady-state 0.366 gives 2.29 per digit, x 4 = 9.2: iterations 12-20 are
still shrinking faster than the steady state.)

## A6 · Top 10 vs beta

The **set never changes**: it is always p00000-p00009, the 10-node core that
holds 76-98% of the rank. The **order first changes at beta 0.7**: p00000 and
p00004 swap 7th and 8th place (beta 0.5 has p00000 7th; 0.7 to 0.99 have p00004
7th). Places 1-6 (p00009, p00001, p00006, p00005, p00003, p00002) and 9-10 never
move. I predicted the 2-node trap would enter the top 10; it cannot, because
nothing links into it.

## A7 · Machine

- CPU: 11th Gen Intel Core i5-1135G7 @ 2.40 GHz, 4 cores / 8 threads
- RAM: 7.7 GB total, **0.7 GB free** at measurement time
- OS / Python: Windows 11 Home 10.0.26200, Python 3.14.8 (platform string in the JSON)
- Power: **on battery**, 48%, discharging
- Also running: Claude Code (3 processes, ~680 MB), Microsoft Edge, Notion,
  Discord, ChatGPT desktop, iCloud, iPSMonitor, Explorer
