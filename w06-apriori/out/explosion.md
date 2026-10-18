# Task 2 · Explosion

All runs on this laptop: `task2_explosion.py` (PlainApriori, tracemalloc on),
bench data 2,000 items x 20,000 baskets.

## A3 · Counters and answers against support

| support | frequent items | C(f,2) | peak counters | frequent pairs | seconds (tracemalloc on) | traced MB |
|---|---|---|---|---|---|---|
| 400 | 146   | 10,585    | 10,585  | 249     | 0.73 | 1.1 |
| 200 | 345   | 59,340    | 58,626  | 776     | 1.25 | 6.7 |
| 100 | 825   | 339,900   | 273,701 | 2,244   | 4.13 | 28.6 |
| 50  | 1,849 | 1,708,476 | 820,259 | 6,397   | 7.01 | 107.7 |
| 25  | 2,000 | 1,999,000 | 893,456 | 17,045  | 8.69 | 107.7 |
| 12  | 2,000 | 1,999,000 | 893,456 | 43,116  | 5.96 | 110.0 |
| 6   | 2,000 | 1,999,000 | 893,456 | 101,938 | 4.58 | 126.5 |
| 3   | 2,000 | 1,999,000 | 893,456 | 250,054 | 5.05 | 163.9 |
| 1   | 2,000 | 1,999,000 | 893,456 | 893,456 | 6.32 | 334.3 |

(frequent items and C(f,2) from a separate count over the same baskets.)

## A2 · Where it became unbearable: it did not

Support 3 finished in 5.05 s; the worker's peak working set was 327 MB and
system free RAM never fell below 692 MB (sampled every 0.5 s). Support 1, the
floor, took 6.32 s with a 546 MB peak working set and 521 MB minimum free.
Nothing ran out.
The reason is the data, not the laptop: the least common item appears 32 times,
so at support <= 32 every item survives pass one, and PlainApriori counts every
pair that ever co-occurs: 893,456 of the 1,999,000 possible. That is the ceiling;
no lower support can need more counters, so halving further cannot break it.

## A4 · Counter growth per halving

400->200 x5.54, 200->100 x4.67, 100->50 x3.00, 50->25 x1.09, then x1.00.
Worse than doubling while pass one still removes items (x3.0-5.5 per halving),
because the counters track C(f,2) and f itself grows x2.2-2.4 per halving
(146 -> 345 -> 825 -> 1,849), so C(f,2) grows x5.0-5.7. The fill rate
counters / C(f,2) is 100.0% / 98.8% / 80.5% / 48.0% / 44.7% at support
400 / 200 / 100 / 50 / <=25 (at 400 exactly: C(146,2) = 10,585 = counters).
As f grows, a smaller share of possible pairs ever shares a basket, and that
falling fill rate is why the counter growth bends from x5.5 to x3.0 while
C(f,2) keeps growing x5. Below support 32 it is flat: f is capped at 2,000.

## A5 · Answers grow differently

Frequent pairs grow x2.4-3.1 per halving from 400 to 3 (249 -> 250,054, x1,004),
then x3.6 from 3 to 1 (250,054 -> 893,456). Counters grew x77 from 400 to 50 while answers grew x25.7:
counters per answer went 42 -> 76 -> 122 -> 128. That gap is the whole problem:
the memory you pay for is decided by how many pairs you might have to count,
not by how many answers there are. Here the gap closes below 25 (3.6 counters
per answer at support 3, exactly 1 at support 1, where every co-occurring pair is
an answer: 893,456 = 893,456) only because the counters hit the co-occurrence
ceiling of this small dataset. So the curve runs from 42 counters per answer at
support 400 to 1 at support 1. On real data with more items and baskets that
ceiling is far higher.

## Timing and tracemalloc

Without tracemalloc (same PlainApriori, same baskets, two runs each): support 50
took 1.49 / 1.37 s and support 3 took 1.62 / 1.79 s. With tracemalloc on, 7.01 s
and 5.05 s: tracemalloc inflates the time ~3-5x, so the seconds column is not the
algorithm's cost. With tracemalloc on, times also do not follow the counters
(8.69 s at 25, 4.58 s at 6, same 893,456 counters); I did not find out why.

## A6 · Machine

- CPU: 11th Gen Intel Core i5-1135G7 @ 2.40 GHz, 4 cores / 8 threads
- RAM: 7.7 GB total, 0.75 GB free before the runs (Memory Compression 929 MB)
- Windows 11 Home 10.0.26200, Python 3.14.8; on AC power, battery 63%
- Also running: Claude Code (3 processes, ~940 MB), Microsoft Edge, Defender
  (MsMpEng), Explorer, ChatGPT desktop, Discord
