# Week 7 · Task 2 — The Contrast Curve

All numbers measured on this laptop (A7 below). `sample_distances` seeds with
`random.Random(246 + dim)`, so every row is deterministic and reproducible.

## A1 / A2 — contrast against dimension

`pairs` is the number of sampled pairs with i ≠ j.

The row d=50, n=1000, pairs 19,977 appears three times in `curse.json`, once from
each sweep. The statistics were identical all three times; only the time moved,
0.540 s against 0.154–0.179 s.

| d | n | pairs | mean | min | max | contrast | rel.sd | seconds |
|---|---|---|---|---|---|---|---|---|
| 2 | 1000 | 19978 | 0.521 | 0.003 | 1.326 | 488.582 | 0.4759 | 0.050 |
| 5 | 1000 | 19977 | 0.884 | 0.111 | 1.687 | 14.257 | 0.2816 | 0.077 |
| 10 | 1000 | 19977 | 1.274 | 0.438 | 2.159 | 3.925 | 0.1927 | 0.065 |
| 20 | 1000 | 19981 | 1.815 | 0.821 | 2.670 | 2.253 | 0.1352 | 0.143 |
| 50 | 1000 | 19977 | 2.867 | 1.909 | 3.785 | 0.982 | 0.0830 | 0.540 |
| 100 | 1000 | 19974 | 4.068 | 3.206 | 4.954 | 0.545 | 0.0598 | 0.702 |
| 200 | 1000 | 19980 | 5.776 | 4.871 | 6.682 | 0.372 | 0.0414 | 0.830 |
| 500 | 2000 | 19983 | 9.126 | 8.099 | 10.176 | 0.256 | 0.0264 | 2.028 |
| 1000 | 2000 | 19997 | 12.909 | 11.970 | 13.806 | 0.153 | 0.0186 | 4.341 |

## A3 — what contrast does

Contrast falls by more than three orders of magnitude, from 488.6 at d=2 to 0.153 at d=1000.
It first drops below 1 at **d = 50** (0.982) and below 0.5 between **d = 100 and 200**
(0.545 → 0.372).

The threshold at d=50 is within seed noise. Ten seeds at d=50, n=1000 give
contrast 0.856–1.068 (mean 0.980, sd 0.067), and only 6 of the 10 fall below 1.
So the honest answer is "around d ≈ 50", not "at 50".

A Gaussian-tail estimate predicts both crossings. The extremes of 20,000 samples
sit at about z = 3.9 sd, so contrast ≈ 2·z·rs / (1 − z·rs).
- contrast = 1 needs rs = 0.0855, i.e. d ≈ 48.
- contrast = 0.5 needs rs = 0.0513, i.e. d ≈ 133.

## A4 — how the mean grows: derived, then checked

For one coordinate with x, y ~ U(0,1):

- E[(x−y)²] = 1/6, so S = D² has **E[S] = d/6 exactly**.
- E[(x−y)⁴] = 1/15, so Var[(x−y)²] = 1/15 − 1/36 = 7/180, and Var[S] = 7d/180.
- Expanding √S to second order around E[S]:
  E[D] ≈ √E[S] − Var[S] / (8·E[S]^{3/2}).
  The ratio Var[S] / (8·E[S]²) is (7d/180) / (8d²/36) = 7/(40d).

  **E[D] ≈ √(d/6) · (1 − 7/(40d))**, and 7/40 = 0.175. The correction is derived, not fitted.
- Relative sd: rs ≈ √Var[S] / (2·E[S]) = 3·√(7/180) / √d = **0.5916 / √d**.

The predictions for d = 500 and 1000 were written down before those runs:

| d | √(E D²) measured | √(d/6) | mean measured | predicted mean | rel.sd measured | predicted |
|---|---|---|---|---|---|---|
| 2 | 0.577 | 0.577 | 0.521 | 0.527 | 0.476 | 0.418 |
| 5 | 0.919 | 0.913 | 0.884 | 0.881 | 0.282 | 0.265 |
| 20 | 1.832 | 1.826 | 1.815 | 1.810 | 0.135 | 0.132 |
| 200 | 5.781 | 5.774 | 5.776 | 5.768 | 0.041 | 0.042 |
| 500 | 9.129 | 9.129 | 9.126 | **9.125** | 0.026 | **0.0265** |
| 1000 | 12.911 | 12.910 | 12.909 | **12.908** | 0.019 | **0.0187** |

So the mean grows like **√d with coefficient 1/√6 = 0.408**, not linearly. For d ≥ 20,
mean/√d stays between 0.4055 and 0.4084, and the local log-log slope is 0.499–0.506.

Between d = 2 and 5 the slope is 0.577, steeper than ½. The cause is Jensen's gap
(E[√S] < √E[S]), and this was measured, not assumed: on the same samples √(E D²)
matches √(d/6) even at d=2 (0.577 vs 0.577). Only the mean lags.

At d = 2 the second-order formula is still 1.2% off (0.527 vs 0.521). It is an
expansion in 1/d, so it is weakest exactly there.

## A5 — relative standard deviation

rel.sd falls smoothly, 0.476 → 0.0186, and follows 0.5916/√d to within 0.003 from d = 20 on.

**rel.sd is the better measure of "distance stopped meaning anything".** It uses every
pair. Contrast is decided by two extreme samples.

Across ten seeds at d = 50, n = 1000:

| measure | coefficient of variation |
|---|---|
| contrast | 6.9% |
| rel.sd | 0.7% |

The same comparison at n = 5000 gives 11.4% against 0.7%. That the d=50 "below 1" verdict flips between seeds is exactly what this difference predicts.

## A6 — does contrast depend on n?

Both runs below are at d = 50.

**Point count, with pairs held at 20,000:**

| n | distinct pairs n(n−1)/2 | contrast | rel.sd |
|---|---|---|---|
| 50 | 1,225 | 0.731 | 0.0781 |
| 100 | 4,950 | 0.811 | 0.0812 |
| 200 | 19,900 | 0.937 | 0.0816 |
| 1000 | 499,500 | 0.982 | 0.0830 |
| 5000 | 12,497,500 | 0.877 | 0.0836 |

**Pair count, with n held at 1000:**

| pairs sampled | min | max | contrast |
|---|---|---|---|
| 1,998 | 2.015 | 3.629 | 0.801 |
| 19,977 | 1.909 | 3.785 | 0.982 |
| 199,779 | 1.700 | 3.899 | 1.293 |

Contrast depends on both, but they are different kinds of dependence.

- **n is a property of the data.** With few points there are few distinct pairs:
  1,225 at n=50, each sampled about 16 times. So the extremes come from a smaller
  population, and contrast is lower (0.731). Once n(n−1)/2 is far above the sampled
  pairs, n stops mattering. Ten seeds give mean contrast 0.980 at n=1000 and 1.019
  at n=5000, a difference inside one sd (0.067 / 0.116). The drop to 0.877 at
  n = 5000 in the table is one seed's draw.
- **The pair count is a property of the measurement.** More samples reach further
  into both tails: max rises 3.629 → 3.899 and min falls 2.015 → 1.700, so contrast
  rises monotonically (0.801 → 0.982 → 1.293) at a fixed d and fixed data. This is a
  pure sampling effect, independent of dimension. rel.sd barely moves (0.0816 → 0.0827).

## A7 — machine

| | |
|---|---|
| CPU | Intel i5-1135G7 (4 cores / 8 threads), "Intel64 Family 6 Model 140 Stepping 1" |
| RAM | 7.7 GB |
| OS / Python | Windows 11 (10.0.26200), Python 3.14.8 |
| power | AC connected |
| load | Discord, Notion, Edge, ChatGPT and iCloud running; 286 MB of 7,865 MB RAM free just before the first run |

**Largest run:** d=1000, n=2000 took **4.341 s** of sampling. The whole command
(`--dims 500,1000 --points 2000`) took 7.13 s wall.

Repeating that d=1000 sample three times from a separate script gave 5.178 / 5.096 / 4.966 s:
- spread among those three: 4.3%
- all three 14–19% above the 4.341 s in-script run

The same row d=50, n=1000 took 0.540 s in the first sweep and 0.154 / 0.179 s in later
runs. The cause of that 3.5× gap was not measured, so seconds here are indicative
only. The distance statistics are deterministic and unaffected.

## A8 — does this threaten week 3's LSH on Jaccard?

**No.** Measured on week 3's own documents (`w03-lsh/bench.py build()`: 2,120 sets of
60 shingles from a vocabulary of 5,000).

**The gap.** Among 19,990 sampled background pairs (true pairs excluded), the largest
Jaccard is 0.0526. The 121 true pairs run 0.6216–0.8889. The two ranges do not
overlap, and the true minimum is 11.8× the background maximum. A gap is unchanged
by adding a constant, so it reads the same whether written as similarity or as
distance 1 − J.

**The distribution is bimodal, checked over all 2,246,140 pairs:**

| Jaccard | pairs |
|---|---|
| [0, 0.1) | 2,246,018 |
| [0.1, 0.5) | 0 |
| [0.5, 0.6) | 1 (0.5584) |
| ≥ 0.6 | 121 |

The curse of dimensionality is "every pair becomes about equally far apart". Here a
background mass and a mass of near-duplicates are separated by an empty band.
task2.md's point is exactly this: shingle sets are not uniform points in a cube, and
the near-duplicates are planted structure. The one pair at 0.5584 sits just under the
threshold (most likely a planted clone that changed many shingles). It is the hard
case for the S-curve, but a matter of where to put the threshold, not of the curse.
It is not in `bench.truth()`. Re-running week 3's `YourFinder` with its comparisons
recorded shows it was one of them: 126 comparisons = the 121 true pairs + the 0.5584
pair + 4 background pairs (0.0169–0.0256). The exact Jaccard check rejected all five,
so 121 were reported at 100% recall.

**What LSH needs** is a separation on both sides of the 0.6 threshold, not a small
rel.sd.

rel.sd cannot answer this question at all. It is not invariant to adding a constant.
The same background pairs give:

| written as | mean | sd | rel.sd |
|---|---|---|---|
| similarity J | 0.0061 | 0.0072 | 1.180 |
| distance 1 − J | 0.9939 | 0.0072 | 0.0072 |

The sd is identical and the ratio differs 164×. Comparing either form with the
Euclidean 0.0186 gives opposite verdicts, so it is no evidence either way. An earlier
draft of this answer made exactly that comparison, quoting 0.0085 from a sample that
still contained one planted pair; it is withdrawn.

MinHash also never computes a distance across the 5,000 dimensions. Its band
probability 1 − (1 − s^r)^b depends only on s, so a background at s ≈ 0.006 collides
with probability about 30 · 0.006⁴ ≈ 4·10⁻⁸.

The threat would be real if the "near-duplicates" were themselves only marginally
closer than the background. Then no hash family can separate them, because there is
nothing left to separate.
