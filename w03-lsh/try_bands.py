#!/usr/bin/env python3
"""Move the S-curve step the wrong way and watch recall fall.

task3.md asks what happens to recall when the step moves in the wrong
direction, and tells you to try it. This runs the same finder at several band
counts without touching task3_scale.py, so the submitted file keeps the one
configuration I argued for.

    python try_bands.py

n stays at 120 and only b changes, so r = 120/b and the step (1/b)^(1/r) moves
up as b falls. The threshold is 0.6 and the hardest planted pair in this
harness sits at s = 0.6216, so the theory column is that pair's chance of
being looked at at all.
"""
import bench
from task3_scale import YourFinder

docs = bench.build()
true_pairs = bench.truth(docs)
HARDEST = 0.6216  # the lowest-similarity planted pair in this corpus

print(f"\n  {len(docs):,} documents, threshold {bench.THRESHOLD}, "
      f"{len(true_pairs)} truly similar pairs")
print(f"  baseline is {len(docs) * (len(docs) - 1) // 2:,} comparisons\n")
print("    b    r    step    comparisons    recall    missed    P(hardest pair)")
print("  " + "-" * 68)

for b in (30, 20, 15, 12, 10, 8, 6):
    r = 120 // b

    class Variant(YourFinder):
        N_HASHES = 120
        BANDS = b

    counter = bench.Counter()
    found = {(min(p), max(p)) for p in Variant(bench.THRESHOLD).find(docs, counter)}
    hit = len(found & true_pairs)

    step = (1 / b) ** (1 / r)
    theory = 1 - (1 - HARDEST ** r) ** b
    flag = "   <- below the 90% floor" if hit / len(true_pairs) < 0.90 else ""
    print(f"  {b:>5} {r:>4}   {step:.3f}   {counter.calls:>12,}   "
          f"{hit / len(true_pairs):>6.1%}   {len(true_pairs) - hit:>6}   "
          f"{theory:>12.3f}{flag}")

print("""
  Read the comparisons column and the recall column together. The score the
  harness charges keeps improving all the way down, while the answer rots.
  That is the failure mode R3 exists to catch, and it is silent.
""")
