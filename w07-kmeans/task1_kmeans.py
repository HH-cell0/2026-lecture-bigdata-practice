#!/usr/bin/env python3
"""Week 7 · Task 1 — k-means, and the thing that decides the answer.

Textbook §7.1 (clustering, the curse of dimensionality), §7.3 (k-means).

k-means is four lines: pick centroids, assign every point to the nearest one,
move each centroid to the mean of its points, repeat. It always converges.

It converges to a **local** optimum, and which one depends entirely on where you
started. That is not a footnote - it is the difference between a clustering that
means something and one that does not, and you can watch it happen on nine points.

    python3 task1_kmeans.py --verify
"""
import argparse, math, random

# Three obvious blobs of three points each. Any sensible clustering finds them.
BLOBS = [(0.0, 0.0), (0.2, 0.1), (0.1, 0.2),
         (8.0, 8.0), (8.2, 8.1), (8.1, 8.2),
         (0.0, 8.0), (0.2, 8.1), (0.1, 8.2)]


def euclidean(a, b):
    """Distance between two points of any dimension."""
    # zip pairs coordinates whatever the length, so one formula covers every d.
    # Same expression as bench.py's Distance, so Task 1 and Task 3 agree.
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def assign(points, centroids):
    """Nearest centroid for each point. Return a list of centroid indices.

    Ties go to the lower index, so that everybody's answer is the same.
    """
    labels = []
    for p in points:
        best, bi = None, 0
        for j, c in enumerate(centroids):
            d = euclidean(p, c)
            # Strict "<": an equal distance found later never replaces the
            # earlier one, so a tie keeps the lower index (R2).
            if best is None or d < best:
                best, bi = d, j
        labels.append(bi)
    return labels


def update(points, labels, k, previous=None):
    """Move each centroid to the mean of its points.

    An empty cluster has no mean. Decide what you do - and say so, because the
    choice changes the result and there is more than one defensible answer.

    R3 choice: an empty cluster KEEPS ITS PREVIOUS CENTROID. That is the rule
    in task3_fewer.py's _means, and Task 3 must match that baseline's SSE, so
    using the same rule here keeps the week consistent. It also cannot raise
    SSE: a cluster with no points contributes nothing whichever centroid it
    keeps. The cost: if it never wins a point back, the result has k-1 clusters.

    `previous` is extra (the stub signature has no old centroids to keep), and
    kmeans() always passes it. Called as update(points, labels, k) with no
    `previous`, there is nothing to keep, so an empty cluster falls back to the
    other defensible rule: it takes the point furthest from its own new
    centroid, a different point for each empty cluster. Either way k
    centroids come back.
    """
    sums = [None] * k
    counts = [0] * k
    # One pass over the points: accumulate a coordinate sum per cluster.
    for p, l in zip(points, labels):
        if sums[l] is None:
            sums[l] = list(p)
        else:
            for i, v in enumerate(p):
                sums[l][i] += v
        counts[l] += 1
    out = []
    for j in range(k):
        if counts[j]:
            out.append(tuple(s / counts[j] for s in sums[j]))
        elif previous is not None:
            out.append(tuple(previous[j]))
        else:
            out.append(None)  # filled below, once every non-empty mean exists
    if None in out:
        # Fallback without `previous`: rank points by distance to their own
        # centroid, furthest first. All labels point at non-empty clusters,
        # so every out[labels[i]] here is a real mean.
        order = sorted(range(len(points)),
                       key=lambda i: euclidean(points[i], out[labels[i]]),
                       reverse=True)
        # One distinct point per empty cluster, so two empties never collide.
        for j, i in zip([j for j in range(k) if out[j] is None], order):
            out[j] = tuple(points[i])
    return out


def kmeans(points, k, init="random", seed=246, max_iter=100):
    """Run to convergence. Return (labels, centroids, sse).

    `sse` is the sum over points of the squared distance to their own centroid.
    It is what k-means minimises, and it is how you compare two runs.

    `init` is either:
        "random"   pick k points at random as the starting centroids
        "++"       k-means++ (§7.3.2): pick the first at random, then pick each
                   next one with probability proportional to the squared distance
                   to the nearest centroid already chosen

    Set `kmeans.iterations` to how many passes you used.
    """
    # One generator per call, seeded, so a seed always gives the same run.
    rng = random.Random(seed)
    if init == "random":
        # sample() draws without replacement: k distinct starting points.
        centroids = [tuple(p) for p in rng.sample(points, k)]
    elif init == "++":
        centroids = [tuple(rng.choice(points))]
        # d2[i] = squared distance from point i to its nearest chosen centroid.
        # Updated against the newest centroid only, so each new pick costs n
        # distances and the whole init costs (k-1)*n, not k*k*n/2.
        d2 = [euclidean(p, centroids[0]) ** 2 for p in points]
        while len(centroids) < k:
            # Weight D^2 (§7.3.2): far points are likely, chosen points have
            # weight 0 and can never be picked twice.
            c = tuple(rng.choices(points, weights=d2)[0])
            centroids.append(c)
            d2 = [min(old, euclidean(p, c) ** 2) for old, p in zip(d2, points)]
    else:
        raise ValueError(f"unknown init {init!r}")

    labels = None
    for it in range(1, max_iter + 1):
        new = assign(points, centroids)
        kmeans.iterations = it
        # Converged when no point moved: the next update would give the same
        # centroids. The final unchanged pass is counted, as in NaiveKMeans.
        if new == labels:
            break
        labels = new
        centroids = update(points, labels, k, previous=centroids)
    return labels, centroids, sse_of(points, labels, centroids)


def sse_of(points, labels, centroids):
    """Sum of squared distances from each point to its assigned centroid."""
    # Squared, not plain distance: this is the quantity k-means minimises.
    return sum(euclidean(p, centroids[l]) ** 2 for p, l in zip(points, labels))


# ------------------------------------------------------------------- harness
def verify():
    fails = 0

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<50} {detail}")
        fails += not ok

    try:
        check("distance in 2d", abs(euclidean((0, 0), (3, 4)) - 5) < 1e-9)
        check("distance in 5d",
              abs(euclidean((0,) * 5, (1,) * 5) - math.sqrt(5)) < 1e-9)
    except NotImplementedError:
        print("  euclidean is still a stub"); return 1

    try:
        labels, cents, sse = kmeans(BLOBS, 3, init="++", seed=1)
    except NotImplementedError:
        print("  kmeans is still a stub"); return 1

    groups = {}
    for p, l in zip(BLOBS, labels):
        groups.setdefault(l, []).append(p)
    check("three clusters of three", sorted(len(g) for g in groups.values()) == [3, 3, 3],
          sorted(len(g) for g in groups.values()))
    check("the three blobs were recovered",
          all(max(q[0] for q in g) - min(q[0] for q in g) < 1 and
              max(q[1] for q in g) - min(q[1] for q in g) < 1
              for g in groups.values()))
    check("sse is small when clusters are right", sse < 1.0, f"sse {sse:.4f}")

    # Bad luck with random starts should sometimes be visibly worse.
    randoms = [kmeans(BLOBS, 3, init="random", seed=s)[2] for s in range(40)]
    plusplus = [kmeans(BLOBS, 3, init="++", seed=s)[2] for s in range(40)]
    check("random init sometimes lands badly", max(randoms) > min(randoms) * 5,
          f"sse from {min(randoms):.3f} to {max(randoms):.3f}")
    check("k-means++ is more reliable than random",
          sum(plusplus) / len(plusplus) <= sum(randoms) / len(randoms),
          f"mean sse: ++ {sum(plusplus) / len(plusplus):.3f} vs "
          f"random {sum(randoms) / len(randoms):.3f}")

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
