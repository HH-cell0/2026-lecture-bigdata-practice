#!/usr/bin/env python3
"""Three ways to combine Flajolet-Martin's hashes, on the same maxima.

task1.md asks which combining rule you used and what the others gave you. This
runs every rule on the *same* 64 maxima per trial, so the rules differ only in
how they combine, never in what they saw. task1_sketches.py keeps its one
rule and its one command (--verify); the comparison lives here.

    python try_combining.py            # verify()'s stream, every rule
    python try_combining.py --range    # 40k .. 2.56M distinct, two rules

Only the hash seed changes between trials, because the question is how much
the answer depends on which 64 hash functions you happened to draw.
"""
import argparse, os, random, statistics
from multiprocessing import Pool
from task1_sketches import fm_maxima, combine_mean, combine_median, combine_groups

SEEDS = range(240, 260)  # 20 hash seeds; includes 246, the one verify uses

RULES = {
    "mean of 2^R": combine_mean,
    "median of 2^R": combine_median,
    "groups of 2": lambda R: combine_groups(R, 2),
    "groups of 4": lambda R: combine_groups(R, 4),
    "groups of 8": lambda R: combine_groups(R, 8),
    "groups of 16": lambda R: combine_groups(R, 16),
}


def rule_table():
    # Same construction and seed as verify(), so seed 246 reproduces its 1.95x.
    rng = random.Random(246)
    stream = [f"k{rng.randrange(20_000)}" for _ in range(120_000)]
    true = len(set(stream))
    ratios = {name: [] for name in RULES}
    for seed in SEEDS:
        # One pass per seed; every rule then reads the same R.
        R = fm_maxima(stream, 64, seed)
        for name, rule in RULES.items():
            ratios[name].append(rule(R) / true)

    print(f"\n  true distinct {true:,}, {len(SEEDS)} hash seeds, 64 hashes each\n")
    print(f"  {'rule':<16}{'min':>7}{'median':>8}{'max':>7}   inside 2x")
    print("  " + "-" * 50)
    for name, rs in ratios.items():
        inside = sum(0.5 <= r <= 2.0 for r in rs)
        print(f"  {name:<16}{min(rs):>7.2f}{statistics.median(rs):>8.2f}"
              f"{max(rs):>7.2f}   {inside:>2}/{len(rs)}")


def _one_trial(job):
    # Feed each distinct key exactly once. R is a maximum, and a maximum does
    # not change when an item repeats, so this gives the same R as any stream
    # with these D distinct keys - at a fraction of the items to hash. The
    # key names match task2_limits.py's "key-{i}".
    d, seed = job
    R = fm_maxima((f"key-{i}" for i in range(d)), 64, seed)
    return d, combine_median(R) / d, combine_groups(R, 2) / d


def range_table():
    sizes = [40_000, 160_000, 640_000, 2_560_000]
    jobs = [(d, s) for d in sizes for s in SEEDS]
    # 80 independent trials, ~68M keys in total; at ~33us a key that is over
    # half an hour on one core, so spread it over the laptop's 4 cores.
    with Pool(os.cpu_count() // 2 or 1) as pool:
        results = pool.map(_one_trial, jobs, chunksize=1)

    print(f"\n  {len(SEEDS)} hash seeds per size, 64 hashes each\n")
    print(f"  {'distinct':>10}  {'rule':<14}{'min':>6}{'median':>8}{'max':>6}"
          f"{'worst':>7}   outside 2x")
    print("  " + "-" * 66)
    for d in sizes:
        for col, name in [(1, "median of 2^R"), (2, "groups of 2")]:
            rs = [r[col] for r in results if r[0] == d]
            # "worst" is the factor the estimate is off by, in whichever
            # direction: 0.5x and 2x are equally bad, so compare max(r, 1/r).
            worst = max(max(r, 1 / r) for r in rs)
            outside = sum(not 0.5 <= r <= 2.0 for r in rs)
            print(f"  {d:>10,}  {name:<14}{min(rs):>6.2f}"
                  f"{statistics.median(rs):>8.2f}{max(rs):>6.2f}"
                  f"{worst:>7.2f}   {outside:>2}/{len(rs)}")


if __name__ == "__main__":
    # The guard is required, not style: on Windows each Pool worker re-imports
    # this file, and without it every worker would start its own pool.
    p = argparse.ArgumentParser()
    p.add_argument("--range", action="store_true")
    a = p.parse_args()
    range_table() if a.range else rule_table()
