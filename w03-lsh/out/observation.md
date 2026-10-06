# Week 3 · Observations

## Task 1 · Minhash and LSH from the matrix up

I walk the rows once instead of once per column because the one-pass version is the
only one that survives a matrix too large to hold: a row can be hashed, used to
update every column that has a 1 in it, and then thrown away, which is what lets the
data arrive as a stream. Re-scanning per column gives the same signatures but
assumes the whole matrix is still there to be re-read, and not fitting in memory is
the subject of this course.

**R5 decision:** when the signature length does not divide by the band count I spread
the remainder one row at a time across the leading bands, so every row lands in
exactly one band and no two bands differ in width by more than one. Dropping the
leftover rows throws away hashing that was already paid for; giving them all to one
band makes that band wider, and a band of r rows has its own step at (1/b)^(1/r), so
one fat band splits the S-curve into two curves that sit far apart.

The estimate for S1–S4 came out at 1.0 when the truth is 2/3 because each hash is one
Bernoulli trial whose success probability is the real similarity, so with two hashes
the estimate can only ever be 0, 0.5 or 1.0 — **2/3 is not a value two hashes can
produce**, and 1.0 had probability (2/3)² = 0.44. The fix is more hashes: the error
is sqrt(p(1-p)/n), so 120 hashes brings it from 0.33 to 0.043. The cost is exactly
what I measured in Task 2 — 5,000 rows × 120 hashes = 600,000 evaluations, which is
the 0.6 s fixed cost in A8, and 9.4 KB per document, which is the signature in A5.
It also buys less and less: halving the error again needs four times the hashes.

## Task 2 · The crossover on my own machine

On this machine — Intel i5-1135G7, 4 cores, 7.7 GB RAM — **the crossover is around
n ≈ 500**: brute force wins up to 500 (0.75 s against 0.77 s, nearly a tie) and loses
from 1,000 on (3.20 s against 0.99 s). LSH loses below that because it pays a fixed
0.6 s before comparing anything: the signature pass walks all 5,000 shingle rows and
computes 120 hashes at each one whether there are 125 documents or 8,000.

**The quadratic check held**, and the per-comparison column is the reason — the cost
of one comparison stayed between 5.2 and 7.1 µs across a 64× range of n, so the time
is quadratic because the *count* is, not because each comparison got dearer. One
point did not fit: n = 4,000 first read 25% high, so I measured it again and got
56.83 s instead of 65.47 s. But LSH moved the *opposite* way in that same re-run
(2.37 s → 2.77 s), so the explanation is not background load but roughly **15%
run-to-run variance** on this laptop. Spanning wider avoids it: n = 2,000 → 8,000 is
4×, predicting 16.00× and measuring 16.39×.

It became unpleasant at **n = 8,000, where brute force took 217 s**, and what ran out
was **time, not memory** — by a wide margin. At that size peak memory was 92 KB for
brute force and 71.6 MB for LSH, 0.91% of 7.7 GB. Extrapolating, LSH would need about
888,000 documents to exhaust this RAM, and brute force on 888,000 documents would run
for roughly 31 days. Brute force never meets a memory wall because the time wall
arrives thousands of times sooner.

## Task 3 · Finding the same pairs with far fewer comparisons

**n = 120 hashes, b = 30 bands, r = 4.** The step of 1 - (1 - s^r)^b sits near
(1/b)^(1/r) = (1/30)^(1/4) = **0.427**, deliberately *below* the 0.6 threshold. The
step is where the curve crosses one half, so putting it at the threshold would mean
coin-flipping on pairs that sit exactly there, and the hardest planted pair in this
harness is at s = 0.6216. At 0.427 that pair becomes a candidate with probability
0.992, while an average random pair (s ≈ 0.006) does so with probability 3.9e-08 —
0.087 expected false candidates across all 2,246,140 pairs. Result: **126 comparisons,
100% recall, 100% precision, 99.99% avoided.**

I moved the step the wrong way to see it. Holding n = 120 and lowering b: at b = 20
the step rises to 0.607 and recall falls to 97.5% — **three real pairs given up to
save eight comparisons out of 2.2 million**, which is not a close trade. At b = 15
recall is 71.1%, and at b = 6 it is 8.3% while the comparison count drops to 10, a
99.9996% saving that finds one true pair in twelve. The comparison count — the number
the harness scores — keeps improving the whole way down while the answer rots, which
is why recall is the first number to read.

The harness not charging for hashing is fair while comparison is the expensive part,
and here it is: hashing is linear in n, comparison is quadratic. It stops being fair
once the linear term dominates in practice — below the crossover at n ≈ 500 the
uncharged 0.6 s was already larger than the entire brute-force run, and it would also
stop being fair at any scale where the signatures no longer fit in memory, since the
9.4 KB per document I measured would then be paid in disk traffic rather than free.
