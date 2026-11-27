# Public improvement engines and exact methods for Santa 2026 – The Elf Calculator (state on 2026-11-24)

Read-level tags used on every finding:

- **[src-full]** a source file read in full, at repository HEAD on 2026-11-24
- **[src-part]** a source file read in part (the part is named)
- **[doc]** a README, notice or status document read in full unless a part is named
- **[doc-3p]** a third party's written description of someone else's notebook; not checked against the notebook
- (Inference) marks my own reading or design judgement

What was and was not accessed:

- No kaggle.com page was fetched (round one showed they cannot be read). Everything comes from GitHub raw files. The GitHub REST API returned HTTP 403 "rate limit exceeded", so directory listings were taken from the HTML tree pages; GitHub code search (needs login) was not used. One web search for the engine file name returned nothing relevant.
- `elfopt.cpp` is not in `Hansen0223/Santa_2026`. The only copy found is in `radjapov/santa2026` under `third_party/goodpjw_dag_lns/`. That repository's README calls itself a team's private working repository, although it was readable without login; it labels `third_party/` as public Kaggle code under Apache-2.0 and its loop script names the file as goodpjw2008's code. I read the third-party engine files, the README and one loop script (for run parameters) and nothing else from it. Which dataset version this copy corresponds to is not stated; the run scripts beside it refer to binaries `elfopt3`, `elfopt6` and `elfopt8`.
- No solution or program file (CSV, gz) was downloaded. Source text was read from a temporary directory outside the project, which was deleted afterwards; the session's own tool-output cache (outside the project) still holds the printed text of some files.
- Not read: `anneal_diverse.cpp` (Wang variant), `elf_multiplier_frontier.cpp`, `elf_multiplier_lanes.cpp`, `elf_window.cpp`, `elf_global_schedule.cpp` (only header comments and argument parsing of the first two), `exact_frontier.hpp` (comments only), `arsen_v7/` and `arsen_current/` sources, `run_solver.py`, the guide notebook (not re-read), and all `.json.gz` result archives.

Short names for URLs below: `H/` = `https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/`, `R/` = `https://raw.githubusercontent.com/radjapov/santa2026/HEAD/`.

## 1. The public value-graph search engine (elfopt.cpp) and the C++ engine from "Arithmetic Recipe Pool and MILP": neighbourhoods, replacement search, acceptance, shaking, crossover, 48-register check

### Takeaway

The two engines are different designs. `elfopt.cpp` is a classic LNS: remove the exclusive cone of a group of 1–3 targets (or everything dominated by one shared helper), rebuild with an exact search to depth 4 plus `X·Y ± R` shapes, accept equal cost with probability 0.3, and "kick" by accepting a rebuild up to 1–2 instructions longer. The Wang engine never runs a deep search; it walks on the plateau by swapping single recipes for one-step alternatives under a length cap that cycles through +2, +1, 0, then applies a bit-parallel "delete one value" and "add one new value, delete two" test, and crosses a pool of up to 12 near-best graphs by greedy randomised deletion over their recipe union. Neither repairs a register overflow: both try a few alternative orders and otherwise reject the candidate.

### Cited Findings

#### 1A. elfopt.cpp (goodpjw2008, "DAG LNS")

Source: [elfopt.cpp](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/elfopt.cpp), 855 lines **[src-full]**; run scripts [driver.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/driver.py), [recomb_pass.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/recomb_pass.py), [loop.sh](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/loop.sh), [schedule8.sh](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/schedule8.sh) **[src-full]**.

- **Data model.** The program is replayed into a value DAG with one node per distinct value (the first definition of a repeated value wins); start values come first. Each node keeps its operation, two operand indices and a floating-point `pos` equal to its original instruction index. Nodes not reachable backwards from a target are dropped. Cost is the number of computed nodes. **[src-full]** — [elfopt.cpp](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/elfopt.cpp)
- **Per-node target mask.** For every node the engine computes a 64-bit mask of the computed targets that depend on it (so at most 64 targets). All neighbourhoods are defined through this mask. **[src-full]** — same file
- **Neighbourhood 1, target group.** Given a set G of targets, remove every computed node whose mask is non-empty and a subset of G (the nodes that only targets in G need, including helpers shared only inside G). The nodes to rebuild, Q, are the targets in G that no target outside G depends on. Candidate groups each round: every single target; every distinct mask of 2 to `maxGroup` targets that some node actually has (so only groups that share an exclusive helper); and `nt` random pairs. They are tried in random order. `maxGroup` defaults to 3 (`--group`). **[src-full]** — same file
- **Neighbourhood 2, helper-rooted.** For a non-target node v that at least two targets depend on, remove v together with every node that cannot reach a target without passing through v (computed by a reverse sweep), provided at least two nodes are removed; Q = {v}. The value v is kept and re-derived. Helper moves are tried first in every round, in random order. **[src-full]** — same file
- **Available values.** The pool for the rebuild is every node that is not removed and is not a descendant of any node in Q. It is ordered by `4·fan-out + 8 if start value + random(0..2)`, descending; the order matters because the depth-4 search only uses the first K = 48 pool values on one side (`--K`). **[src-full]** — same file
- **Rebuild budget.** With `rs` nodes removed, the rebuild may use at most `rs − 1` instructions, or `rs` when an equal-cost move is allowed, plus `slack` during a kick. **[src-full]** — same file
- **Sequential rebuild with pool growth.** For |Q| = 1 one order is tried, for 2 both orders, for 3 or more `nOrders` = 3 random orders. Within an order each target is searched in turn with the remaining budget minus one instruction reserved for each later target; the intermediate values of an earlier target are added to the pool before the next one is searched, so later targets can share them. The best order is kept. New steps receive a `pos` just before the rebuilt node's old position. **[src-full]** — same file
- **Single-target search `find(T, maxc)`.** S1 is a hash of every value one operation away from a pool pair (including a+a and a·a), with one recipe kept per value. The search returns the cheapest derivation level by level, with random start offsets for tie-breaking:
  - cost 1: T in S1;
  - cost 2: T = w op x with x in the pool and w in S1 (six inverse forms per x), plus T = h+h and T = s·s;
  - cost 3: T = f op g with f, g in S1; or T = (f op y) op x with x, y in the pool and f in S1;
  - cost 4 (`find4`, switch `--deep`): meet in the middle. A "need" hash holds every w with T = w op g (g in S1) or T = (w op y) op x (x any pool value, y among the first K); then every value u op y with u in S1 and y among the first K is streamed against the hash;
  - cost 5 and above (`findWindow`, switch `--window`): product shapes T = X·Y ± R with X in pool ∪ S1, Y one of the four values nearest T/X in the sorted pool ∪ S1, and R in pool ∪ S1 or built in exactly two steps; also X in the pool with Y = ⌊T/X⌋ or ⌊T/X⌋+1 built in two steps.
  **[src-full]** — same file
- **Pair search `findPair(T1, T2)`** (when |Q| = 2, switch `--pairs`): collect for each target all w with T = w op p (p in pool), T = w+w or T = w·w; a w common to both lists costs cost(w) + 2 with cost(w) ≤ 2; otherwise look for w in S1 that finishes one target in one step and the other in two (total 4). **[src-full]** — same file
- **Rebuilding the DAG.** Kept nodes and new steps are merged and de-duplicated by value (kept definitions win), operands are re-linked by value, and a topological order is produced by a priority queue on `pos`. Dead nodes are removed again. **[src-full]** — same file
- **Acceptance rule.** Per attempt, "equal allowed" is drawn with probability `eqProb` = 0.3 (`--eq`). A strictly smaller DAG is always accepted; an equal one only if drawn; a larger one never, outside a kick. The first accepted move ends the round. The best DAG is stored separately. After more than 200 consecutive rounds that only moved sideways the search returns to the best DAG. If a round finds no move at all, it kicks if kicks remain, otherwise returns to the best and stops after more than three such rounds, even if time is left. **[src-full]** — same file
- **Kick (shaking).** Up to 30 tries: pick one random target, with probability 1/2 add a second, set `slack = kickSlack`, run the target-group move with equal allowed, and take the result only if it is strictly longer than the current DAG. Defaults are `--kicks 0`, `--kslack 1`; the published loops run `--kicks 1000 --kslack 2`. **[src-full]** — same file; [recomb_pass.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/recomb_pass.py); [lns_loop.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/tools/lns_loop.py)
- **48-register check.** `pressure()` walks the current node order and counts live values (a start value occupies a register until its last use; operands that die at an instruction free their register before the write). If the peak exceeds 48, one greedy list schedule is tried: among ready nodes pick the one minimising `(1 if it has users) − (number of operands it frees) + 1e-6·pos`. If the peak is still above 48 the move is rejected; counters `rejP` and `rejPstrict` record how often, the second for moves that would have been strict improvements. There is no recomputation and no repair. Emission assigns the lowest free register. **[src-full]** — same file
- **Crossover.** None inside the engine. With `--dump` it writes every recipe of every accepted DAG; with `--hall 1` also every derivation the searcher found, including ones up to two instructions over budget; with `--alts N` up to N alternative derivations of cost ≤ 3 for each target's exclusive cone. These recipes feed the CP-SAT recombiner in section 2. **[src-full]** — same file
- **Constructor.** `--construct` builds a program from scratch: repeatedly build the cheapest remaining target with the same search, and when nothing is reachable within `--cmax` 5, split the smallest target as T = X·Y ± R with X from the pool, estimating deeper costs as `2 + log2(v)/9`. **[src-full]** — same file
- **Parameters and run time.** Wall-clock limit per puzzle `--time` (default 10 s). The published driver uses 60 s per puzzle and 20 processes; the recombination pass 15–20 s; a third party's loop 15 s for puzzles of 60–180 instructions. The seed is random per shard. **[src-full]** — [driver.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/driver.py); [loop.sh](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/loop.sh); [lns_loop.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/tools/lns_loop.py)
- **Lineage.** "The arithmetic value-DAG search builds on prvsiyan's public work." **[doc]** — [generative/NOTICE.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/NOTICE.md)

Pseudocode of one round (my own wording):

```
analyse(): users[], target mask per node
for v in shuffled(non-target nodes with >=2 dependent targets):      # helper move
    R = {v} + nodes dominated by v;  if |R| < 2: continue
    if try_remove(R, Q=[v], equal_ok = rand < 0.3): accept; goto next round
for G in shuffled(single targets + exclusive-helper groups of 2..maxGroup + random pairs):
    R = nodes whose mask is a subset of G;  Q = targets of G not needed outside G
    if try_remove(R, Q, equal_ok = rand < 0.3): accept; goto next round
no move: kick if allowed, else return to best (stop after 4 such rounds)

try_remove(R, Q, equal_ok):
    budget = |R| - (0 if equal_ok else 1) + slack
    pool = nodes not in R and not descendants of Q, sorted by fan-out
    for each order of Q (1, 2 or 3 orders):
        steps = []
        for q in order: part = find(value(q), remaining budget - 1 per later target)
                        fail if none; steps += part; add part's values to pool
    if |Q| == 2: also findPair
    new DAG = kept nodes + best steps; reject if longer than allowed
    reject if live values > 48 after one greedy re-schedule
```

#### 1B. Wang Jakie's engine ("Arithmetic Recipe Pool and MILP", notebook version 5)

Source: [common.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/common.inc), [compact.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/compact.inc), [cross.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/cross.inc), [fast_perturb.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/fast_perturb.inc), [cache_perturb.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/cache_perturb.inc), [cache_lookup.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/cache_lookup.inc), [neutral.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/neutral.inc), [anneal.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/anneal.cpp), [incremental.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/incremental.cpp), [compact_rotate.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/compact_rotate.cpp), [main.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/main.inc) **[src-full]**; `anneal_seeded.cpp` read as a diff against `anneal.cpp` **[src-full]**; about 1,300 lines in total. The mirror states the original files are reproduced unmodified. **[doc]** — [wang/NOTICE.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/NOTICE.md)

- **Data model.** A graph is a hash map `value → (op, a, b)`; cost is the number of computed values reached by a depth-first walk from the targets. The walk fails on a cycle or a missing definition, so every edit is validated by re-walking, and unused values disappear automatically. **[src-full]** — [common.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/common.inc)
- **Main loop (`anneal`, `incremental`).** The run length is a round count, not a time limit. One round = shake, rebuild one small cone, compile, deletion test, pool update, and every fifth round a crossover. The length cap relative to the best program follows a fixed nine-round cycle: +1, +2, +2, +1, +1, +1, 0, 0, 0. The working graph restarts from the champion at cycle position 0 and jumps to a random pool member at position 5. A candidate that fails to compile or exceeds the cap resets the working graph to the champion. There is no temperature and no random acceptance of worse moves. **[src-full]** — [anneal.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/anneal.cpp)
- **Shaking (`perturb`).** Build a table of every value not in the graph that is one operation away from two live values (all recipes kept per value). Then for computed values v in random order, and for a live value `fixed` taken from a random rotation, form each of the six ways to write v with `fixed` as one operand; the other operand is `need`.
  - If `need` is already live: with probability 1/4 rewire v to (`fixed`, `need`).
  - Otherwise, if v has a private computed operand or the cap leaves slack: sample one recipe for `need` from the table and try v = `fixed` op `need` with `need` added as a new value. With no slack the swap is only tried when a private operand of the old recipe would become unused.
  - An edit stands only if the graph stays acyclic and within the cap. At most 12 attempts per v; the shake stops after 3–10 successful swaps (`3 + rng() % 8`).
  **[src-full]** — [fast_perturb.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/fast_perturb.inc)
- **`incremental` variant.** Same moves; the one-step table is kept between rounds and only pairs involving newly seen values are added; it is rebuilt when the indexed set exceeds 1.25 × live values + 15. Sampling skips recipes whose operands are no longer live. **[src-full]** — [cache_lookup.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/cache_lookup.inc); [cache_perturb.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/cache_perturb.inc)
- **Small-cone rebuild (`rotate`).** For a value v in random order, the cut is v plus its private ancestors; cuts smaller than 3 are skipped, and at most 12 qualifying roots are scanned. Banned values are the cut and all its descendants. v is rebuilt with exactly three instructions in one of two shapes, each limited to 12 trials: "balanced" v = a op b with a and b both new one-step values (a drawn from one-step results of the first 24 allowed values, cut leaves first); "chain" v = b op x, b = a op y, a one step from allowed values, with x, y among the first 32 allowed values. This shortens the program when the cut had more than three nodes and is a sideways move when it had three. **[src-full]** — [anneal.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/anneal.cpp)
- **Deletion test (`knockout`).** Works when starts plus live values number at most 512.
  1. `direct[v]` = every one-operation recipe for an existing value v from two existing values (all pairs).
  2. Library of new "middle" values x: one operation from two existing values and either producible by two different pairs, or equal to half or the square root of an existing computed value. Each middle stores how it can be made and which existing values it can make with one other existing value (obtained by reversing each identity, so no second all-pairs scan).
  3. Bit-parallel closure: one bit per deletable (non-target) value d; `row[v]` bit d means "v is still derivable when d is removed". If some d leaves all targets derivable, rebuild without d: one instruction saved.
  4. Otherwise, for each middle h in random order, compute the set of d that become deletable once h is added. If the set has at least two members, try adding h and removing one, then removing each pair: net one instruction saved.
  5. In "neighbors" mode it instead returns equal-length graphs in which one old value is exchanged for one middle.
  **[src-full]** — [compact.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/compact.inc)
- **Crossover of programs of the same puzzle (`crossover`).** No solver is involved.
  1. Value set = starts ∪ live values of the champion ∪ live values of every pool graph.
  2. Recipe set = each graph's own recipes plus every one-operation recipe between two values of the set that yields a value of the set.
  3. Seven attempts. Give each non-target value a key: pure random on attempts 0, 3, 6; otherwise random + 0.22 or 0.09 × (number of pool graphs containing it). In ascending key order, ban the value and keep the ban if all targets remain derivable by forward closure (first available recipe per value).
  4. The surviving set defines a graph; it is accepted if it has fewer computed values than the best program and compiles into 48 registers.
  **[src-full]** — [cross.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/cross.inc)
- **Pool.** Working graphs within one instruction of the best are pushed into the pool after each round; above 12 entries one of the five oldest is removed at random. Crossover runs every fifth round once the pool holds four graphs. **[src-full]** — [anneal.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/anneal.cpp)
- **Seeded variant.** `anneal_seeded.cpp` adds one loop that puts the graphs of the other supplied programs of the same puzzle into the pool before the first round. GoodPJW's version 10 package contains 18 C++ and include files, 16 byte-identical to Wang's; its driver picks at most 4 different historical programs, each at most 3 instructions longer than the parent, and cycles strategies and seeds. The idea of pre-loading parents is credited to E-Max AI (RoyalAceCat). **[src-full]** for the diff; **[doc]** — [goodpjw-incremental README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/goodpjw-incremental/README.md)
- **`compact_rotate` (older strategy).** No slack: every fourth round restart from the champion, every third round a neutral "diversify" (the same recipe swap restricted to exchanges that keep the length), then rotate, compile, knockout; a population of five graphs is crossed and the three oldest dropped. **[src-full]** — [compact_rotate.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/compact_rotate.cpp); [neutral.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/neutral.inc)
- **48-register check (`compile`).** Order = depth-first post-order from the targets in their current (shuffled) order. Allocation frees an operand's register at its last use before choosing the destination and fails if none is free. On failure: one greedy "pressure" order (ready node minimising `has consumers − operands released`), then up to 18 further depth-first orders with reversed and then randomly shuffled target order. If all fail the candidate is dropped. No recomputation. **[src-full]** — [common.inc](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/common.inc)
- **Run time.** 50 puzzles averaging 113 instructions, 360 rounds each: 100.2 s cumulative wall time for the single-parent arm and 100.3 s for the crossover arm, about 2 s per puzzle. **[doc]** — [fresh-public-recombination README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/fresh-public-recombination/README.md)
- **Round counts in use.** 35 (adapter default), 180, 220, 360 and 680 in the collaboration's experiments; 1,500 and 3,000 in GoodPJW's schedule, which alternates `anneal_diverse`, `anneal_seeded` and `incremental_diverse` with up to 8 seed programs and a plateau archive of equal or near-length alternatives used as new starting points. **[doc]** — [wang/NOTICE.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/wang/NOTICE.md); **[src-full]** — [schedule8.sh](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/schedule8.sh)

Pseudocode of the main loop (my own wording):

```
best = input program; champion = graph(best); work = champion; pool = []
for turn in 0 .. rounds-1:
    c = turn mod 9
    if c == 0: work = champion
    elif c == 5 and pool: work = random(pool)
    cap = len(best) + [1,2,2,1,1,1,0,0,0][c]
    shake(work, cap, swaps = 3..10)          # one-step recipe swaps
    rebuild_one_cone(work, cap)              # 3-instruction balanced/chain templates
    prog = compile(work)                     # 48 registers, several orders
    if prog is None or len(prog) > cap: work = champion; continue
    if len(prog) < len(best): best, champion = prog, work
    if deletion_test(work, prog) and len(prog) < len(best): best, champion = prog, work
    if len(prog) <= len(best) + 1: pool.push(work); keep at most 12
    if turn mod 5 == 4 and len(pool) >= 4:
        if crossover(champion, pool) finds shorter: champion = work = result
```

#### 1C. Measured gains of these engines

No README gives a date for an individual run. All figures below come from `Hansen0223/Santa_2026`, whose independent line went from 146,435 on 2026-11-19 21:44 BJT to 139,271 on 2026-11-24 13:38 BJT (round-one notes), so every run lies inside that window.

- GoodPJW release 5 engine on independent programs: 142,219 → 141,890 (329 saved, 218 puzzles); on publicly attributed programs: 135,222 → 135,167 (55 saved, 42 puzzles). Each puzzle's search received only its own parent program. **[doc]** — [methods.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/methods.md)
- Wang engine as packaged in GoodPJW release 10, 16 independent puzzles, 180 rounds per arm: single-parent incremental 2 puzzles / 3 saved; multi-parent incremental 3 / 3; multi-parent anneal 3 / 4; independent line 140,811 → 140,805. On 269 further puzzles (807 searches): single-parent incremental 38, multi-parent incremental 24, multi-parent anneal 28; best per puzzle 46 puzzles / 60 saved; 140,811 → 140,745 including the pilot. Extra parents helped one puzzle and hurt another. **[doc]** — [goodpjw-incremental README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/goodpjw-incremental/README.md)
- Wang multi-parent search, 680 rounds, on 25 puzzles with parents from a collaborator's independently built programs: 21 puzzles / 129 saved on the independent line, 8 puzzles / 39 on the public-assisted line. A second round on the same puzzles: 11 puzzles / 18. **[doc]** — [recipe-union README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/recipe-union/README.md)
- 50 freshly merged public rows (frozen total 134,324), 360 rounds: single-parent saved 2, external-parent crossover saved 3; 134,324 → 134,321. **[doc]** — [fresh-public-recombination README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/fresh-public-recombination/README.md)
- Four local rewrites applied after annealing (group rewrite, intermediate replacement, factorisation with remainder, costed recipe combination), in both orders: 170 independent puzzles, 16 puzzles / 32 saved on a 141,026 parent; 5 puzzles / 6 on a 134,430 public parent in the pilot and 0 on its 13 hold-out puzzles. **[doc]** — [wang-polish README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/wang-polish/README.md)
- Zero results: a same-score public version (128,492) crossed with the 128,49x merge on 47 puzzles; near-tie public programs (at most two instructions longer) on 553 puzzles at 128,494, with and without enumerated extra recipes; 57 puzzles whose intermediate sets differ by at least four values under three equal-round search orders. **[doc]** — [recipe-union README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/recipe-union/README.md)
- Another team: a private Rust LNS improved 1 of 100 medium puzzles (129 → 128) at 132,542. **[doc-3p]** — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)

### Inferences

- (Inference) Round one's "1.8 seconds per group" is most likely a misreading. In the engine `--group` is the maximum target-group size and `--time` is a per-puzzle wall-clock limit, so the pilot compared `--group 3` against `--group 8` and each arm got 1.8 s. A full pass over 1,000 puzzles at that setting is about half a CPU-hour, which matters when judging the 329-instruction gain.
- (Inference) `find4` does not cover every four-instruction shape. It finds ((u op y) op g) and (((u op y) op y′) op x) with u, g in S1; it does not find (f op g) op x with f, g in S1, nor shapes that reuse an intermediate twice. A complete depth-4 table is therefore not what produced the public gains.
- (Inference) Mapping to the user's existing search. Already present: the helper-rooted move (remove private ancestors, re-derive the node), equal-cost acceptance, and a topological-order register check. Missing, in the order the sources support them:
  1. Target-group move: remove everything used only by a group of 2–3 targets that share an exclusive helper, rebuild them one after another while adding each rebuilt target's intermediates to the pool, plus the two-target shared-helper search.
  2. Kick: accept a rebuild 1–2 instructions longer for one or two random targets, keep the best separately, return to it after 200 sideways rounds.
  3. Plateau walk by one-step recipe swap (v = fixed op need with `need` a new value one operation from live values), under a cap that cycles +2/+1/0. It costs microseconds per edit and changes the set of intermediate values, which is what the later deletion test and crossover feed on.
  4. Bit-parallel deletion test, and the "add one middle value, delete two" exchange.
  5. A pool of up to 12 near-best graphs with greedy randomised deletion over the union of their values and all one-step recipes among those values.
- (Inference) The greedy crossover is a cheap stand-in for the CP-SAT model of section 2: same pool (values of several graphs plus all one-operation recipes among them), same objective (fewest values), but a randomised inclusion-minimal solution instead of an optimal one. It runs inside the search loop every five rounds, which a solver call cannot.
- (Inference) Neither engine spends effort on registers. Both reject on overflow after a handful of orders. If the user's search already rejects on a failed topological order, adding the greedy "frees most registers first" order and a few shuffled depth-first orders is all the public engines do.

### Gaps

- Which GoodPJW dataset version the mirrored `elfopt.cpp` corresponds to is unknown; release 5 (the one measured at 329) may differ.
- `anneal_diverse.cpp` (pool binned by number of shared target ancestors and chain depth) and the `incremental_diverse` strategy were not read.
- No source gives the acceptance rate, the share of gains per move type, or the per-round time of `elfopt.cpp` on a given program length.
- prvsiyan's earlier work that `elfopt.cpp` builds on was not located.

## 2. The CP-SAT/MILP recipe recombiner: variables, constraints, cycle prevention, extra recipes, limits, and what happens when the selection does not fit 48 registers

### Takeaway

All public recombiners use the same model: one Boolean per value, one Boolean per recipe, "a chosen recipe needs its operands", "a built value has exactly one chosen recipe", targets forced, minimise the number of values, with cycles prevented by an integer level per value. They differ in the pool. Recombining existing recipes alone is worth almost nothing (7 instructions at 141.6k for a single parent, 0 on most public tests); the measured 58 comes from adding up to 24 new helper values ranked by how many old instructions they make removable. A selection that does not schedule into 48 registers is simply discarded; only Arsen's code tries a recomputing compiler first.

### Cited Findings

#### 2A. Arsen Zakaryan's version 15 recombiner

Source: [recombine2026.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/recombine2026.py), [recipe_milp.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/recipe_milp.py) **[src-full]**; the mirror records both as unmodified with SHA-256 hashes. **[doc]** — [SOURCE.json](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/SOURCE.json)

- **Input programs.** Distinct programs for the puzzle, sorted by length; those within `slack` = 3 instructions of the shortest, at most 12. The shortest is the "primary". **[src-full]** — [recombine2026.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/recombine2026.py)
- **Pool (`make_pool`).** Values = starts ∪ every value computed by any input program. Recipes per value = the recipe each program uses, plus every a+b, |a−b|, a·b and exact quotient of two pool values that equals a pool value (all pairs), excluding recipes that use the value itself. Commutative recipes are stored in canonical operand order. **[src-full]** — [recipe_milp.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/recipe_milp.py)
- **Extra values (`helpers`).** New values h not in the pool, one operation from two values of the primary program (at most two witnesses kept per h), such that some primary value v equals h op a for a primary value a. They are ranked by the number of different v they serve and the top `helpers` are added with their making and using recipes. The default is 0 in `recombine2026.py` and 300 in the older `recipe_milp.py`. **[src-full]** — same file
- **Model.** For each non-start pool value v: Boolean `active[v]`, integer `depth[v]` in 0..n. For each recipe r of v: Boolean `selected[v,r]`. Constraints: `selected[v,r] ⇒ active[p]` and `depth[v] > depth[p]` (enforced only if selected) for each non-start operand p; `Σ_r selected[v,r] = active[v]`; `active[t] = 1` for targets; `Σ active ≤` size of the primary graph. Objective: `(n+1)·Σ active + Σ selected recipes that differ from the primary's`. The primary program is given as a hint, including depths. **[src-full]** — [recombine2026.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/recombine2026.py)
- **Cycle prevention.** The integer depth per value with a strict inequality along every selected recipe; no cut generation in this file. **[src-full]** — same file
- **Solver settings.** One worker, random seed 20261120, `max_deterministic_time = budget` (default 2.0). **[src-full]** — same file
- **Scheduling.** Only if the selected graph has fewer values than the best program, 15 schedules are tried. Three are list schedules without recomputation, with priorities (rank in primary), (registers gained − registers freed, rank) and (that delta, −fan-out, bit length); they fail when no register is free. Twelve use `compile_graph`: depth-first order from the targets (original, reversed or shuffled), emit on demand, and when no register is free evict the live non-start value with the largest `distance to next use / (1 + rebuild cost)^1.5` (odd seeds) or the largest distance (even seeds); an evicted value is recomputed when needed again. Compilation aborts once the program reaches the incumbent's length. A candidate is kept only if its replayed length is strictly shorter. **[src-full]** — [recombine2026.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/recombine2026.py); [recipe_milp.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/recipe_milp.py)
- **If nothing schedules.** The incumbent is returned. Nothing is fed back to the model. **[src-full]** — same files
- **Older selectors in `recipe_milp.py`.** (a) Ordered MILP: fix a topological order of the pool (four orders: primary rank with unknown values first, primary rank with unknown values last, bit length, random), keep only recipes consistent with it, find mandatory values, and solve a node-presence MILP with auxiliary conjunction variables in SciPy/HiGHS, `node_limit` 200. (b) Unordered MILP with lazy cycle cuts: solve, find strongly connected components among chosen recipes, and for each cyclic component of k values add "at most k−1 chosen recipes of these values may read inside the component"; up to 20 rounds, 10 s per solve. (c) The CP-SAT model above without the penalty term. **[src-full]** — [recipe_milp.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/recipe_milp.py)

#### 2B. Local "paid helper" ranking added by Hansen0223

Source: [paid_helpers.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_v15/paid_helpers.py) **[src-full]**.

- For every existing value v, `private[v]` is the set of non-target computed values used only inside v's derivation. Candidate new values h are all one-operation results of two existing values that are not yet present. A use is (v, c) with v = h op c, c existing and not depending on v, and c not already covering all of v's private set. For each way to make h, the saving is the union over its uses of `private[v]` minus what the making recipe or c still needs, so each removable instruction is counted once. Candidates are ranked by removable instructions, then by number of uses; the top 24 contribute their recipes as `extra` to the CP-SAT model, run with a single parent. **[src-full]** — same file
- "Our ranking counts old instructions that can be removed, excludes any still needed to construct the replacement, and counts each removable instruction once across all uses." **[doc]** — [methods.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/methods.md)

#### 2C. GoodPJW's recombiner

Source: [recombine.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/recombine.py), [recomb_pass.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/recomb_pass.py) **[src-full]**.

- **Pool.** Recipes harvested by the LNS during its run (section 1A, `--dump`, in production with `--hall 1`), the current best program's recipes, and the recipes of every bank program at most 3 instructions longer than the best. Then "cross recipes": every a op b = v with a, b and v all in the value set. **[src-full]** — same files
- **Bridge values (optional).** New w = a op b not in the set such that at least two different existing values equal w op c for an existing c; up to 3,000, ranked by number of uses. The production pass calls the recombiner with `bridge=False`. **[src-full]** — same files
- **Model.** Boolean x per value, integer level in 1..|V|+1, Boolean y per recipe; y ⇒ x of each operand; level[v] ≥ level[o] + 1 when y is chosen; Σ y = x; targets forced; minimise Σ x. Hints from the best program. An optional mode fixes the topological order to the best program's and drops the level variables. **[src-full]** — [recombine.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/recombine.py)
- **Limits.** Wall-clock `max_time_in_seconds` 20 by default, 25 in the published loop; one worker. **[src-full]** — [loop.sh](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/loop.sh)
- **Scheduling.** One greedy list schedule (registers freed first, then level) and linear-scan allocation; if more than 48 values are live the function returns nothing and the puzzle keeps its program. **[src-full]** — [recombine.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/recombine.py)
- **Pipeline.** One pass = LNS for 15–20 s per puzzle with kicks and harvesting, also started from up to 2 distinct bank programs at most 1 instruction longer than the best, then CP-SAT per puzzle. In the long-running schedule this pass runs once every eight iterations on a "focus" list; the other iterations run Atakan's optimizers and Wang's strategies. **[src-full]** — [recomb_pass.py](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/recomb_pass.py); [schedule8.sh](https://raw.githubusercontent.com/radjapov/santa2026/HEAD/third_party/goodpjw_dag_lns/schedule8.sh)

#### 2D. Measured results

- Arsen v15 on the independent parent 141,613, single parent, deterministic-time budget 0.22 per call: zero helpers saved 7; the published ranking with 24 helpers saved 20; the local ranking with 24 helpers saved 51; best per puzzle 55; a repeat on the winners 3 more; total 58 on 51 puzzles → 141,555. On the public parent 135,161: 2, 9, 17; best per puzzle plus a repeat on the 20 changed programs 23 → 135,138. "An optimal CP-SAT status applies to the enumerated recipes." **[doc]** — [methods.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/methods.md)
- A wider pool did nothing: the published ranking with 96 helpers and the local ranking with 8 helpers each gave zero on 160 public puzzles at the same budget. **[doc]** — same file
- Two public versions merged (existing recipes; plus up to 24 helpers; plus reverse-derived recipes), 0.65 s per puzzle, 96 puzzles, 288 searches: zero. **[doc]** — [release-crossover README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/release-crossover/README.md)
- Union of several parents' recipes, two search forms, 96 puzzles on each line: zero. Choosing a parent per target for whole derivation cones (54 puzzles, optimal within the candidate sub-graphs): zero. **[doc]** — [recipe-union README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/recipe-union/README.md)
- Values borrowed from other programs with extra recipes enumerated over them: independent 607 puzzles, 5 puzzles / 6 saved, all from the newly enumerated recipes; public 230 puzzles, zero. **[doc]** — same file
- Forcing the model to abandon at least 2 or 6 of the current intermediates while allowing up to 2 extra instructions, then continuing the search from that program: independent 607 puzzles, 36 puzzles / 42 saved, 16 of them beating direct search with the same seed and rounds; public 112 and 130 puzzles, zero. **[doc]** — same file
- Minimum-cut mixing of two parents at chosen boundary values: independent 614 puzzles, 9 puzzles / 10 saved; public 160, zero. **[doc]** — same file
- Ranking new values by the drop in an LP relaxation: 144 integer selections, all optimal within the given recipe sets, no real puzzle shortened; a planted two-target example went from 6 to 3. **[doc]** — [helper-pricing README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/helper-pricing/README.md)
- Another team: CP-SAT crossover over eight trajectory portfolios saved zero on 100 puzzles at 132,542; a Kaggle author is reported to have found no fixed-universe extraction below the incumbent on 973 puzzles. **[doc-3p]** — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)

### Inferences

- (Inference) The model is small enough to copy exactly: values are labels, so 60-bit arithmetic never enters the solver. With 100–150 values per program and up to 12 programs, the all-pairs recipe scan is at most a few million hash lookups.
- (Inference) The pool decides everything. Ordered by measured effect on 140k-level programs: recipes of existing programs (about 0–7); all one-step recipes among existing values (included in that figure); new values that connect two or more existing values (20); new values ranked by removable private instructions (51); recipes harvested during an LNS run, including rejected over-budget derivations (GoodPJW's production choice, no isolated measurement found).
- (Inference) For the user's five solvers the closest tested analogue is "values borrowed from other programs plus enumerated recipes" (6 saved on 607 puzzles) and "forced alternates followed by search" (42 saved). The recombiner pays mainly as a generator of structurally different starting points for the LNS, not as a final optimiser.
- (Inference) The deterministic-time budget of 0.22 and the 0.65 s limit show these models solve to optimality almost instantly at this size; a 1–5 minute limit per puzzle, as round one proposed, is unnecessary unless thousands of new helper values are added.
- (Inference) Register failure after selection has no public remedy beyond trying more orders and a recomputing compiler. Since the model minimises values and not live range, adding a second objective term or re-solving with the offending value set excluded would be new work.

### Gaps

- How often a CP-SAT-optimal selection failed to schedule is not reported in any file read; the per-puzzle statistics are in archives that were not opened.
- No isolated measurement of GoodPJW's harvest-then-recombine pass was found; its notebook titles ("LNS + CP-SAT Recombine | LB 135,921") mix both stages.
- `arsen_current/` (depth-four cuts with mixed-integer recipe selection) and `component_select.py` (Boolean graph selection by independent components) were not read.

## 3. "Joint Recipes for Large Puzzles" (bundle re-pricing) and the withheld-target move: procedures, re-pricing search, and when they gained

### Takeaway

The bundle move as published is not a deep search around a cut. It is simulated annealing over recipe choices in an enriched pool, with one compound move that redirects every user of a value with 2–5 uses to an alternative recipe so the value and its private ancestors die together, and one that makes up to three nodes adopt a newly added helper. The withheld-target move drops the target with the largest private cone (or 2–3 targets with the most shared exclusive work), optimises the smaller puzzle with the Wang engine, re-attaches the dropped targets with one- or two-step derivations if that beats restoring their old cones, accepts up to 3 instructions over the old length, and optimises again. Both gained on 140k-level independent programs and nothing on public programs at 128k–134k.

### Cited Findings

#### 3A. Atakan Aldemir's whole-graph search (notebook version 15)

Source: [elf_whole_graph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/atakan_v15/elf_whole_graph.cpp), 445 lines **[src-full]**; the mirror records the file as byte-identical to the notebook's embedded source. **[doc]** — [atakan_v15/SOURCE.json](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/atakan_v15/SOURCE.json)

- **Pool construction.** Nodes are the values of the input program, each with a list of alternative recipes; index 0 is the incumbent recipe. **[src-full]** — same file
- **Enrichment (`enrich(breadth, rounds, rng, style)`), per round:**
  1. Compute each node's private-cone size under the incumbent recipes.
  2. All pairs of nodes under the four operations: a result that is an existing computed node becomes an alternative recipe for it (cap 17, later 25); a result that is new goes into a draft table with up to three recipes.
  3. Promotion: for every computed node r and other node b, every inverse x with r = x op b that is in the draft is a candidate helper; its utility adds `min(private size of r, 6)` once per r. Candidates need utility ≥ 2 or two different roots, are ranked by `utility + (style mod 3 + 1) × distinct roots` with a random tie-break, and the top `breadth` are added as nodes with their recipes and the recipes that use them.
  4. "Bonds" (style ≥ 3, first round): for nodes with private size ≥ 3, sample draft values x and test whether t − x, t + x or t / x is also a draft value; if so both are added and the node gets the recipe x op y. At most 6 per node.
  **[src-full]** — same file
- **State and cost.** One recipe index per node. Cost is the number of computed nodes reached from the targets; a cycle returns a sentinel cost and the cycle's node list. **[src-full]** — same file
- **Moves.**
  1. Fan-out retirement (style ≥ 3, one step in five): pick a random live value v with 2–5 users; switch every user to its best alternative recipe that does not read v, scoring `4 × (operands already live) + random(0..6)`; abort if any user has no alternative; at least two users must change.
  2. Hub adoption (style > 0, one step in seven): pick a newly added helper with at least two supporting recipes and switch up to three live nodes to recipes that read it.
  3. Single change: a random live node with more than one recipe takes another recipe, three times out of four biased toward recipes whose operands are already live; every ninth step (style ≥ 2) one operand's recipe is re-drawn as well.
  4. Cycle repair (style > 0): up to three times, pick a node on the reported cycle that has a recipe avoiding all cycle members and switch it.
  **[src-full]** — same file
- **Acceptance.** Metropolis: accept if cost does not rise (style 0 only strict decreases), else with probability `exp(−Δ/T)`. T starts each epoch at 1.55 (style ≥ 2) or 0.85 and decays geometrically to 2.5% of that; an epoch is `max(128, steps/4)` steps and each epoch restarts from the best state. `worlds` outer restarts rebuild and re-enrich the pool from the best program so far. **[src-full]** — same file
- **Registers.** Whenever the graph cost drops below the best program length (and every 19th step on ties), the graph is frozen and up to 24 schedules are tried; a physical program is kept only if shorter. **[src-full]** — same file
- **Command line.** `width layers steps worlds mode seed`; mode ≥ 9 only prints the enriched pool. **[src-full]** — same file

#### 3B. Multiplier lanes, multiplier frontier and later versions

Only the header comments and argument parsing of [elf_multiplier_frontier.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/atakan_v15/elf_multiplier_frontier.cpp) and the comment lines of [elf_multiplier_lanes.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/atakan_v15/elf_multiplier_lanes.cpp) were read **[src-part]**; the mechanism below is another team's description of the notebook's decoded source **[doc-3p]** — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md).

- Lanes: "Rewrite several target chains around a single, explicitly paid multiplier." **[src-part]** Factors are proposed from existing multipliers, quotients, common divisors and new one-write values; a factor is supported by quotient-and-remainder witnesses at several roots; root rewrites are grouped by factor into packets (up to four to seven roots), every constructed value is interned once, and the union is priced against the complete reachable graph. Packets that do not improve alone are kept because they may pay when more roots join. **[doc-3p]**
- Frontier: "Explore several physically equal-cost arithmetic graphs in parallel." **[src-part]** Arguments are `frontier_width node_budget packet_width depth style salt`. It keeps a beam of equal-length programs de-duplicated by a graph fingerprint and grafts backward recipe slices from different surviving branches. **[src-part]** and **[doc-3p]**
- Author's own measurements, on the author's inherited programs, not reproduced by the describing team: V14 lanes 138,905 → 138,769 (136 across 88 of 635 selected puzzles); same puzzles and parameters, single-root rewrites saved 5 and same-factor packets 10; V15 frontier 138,769 → 138,681 (88 across 60 of 238 puzzles); V16 block rebuild with cuts of four to eight targets 138,681 → 138,667 (14 in 13 puzzles, 1.9 s per puzzle); the "V30" interface and numeric-splice work 138,280 → 138,273. **[doc-3p]** — same note
- The V15 cohort is puzzles with at least 25 targets, largest start value at most 100 and largest target of 50–59 bits. **[doc]** — [atakan-frontier README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/atakan-frontier/README.md)
- Reproduction by the collaboration, width 4, 14-state budget, packet size 4, depth 6: independent parent 140,745 → 140,736 (8 puzzles, 9 instructions out of 120 tested); 0 of 24 public puzzles at 134,311. **[doc]** — same README
- Zero results for the later mechanisms: interface closure, joint interface and relay searches at 900 ms per case on 54 + 54 puzzles; two joint-interface searches on 72 + 72 puzzles with 60 cuts each; multi-target block search on 24 + 32 puzzles. **[doc]** — same README
- The notebook author's own later controls: joint-interface pilot zero gains on 40 cases despite 9,419 removable ports; relay and outside-alias pilots zero; the "retire every direct consumer" coalition variant saved one instruction in 72 cases. **[doc-3p]** — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)
- A diagnostic on a 132.5k portfolio: 31,320 non-target helpers with fan-out at least three; 5,364 of their consumers have an alternative single-operation recipe independent of the helper, but no helper has its entire consumer set covered. A two-root factor-packet probe (20,345 one- or two-operation factor families, 11,949 pair evaluations) found no smaller graph. **[doc-3p]** — same note

#### 3C. Withheld targets

Source: [compare.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/withheld-targets/compare.py), [design.json](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/withheld-targets/design.json) **[src-full]**; [README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/withheld-targets/README.md) **[doc]**. The search engine is Wang's unmodified `incremental.cpp`. **[src-full]** — [reactive-tabu/build.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/reactive-tabu/build.py)

- **Eligibility.** 6 to 45 distinct targets outside the start values, at least 35 instructions, not already proven optimal, a target with at least two exclusive operations, and a group of two or three targets with at least four jointly exclusive operations. **[src-full]** — [design.json](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/withheld-targets/design.json)
- **Choosing what to withhold.** For every value compute the set of targets whose derivation contains it, and count values per set. "One": the target with the most values used by it alone. "Group": over all pairs and triples, `shared` = values used by exactly two (or all three) of them, `cost` = shared + their private values; choose the maximum of (shared, cost per target, cost) with cost ≥ 4. **[src-full]** — [compare.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/withheld-targets/compare.py)
- **Procedure.**
  1. Reduced puzzle = original without the withheld targets. Its starting program is the old graph restricted to the remaining targets, recompiled.
  2. Run the engine on the reduced puzzle: 220 rounds, seed 1.
  3. Re-attach (`repair`). Initial graph = old recipes overlaid with the optimised reduced program's recipes, which brings back each withheld target with its old derivation. Then, in both orders of the withheld targets, for each target t and each start or backbone value c, take every inverse w with t = w op c: if w is a start or backbone value, patch t in one step; if w is one operation from two such values, patch in two steps. Keep the patch that most reduces the live graph. Compile both the initial and the patched graph, take the shorter (the later one on ties), and accept it if it is at most 3 instructions longer than the original program, otherwise fall back to the original.
  4. Run the engine on the full puzzle from that program: 220 rounds, seed 2. Result = shortest of original, re-attached and final.
  5. Control arm: two full-puzzle passes of 220 rounds with the same two seeds.
  **[src-full]** — same file
- **Results.** Independent line: development 8 puzzles, 2 puzzles / 3 saved; hold-out 16 puzzles, 7 puzzles / 9 saved, all 7 strictly better than the control. Public-assisted line: no direct gain in groups of the same size. Extension to 873 further independent puzzles: best per puzzle 132 puzzles / 194 saved; the control alone 90; single-target removal 116; group removal 102; 73 puzzles where a rebuild beat the control, worth 104 beyond it; 140,663 → 140,469. **[doc]** — [withheld-targets README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/withheld-targets/README.md)
- **Related variants in the same folder.** Keep each target's last three layers or its whole private branch, treat the values they need as new targets, shorten the prefix, re-join: 144 independent puzzles, 6 saved (all from the private-branch form); public line zero. Reverse deletion of helpers from an enlarged prefix on 40 + 40 puzzles: zero. **[doc]** — same README
- **Temporary targets (the opposite move).** Attach the derivation of an intermediate value from an older program of the same puzzle that the current program does not use, require it as an extra target for 160 rounds, drop the requirement, search 160 more rounds. Independent line: 19 puzzles / 28 saved over three groups, down to 140,694, with five to six puzzles where forcing the value beat both controls (same recipe attached but not forced; random value forced). Public line: 4 saved on three puzzles, to 134,178. **[doc]** — [temporary-targets README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/temporary-targets/README.md)

Pseudocode of the withheld-target move (my own wording):

```
D = target with largest private cone, or 2-3 targets maximising (shared exclusive ops, ops per target)
P1 = restrict(old_graph, targets - D); compile
P1 = search(reduced puzzle, P1, rounds=220)
G  = old_graph overlaid with graph(P1)                 # D returns with its old cones
for order in (D, reversed D):
    for t in order:
        for c in starts + values(P1), for w with t = w op c:
            if w available: try {t = w op c}
            elif w is one op from two available values: try {w, t}
        keep the patch giving the smallest live graph
P2 = shortest compiled candidate; if len(P2) > len(old) + 3: P2 = old
P3 = search(full puzzle, P2, rounds=220)
return shortest(old, P2, P3)
```

### Inferences

- (Inference) The user's existing move "forbid a shared intermediate and re-derive its users without it" is the search-based counterpart of the fan-out retirement. The public version differs in two ways: alternatives come from a pre-built pool that already contains helper values serving several nodes, so all users are switched in one step; and the result is judged by Metropolis, so a retirement that costs +1 can be kept and repaid later.
- (Inference) The enrichment step is the part worth copying into a value-graph search: rank candidate new values by the summed private-cone size of the nodes they could re-derive, capped at 6 per node, and add both their making recipes and their using recipes. It is the same idea as the "paid helper" ranking in section 2B, reached independently by two authors.
- (Inference) Evidence that packets matter more than depth: the only matched ablation found gives 5 saved for single-root rewrites against 10 for same-factor packets, and the guide's exact depth-5 re-pricing of a cut (round one) gave zero. A wider or deeper re-pricing search is not what the public gains came from.
- (Inference) The withheld-target gain is partly a diversification effect: the control with the same rounds saved 90 and the removal arms 116 and 102, while the union reached 194. Running the same engine from a structurally different start is what pays; the +3 tolerance at re-attachment is what creates the different start.
- (Inference) The move suits the user's situation: it needs only a reduced-puzzle run of the existing search, a one- and two-step re-attachment from the new value set, and a second run. The selection rule is computable from the per-node target masks described in section 1A.
- (Inference) All of these moves were measured at zero on public programs at 128k–134k. They are tools for the 144k → about 139k range.

### Gaps

- The guide notebook's "21 instructions through a joint cut with a deeper reverse search" could not be traced to a specific file; the block-rebuild source of notebook version 16 and the interface-closure sources are not in the mirror that was read.
- `elf_multiplier_lanes.cpp` and `elf_multiplier_frontier.cpp` were not read in full, so the packet pricing and the beam are described from a third party's notes and may be inaccurate in detail.
- The per-puzzle distribution of the 194 withheld-target savings by puzzle size or family is in an archive that was not opened.

## 4. Exact methods: how the lower bound and the 21 optimality proofs were obtained, sizes handled, run time, and extension to 13 targets

### Takeaway

Every proof uses one relaxation: all values ever produced stay available, so a program is just a set of distinct new values. A puzzle with m targets outside the start values needs m instructions plus one per extra "helper" value; a sharded depth-first search that exhausts every set of h helpers proves a bound of m + h + 1. The 21 proven optima are 16 tiny-domain puzzles plus five with 8–12 targets and 7–10 helpers. Cost grows 13 to 67 times per additional helper, and at 11 helpers the two attempted puzzles left hundreds of shards undecided, so puzzles with up to 13 targets can only be closed when their optimum needs about 10 helpers or fewer. At repository HEAD the merged bound reads 38,005, not 37,992.

### Cited Findings

Sources: [exact_helpers.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/exact_helpers.cpp) (521 lines), [tiny.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/tiny.py), [lower_bounds.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/lower_bounds.py), [solvers/proofs/shard_decision.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/solvers/proofs/shard_decision.py) **[src-full]**; [proofs/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs/README.md) (dated 2026-11-20), [proof-status.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/proof-status.md), [OPTIMALITY-BARRIER.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs_ext/OPTIMALITY-BARRIER.md), [STRONGER-BOUNDS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs_ext/STRONGER-BOUNDS.md) **[doc]**; [proofs_ext/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs_ext/README.md) first 14,000 characters **[doc]**.

- **Relaxation.** "The search allows every number already produced to remain available. Any real register program can be simulated in this model; instructions that regenerate an existing value can be skipped. A proof of infeasibility in this model therefore covers every legal 48-register program." Positivity, the value limit and exact division are still checked. **[doc]** — [proofs/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs/README.md)
- **What is decided.** For a helper budget h: is there a set of at most h values, neither starts nor targets, with which every target becomes derivable? If every shard answers no, the puzzle needs at least `missing targets + h + 1` instructions. A shard that hits its node cap answers UNKNOWN and proves nothing. A FOUND answer returns the value sequence, which is turned into a program and replayed. **[src-full]** — [exact_helpers.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/exact_helpers.cpp); [shard_decision.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/solvers/proofs/shard_decision.py)
- **Search.**
  1. Target saturation: at every state add all targets one operation away from the current values, repeatedly; this uses no helper budget.
  2. Branch on the next helper: every one-operation result of two current values that is new, in increasing value order.
  3. Order symmetry: once the branch "v next" has failed, v is forbidden in the later sibling branches, because any solution containing v would have been found there.
  4. With two helpers left: for the first of them, test whether any last helper could cover all still-uncovered targets. The test uses an index `unary[x]` = targets obtainable from x and one start, target or earlier helper (targets are allowed as operands even if not yet built), extended incrementally as helpers are chosen, plus a pre-computed list of "exceptional" pairs that yield two different targets at once.
  5. With one helper left: the helper must cover every remaining target under the same optimistic index.
  **[src-full]** — [exact_helpers.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/exact_helpers.cpp)
- **Exceptional pairs.** Two different outputs of one operand pair must be two of sum, positive difference, product and exact quotient; the six systems are solved in integers for every ordered pair of targets. An audit mode re-checks by brute force over the whole value range that no such pair was missed. **[src-full]** — same file; [lower_bounds.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/lower_bounds.py)
- **Sharding.** The candidate list at depth 0 is split by index modulo `shards`, at depth 1 modulo a second count, optionally at depth 2 modulo a third; candidates belonging to other shards are put in the forbidden set. Results are check-pointed per shard in SQLite. **[src-full]** — [exact_helpers.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/exact_helpers.cpp); [shard_decision.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/solvers/proofs/shard_decision.py)
- **Variants.** A dense bitmap version for value limits up to 8,191; an incremental version that maintains the one-step neighbour set reversibly; an option that bounds the combined coverage of the last two helpers earlier. **[src-full]** for the first, **[src-part]** (comments) for the others — [exact_frontier.hpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/exact_frontier.hpp)
- **Tiny puzzles.** For value limit ≤ 128 a Python search over bitmask states with iterative deepening on the helper count, a failure memo per state and a 100,000-node cap proves the optimum directly. **[src-full]** — [tiny.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/tiny.py)
- **Cheap bound for all 1,000 puzzles.** Targets not one operation away from starts ∪ targets are "unsupported". Each helper can support a counted number of them through one operand from that set, and each pair of helpers at most one more except for the enumerated exceptional pairs; the smallest h whose best-case coverage reaches the number of unsupported targets is a helper bound. A second bound counts the steps before the largest value can reach the smallest missing target under doubling or squaring. Bound = missing targets + max of the two. **[src-full]** — [lower_bounds.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/lower_bounds.py)
- **History of the total.** 33,331 from the counting bound; +235 from restricting where the first two helpers can come from (33,566); 33,586 on 2026-11-20 after four exhaustive searches; later rounds add graph arguments on four helpers (113 puzzles), target-subset capacity (10), "two triangles sharing an edge" (622 puzzles), condition trees on the first helper (404 puzzles), branching on whether a named helper is used (47 of 622 puzzles, 37,968), and replayed external shard proofs (37,980). **[doc]** — [proofs/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs/README.md); [proof-status.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/proof-status.md)
- **Current total.** "The proven total lower bound over the 1,000 puzzles is 38,005, of which 21 puzzles have a feasible program that meets the bound, 151 instructions in total." **[doc]** — [proof-status.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/proof-status.md)
- **Proven optima beyond the tiny domain.**

  | Puzzle | Targets outside starts | Helper budget excluded | Shards | Nodes | Optimum |
  |---|---:|---:|---:|---:|---:|
  | 0892 | 8 | 7 | 34 | 74,700,636 | 16 |
  | 0399 | not stated | 9 | 20 | 8,584,596,950 | 21 |
  | 0289 | not stated | up to 10 | 288 | not stated | 18 |
  | 0882 | 12 | 10 | 768 + 240 refined | cap 120 M per shard | 23 |
  | 0149 | not stated | not stated | not stated | not stated | 16 |

  **[doc]** — [proofs/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs/README.md); [proof-status.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/proof-status.md); [proofs_ext/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs_ext/README.md)
- On 2026-11-20, 17 puzzles were proven optimal with 73 instructions in total: 16 small-domain puzzles plus 0892. **[doc]** — [proofs/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs/README.md)
- **Run time.** 0892 at 7 helpers: about 174 s with 8 concurrent workers. Throughput about 164,000 nodes per second per core. Whole-grid times for single budgets at 6–8 helpers: 79 s to 638 s (16.2 M to 73.7 M nodes). The pair audit takes 1.4 s for a value limit of 8.2e6, 639 s for 4.0e9, and did not finish in 15 minutes for 8.8e11. **[doc]** — [proofs/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs/README.md); [proofs_ext/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs_ext/README.md)
- **Growth.** Nodes in shard 0 per helper budget, puzzle 0777 (11 targets): 2, 26, 583, 16,124, 541,670, 21,666,846 for h = 3..8, ratios 13 to 40; puzzle 0773 (8 targets): 2, 91, 6,101, 388,394 for h = 3..6, ratios 45 to 67. Two-core time estimates: 1e8 nodes 5 minutes, 1e9 51 minutes, 1e10 8.5 hours, 1e11 3.5 days, 1e12 35 days. **[doc]** — [OPTIMALITY-BARRIER.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs_ext/OPTIMALITY-BARRIER.md)
- **Puzzles with 11–13 targets that did not close.** 0024 (13 targets): 10 helpers excluded with 383 shards plus 8 refined cells and 161,112,222 nodes, bound 24, best program 28; at 11 helpers 164 of 384 shards were excluded and 220 hit the cap. 0113 (11 targets): 11 helpers excluded with 356 shards plus 224 refined cells and 536,765,283 nodes, bound 23, best program 26. 0971: at 9 helpers 344 of 768 shards excluded; raising the cap to 12 M nodes on 435 shards expanded over 5.1 billion nodes and excluded 11 more; bound 15, best program 17. **[doc]** — [proof-status.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/proof-status.md)
- "For puzzles with a value range of 1e9 or more, both the audit and the grid take from a dozen minutes to hours, and the cost doubles or more with each extra budget level; closing puzzles with a gap of 3 needs three successive all-UNSAT grids." **[doc, translated from Chinese]** — [proofs_ext/README.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs_ext/README.md)
- **Does the exact search find shorter programs?** A conditional version on 34 puzzles of 16–52 instructions (selected old intermediate values added as required outputs, a subset of old values omitted, up to three free values allowed): 2 subsets with a valid witness on the independent parent (0021 from 43 to 42, 0221 from 38 to 37), 27,025 subsets exhaustively ruled out, 700 stopped at the node limit; 0 witnesses on the public parent. **[doc]** — [methods.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/methods.md)
- Fixed-boundary segments: 9,771 distinct input/output segments checked across two 1,000-puzzle candidates, 8,988 proven locally shortest; one puzzle (0649) shortened to 118. **[src-part]** (one status line) — [STATUS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/STATUS.md)
- Alternatives considered by a contributor and not built: backward decomposition from targets (blocked by the t − 1 additive decompositions of a target near 1e9) and an explicit SAT encoding (about 4 billion ordered choices for 10,000 candidate values and 40 steps). **[doc]** — [STRONGER-BOUNDS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/proofs_ext/STRONGER-BOUNDS.md)

### Inferences

- (Inference) The 21 proven optima are the 16 tiny-domain puzzles (57 instructions), 0892 (16), 0399 (21), 0289 (18), 0882 (23) and 0149 (16): 57 + 16 + 21 + 18 + 23 + 16 = 151, which matches the stated total.
- (Inference) The number of targets is not the limiting quantity; the search handles up to 64 targets. The limit is the helper budget (about 10 with the pruning described, 11 only partly) and the branching factor, which grows with the number of current values and with the value range. A 13-target puzzle closes only if its optimum is about 13 + 10 or less; puzzle 0024 with best program 28 would need budgets 11 to 14, which at 13–67 times per level is beyond days of multi-core time.
- (Inference) For score, the exact search is worth running in FOUND mode on the user's smallest puzzles: the budget h = (current length − missing targets − 1) asks "is there a program one instruction shorter?". Either it returns a shorter program or it proves the current one optimal and removes the puzzle from later work. The public line found only two such witnesses in 34 puzzles, so the total effect is a few instructions.
- (Inference) The relaxation ignores registers, so a FOUND witness still has to be scheduled into 48 registers; for programs under about 40 instructions that is automatic.

### Gaps

- The list of the 21 puzzle IDs was not read from `puzzle-bounds.csv`; the composition above is inferred from totals.
- Target counts and node totals for 0399, 0289 and 0149 are not in the documents read.
- The folders for the graph-argument bounds (`distinct-helper-edges`, `distinct-diamond`, `subset-capacity`) were not read; only their effect on the total is known. The membership-branching README was read in its first 2,500 characters.
- No wall-clock total for the whole proof effort is given anywhere.

## 5. Verification of the round-one numbers tagged as summary-level

### Takeaway

Both pairs of numbers are confirmed verbatim in the source table. Two qualifications matter: the 329-instruction pass ran at 1.8 s per puzzle with the group size chosen by stratum, and the 58-instruction figure is not recombination of several programs but a single-parent CP-SAT re-selection with 24 newly enumerated helper values, of which plain recombination contributed 7.

### Cited Findings

- Table "Refining a single existing program": GoodPJW v5 on independent programs, parent 142,219, result 141,890, 329 steps saved, 218 puzzles improved; on publicly attributed programs 135,222 → 135,167, 55 saved, 42 puzzles. Arsen v15 with local helper ranking on independent programs 141,613 → 141,555, 58 saved, 51 puzzles; on publicly attributed programs 135,161 → 135,138, 23 saved, 20 puzzles. **[doc]** — [methods.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/methods.md)
- "The independent pilot compared groups of 3 and 8 on 50 stratified puzzles with matched seeds and 1.8 seconds per group. The full pass chose the group by stratum. Each puzzle search received only its own parent program." **[doc]** — same file
- Breakdown of the 58: single pass with zero helpers 7, published ranking with 24 helpers 20, local ranking with 24 helpers 51; best per puzzle 55; a repeat on the winners 3. Breakdown of the 23 on the public parent: 2, 9, 17, then best per puzzle plus a repeat on the 20 changed programs. One CP-SAT worker, seed 20261120, deterministic-time budget 0.22 per call. **[doc]** — same file
- The tables "report local instruction counts from full 1,000-puzzle replays" on "fixed, hashed parents"; the file carries no date. **[doc]** — same file
- Proven lower bound: round one recorded 37,992 at 2026-11-24 13:21 BJT; the same document at HEAD now states 38,005, still with 21 puzzles proven optimal and 151 instructions. **[doc]** — [proof-status.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/proof-status.md)

### Inferences

- (Inference) "One pass of the public search engine" should be read as roughly 30 CPU-minutes over 1,000 puzzles (1.8 s each, one program per puzzle, no crossover, release 5 of the engine). The same engine is normally run at 15–60 s per puzzle in a loop, so 329 is a floor for what it does to 142k-level programs, not a ceiling.
- (Inference) In the round-one table the row "CP-SAT recipe recombination: −58" should be relabelled "single-parent recipe re-selection with 24 enumerated helper values"; the comparable figure for recombining existing recipes only is −7 at 141.6k and −2 at 135.2k.
- (Inference) The dates of both runs lie between 2026-11-19 21:44 BJT (independent line 146,435) and the later 140k-level experiments; the 142,219 and 141,613 parents fix the order of the two runs but not their day.

### Gaps

- The per-puzzle evidence file (`evidence/solver-experiments.json`) with hashes and gains was not opened, so the strata and which group size each stratum received are unknown.
- No commit history was read, so exact dates for these runs could not be established.
