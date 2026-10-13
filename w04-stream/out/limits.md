# Task 2 · Where Exact Stops Being Possible, on My Own Machine

Every number below is from `out/limits.json`, measured on the machine in A6,
except the tracemalloc-free timings in A2, which were measured separately.
Stream and hash seeds are fixed, so `true_distinct`, the FM estimate and its
ratio are deterministic; only time and memory move between runs.

**Run-to-run deviation** (n = 100,000 measured twice with the same harness):
exact 0.208 → 0.211 s (+1.5%), FM 30.97 → 33.38 s (+7.8%); memory exact
3,925,492 B both times (0.0%), FM 12,922 → 12,818 B (−0.8%). Time moves by up
to ~8%, memory essentially not at all.

---

## A6 · The machine

| | |
|---|---|
| CPU | Intel Core i5-1135G7 — 4 cores, 8 logical processors |
| RAM | 7.7 GB |
| OS | Windows 11 (10.0.26200) |
| Python | 3.14.8 |
| Also running | A Claude Code session. Browser closed. |

---

## A1 / A3 · Sizes and memory

Seven sizes, 100,000 to 6,400,000 — a **64x span**. Four are 4x apart (the
suggested sizes); three more were chosen so that log2 of the distinct count
lands at a different fraction (see A5). Memory is tracemalloc peak.

| n | distinct D | exact time | exact peak | bytes / D | FM time | FM peak | FM ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 36,702 | 0.21 s | 3.93 MB | 107.0 | 31.0 s | 12,922 B | 0.89x |
| 250,000 | 91,750 | 0.55 s | 10.22 MB | 111.4 | 76.1 s | 12,922 B | 1.43x |
| 400,000 | 146,970 | 0.79 s | 11.59 MB | 78.9 | 123.0 s | 12,199 B | 0.89x |
| 700,000 | 256,968 | 1.40 s | 21.40 MB | 83.3 | 211.7 s | 12,195 B | 1.02x |
| 1,600,000 | 587,625 | 3.23 s | 46.65 MB | 79.4 | 495.4 s | 12,107 B | 1.78x |
| 3,000,000 | 1,101,142 | 6.21 s | 89.80 MB | 81.5 | 917.0 s | 12,108 B | 0.95x |
| 6,400,000 | 2,349,909 | 13.43 s | 188.29 MB | 80.1 | 2,123.5 s | 12,064 B | 0.89x |

---

## A2 · Where it stopped, and what ran out

I stopped at **n = 6,400,000**, and it was not the exact set that made me stop.

- **Exact never became unpleasant.** At 6.4M it took **13.43 s** and peaked at
  **188.3 MB**, about 2.3% of 7.7 GB.
- **Flajolet-Martin did.** The same size took **2,123.5 s (35 min)**, 158x the
  exact set. FM costs 302–332 µs per stream item at every size (64 hash
  evaluations in pure Python, per item, repeats included); the set costs
  2.0–2.2 µs.
- **25,000,000 was not run.** Both costs are linear in n, so scaling the 6.4M
  row by 25/6.4: exact ≈ 52 s and ≈ 736 MB (still under 10% of RAM), FM ≈
  8,300 s ≈ **2.3 hours**.

**But the 158x is largely the measuring harness, not FM.** `task2_limits.py`
times both methods with tracemalloc running, and tracemalloc traces every
allocation; FM allocates 64 integers per item. Timing n = 100,000 again
without tracemalloc, twice:

| n = 100,000 | with tracemalloc | without | slowdown from tracing |
|---|---:|---:|---:|
| exact | 0.208 s | 0.062 / 0.057 s | 3.3–3.6x |
| FM | 30.97 s | 2.50 / 2.43 s | 12.4–12.7x |
| FM / exact | **149x** | **40x / 43x** | |

Tracing slows FM about 3.5 times more than it slows the set, because FM
allocates far more per item. So: **under tracemalloc FM was 149–158x slower
than exact; without it, 40–43x** (measured at 100,000 only). The ratio depends
on the measurement method, and the 158x in the table above is not a property
of FM.

Without tracemalloc FM costs 24–25 µs per item. Assuming that stays linear in n,
as the traced per-item cost did (302–332 µs at every size), 6.4M would take
about 160 s and 25M about 10 minutes — slow, but not the 2.3 hours above. I did
not measure either size untraced.

So what ran out was **time under the measuring harness, on the sketch side**.
Memory never came close to binding for the exact answer (2.3% of RAM at 6.4M,
an estimated ~736 MB at 25M). Untraced, neither method became unbearable within
the sizes I ran; FM is still 40x slower than a set per item, which is the price
of its constant memory.

**Where the memory wall would be — extrapolated, not measured.** The A4 fit
(memory = 1.05 MB + 79.7 B × D, all eight rows) reaches 7.7 GiB
(8.27 × 10^9 B) at D ≈ 103.7 million distinct items. With this stream's
D ≈ 0.3672 n (span 0.4n, so D = 0.4n(1 − e^(−2.5))), that is n ≈ 282 million.
This is an **upper bound**: the OS and other processes hold part of the 7.7 GiB,
so swapping would start at a smaller n. Untraced and linear in n, exact would
reach that size in about 2.7–2.9 min (0.57–0.62 µs per item) and FM in about
1.9–2.0 h (24.3–25.0 µs per item), FM still at about 12.9 KB. So **what stops
the exact set is memory**: it hits the wall after about three minutes. **What
stops FM is time**: at the same size its memory is unchanged and it needs about
two hours.

---

## A4 · Two growth rates

**Exact set: about 80 bytes per distinct item, linear in D.** A least-squares
line through all seven points gives **79.7 bytes per distinct item** plus
about **1.07 MB** fixed. The fixed part is why the two smallest sizes show
107–111 bytes/D; from D ≈ 147,000 up, bytes/D stays between 78.9 and 83.3. From
the smallest to the largest size D grew 64.0x and memory 48.0x, the gap again
being the fixed 1 MB.

**FM: zero per item.** Peak memory stayed between **12,064 and 12,922 bytes** at
every size and did not rise with D (it is slightly *lower* at the largest
sizes). Its state is 64 maxima and 128 hash coefficients, fixed by the number of
hashes, not by the data.

At 6.4M the exact set used **15,607x** the memory of FM (188,287,390 B /
12,064 B).

---

## A5 · Accuracy at each size

FM's median can only answer a power of two. So with D measured and
f = frac(log2 D), the only two values the ratio can take near the truth are
2^(−f) (the power of two just below D) and 2^(1−f) (just above).

| n | D | f | 2^(−f) | 2^(1−f) | measured | estimate |
|---:|---:|---:|---:|---:|---:|---|
| 3,000,000 | 1,101,142 | 0.071 | **0.952** | 1.905 | 0.952x | 2^20, below |
| 100,000 | 36,702 | 0.164 | **0.893** | 1.786 | 0.893x | 2^15, below |
| 6,400,000 | 2,349,909 | 0.164 | **0.892** | 1.785 | 0.892x | 2^21, below |
| 400,000 | 146,970 | 0.165 | **0.892** | 1.784 | 0.892x | 2^17, below |
| 1,600,000 | 587,625 | 0.165 | 0.892 | **1.784** | 1.784x | 2^20, above |
| 250,000 | 91,750 | 0.485 | 0.714 | **1.429** | 1.429x | 2^17, above |
| 700,000 | 256,968 | 0.971 | 0.510 | **1.020** | 1.020x | 2^18, above |

All seven estimates are one of the two powers of two next to D — four below,
three above — and nothing in between.

**Does it get better or worse as n grows? Neither.** There is no trend in n.
The clearest pair: **587,625 distinct gave 1.78x, and 2,349,909 — four times as
many — gave 0.89x.** Same f (0.165 vs 0.164), so the same two candidates; the
draw of hashes picked the upper one at the smaller size and the lower one at
the larger.

So the accuracy is decided in two steps. **Where D sits between two powers of
two (f) sets the two possible answers**; which of the two comes out depends on
the hashes, and f alone does not predict it — the four sizes at f ≈ 0.164 gave
three 0.89x and one 1.78x. Sizes spaced 4x apart all share one f, which is why
a 4x series can look like constant accuracy when it is really the same two
candidates every time. At f = 0.971 the lower candidate would have been 0.510x,
a hair inside the factor of two.
