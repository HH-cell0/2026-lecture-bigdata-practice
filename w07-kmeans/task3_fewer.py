#!/usr/bin/env python3
"""Week 7 · Task 3 — The same clustering, with far fewer distances.

Textbook §7.3, and §7.1.3 for why distance is the expensive part.

`NaiveKMeans` does what the definition says: every iteration, compare every
point with every centroid. That is n x k distance computations per pass, and on
a real dataset the distance computation is almost the entire cost.

Most of that work is wasted. After the first couple of iterations, most points
do not change cluster, and most centroids barely move. The triangle inequality
lets you prove a point cannot have changed cluster **without measuring it**.

    python3 bench.py
    python3 bench.py --yours

Correctness first: your final SSE must match the baseline's. Fewer distances
with a worse clustering is not an improvement, it is a different algorithm.
"""


class NaiveKMeans:
    """Every point against every centroid, every iteration."""

    def __init__(self, k, max_iter=50):
        self.k, self.max_iter = k, max_iter

    def run(self, points, initial_centroids, distance):
        centroids = list(initial_centroids)
        labels = [None] * len(points)
        for self.iterations in range(1, self.max_iter + 1):
            changed = False
            for i, p in enumerate(points):
                best, bi = None, 0
                for j, c in enumerate(centroids):
                    d = distance(p, c)
                    if best is None or d < best - 1e-12:
                        best, bi = d, j
                if labels[i] != bi:
                    labels[i] = bi
                    changed = True
            centroids = _means(points, labels, self.k, centroids)
            if not changed:
                break
        return labels, centroids


def _means(points, labels, k, previous):
    out = []
    for j in range(k):
        group = [p for p, l in zip(points, labels) if l == j]
        if group:
            out.append(tuple(sum(v) / len(group) for v in zip(*group)))
        else:
            out.append(previous[j])
    return out


class YourKMeans:
    """Your k-means.

        __init__(k, max_iter=50)
        run(points, initial_centroids, distance) -> (labels, centroids)

    Same starting centroids, same `distance` function - which is counted. That
    counter is your score.

    The idea, from §7.3 and the triangle inequality:

        if a point is much closer to its current centroid than that centroid
        moved, and than any other centroid could have come, then it cannot have
        changed cluster, and you do not have to measure anything

    Keeping enough bookkeeping to make that test cheap, without keeping so much
    that the bookkeeping costs more than the distances, is the task.

    You may call `distance` on two centroids, and those calls are counted too -
    which is the correct accounting, since that is real work. There are k of
    them and n points, and k is much smaller than n. That asymmetry is the
    whole opening.
    """

    # Elkan's bounds. Per point: one upper bound u (distance to own centroid)
    # and k lower bounds l[j] (distance to each centroid) = k + 1 numbers.
    # Per iteration: k(k-1)/2 centroid-centroid distances + k centroid moves.
    # The score counts distance calls, not memory, so k lower bounds win over
    # Hamerly's single one: only the bound that broke has to be re-measured.

    def __init__(self, k, max_iter=50, prune_first=True):
        self.k, self.max_iter = k, max_iter
        # prune_first: use the initial centroid-centroid distances to skip
        # work already in iteration 1 (Elkan's paper). False = measure all of
        # iteration 1 like the baseline, kept to compare the two.
        self.prune_first = prune_first
        # Bookkeeping only, no distance calls: where the savings come from.
        self.stats = {"point_skip": 0,   # u <= s[a]: all k-1 others skipped
                      "lower": 0,        # pair skipped by u <= l[j] alone
                      "half": 0,         # pair skipped by u <= cc[a][j]/2 alone
                      "both": 0,         # pair skipped, either test sufficed
                      "tighten": 0,      # distance calls refreshing u
                      "first_skip": 0,   # iteration-1 pairs skipped by cc/2
                      "first_iter_calls": 0}

    def _centroid_gaps(self, centroids, distance):
        # cc[j][m] = d(c_j, c_m): k(k-1)/2 calls, mirrored, since d is symmetric.
        k = self.k
        cc = [[0.0] * k for _ in range(k)]
        for j in range(k):
            for m in range(j + 1, k):
                cc[j][m] = cc[m][j] = distance(centroids[j], centroids[m])
        # s[j] = half the distance to the nearest other centroid: a point
        # within s[j] of c_j is closer to c_j than to any other centroid.
        s = [0.5 * min(cc[j][m] for m in range(k) if m != j) for j in range(k)]
        return cc, s

    def run(self, points, initial_centroids, distance):
        k, n, st = self.k, len(points), self.stats
        centroids = list(initial_centroids)
        labels = [None] * n
        upper = [0.0] * n
        lower = [[0.0] * k for _ in range(n)]
        calls_before = getattr(distance, "calls", 0)

        # Iteration 1: no bounds exist yet.
        if self.prune_first:
            cc, _ = self._centroid_gaps(centroids, distance)
        for i, p in enumerate(points):
            a, best = 0, distance(p, centroids[0])
            lower[i][0] = best
            for j in range(1, k):
                # d(x,c_j) >= cc[a][j] - d(x,c_a) >= d(x,c_a) when
                # cc[a][j] >= 2 d(x,c_a): c_j cannot be closer, skip it, and
                # cc - d(x,c_a) is still a valid lower bound to remember.
                if self.prune_first and cc[a][j] >= 2 * best:
                    lower[i][j] = cc[a][j] - best
                    st["first_skip"] += 1
                    continue
                d = distance(p, centroids[j])
                lower[i][j] = d
                # Baseline's own test, so the same centroid wins.
                if d < best - 1e-12:
                    a, best = j, d
            labels[i], upper[i] = a, best
        st["first_iter_calls"] = getattr(distance, "calls", 0) - calls_before
        self.iterations = 1
        new = _means(points, labels, k, centroids)

        for self.iterations in range(2, self.max_iter + 1):
            # Move the bounds by how far each centroid moved (k calls):
            # by the triangle inequality the own-centroid distance grows by
            # at most delta[a], every other one shrinks by at most delta[j].
            delta = [distance(c, c2) for c, c2 in zip(centroids, new)]
            centroids = new
            for i in range(n):
                upper[i] += delta[labels[i]]
                li = lower[i]
                for j in range(k):
                    li[j] = max(0.0, li[j] - delta[j])
            cc, s = self._centroid_gaps(centroids, distance)

            changed = False
            for i, p in enumerate(points):
                a, u = labels[i], upper[i]
                if u <= s[a]:
                    # Within half the gap to the nearest other centroid.
                    st["point_skip"] += 1
                    continue
                li, tight = lower[i], False
                for j in range(k):
                    if j == a:
                        continue
                    by_low, by_half = u <= li[j], u <= 0.5 * cc[a][j]
                    if by_low or by_half:
                        st["both" if by_low and by_half else
                           "lower" if by_low else "half"] += 1
                        continue
                    if not tight:
                        # u may be loose: measure once, then test again before
                        # paying for d(x, c_j).
                        u = distance(p, centroids[a])
                        li[a], tight = u, True
                        st["tighten"] += 1
                        by_low, by_half = u <= li[j], u <= 0.5 * cc[a][j]
                        if by_low or by_half:
                            st["both" if by_low and by_half else
                               "lower" if by_low else "half"] += 1
                            continue
                    d = distance(p, centroids[j])
                    li[j] = d
                    if d < u:
                        a, u = j, d
                if a != labels[i]:
                    labels[i] = a
                    changed = True
                upper[i] = u
            new = _means(points, labels, k, centroids)
            if not changed:
                break
        return labels, new
