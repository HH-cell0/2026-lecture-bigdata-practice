#!/usr/bin/env python3
"""Week 3 · Task 1 — Minhash and LSH, built from the matrix up.

Textbook §3.2 - §3.4.

Comparing every pair is quadratic, so it stops being possible somewhere around
a hundred thousand documents. The way out is two ideas stacked:

    minhash   replace a set with a short signature, such that the chance two
              signatures agree in a position equals their Jaccard similarity
    LSH       hash bands of those signatures so that similar pairs collide and
              you only ever compare the ones that did

You build both. The textbook's §3.3.5 example is small enough to check by hand,
and the harness checks you against it.

    python3 task1_minhash.py --verify
"""
import argparse

# §3.3.5. Rows are elements 0..4, columns are the sets S1..S4.
BOOK = [[1, 0, 0, 1],
        [0, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 1, 1],
        [0, 0, 1, 0]]
# The two hash functions the textbook uses on the row numbers.
BOOK_HASHES = [lambda r: (r + 1) % 5, lambda r: (3 * r + 1) % 5]


def jaccard(a, b):
    """|a and b| / |a or b|. Empty union is 0, not an error."""
    # §3.1. The union is the denominator, so two empty sets have nothing to
    # divide by. Returning 0 keeps the caller free of a special case; the
    # alternative (1, "they are identical") would make every empty document a
    # near-duplicate of every other, which is worse than calling them unrelated.
    union = len(a | b)
    if not union:
        return 0
    return len(a & b) / union


def minhash_signatures(columns, hashes, n_rows):
    """Build the signature matrix, one pass over the rows.

    `columns` is [set_of_row_numbers, ...], one entry per document.
    Return [[sig for each hash] for each column].

    The algorithm in §3.3.5 walks each row **once** and updates the signature
    of every column that has a 1 in it:

        sig[h][c] = min(sig[h][c], h(r))

    Doing it that way is the point. If you sort or re-scan per column you have
    written something correct that does not survive a dataset that does not fit
    in memory, and not fitting in memory is what this course is about.
    """
    n_hashes = len(hashes)
    INF = float("inf")
    # sig[column][hash]. Infinity is the identity for min, so the first real
    # value a column sees always wins without a "have I set this yet" flag.
    sig = [[INF] * n_hashes for _ in columns]

    # The sparse matrix, turned on its side: for each row, which columns have a
    # 1 in it. Built by touching each 1 exactly once. This is what lets the
    # loop below handle a row without asking all N columns whether they contain
    # it, and it is the same thing step 2 of the §3.4.3 procedure does when it
    # sorts the document-shingle pairs by shingle.
    rows_to_cols = [[] for _ in range(n_rows)]
    for c, col in enumerate(columns):
        for r in col:
            rows_to_cols[r].append(c)

    # §3.3.5, one pass. Row r is visited once; its n hash values are computed
    # once and reused for every column that has a 1 in that row. Nothing is
    # sorted and no column is read twice, so rows could arrive from a stream
    # and be discarded immediately after - which is the whole reason to write
    # it this way rather than permuting the matrix.
    for r in range(n_rows):
        hv = [h(r) for h in hashes]
        for c in rows_to_cols[r]:
            col_sig = sig[c]
            for i in range(n_hashes):
                if hv[i] < col_sig[i]:
                    col_sig[i] = hv[i]

    return sig


def lsh_candidates(signatures, bands):
    """Split each signature into `bands` bands and hash each band.

    Two columns are candidates if they land in the same bucket for **at least
    one** band. Return {(i, j), ...} with i < j.

    The signature length must divide evenly by `bands`, or you have to decide
    what to do with the remainder. Say what you decided.
    """
    if bands < 1:
        raise ValueError("bands must be at least 1")
    if not signatures:
        return set()

    n = len(signatures[0])
    if bands > n:
        raise ValueError(f"{bands} bands asked of a signature of length {n}")

    # R5 - my decision. The remainder is spread one row at a time across the
    # leading bands, so every row belongs to exactly one band and no two bands
    # differ in width by more than one. With n=10 and bands=3 that gives 4,3,3.
    #
    # The two alternatives are worse. Dropping the leftover rows throws away
    # signal that was already paid for in hashing. Handing all of them to one
    # band makes that band wide, and a band of r rows has its own step at
    # (1/b)^(1/r), so one fat band turns the S-curve into a blend of two curves
    # that sit far apart. An even split still blends two curves when n % bands
    # is nonzero, but the two are adjacent, so the step stays sharp.
    base, extra = divmod(n, bands)
    edges, start = [], 0
    for band in range(bands):
        width = base + (1 if band < extra else 0)
        edges.append((start, start + width))
        start += width

    # §3.4.1. One bucket space per band. Keying on (band, vector) is exactly
    # what "each band must have its own bucket array" buys: the same vector
    # appearing in two different bands can no longer look like a match.
    # Hashing the tuple itself means equal vectors always collide and unequal
    # ones never do, so §3.4.2's "accidental collisions are rare" caveat does
    # not apply - this is the idealised version of that assumption.
    buckets = {}
    for c, sig in enumerate(signatures):
        for band, (lo, hi) in enumerate(edges):
            buckets.setdefault((band, tuple(sig[lo:hi])), []).append(c)

    # A pair is a candidate if it shared a bucket in at least one band, so the
    # set absorbs the duplicates from pairs that agreed in several bands.
    candidates = set()
    for members in buckets.values():
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                i, j = members[a], members[b]
                candidates.add((i, j) if i < j else (j, i))
    return candidates


# ------------------------------------------------------------------- harness
def columns_from_matrix(matrix):
    n_rows, n_cols = len(matrix), len(matrix[0])
    return [{r for r in range(n_rows) if matrix[r][c]} for c in range(n_cols)]


def verify():
    fails = 0

    def check(label, got, want):
        nonlocal fails
        ok = got == want
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<44} {got}"
              + ("" if ok else f"\n{'':>54}want {want}"))
        fails += not ok

    cols = columns_from_matrix(BOOK)
    try:
        # S1 = {0,3}, S4 = {0,2,3}: intersection 2, union 3
        check("jaccard(S1, S4)", round(jaccard(cols[0], cols[3]), 4), round(2 / 3, 4))
        check("jaccard(S1, S2)", jaccard(cols[0], cols[1]), 0.0)
        check("jaccard on empty sets", jaccard(set(), set()), 0)
    except NotImplementedError:
        print("  jaccard is still a stub"); return 1

    try:
        sig = minhash_signatures(cols, BOOK_HASHES, len(BOOK))
    except NotImplementedError:
        print("  minhash_signatures is still a stub"); return 1

    # Figure 3.4 in the textbook.
    check("signature of S1", sig[0], [1, 0])
    check("signature of S2", sig[1], [3, 2])
    check("signature of S3", sig[2], [0, 0])
    check("signature of S4", sig[3], [1, 0])

    try:
        cands = lsh_candidates([[1, 0], [3, 2], [0, 0], [1, 0]], bands=2)
    except NotImplementedError:
        print("  lsh_candidates is still a stub"); return 1
    # With one row per band, S1 and S4 are identical, so they must collide.
    check("S1 and S4 are candidates", (0, 3) in cands, True)
    check("S1 and S2 are not", (0, 1) in cands, False)

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    if not fails:
        print("  Note that S1 and S4 agree in both signature positions, which "
              "estimates\n  their similarity as 1.0 when it is actually 2/3. "
              "Two hashes is not many.")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
