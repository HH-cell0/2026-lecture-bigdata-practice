#!/usr/bin/env python3
"""Week 6 · Task 3 — Make pass two fit.

Textbook §6.3 (PCY), §6.3.2 - §6.3.4.

`PlainApriori` does what Task 1 asked: use pass one to drop infrequent items,
then count every pair of surviving items. That is already much better than
counting all pairs. It is still not enough, because the surviving items are the
common ones, and the common ones appear together constantly.

The harness measures **the peak number of pair counters you held**, because
that is the thing that decides whether the algorithm runs at all. §6.3 is about
spending pass one's spare memory to shrink it.

    python3 bench.py
    python3 bench.py --yours

Correctness first: you must find exactly the same frequent pairs. Finding fewer
is not an optimisation.
"""
from array import array
from collections import Counter
from itertools import combinations


class PlainApriori:
    """Pass one drops infrequent items. Pass two counts every surviving pair."""

    def __init__(self, support):
        self.support = support
        self.peak_counters = 0

    def run(self, baskets):
        counts = Counter()
        for basket in baskets:
            counts.update(basket)
        frequent = {i for i, c in counts.items() if c >= self.support}

        pair_counts = Counter()
        for basket in baskets:
            items = sorted(basket & frequent)
            for pair in combinations(items, 2):
                pair_counts[pair] += 1
            self.peak_counters = max(self.peak_counters, len(pair_counts))

        return {frozenset(p): c for p, c in pair_counts.items()
                if c >= self.support}


class YourAlgorithm:
    """Your frequent-pair finder.

        __init__(support)
        run(baskets) -> {frozenset({a, b}): count}
        .peak_counters -> the most pair counters you ever held at once

    Same pairs as the baseline. Fewer counters.

    Pass one only needs one integer per item, and there are not many items. The
    rest of your memory is sitting idle while you do it. §6.3 spends it: hash
    every pair you see in pass one into a fixed array of buckets, and count the
    buckets rather than the pairs.

    A bucket whose total is below the support threshold cannot contain a
    frequent pair. In pass two you skip every pair landing in such a bucket -
    and the bucket array collapses to a bitmap, one bit each, before you need
    the memory for counters.

    Two things to be careful of:

      * a bucket being frequent does not make its pairs frequent. It is a
        filter, not an answer
      * `peak_counters` is on your honour. Count the pair counters you hold at
        the same time. The bitmap is not a pair counter, but if you keep the
        full bucket counts alive into pass two, that is not free either -
        observation.md asks about it
    """

    # Bucket count, chosen by arithmetic before seeing the data. Pass one hashes
    # T pairs into B buckets, so the average bucket holds T/B. The filter only
    # works if most buckets stay below support s, i.e. T/B well under s.
    #   T estimate from bench's constants: 20,000 baskets * C(20, 2) = 3.8M
    #   T/B = s/2 (average bucket half the threshold) -> B = 2*T/s = 152,000
    #   152,003 is the next prime, so the modulus has no factor in common with
    #   the multiplier 2,000 in bucket_of().
    # Why not tune B down to where C2 = B (about 90k, ~88% cut): below that
    # point peak = C2, which depends on hash collisions and jumps around
    # (80k -> 75.0%, 90k -> 88.4%, 95k -> 86.8%). Above it peak = B, so the
    # cut is the smooth 1 - B/820,259, and a wrong T estimate barely moves it.
    BUCKETS = 152_003

    # Multiplier for the pair index. Item ids in bench are 0..1999, so for
    # a < b, a*2000 + b is a distinct integer per pair: collisions happen only
    # in the final mod B. Correctness never depends on this - a collision can
    # only let an extra pair through the filter, never drop a frequent one.
    ITEMS = 2_000

    def __init__(self, support, buckets=BUCKETS):
        self.support = support
        self.n_buckets = buckets
        # Peak = max over time of the counters held at that moment. Pass one
        # holds B bucket counters; pass two holds the pair counters. They never
        # coexist (the bucket array is deleted before the first pair counter),
        # so the peak is max(B, C2). The 2,000 item counts are left out, as the
        # baseline leaves them out.
        self.peak_counters = 0
        # Reported separately for observation.md and try_buckets.py.
        self.pass2_counters = 0
        self.bitmap_words = 0
        self.frequent_buckets = 0

    def bucket_of(self, a, b):
        # Arithmetic hash, not hash((a, b)). Measured on bench data: C2 34,248
        # vs 91,076 at B=152,003. hash((a, b)) has no collisions before the mod
        # either (1,999,000 distinct values), so that is not the reason. The
        # reason is bench's Zipf weights go by id: popular items have small
        # ids, and every pair with a < 76 maps below 76*2000 = 152,000 < B
        # without wrapping, one bucket each. Those pairs are 61% of all pair
        # occurrences, so the heavy pairs never pile into the same bucket.
        # With shuffled ids this hash is no better (C2 108,394).
        return (a * self.ITEMS + b) % self.n_buckets

    def run(self, baskets):
        s, B = self.support, self.n_buckets

        # Pass one: item counts as in A-Priori, plus every pair of the basket
        # hashed into a bucket. Items are not known to be frequent yet, so all
        # pairs are hashed. array('i') holds real 4-byte ints, one per bucket.
        counts = Counter()
        buckets = array('i', [0]) * B
        for basket in baskets:
            counts.update(basket)
            # sorted so (a, b) always has a < b and one pair has one bucket
            for a, b in combinations(sorted(basket), 2):
                buckets[self.bucket_of(a, b)] += 1
        frequent = {i for i, c in counts.items() if c >= s}
        self.peak_counters = B  # all B bucket counters were held in pass one

        # Fold to one bit per bucket. A bucket total is the sum of its pairs'
        # counts, so a frequent pair can only sit in a frequent bucket: bit 0
        # means none of its pairs can be frequent.
        bitmap = bytearray((B + 7) // 8)
        for i, c in enumerate(buckets):
            if c >= s:
                bitmap[i >> 3] |= 1 << (i & 7)
                self.frequent_buckets += 1
        # Free the counts before any pair counter exists, so the two are never
        # held at the same time. The bitmap stays for all of pass two:
        # ceil(B/32) 32-bit words, not counted as counters (bits are not
        # counters) but reported here.
        del buckets
        self.bitmap_words = (B + 31) // 32

        # Pass two: count only candidates - both items frequent (A-Priori) and
        # the pair's bucket frequent (PCY). Counting only pairs that occur,
        # like the baseline, so the two peaks are comparable.
        pair_counts = Counter()
        for basket in baskets:
            for a, b in combinations(sorted(basket & frequent), 2):
                h = self.bucket_of(a, b)
                if bitmap[h >> 3] >> (h & 7) & 1:
                    pair_counts[(a, b)] += 1
            self.peak_counters = max(self.peak_counters, len(pair_counts))
        self.pass2_counters = len(pair_counts)

        # A frequent bucket does not make its pairs frequent: filter on the
        # real count. Same output format as PlainApriori.
        return {frozenset(p): c for p, c in pair_counts.items() if c >= s}
