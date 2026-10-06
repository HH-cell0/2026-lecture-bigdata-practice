# Task 2 · The Crossover on My Own Machine

Every number below was measured on the machine described in A6. Tasks 1 and 3 run
on fixed-seed data and are comparable with everybody else's; this one is not, and
is not supposed to be.

---

## A6 · The machine

| | |
|---|---|
| CPU | 11th Gen Intel Core i5-1135G7 @ 2.40GHz — 4 cores, 8 logical processors |
| RAM | 7.7 GB |
| OS | Windows |
| Python | 3.14.8 |
| Also running | A browser with the course LMS open. This turned out to matter — see A4. |

---

## A1 / A2 · Sizes measured, and where it stopped being pleasant

Seven sizes, 125 to 8,000 — a **64x span**, well over the 16x required.

I stopped at **n = 8,000**, where brute force took **217.34 s (3 min 37 s)**. That is
past the "a minute of waiting" mark in A2. What ran out was **time**: at that same
size peak memory was 92 KB for brute force and 71.6 MB for LSH, which is 0.91% of
this machine's 7.7 GB. Memory was never close to being the problem, and A5 has the
arithmetic on how far away it actually was.

---

## A3 · Time against n

| n | comparisons | brute force | LSH | LSH comparisons |
|------:|------------:|------------:|--------:|----------------:|
| 125 | 7,750 | 0.04 s | 0.57 s | 0 |
| 250 | 31,125 | 0.18 s | 0.63 s | 1 |
| 500 | 124,750 | 0.75 s | 0.77 s | 7 |
| 1,000 | 499,500 | 3.20 s | 0.99 s | 27 |
| 2,000 | 1,999,000 | 13.26 s | 1.76 s | 110 |
| 4,000 | 7,998,000 | 56.83 s † | 2.77 s † | 242 |
| 8,000 | 31,996,000 | 217.34 s | 4.18 s | 487 |

† n = 4,000 was measured twice. See A4.

```
            brute force                              LSH
 125  |                                        0.04  |                       0.57
 250  |                                        0.18  |#                      0.63
 500  |#                                       0.75  |#                      0.77
1000  |####                                    3.20  |##                     0.99
2000  |################                       13.26  |#####                  1.76
4000  |##################################################################### 56.83
                                                     |#########              2.77
8000  |  (clipped, 3.8x the bar above)        217.34 |##############         4.18
```

Going from 125 to 8,000 documents multiplies brute-force time by **5,400x** and LSH
time by **7.3x**. That gap is the whole subject.

---

## A4 · Is the brute-force curve quadratic?

Doubling n should roughly quadruple the time. Checked against my own numbers:

| interval | comparisons x | time x | time per comparison |
|---|---:|---:|---:|
| 125 → 250 | 4.016 | **4.50** | 5.78 us |
| 250 → 500 | 4.008 | **4.17** | 6.01 us |
| 500 → 1,000 | 4.004 | **4.27** | 6.41 us |
| 1,000 → 2,000 | 4.002 | **4.14** | 6.63 us |
| 2,000 → 4,000 | 4.001 | **4.29** | 7.11 us |
| 4,000 → 8,000 | 4.001 | **3.82** | 6.79 us |

**It holds**, and every interval lands between 3.82x and 4.50x.

The right-hand column is the reason. The cost of one comparison stays between 5.2
and 7.1 us across a 64x range of n. The time is quadratic not because each
comparison gets more expensive, but because the *number* of them is quadratic —
which the middle column confirms exactly: 4.00x more comparisons every time n
doubles, by construction.

### The measurement I had to redo

My first reading at n = 4,000 was **65.47 s**, which is 8.19 us per comparison — on
its own, 25% above every other row. That single inflated point made the interval
into it look too steep (4.94x) and the interval out of it too shallow (3.32x), so
the quadratic check appeared to fail at exactly one place and in two directions at
once. That pattern is the signature of one bad point, not of the algorithm changing.

I re-ran that size alone:

| n = 4,000 | brute force | LSH |
|---|---:|---:|
| first pass (browser open) | 65.47 s | 2.37 s |
| second pass | **56.83 s** | **2.77 s** |
| change | −13.2% | **+16.9%** |

Brute force got 13% faster, which fits the interference story. But **LSH got 17%
slower in the same run**, which does not. If background load were the whole
explanation both would have moved the same way.

So the honest conclusion is not "the browser did it" but something weaker and more
useful: **this machine has roughly 15% run-to-run variance at this scale.** On a
4-core laptop part the likely causes are turbo clock behaviour and thermal limits,
which depend on how hot the machine already was, not only on what else is running.
A single reading at a single size on this hardware is not trustworthy to better than
about 15%, and I only found that out by measuring the same point twice.

The table above uses the second pass. The first is kept here rather than deleted,
because it is evidence about the measurement rather than a mistake to hide.

### Checking over a wider span

Single-point noise is avoided by spanning further. From n = 2,000 to n = 8,000 is a
**4x** increase, so the quadratic prediction is 16x:

```
    predicted  16.00x
    measured   16.39x        (13.26 s -> 217.34 s)
```

Neither endpoint is the re-measured point, and the 2.4% excess is the extra memory
traffic a larger working set brings. This is the check I would trust.

---

## A5 · Peak memory at the largest n

| n | brute force | LSH | ratio |
|------:|------------:|----------:|------:|
| 125 | 6.4 KB | 1.4 MB | 226x |
| 1,000 | 9.1 KB | 9.5 MB | 1,061x |
| 8,000 | **92.0 KB** | **71.6 MB** | **797x** |

LSH doubles its memory every time n doubles — 1.97x, 1.98x, 1.94x, 1.98x, 1.97x —
so it is cleanly linear, about **9.4 KB per document**: a 120-integer signature plus
the inverted index from shingle to document.

Brute force is the more interesting column. It uses almost nothing, and what little
it uses is **not the algorithm**. The comparison loop only ever holds two documents
at a time, which is O(1) in the corpus. The 92 KB is the *answer* — the set of pairs
it found, which grows only because this harness plants near-duplicates in proportion
to the corpus size.

**So the 797x ratio is real but it is not the point.** In absolute terms LSH used
**0.91% of 7.7 GB**. Extrapolating the linear fit, LSH would need roughly **888,000
documents** to exhaust this machine's RAM — and at 888,000 documents brute force
would need about **31 days**.

That is the honest shape of the trade. For brute force, memory never becomes the
binding constraint, because time becomes impossible thousands of times sooner. For
LSH it is the reverse: time stays cheap and memory is what eventually bites — which
is the situation the rest of this course is about.

---

## A7 · The crossover

| n | brute force | LSH | winner |
|------:|---------:|--------:|---|
| 125 | 0.04 s | 0.57 s | brute force |
| 250 | 0.18 s | 0.63 s | brute force |
| 500 | 0.75 s | 0.77 s | brute force, by 0.02 s |
| 1,000 | 3.20 s | 0.99 s | LSH |

**The crossover is between 500 and 1,000, and n = 500 is nearly a dead heat.**
Fitting the two trends — brute force at 6.59 us per comparison, LSH at
`0.601 s + 0.000470 x n` — and solving for where they meet gives

```
    n ≈ 505
```

which matches the measured near-tie at 500. Given the 15% run-to-run variance found
in A4, I would report this as **a crossover somewhere around 500**, not as a number
with three digits of meaning.

---

## A8 · Why LSH loses at small n

The fitted LSH line answers this directly:

```
    LSH time  =  0.601 s  +  0.000470 x n
                 ^^^^^^^
                 paid before a single pair is compared
```

That **0.601 s intercept is the fixed cost**, and it is specific. Building the
signature matrix walks the whole shingle space — 5,000 rows — and computes 120 hash
values at every row. That is **600,000 hash evaluations**, and it happens whether
there are 125 documents or 8,000. The banding and bucketing that follow are linear
in n and comparatively cheap. The floor is the hashing.

So at n = 125, LSH spends **0.57 s to avoid 7,750 comparisons that would have cost
0.04 s**. It is not slow — it is paying for machinery the problem did not need. The
machinery only starts earning at around n ≈ 500, where the quadratic term finally
overtakes a constant that was there the whole time.

Worth recording what it buys once it does earn out: at n = 8,000 LSH made **487
comparisons instead of 31,996,000** — **99.9985% avoided** — in 4.18 s instead of
217.34 s.

---

## Note on the harness

`task2_crossover.py` originally built its corpus with `bench.build()[:n]`, and
`bench.build()` returns exactly `N_DOCS + PLANTED` = **2,120** documents. Every size
above 2,120 silently measured the same 2,120 documents while recording the n that
was asked for, so the `--sizes 4000,8000,16000` suggested in the task notes would
have produced three identical timings labelled as three different sizes. The
automated check in `test_tasks.py` only reads the recorded n, so that would have
passed while A4 was being tested against data that never actually doubled.

I replaced it with `build_n(n, bench)`, which returns a prefix of `bench.build()`
below 2,120 — so those rows are the same documents Task 3 is scored on — and above
it runs the same generator at the requested size: identical VOCAB and shingle count,
planted pairs held at the same fraction of the corpus, same fixed seed. An assertion
now fails loudly if the corpus is not the size that was asked for.

The comparison counts in A3 are the evidence that it works: 7,998,000 at n = 4,000
and 31,996,000 at n = 8,000 are exactly C(n,2). Under the original code both rows
would have read 2,246,140.
