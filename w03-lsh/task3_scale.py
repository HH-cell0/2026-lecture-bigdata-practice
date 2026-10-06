#!/usr/bin/env python3
"""Week 3 · Task 3 — Find the same pairs without comparing everything.

Textbook §3.4.

`BruteForce` compares every pair. On 3,000 documents that is 4.5 million
comparisons and it is completely correct. On 3 million documents it is 4.5
trillion and it is completely useless.

Beat it. Find the same near-duplicate pairs while making far fewer comparisons.

    python3 bench.py
    python3 bench.py --yours

The harness counts every call you make to `similarity()`. That is your score.
It also checks **recall** - which of the truly similar pairs you found. Skipping
comparisons is easy; skipping comparisons without losing the pairs is the task.
"""
import random

from task1_minhash import lsh_candidates, minhash_signatures


class BruteForce:
    """Correct, and quadratic."""

    def __init__(self, threshold):
        self.threshold = threshold

    def find(self, docs, similarity):
        """docs is [set_of_shingles, ...]. Return {(i, j), ...} with i < j."""
        out = set()
        for i in range(len(docs)):
            for j in range(i + 1, len(docs)):
                if similarity(docs[i], docs[j]) >= self.threshold:
                    out.add((i, j))
        return out


class YourFinder:
    """Your near-duplicate finder.

        __init__(threshold)
        find(docs, similarity) -> {(i, j), ...}

    `similarity(a, b)` is the only way to compare two documents, and every call
    is counted. Everything else - signatures, banding, bucketing - is free, in
    the sense that the harness does not charge you for it. That is deliberate:
    it is also roughly true at scale, where the comparison is the expensive
    part and the hashing is linear.

    Two knobs decide everything:

        the number of hashes in a signature
        how many bands you split it into

    §3.4.2 gives you the relationship between those and the probability that a
    pair at similarity s becomes a candidate. It is an S-curve, and where its
    step sits is something you choose. Choose it on purpose and be able to say
    why in observation.md - a threshold of 0.8 does not mean bands should be
    anything in particular until you have done the arithmetic.

    You may reuse your Task 1 code.

    ---------------------------------------------------------------- my choice

    n = 120 hashes, b = 30 bands, so r = 4 rows per band.

    §3.4.2. A pair at similarity s becomes a candidate with probability

        1 - (1 - s^r)^b

    and the step of that S-curve sits near (1/b)^(1/r). For b=30, r=4 that is

        (1/30)^(1/4) = 0.427

    which is well **below** the threshold of 0.6, and that is on purpose. The
    step is where the curve crosses one half; putting it at the threshold would
    mean coin-flipping on pairs that sit exactly at 0.6, and the planted pairs
    in this harness bottom out at s = 0.6216. Pushing the step down to 0.427
    buys:

        s = 0.6216 (the hardest true pair)   P = 0.992
        s = 0.6667 (the 10th percentile)     P = 0.999
        s = 0.006  (an average random pair)  P = 3.9e-08

    The last line is what makes the trade cheap. A step that low lets far more
    pairs through in principle, but "more" is measured against a base rate of
    4e-08: across all 2,246,140 pairs the expected number of false candidates
    is 0.087. So the extra comparisons the low step costs are, in this data,
    less than one.

    What it costs in general is precision, and the cost scales with how much
    mass the data has just under the threshold. Here there is none - the gap
    between the planted pairs (0.62 and up) and everything else (0.006) is
    enormous. On real near-duplicate data that gap is filled, and a step at
    0.427 would drag in every pair above it; the step would have to move up
    toward the threshold and recall would be traded away for it.

    Moving the step the wrong way, measured on this harness by varying b at
    n=120 and leaving everything else alone:

        b    r    step     comparisons    recall
       30    4   0.427            126     100.0%
       20    6   0.607            118      97.5%
       15    8   0.713             86      71.1%
       12   10   0.780             59      48.8%
        6   20   0.914             10       8.3%

    Read the two columns on the right together, because that is the actual
    lesson. Comparisons keep falling as the step rises, and the score the
    harness charges keeps improving, while the answer quietly rots. The b=6
    row avoids 99.9996% of the comparisons and finds one true pair in twelve.
    R3 exists to make that row fail, and recall is the first number to read.

    Note also how little is bought by being wrong: b=20 gives up 3 real pairs
    to save 8 comparisons out of 2,246,140. The trade is not close.

    The other direction is merely wasteful rather than wrong - b=40, r=3 puts
    the step at 0.292 and spends 265 comparisons for the same 100% recall. The
    curve has already flattened at the top by b=30, so the extra width buys
    nothing here.
    """

    # §3.4.2 - see the arithmetic above. n = BANDS * ROWS_PER_BAND.
    N_HASHES = 120
    BANDS = 30

    # A prime comfortably larger than any shingle id, for h(x) = (a*x + b) % P.
    _PRIME = 10_000_019
    # Fixed so the submitted numbers are reproducible, like the harness's seed.
    _SEED = 20260315

    def __init__(self, threshold):
        self.threshold = threshold

        # n independent hash functions standing in for n random permutations
        # of the rows (§3.3.4 - permuting a real matrix is not feasible, so
        # the permutation is simulated). Each is drawn once and kept, because
        # two documents have to be hashed by the *same* functions to be
        # comparable. `a` is never 0, which would collapse the function to a
        # constant and waste a row of the signature.
        rng = random.Random(self._SEED)
        self._hashes = [
            self._make_hash(rng.randrange(1, self._PRIME),
                            rng.randrange(0, self._PRIME))
            for _ in range(self.N_HASHES)
        ]

    @classmethod
    def _make_hash(cls, a, b):
        # A factory, not a lambda in the loop: a bare lambda would close over
        # the loop variable and all n functions would end up identical.
        prime = cls._PRIME
        return lambda x: (a * x + b) % prime

    def find(self, docs, similarity):
        """docs is [set_of_shingles, ...]. Return {(i, j), ...} with i < j."""
        if not docs:
            return set()

        # minhash_signatures walks rows 0..n_rows-1, and here a "row" is a
        # shingle id, so the row count is one past the largest id in use.
        largest = max((max(d) for d in docs if d), default=-1)
        signatures = minhash_signatures(docs, self._hashes, largest + 1)

        # Everything above is linear in the documents and is not charged by the
        # harness. The line below is where the score is decided: only pairs
        # that shared a bucket in at least one band are ever compared.
        candidates = lsh_candidates(signatures, self.BANDS)

        # §3.4.3 step 7. Being a candidate is a claim about the signatures, not
        # about the documents, so each survivor is still checked against the
        # real sets. This is the only place similarity() is called, and it is
        # called once per candidate.
        return {(i, j) for i, j in candidates
                if similarity(docs[i], docs[j]) >= self.threshold}
