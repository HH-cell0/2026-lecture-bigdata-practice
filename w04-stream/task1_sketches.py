#!/usr/bin/env python3
"""Week 4 · Task 1 — Answer questions about a stream you cannot store.

Textbook §4.3 (sampling), §4.4 (Bloom filter), §4.5 (Flajolet-Martin).

The premise of the whole chapter: the stream is longer than your memory, it
goes past once, and you still have to answer. Every method here trades an exact
answer for a bounded amount of space, and the job is to know exactly what you
traded.

You build three, and the harness checks each against the truth it is
approximating.

    python3 task1_sketches.py --verify
"""
import argparse, hashlib, math, random, statistics


def _digest64(item, salt=b""):
    """A 64-bit hash of `item` that is the same on every run.

    Python's built-in hash() is randomised per process for strings, so a filter
    built today would disagree with the same filter built tomorrow, and nothing
    measured here would be reproducible. blake2b is in the standard library,
    deterministic, and takes a salt, which is how one function becomes many.
    """
    d = hashlib.blake2b(str(item).encode(), digest_size=8, salt=salt).digest()
    return int.from_bytes(d, "little")


class BloomFilter:
    """Membership, with one-sided error.

    A Bloom filter never says "no" about something you inserted. It sometimes
    says "yes" about something you did not. That asymmetry is the entire design
    and it is why it is useful for "have I seen this before" and useless for
    "is this definitely in the set".

    `m` bits, `k` hash functions.
    """

    def __init__(self, m, k, seed=246):
        self.m, self.k = m, k
        # One bit per position, packed 8 to a byte. A list of bools would spend
        # a whole Python object (8 bytes of pointer at least) on every bit, and
        # the point of the structure is that it is m bits and nothing more.
        self.bits = bytearray((m + 7) // 8)
        # k hash functions = the same hash with k different salts. §4.4.2's
        # formula assumes the k positions are independent, so I give each one
        # its own salt rather than deriving them from one hash (h1 + i*h2),
        # which is cheaper but only approximately independent. blake2b's salt
        # is at most 16 bytes: 8 for the seed, 8 for which hash this is.
        self.salts = [seed.to_bytes(8, "little") + i.to_bytes(8, "little")
                      for i in range(k)]

    def _positions(self, item):
        # A 64-bit value mod m. When m is a power of two (8192 in the harness)
        # this is exactly uniform; otherwise the bias is at most m / 2^64,
        # which is far below anything 20,000 queries could detect.
        return [_digest64(item, s) % self.m for s in self.salts]

    def add(self, item):
        # Only ever set bits, never clear them. This line is the whole reason
        # R1 holds: once an item's k bits are 1 nothing can turn them back to
        # 0, so asking about that item later always finds all k set.
        for p in self._positions(item):
            self.bits[p >> 3] |= 1 << (p & 7)

    def __contains__(self, item):
        # "Yes" needs all k bits; one 0 is proof the item was never added. A
        # false positive is the other direction: k bits that other items
        # happened to set between them.
        return all(self.bits[p >> 3] >> (p & 7) & 1
                   for p in self._positions(item))

    def expected_fp_rate(self, n_inserted):
        """The textbook's predicted false-positive rate after n insertions.

        §4.4.2 derives it. Return the number, do not measure it - the harness
        measures separately and compares the two.
        """
        # n items each throw k darts at m bits: kn darts. A given bit stays 0
        # with probability (1 - 1/m)^(kn) ~ e^(-kn/m), the textbook's
        # approximation. A non-member is a false positive when all k of its own
        # bits are 1, and the bits are treated as independent, hence the ^k.
        # Harness numbers: m=8192, k=5, n=800 -> kn/m = 0.4883,
        # e^-0.4883 = 0.6137, (1 - 0.6137)^5 = 0.3863^5 = 0.860%.
        return (1 - math.exp(-self.k * n_inserted / self.m)) ** self.k


def flajolet_martin(stream, n_hashes=64, seed=246):
    """Estimate how many DISTINCT items went past, in almost no memory.

    §4.5. Hash each item, count trailing zeros in the hash, keep the maximum.
    A maximum of R suggests about 2^R distinct items, because seeing R trailing
    zeros is a 1-in-2^R event.

    One hash gives an estimate with enormous variance, so you use many and
    combine them. How you combine them matters a great deal:

      * averaging 2^R directly is dominated by whichever hash got lucky - the
        values are exponential, so one outlier swamps the rest
      * the median is robust but can only ever be a power of two
      * §4.5.3 suggests grouping, and combining twice

    The harness accepts anything **within a factor of two** of the truth. That is
    not a generous tolerance, it is an honest one: this method really is that
    crude, and HyperLogLog exists because of it. Getting inside a factor of two
    reliably is the requirement; getting closer than that is not expected here.

    Return your estimate as a float.
    """
    # Combining rule: median of 2^R. R4 asks for "within 2x, reliably", and
    # the median is the rule that one lucky hash cannot drag outside that
    # band; its cost is that the answer is a power of two (or the midpoint of
    # two). try_combining.py runs every rule on the same maxima across 20 hash
    # seeds; that table, not this comment, is the evidence for the choice.
    return combine_median(fm_maxima(stream, n_hashes, seed))


# The family of hash functions. 2^61 - 1 is a Mersenne prime, so
# h(x) = (a*x + b) mod p is the standard universal family, and 61 bits leave
# room to count up to 2^60 trailing zeros' worth of distinct items.
_P = (1 << 61) - 1


def fm_maxima(stream, n_hashes=64, seed=246):
    """One pass over the stream; return the max trailing-zero count per hash.

    This is the only part that touches the stream, and its state is n_hashes
    small integers plus 2*n_hashes coefficients, whatever the stream length.
    That fixed size is what Task 2 measures against the exact set.
    """
    rng = random.Random(seed)
    # a >= 1 so no hash is the constant b. Drawing them from a seeded rng
    # makes every run see the same 64 functions.
    coeffs = [(rng.randrange(1, _P), rng.randrange(_P)) for _ in range(n_hashes)]
    R = [0] * n_hashes
    # Iterate, never list(): Task 2 hands this a generator, and turning it into
    # a list would store the stream (R6) and inflate the memory Task 2 reports.
    for item in stream:
        # One blake2b per item, then 64 cheap multiplications, instead of 64
        # blake2b calls. At millions of items in Task 2 the cryptographic hash
        # is the expensive part, so it is paid once.
        x = _digest64(item) % _P
        for i, (a, b) in enumerate(coeffs):
            h = (a * x + b) % _P
            # h & -h isolates the lowest set bit, so its bit_length minus one
            # is the number of trailing zeros, without formatting a string.
            # h == 0 happens with probability 1/2^61; it has no lowest set bit,
            # so skip it rather than let it claim 61 zeros and 2^61 items.
            if h:
                t = (h & -h).bit_length() - 1
                if t > R[i]:
                    R[i] = t
    return R


def combine_mean(R):
    # Average of 2^R. Unbiased-looking, but 2^R is exponential in R: one hash
    # that sees one extra zero doubles its own term, so one lucky hash out of
    # 64 can move the whole average.
    return sum(2.0 ** r for r in R) / len(R)


def combine_median(R):
    # Median of 2^R. One outlier cannot move it, but every value is a power of
    # two, so the answer can only be 2^j (or the midpoint of two neighbours,
    # since 64 is even and statistics.median averages the middle pair).
    return float(statistics.median(2.0 ** r for r in R))


def combine_groups(R, group_size=8):
    # §4.5.3: average within small groups, then take the median of the group
    # averages. The averages fill in the gaps between powers of two; the
    # median throws out the groups that a lucky hash dragged upward.
    groups = [R[i:i + group_size] for i in range(0, len(R), group_size)]
    return float(statistics.median(combine_mean(g) for g in groups))


def reservoir_sample(stream, k, seed=246):
    """Keep k items uniformly at random from a stream of unknown length.

    §4.3. Every item that went past must end up with the same probability k/n
    of being in your sample, and you only ever hold k of them.

    Return a list of k items (or fewer if the stream was shorter).
    """
    rng = random.Random(seed)
    sample = []
    # n is how many items have gone past *so far*. It grows by one per item and
    # is the only notion of length this function ever has: every decision
    # below uses the current n, never the final one, which is how it stays
    # correct for a stream whose length it never learns.
    for n, item in enumerate(stream, start=1):
        if n <= k:
            # The first k items fill the reservoir. At this point each of them
            # is in the sample with probability 1 = k/n for n = k.
            sample.append(item)
        else:
            # One draw does two jobs. j < k happens with probability k/n, which
            # is the chance the new item must have; and given j < k, j is
            # uniform over the k slots, so the item it evicts is a uniform pick.
            # Induction: an old item was in with probability k/(n-1), survives
            # with 1 - (k/n)(1/k) = (n-1)/n, so k/(n-1) * (n-1)/n = k/n.
            j = rng.randrange(n)
            if j < k:
                sample[j] = item
    return sample


# ------------------------------------------------------------------- harness
def verify():
    fails = 0
    rng = random.Random(246)

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<46} {detail}")
        fails += not ok

    # --- Bloom: no false negatives, ever
    try:
        bf = BloomFilter(m=8192, k=5)
    except NotImplementedError:
        print("  BloomFilter is still a stub"); return 1
    inserted = [f"item-{i}" for i in range(800)]
    for x in inserted:
        bf.add(x)
    check("no false negatives", all(x in bf for x in inserted))

    absent = [f"other-{i}" for i in range(20_000)]
    fp = sum(1 for x in absent if x in bf) / len(absent)
    predicted = bf.expected_fp_rate(len(inserted))
    close = abs(fp - predicted) < max(0.02, predicted * 0.5)
    check("measured false-positive rate matches theory", close,
          f"measured {fp:.3%}, predicted {predicted:.3%}")

    # --- Flajolet-Martin: a factor of two is what this method gives you
    try:
        distinct = 20_000
        stream = [f"k{rng.randrange(distinct)}" for _ in range(120_000)]
        est = flajolet_martin(stream)
    except NotImplementedError:
        print("  flajolet_martin is still a stub"); return 1
    true_distinct = len(set(stream))
    ratio = est / true_distinct
    check("distinct estimate within a factor of 2", 0.5 <= ratio <= 2.0,
          f"estimated {est:,.0f}, true {true_distinct:,} ({ratio:.2f}x)")

    # --- Reservoir: uniform over many trials
    try:
        counts = [0] * 20
        trials = 4000
        for t in range(trials):
            s = reservoir_sample(range(20), 5, seed=t)
            for i in s:
                counts[i] += 1
    except NotImplementedError:
        print("  reservoir_sample is still a stub"); return 1
    expected = trials * 5 / 20
    spread = (max(counts) - min(counts)) / expected
    check("reservoir is uniform across items", spread < 0.15,
          f"spread {spread:.1%} around {expected:.0f}")

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
