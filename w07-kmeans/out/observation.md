# Week 7 · Observations

## Task 1

- R3: an empty cluster keeps its previous centroid. This is a constraint, not a free choice, because Task 3 must match the SSE of `NaiveKMeans`, whose `_means` does the same. Random init emptied a cluster on 3 of 40 seeds (22, 23, 37); all three ended on 2 clusters at SSE 96.120. Moving the dead centroid to the furthest point instead recovered the blobs (SSE 0.120) on all three.
- Over 40 seeds, random found the blobs 24 times and k-means++ 40 times. ++ costs (k−1)·n = 18 distances before iterating, against 27 for one assignment pass, and every ++ run converged in 2 passes. I would rather not pay when k is large, since that is k−1 sequential passes over the data.
- SSE vs k was 256.12, 96.12, 0.12, 0.09, …, 0.00 for k = 1…9. It reaches 0 at k = n, so minimising SSE always picks one cluster per point. The signal is the elbow: −160 and −96 up to k = 3, then −0.03.

## Task 2

- At n = 1000 and 20,000 pairs, contrast drops below 1 at d ≈ 50 (0.982) and below 0.5 between d = 100 and 200. At d = 50 only 6 of 10 seeds fall below 1 (0.856–1.068), while rel.sd varies 0.7% and follows the derived 0.5916/√d.
- At d = 50, contrast rose with n (0.731 at n = 50) until n(n−1)/2 far exceeded the sampled pairs, then stopped (seed means 0.980 at n = 1000, 1.019 at n = 5000). At fixed data it rose 0.801 → 0.982 → 1.293 with 2k/20k/200k pairs. n is a data property; the pair count is a measurement artefact.
- No threat to week 3's LSH, which needs separation around the 0.6 threshold, not every pair being alike. Over all 2,246,140 pairs the distribution is bimodal: 2,246,018 pairs below 0.1, none in [0.1, 0.5), and 121 true pairs at 0.6216–0.8889, 11.8× the sampled background maximum of 0.0526.

## Task 3

- Elkan stores 13 numbers per point (one upper bound, k = 12 lower bounds), plus 66 centroid–centroid and 12 movement distances per iteration (3,276 calls in total). R5: switching bounds off one at a time, the lower bounds do the work. Without them calls go 330,077 → 1,748,780; without the cc/2 pair test only to 357,413; without the s point test they do not change at all, since u ≤ s[a] ≤ cc[a][j]/2. Keeping them costs 240,000 floats, each decremented every iteration.
- The SSE difference is exactly 0.0: labels matched the baseline in all 43 iterations, and the same `_means` on the same labels gives bit-identical centroids. A skip happens only when the triangle inequality proves the nearest centroid cannot change, so nothing is approximated.
- Measuring all of iteration 1 was 240,000 of 398,366 calls (60.2%). task3.md says it cannot be pruned, but measuring the 66 initial centroid–centroid distances first skips 68,349 pairs via d(c_a, c_j) ≥ 2·d(x, c_a). That brings it to 171,717 of 330,077 (52.0%), the submitted 96.8% cut.
