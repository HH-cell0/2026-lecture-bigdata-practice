# Week 4 · Observations

## Task 1

- `add` only ever sets bits and nothing clears them, so an inserted item's k bits are still 1 whenever it is queried.
- Predicted 0.860% ((1 − e^(−5·800/8192))^5), measured 0.755% (151 of 20,000); the gap is 1.6σ with σ = 0.065%p at 20,000 queries, so sampling noise, not a wrong formula.
- Median of 2^R: 20/20 seeds inside 2x and 80/80 in the 40k–2.56M range test, but every estimate is a power of two, so the ratio is fixed at 2^(−f) or 2^(1−f) (f = frac(log2 D)); groups of 8 passed 8/20 seeds, groups of 2 was outside 2x in 5/80 range trials, mean of 2^R passed 3/20 with a worst of 33.6x.
- `j = rng.randrange(n)` then `if j < k` (task1_sketches.py:206–207), where n is the count so far from `enumerate`, keeps each new item with probability k/n for the current n, so the final length is never needed.

## Task 2

- Up to 6.4M neither method became unbearable untraced (exact 13.43 s, 188.3 MB); extrapolated, exact's memory wall is n ≈ 282M (upper bound, 7.7 GiB), reached in about 3 min, so exact stops on memory, while FM at that size needs about 2 h, so FM stops on time.
- Exact: 1.05 MB + 79.7 B × D, linear but not proportional (D ×64, memory ×48); FM: 12.1–12.9 KB at every size, flat.
- Enough for "did today's visitors run in the thousands or the millions?", since 2x cannot cross a factor of 1,000; not enough for "did visitors rise today versus yesterday?", since D = 587,625 read 1.78x and D = 2,349,909 read 0.89x, so a 2x swing is within the estimator's error.

## Task 3

- k from 1 to 7: k* = (m/n)·ln 2 = 10 × 0.693 = 6.93, and k = 6/7/8 give 0.844/0.819/0.846%.
- Floor (1/2)^6.93 = 0.819%; measured 1,622/200,000 = 0.811%, −0.42σ (σ = 0.020%p).
- Unknown n: a scalable Bloom filter, starting a new, larger filter whenever the current one reaches its design n; guessing low raises FP (16,000 items in this k=7 filter → 13.8%, worse than the 9.5% baseline), guessing high wastes bits (4,000 items → 0.020%, where 40,000 bits would have met 0.82%).
