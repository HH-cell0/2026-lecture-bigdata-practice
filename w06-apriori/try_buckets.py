#!/usr/bin/env python3
"""What the bucket count does to PCY, and where PCY starts winning.

task3.md asks what happens when the bucket array is made much smaller, and at
what data size PCY beats plain A-Priori. task3_pcy.py keeps its one bucket
count (152,003); the sweeps live here and only pass `buckets=` to it.

    python try_buckets.py              # E1: bucket sweep on bench data
    python try_buckets.py --hash       # E2: arithmetic vs tuple hash
    python try_buckets.py --scale      # E3: grow the data, find the crossover
    python try_buckets.py --bytes      # E4: the same peaks in bytes

Peak counters are deterministic (fixed seed), so they are measured once; only
the times would vary between runs.
"""
import argparse, random, time, tracemalloc
from collections import Counter
from itertools import combinations
import bench
from task3_pcy import PlainApriori, YourAlgorithm

S = bench.SUPPORT


class TupleHash(YourAlgorithm):
    # Same algorithm, Python's tuple hash instead of a*2000 + b.
    def bucket_of(self, a, b):
        return hash((a, b)) % self.n_buckets


class ShuffledIds(YourAlgorithm):
    # Arithmetic hash on randomly relabelled ids. If the arithmetic hash only
    # wins because popular items have small ids, this loses that advantage.
    PERM = list(range(bench.ITEMS))
    random.Random(1).shuffle(PERM)

    def bucket_of(self, a, b):
        x, y = sorted((self.PERM[a], self.PERM[b]))
        return (x * self.ITEMS + y) % self.n_buckets


def pair_occurrences(baskets):
    # T: how many pairs pass one hashes, the numerator of the average bucket
    # load T/B.
    return sum(len(b) * (len(b) - 1) // 2 for b in baskets)


def baseline(baskets, s):
    algo = PlainApriori(s)
    return algo.run(baskets), algo.peak_counters


def pcy(cls, baskets, s, B):
    algo = cls(s, B)
    t0 = time.perf_counter()
    pairs = algo.run(baskets)
    return pairs, algo, time.perf_counter() - t0


def sweep():
    baskets = bench.build()
    ref, base = baseline(baskets, S)
    T = pair_occurrences(baskets)
    print(f"\n  T = {T:,} pair occurrences, T/s = {T / S:,.0f}, "
          f"baseline peak {base:,}\n")
    print(f"  {'B':>9} {'T/B':>6} {'freq buckets':>14} {'C2':>9} {'peak':>9}"
          f" {'cut':>7} {'bitmap words':>13}  R3    time")
    for B in (1_000_003, 500_009, 250_007, 200_003, 152_003, 120_011, 100_003,
              95_003, 90_001, 80_021, 70_001, 50_021, 20_011, 10_007, 1_009):
        pairs, a, t = pcy(YourAlgorithm, baskets, S, B)
        print(f"  {B:>9,} {T / B:>6.1f} {a.frequent_buckets:>7,} "
              f"({a.frequent_buckets / B:>4.0%}) {a.pass2_counters:>9,} "
              f"{a.peak_counters:>9,} {1 - a.peak_counters / base:>7.1%} "
              f"{a.bitmap_words:>13,}  {'ok' if pairs == ref else 'FAIL'}"
              f"  {t:5.2f}s")


def hashes():
    baskets = bench.build()
    ref, base = baseline(baskets, S)
    print(f"\n  C2 and cut by hash, baseline peak {base:,}\n")
    print(f"  {'B':>9}  {'arith C2':>9} {'cut':>6}  {'tuple C2':>9} {'cut':>6}"
          f"  {'shuffled C2':>11} {'cut':>6}")
    for B in (70_001, 100_003, 120_011, 152_003, 200_003, 250_007):
        row = []
        for cls in (YourAlgorithm, TupleHash, ShuffledIds):
            pairs, a, _ = pcy(cls, baskets, S, B)
            assert pairs == ref, (cls.__name__, B)
            row.append((a.pass2_counters, 1 - a.peak_counters / base))
        print(f"  {B:>9,}" + "".join(f"  {c:>9,} {x:>6.1%}" if i < 2 else
                                     f"  {c:>11,} {x:>6.1%}"
                                     for i, (c, x) in enumerate(row)))


def scale():
    # Support grows with N at the bench's fraction 50/20,000 = 1/400, so each
    # N is a multiple of 400 and s stays an integer.
    print("\n  support = N/400 (same fraction as bench)\n")
    print(f"  {'N':>7} {'s':>4} {'T':>11} {'T/s':>8} {'baseline':>10}"
          f" {'PCY 152k':>9} {'C2':>7} {'PCY 1M':>10} {'C2':>7}")
    for n in (1_200, 2_000, 4_000, 10_000, 20_000, 30_000, 40_000, 80_000):
        _scale_row(n, n // 400)
    print("\n  support fixed at 50\n")
    for n in (10_000, 20_000, 40_000, 80_000):
        _scale_row(n, 50)


def _scale_row(n, s):
    bench.BASKETS = n  # build() reads this global; restored nowhere because
    baskets = bench.build()  # every row sets it
    T = pair_occurrences(baskets)
    ref, base = baseline(baskets, s)
    cells = []
    for B in (152_003, 1_000_003):
        pairs, a, _ = pcy(YourAlgorithm, baskets, s, B)
        assert pairs == ref, (n, s, B)
        win = "<" if a.peak_counters < base else " "
        cells.append(f" {a.peak_counters:>8,}{win} {a.pass2_counters:>6,}")
    print(f"  {n:>7,} {s:>4} {T:>11,} {T / s:>8,.0f} {base:>10,}" + "".join(cells))


def bytes_():
    # The counter unit treats a bucket and a pair counter as equal. In memory
    # a bucket is a 4-byte int in an array; a pair counter is a dict entry
    # with a tuple key. Measure both with tracemalloc.
    baskets = bench.build()
    frequent = {i for i, c in Counter(x for b in baskets for x in b).items()
                if c >= S}
    tracemalloc.start()
    pc = Counter()
    for b in baskets:
        for p in combinations(sorted(b & frequent), 2):
            pc[p] += 1
    base_bytes = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    print(f"\n  baseline pair counters {len(pc):,}: {base_bytes / 1e6:6.1f} MB"
          f"  ({base_bytes / len(pc):.0f} B each)")
    print(f"  textbook triples, 12 B each:     {len(pc) * 12 / 1e6:6.1f} MB")
    for B in (152_003, 1_000_003):
        from array import array
        tracemalloc.start()
        arr = array('i', [0]) * B
        got = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        del arr
        print(f"  bucket array B={B:>9,}:      {got / 1e6:6.1f} MB")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hash", action="store_true")
    p.add_argument("--scale", action="store_true")
    p.add_argument("--bytes", action="store_true")
    a = p.parse_args()
    if a.hash:
        hashes()
    elif a.scale:
        scale()
    elif a.bytes:
        bytes_()
    else:
        sweep()
    print()


if __name__ == "__main__":
    main()
