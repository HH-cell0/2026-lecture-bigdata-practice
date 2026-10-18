#!/usr/bin/env python3
"""Week 5 · Task 3 — PageRank on a graph that will not fit as a matrix.

Textbook §5.2 (efficient PageRank), §5.2.1 - §5.2.3.

`DenseMatrix` is PageRank written the way the equations are written: build the
transition matrix M, multiply. It is correct, it is easy to read, and it stores
n^2 numbers for a graph with almost no edges.

The web's matrix is about 99.9999% zeros. Storing them is the problem, and
§5.2 is the chapter about not doing that.

    python3 bench.py
    python3 bench.py --yours

Correctness first: the harness compares your ranks against the dense version
element by element. A fast PageRank that ranks pages differently is a different
algorithm, not a faster one.
"""


class DenseMatrix:
    """PageRank as written in the equations. Stores n^2 floats."""

    def __init__(self, beta=0.85, tol=1e-10, max_iter=100):
        self.beta, self.tol, self.max_iter = beta, tol, max_iter

    def run(self, graph):
        nodes = list(graph)
        n = len(nodes)
        index = {v: i for i, v in enumerate(nodes)}

        # the full transition matrix, zeros and all
        M = [[0.0] * n for _ in range(n)]
        for v, outs in graph.items():
            if outs:
                share = 1.0 / len(outs)
                for w in outs:
                    M[index[w]][index[v]] = share
            else:
                for i in range(n):           # dead end: spread it everywhere
                    M[i][index[v]] = 1.0 / n

        r = [1.0 / n] * n
        for self.iterations in range(1, self.max_iter + 1):
            nr = [0.0] * n
            for i in range(n):
                row = M[i]
                s = 0.0
                for j in range(n):
                    if row[j]:
                        s += row[j] * r[j]
                nr[i] = self.beta * s + (1 - self.beta) / n
            delta = sum(abs(a - b) for a, b in zip(nr, r))
            r = nr
            if delta < self.tol:
                break
        return {v: r[index[v]] for v in nodes}

    def memory_floats(self):
        return getattr(self, "_n", 0) ** 2


class YourPageRank:
    """Your PageRank.

        __init__(beta=0.85, tol=1e-10, max_iter=100)
        run(graph) -> {node: rank}
        memory_floats() -> the largest number of floats you held at once

    Same ranks, to within 1e-9 per node. Far less memory.

    `graph` is {node: [out-neighbours]}. Note what that already is: an adjacency
    list, which is the sparse representation. The dense version throws that
    structure away and then pays to get it back.

    Two things to be careful about, and they are the same two as Task 1:

      * dead ends, whose rank has to go somewhere
      * the teleport term, which touches every node and is therefore the one
        part that looks like it needs a dense operation - it does not, and
        working out why is the point of §5.2.3

    `memory_floats()` is on your honour and the harness reads it. Count the
    numbers you actually hold at once.
    """

    def __init__(self, beta=0.85, tol=1e-10, max_iter=100):
        # Same parameters and defaults as DenseMatrix, so both stop by the same rule.
        self.beta, self.tol, self.max_iter = beta, tol, max_iter

    def run(self, graph):
        # Same node order as DenseMatrix, so the returned ranks line up node by node.
        nodes = list(graph)
        n = len(nodes)
        self._n = n
        index = {v: i for i, v in enumerate(nodes)}
        # The adjacency list re-indexed to integers: E + n ints, no floats. This is
        # what we keep instead of M - the graph already was the sparse matrix.
        adj = [[index[w] for w in graph[v]] for v in nodes]
        dead = [i for i, a in enumerate(adj) if not a]

        r = [1.0 / n] * n
        for self.iterations in range(1, self.max_iter + 1):
            # Dead-end columns of M are all 1/n and teleport adds (1-beta)/n, so
            # both reduce to one scalar given to every node:
            # beta * D / n + (1 - beta) / n, with D the rank sitting on dead ends.
            # No n x n operation: (1/n everywhere) times r is just sum / n.
            base = (self.beta * sum(r[j] for j in dead) + (1 - self.beta)) / n
            nr = [0.0] * n
            for u, a in enumerate(adj):
                if a:
                    # Divide inline instead of storing a 1/outdeg table, which
                    # would be n more floats held.
                    share = r[u] / len(a)
                    for w in a:
                        nr[w] += share
            nr = [self.beta * s + base for s in nr]
            # Same L1 stopping rule as DenseMatrix.
            delta = sum(abs(x - y) for x, y in zip(nr, r))
            r = nr
            if delta < self.tol:
                break
        return {v: r[index[v]] for v in nodes}

    def memory_floats(self):
        # r and nr are the only float arrays, and both are alive during an
        # iteration: 2n. Scalars (base, share, delta) are O(1) and not counted.
        return 2 * getattr(self, "_n", 0)
