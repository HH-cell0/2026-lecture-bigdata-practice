# Week 5 · Observations

## Task 1

- Without the fix a dead end's rank goes nowhere (total 1 → 2/3 → 1/6 → 0 by iteration 3); I spread the leaked amount, 1 − sum(β·M·r), equally over all N nodes, which is the same as giving each dead end a link to every node (other options: delete dead ends recursively, or renormalise).
- Both failures are rank that cannot get out (nowhere to go from a dead end, nowhere but the trap from inside it), and giving every node a share every step lets it back out: the trap leaves A 0.15/4 = 0.0375 and the dead-end graph keeps a sum of 1.000000.
- β is the chance the surfer clicks a random out-link of the current page; with 1 − β (0.15) they jump to a uniformly random page instead, on average once every 1/(1 − β) = 6.7 clicks.

## Task 2

- β 0.5/0.7/0.85/0.95/0.99 took 14/17/20/23/24 iterations, because the error shrinks by β·ρ per iteration with ρ = 0.431 set by the 10-node core p00000–p00009, and the bound ln(tol)/ln(β) assumes a |λ2| = 1 part this graph does not have (the 2-node trap has 0 in-links). In a separate run, β 0.999/0.9999/0.99999 all stopped at 24 where that bound predicts 23,014/230,247/2,302,574.
- 1,200 → 20,000 nodes: iterations 20 → 21, time per iteration 1.2 → 23.6–24.0 ms (~18–20× for 17.3× the edges); iterations depend on the shrink rate (same ρ, error curve shifted 2.5× ≈ 1 iteration), time on the work per iteration, which is linear in edges.
- The top-10 set is always p00000–p00009 (76–98% of the rank) and only places 7/8 swap (p00000 ↔ p00004) at β 0.7, so on this graph trust which pages made the top 10, but not a one-place gap, which a chosen β can flip.

## Task 3

- Instead of M: r and nr (2n = 2,400 floats) plus the adjacency list re-indexed to ints (E + n = 5,877 + 1,200 ints, no floats), dividing by out-degree inline, so 1,440,000 / 2,400 = 600× fewer floats.
- Teleport and dead-end columns are a matrix of all 1/n, and (all 1/n)·r is just one number, so each iteration computes the scalar (β·D + 1 − β)/n once (D = rank on the 12 dead ends) and adds it to every node while writing nr: n additions, not n².
- Worst difference 6.94e-17 (952 of 1,200 nodes non-zero), ~7 digits under 1e-9; it is rounding order: adding the dead-end rank interleaved per column like the dense code cuts it to 1.08e-19, and also using (1/deg)·r makes it exactly 0.
