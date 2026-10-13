#!/usr/bin/env python3
"""Week 4 · Task 3 — Same memory, fewer mistakes.

Textbook §4.4 (Bloom filters), §4.5 (counting distinct).

`NaiveFilter` is a membership filter in a fixed number of bits. It works. It
also makes far more mistakes than it has to with the memory it was given, and
it does so for a reason you can find by reading §4.4.2 and doing one derivative.

You get **exactly the same number of bits**. Make fewer mistakes.

    python3 bench.py
    python3 bench.py --yours

The rule that makes this interesting: a false negative is not allowed. Ever.
The whole point of this structure is that "no" means no. A filter that gets a
better score by occasionally forgetting something it was given has not improved
anything, it has broken the contract.
"""
import hashlib
import math


class NaiveFilter:
    """One hash function, and the bits it was given."""

    def __init__(self, n_bits, seed=246):
        self.n_bits = n_bits
        self.seed = seed
        self.bits = bytearray(n_bits)

    def _index(self, item):
        d = hashlib.blake2b(str(item).encode(), digest_size=8,
                            key=str(self.seed).encode()).digest()
        return int.from_bytes(d, "big") % self.n_bits

    def add(self, item):
        self.bits[self._index(item)] = 1

    def __contains__(self, item):
        return bool(self.bits[self._index(item)])

    def memory_bits(self):
        return self.n_bits


class YourFilter:
    """Your filter.

        __init__(n_bits, seed=246)
        add(item)
        item in filter  ->  bool
        memory_bits()   ->  how many bits you are using

    `memory_bits()` must not exceed the `n_bits` you were given. The harness
    checks. Counting only some of your memory is not an optimisation.

    §4.4.2 gives the false-positive rate of a filter with m bits, k hashes and
    n items inserted. There is a k that minimises it, and it depends on m/n.
    The harness tells you n before you start, so you have no excuse for guessing.

    Then there is a second question, which is worth more: the harness inserts
    a **known** number of items, but a real stream does not tell you n in
    advance. What would you do then? You do not have to implement it - but
    observation.md asks.
    """

    def __init__(self, n_bits, seed=246, n_expected=8_000):
        # n_expected defaults to bench.py's N_INSERT. It is optional so that
        # bench's call YourFilter(N_BITS, seed=SEED) works unchanged (R1, R2),
        # and it is an argument rather than a buried constant so that the one
        # assumption this filter rests on is visible at the call site.
        self.n_bits = n_bits
        self.seed = seed
        # §4.4.2: FP(k) = (1 - e^(-kn/m))^k. Write p = e^(-kn/m); setting
        # d/dk ln FP = 0 gives p = 1/2, i.e. k* = (m/n) ln 2. Here m/n = 10,
        # so k* = 6.93. k must be an integer, so compare the neighbours:
        # k=6 -> 0.8436%, k=7 -> 0.8194%, k=8 -> 0.8455%, floor 0.81925%.
        # round() picks 7, the lower of the two; at this m/n rounding and
        # comparing agree, and computing it keeps the derivation in the code.
        self.k = max(1, round(n_bits / n_expected * math.log(2)))
        # One bit per position, 8 to a byte: 80,000 bits is 10,000 bytes.
        # NaiveFilter's bytearray(n_bits) spends a whole byte per bit, 8x the
        # memory it reports; packing is what makes memory_bits() honest.
        self.bits = bytearray((n_bits + 7) // 8)

    def _positions(self, item):
        # k positions from k salted blake2b calls. The salt is the loop index
        # i, built here and thrown away, never stored: the only state that
        # grows with what was inserted is self.bits, so R3's "count all of
        # your memory" has nothing else to count. Separate salts rather than
        # double hashing (h1 + i*h2) because §4.4.2 assumes the k positions
        # are independent, and that is the formula k=7 was chosen from.
        # The seed goes in as the key, as in NaiveFilter.
        key = str(self.seed).encode()
        data = str(item).encode()
        for i in range(self.k):
            d = hashlib.blake2b(data, digest_size=8, key=key,
                                salt=i.to_bytes(16, "little")).digest()
            # 64-bit value mod 80,000: the bias is at most m / 2^64, far below
            # what 200,000 queries could detect.
            yield int.from_bytes(d, "big") % self.n_bits

    def add(self, item):
        # Bits are only ever set, never cleared, so an inserted item's k bits
        # stay 1 forever and asking about it again always says yes: R4.
        for p in self._positions(item):
            self.bits[p >> 3] |= 1 << (p & 7)

    def __contains__(self, item):
        # One 0 among the k bits proves the item was never added. all() stops
        # at the first 0, so most absent items cost fewer than k hashes.
        return all(self.bits[p >> 3] >> (p & 7) & 1
                   for p in self._positions(item))

    def memory_bits(self):
        # Every byte of the bit array, times 8: 10,000 * 8 = 80,000, exactly
        # the budget. n_bits, seed and k are three scalars of configuration,
        # the same kind NaiveFilter keeps and does not count.
        return len(self.bits) * 8
