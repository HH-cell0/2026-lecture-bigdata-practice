#!/usr/bin/env python3
"""Week 3 · Task 2 — Find the crossover on your own machine.

Textbook §3.4.

Everybody knows brute force is quadratic and LSH is not. That is not the
interesting question. The interesting question is **where, on the machine in
front of you, does it start to matter** - and that answer is yours alone. It
depends on your CPU, your memory, and how big your shingle sets are.

This script gives you the timing loop. The two methods are yours: import them
from Task 1 and Task 3.

    python3 task2_crossover.py --sizes 500,1000,2000,4000
    python3 task2_crossover.py --sizes 8000,16000          # keep going

Write down where it hurts. That is the deliverable.
"""
import argparse, json, os, platform, time, tracemalloc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def machine():
    return {
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "python": platform.python_version(),
    }


def build_n(n, bench):
    """n documents, using bench.py's own recipe.

    Why this exists. The script originally did `bench.build()[:n]`, and
    bench.build() returns exactly N_DOCS + PLANTED = 2,120 documents. Every
    size above that silently measured the same 2,120 documents while recording
    the n that was asked for, so `--sizes 4000,8000,16000` produced three
    identical timings labelled as four-, eight- and sixteen-thousand. The
    automated check in test_tasks.py only reads the recorded n, so that would
    have passed while A4 - doubling n should quadruple the time - was being
    tested against data that never doubled.

    Below 2,120 this returns a prefix of bench.build(), so those rows are the
    same documents Task 3 is scored on. Above it, the same generator is run at
    the requested size: identical VOCAB and shingle count, and the planted
    pairs kept at the same fraction of the corpus, so the curve stays one
    curve. The seed is fixed, so re-running a size reproduces it.
    """
    base = bench.build()
    if n <= len(base):
        return base[:n]

    import random
    planted = round(n * bench.PLANTED / (bench.N_DOCS + bench.PLANTED))
    originals = n - planted
    rng = random.Random(bench.SEED)
    docs = [set(rng.sample(range(bench.VOCAB), bench.SHINGLES))
            for _ in range(originals)]
    for _ in range(planted):
        clone = set(docs[rng.randrange(originals)])
        for _ in range(rng.randint(4, 14)):
            clone.discard(rng.choice(list(clone)))
            clone.add(rng.randrange(bench.VOCAB))
        docs.append(clone)
    rng.shuffle(docs)
    return docs


def timed(fn, *args):
    """Wall time and peak memory of one call."""
    tracemalloc.start()
    t0 = time.perf_counter()
    result = fn(*args)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="250,500,1000,2000",
                   help="comma-separated document counts to try")
    p.add_argument("--threshold", type=float, default=0.6)
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    import bench
    from task3_scale import BruteForce
    try:
        from task3_scale import YourFinder
    except Exception:
        YourFinder = None

    rows = []
    for n in [int(x) for x in a.sizes.split(",")]:
        docs = build_n(n, bench)
        assert len(docs) == n, f"asked for {n} documents, got {len(docs)}"
        sim = bench.Counter()
        _, t_brute, m_brute = timed(BruteForce(a.threshold).find, docs, sim)
        c_brute = sim.calls

        row = {"n": n, "brute_s": t_brute, "brute_calls": c_brute,
               "brute_peak_bytes": m_brute}

        if YourFinder is not None:
            sim2 = bench.Counter()
            try:
                _, t_lsh, m_lsh = timed(YourFinder(a.threshold).find, docs, sim2)
                row.update({"lsh_s": t_lsh, "lsh_calls": sim2.calls,
                            "lsh_peak_bytes": m_lsh})
            except NotImplementedError:
                pass

        rows.append(row)
        line = f"  n={n:>6}  brute {t_brute:>8.2f}s  {c_brute:>12,} cmp"
        if "lsh_s" in row:
            line += f"   |  lsh {row['lsh_s']:>7.2f}s  {row['lsh_calls']:>9,} cmp"
        print(line)

    path = os.path.join(OUT, "crossover.json")
    prior = json.load(open(path)) if os.path.exists(path) else {"runs": []}
    prior["machine"] = machine()
    prior["runs"].extend(rows)
    json.dump(prior, open(path, "w"), indent=2)
    print(f"\n  -> out/crossover.json  ({len(prior['runs'])} measurement(s))")
    print("  Keep raising --sizes until something becomes unpleasant. Record where.")


if __name__ == "__main__":
    main()
