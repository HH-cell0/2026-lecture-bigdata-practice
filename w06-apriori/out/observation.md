# Week 6 · Observations

## Task 1

- On bench data the planted pair {241, 258} (support 299 and 387, together in 60 baskets) gives 241→258 = 60/299 = 0.201 but 258→241 = 60/387 = 0.155; 241→258 is the useful claim (the rarer item predicts the other better), while lift is 10.37 both ways because s(ij)·N/(s(i)·s(j)) is symmetric.
- Highest confidence: 1468→0 at 0.839 (52 of 62 baskets), lift 1.28; I do not believe it: item 0 is in 65.4% of baskets (40.5 of 62 expected by chance), 1468 is not in a planted pair (bench plants only ids < 300), it is the top of 12,794 rules, and rules into 0 have median lift 1.001, while the planted pairs run from lift 1.29 to 15.11 at confidence 0.03–0.37, the strongest reaching 15.
- Brute force needs C(2000, 2) = 1,999,000 counters; after pass one 1,849 items survive, so a triangular matrix needs C(1849, 2) = 1,708,476 (only 14.5% fewer) and counting only pairs that co-occur needs 820,259.

## Task 2

- It never became unbearable: support 1 (the floor) finished in 6.32 s with a 546 MB peak working set and at least 521 MB RAM still free, because the rarest item appears 32 times, so at support ≤ 32 every item survives and counters hit the ceiling of 893,456 co-occurring pairs.
- Counters grew ×5.54 / ×4.67 / ×3.00 per halving from 400 to 50, worse than doubling because they follow C(f, 2) and f grows ×2.2–2.4 per halving; then ×1.09 and ×1.00 once f is capped at 2,000.
- Answers grew only ×2.4–3.1 per halving: from 400 to 50 counters grew ×77 but answers ×25.7 (counters per answer 42 → 128), so "a slightly lower threshold" costs memory set by the pairs you might count, not by the answers you get.

## Task 3

- B = 152,003: T ≈ 20,000 × C(20, 2) = 3.8M pair occurrences from bench's constants, and B = 2T/s = 152,000 (average bucket at s/2), rounded up to a prime; this is above the balance point (C2 = 34,248 < B), so peak = B and the cut 1 − B/820,259 = 81.5% is smooth, whereas below it peak = C2 jumps with hash collisions (80k 75.0%, 90k 88.4%); measured T = 3,427,037.
- R5: peak = max(B, C2) = 152,003 because the bucket array is freed before the first pair counter; the bitmap, ⌈B/32⌉ = 4,751 words (3.1% of B), sits next to C2 for all of pass two and is not counted (bits are not counters); with B = 1M pass two drops to 7,125 but pass one holds 1,000,003, −21.9% in counters, yet in bytes it wins (Counter 94.5 MB at 115 B/pair vs 4.0 MB array); PCY wins once co-occurring pairs exceed B: ~30k baskets for B = 1M (1,000,513 vs 1,000,003), 1,200–2,000 for B = 152k; that point does not move with N when support scales with N (T/s stayed 68,483–69,926 from 1.2k to 80k), and depends on pairs per basket, support fraction and item count.
- Shrinking B pushes the average bucket T/B past s: at B = 20,011 (T/B = 171) 93% of buckets are frequent and the cut is 1.9%; at B ≤ 10,007 100% are frequent, the bitmap passes every pair and the cut is 0%; the frequent pairs were identical at every B, because a false positive only costs a counter, never an answer.
