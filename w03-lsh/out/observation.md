# Week 3 · Observations

## Task 1

- One pass over the rows, not one per column, because only that version survives a matrix too large to hold: a row is hashed, used, and dropped.
- R5: leftover rows go one at a time to the leading bands, so none are wasted and no two bands differ in width by more than one.
- Two hashes can only return 0, 0.5 or 1.0, so 2/3 is unreachable and 1.0 had probability 0.44; more hashes narrow it (error sqrt(p(1-p)/n), 0.33 down to 0.043 at n=120) and cost the 0.6 s and 9.4 KB per document I measured in Task 2.

## Task 2

- Crossover at n ≈ 500 on an i5-1135G7 with 7.7 GB: 0.75 s against 0.77 s at n=500, 3.20 s against 0.99 s at n=1,000, because LSH pays 0.6 s hashing 5,000 rows 120 times before it compares anything.
- The quadratic held, 3.82x to 4.50x per doubling with the cost per comparison staying near 6 µs; n=4,000 first read 25% high, and re-running it showed about 15% run-to-run variance rather than background load, since LSH moved the other way in the same run.
- Unpleasant at n=8,000 (217 s), and time ran out rather than memory: peak was 92 KB for brute force against 71.6 MB for LSH, under 1% of RAM.

## Task 3

- n=120, b=30, r=4 puts the step at (1/30)^(1/4) = 0.427, deliberately below the 0.6 threshold, since the hardest planted pair sits at 0.6216 and a step at the threshold would coin-flip on it; 126 comparisons at 100% recall.
- Moving the step up: b=20 (step 0.607) loses three real pairs to save eight comparisons out of 2.2 million, and b=6 (step 0.914) gets to 10 comparisons at 8.3% recall, so the number the harness scores keeps improving while the answer collapses.
- Not charging for hashing is fair while comparison is quadratic and hashing linear; it stops being fair below the crossover, where the free 0.6 s already exceeded the whole brute-force run, and at any scale where the signatures no longer fit in memory.
