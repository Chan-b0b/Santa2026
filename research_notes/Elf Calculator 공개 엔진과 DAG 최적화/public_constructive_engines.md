# Public constructive engines for Santa 2026 – The Elf Calculator, at implementation level (state as of 2026-11-24)

Read-level tags on every finding:

- **[src-full]** source file read in full
- **[src-part]** source file read in part (the lines named, or header plus grep)
- **[doc]** README, NOTICE, research note or notebook text (not code)
- **[derived]** my own arithmetic on something read in source; not stated by the author
- **[search]** search summary only

Access summary. kaggle.com was not fetched. The GitHub REST API returned "rate limit exceeded" for unauthenticated calls, so file lists came from blob-less shallow clones (names only) and file contents from raw.githubusercontent.com. Only source code, READMEs, notices and small metadata JSON were fetched, into a temporary directory outside the project; no solution or program file (CSV, gz) was downloaded and no code was copied into the project. Three web searches were tried: two returned nothing relevant and one was refused by the organisation's content policy because the query contained an account handle; it was not retried. Authors are identified by the account handle that appears in the cited URL. Times marked BJT are Beijing time (UTC+8) as written in the source.

Engines and what was read:

| Engine (origin) | File read | Depth |
|---|---|---|
| `tonylica` "Elf Calculator With Register Reuse" (base engine) | [generative/tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp), 471 lines | src-full |
| `konbu17` "Wider Dictionary + Portfolio (163k)" | [generative/konbu.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/konbu.cpp), 611 lines; read as a diff against tony.cpp (every changed line). The copy carries extra "local changes" by the hosting repository | src-full (diff) |
| `alexchilton` "Rudolph the Red-Nosed Register Allocator" | [generative/rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp), 780 lines; also carries local changes | src-full |
| `arsen123` "original dictionary solver source" | [generative/recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/recovered/solver.cpp) (241 lines), [generative/arsen.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen.cpp) (168 lines), diff to [arsen_current/recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_current/recovered/solver.cpp) | src-full |
| `Juan-Severiano/santa-2026` | [cpp/beam_search.cpp](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/cpp/beam_search.cpp) lines 1–60 and 300–600 of 1,182 (byte-identical to Hansen0223 `generative/juan.cpp`); [src/santa2026/beam.py](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/src/santa2026/beam.py) full; README, THIRD_PARTY.md, docs/research/2026-11-21-public-methods.md full; rust/README.md grep only; rust/construct.rs not read | src-part + doc |
| `Yukisiooisiiyo/kaggle-santa` | [src/solver.cpp](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/src/solver.cpp) 654 lines, [tools/portfolio.py](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/tools/portfolio.py), README | src-full |
| `munhof/kaggle.1-santa2026` | [pending_dictionary.hpp](https://raw.githubusercontent.com/munhof/kaggle.1-santa2026/HEAD/elf_calculator/constructors/pending_dictionary.hpp), [target_planner.inc](https://raw.githubusercontent.com/munhof/kaggle.1-santa2026/HEAD/elf_calculator/constructors/target_planner.inc) full; scripts/target_planner.py first 60 lines; README full; experiment diary notebook not read | src-full / src-part |
| `pablodiegoo` "Deterministic Atlas Solver" | [generative/atlas.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/atlas.cpp): header (45 lines) and lines 5925–6010 of 6,295 | src-part |
| Hansen0223 `generative/` driver | [generative/run_source.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/run_source.py) first 230 of 357 lines | src-part |
| `goodpjw2008` dataset code (`elfopt.cpp`), `ozertuu` notebook, `asteriospanoras` dataset | not read: no copy of the code was found in the files listed; known only through third-party notices | doc only |

## 1. The backward beam search: state, decompositions, dictionary, limits, assembly

### Takeaway

Every public beam constructor that was read descends from one 470-line design: for each target, rebuild from scratch a hash dictionary of all values reachable in 0, 1 or 2 instructions from about 56–112 chosen "leaf" values (roughly one to several million entries), then run a beam over a single shrinking residual where each step is `v = child × f ± a` or `v = a − child` with `f` and `a` taken from the dictionary, ranked by `instructions spent + 0.18 × log2(residual)`. The search plans on an unbounded value graph (value → one recipe); the 48 registers are handled afterwards by a separate compile step.

### Cited Findings

**Search state and ranking (base engine)**

- A state is one residual integer plus bookkeeping: `(residual v, cost so far, parent state, link = (factor id, atom id, op), rank)`. There is no set of open values; the path is a single spine, and every side operand must be a dictionary entry. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- A link means `parent = child × factor + atom`, `parent = child × factor − atom`, or `parent = atom − child`; factor and atom are optional. Step cost is `(1 + dictcost(factor))` if a factor is used plus `(1 + dictcost(atom))` if an atom is used, where dictcost is 0, 1 or 2. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Rank is `cost + 0.18 × log2(child)`; the constant is named ALPHA in the parameterised version. 0.18 instructions per bit is the same as assuming 5.6 bits removed per instruction. [src-full] — [konbu.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/konbu.cpp); the 5.6 figure is [derived]
- A child that is itself in the dictionary ends the path with total `cost + dictcost(child)`; the best total is kept as `best`. A non-terminal child is kept only if it is strictly smaller than its parent, `cost + 3 < best`, it was not reached before at equal or lower cost, and it fits in the beam. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Limits: beam width defaults to 3 (first command-line argument); at most 20 levels; if nothing is found the target is built by binary doubling. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)

**Decompositions generated for a residual v (base engine)**

- Additive, nearest values: in each of the three cost layers (0, 1, 2 instructions) of the sorted dictionary, the 8 entries around v (4 below, 4 at or above) give child `|v − a|`. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- For every dictionary entry `a` of cost at most 1 (leaves and one-step values, `a ≠ 1`):
  - if `|v − a|` or `v + a` is in the dictionary, finish there (`v = d + a`, `v = a − d`, `v = d − a`);
  - if `|v − a|` or `v + a` is divisible by 16, strip the largest power of two `2^k` (k ≥ 4) that is in the dictionary: child `= (v ∓ a) / 2^k`, factor `2^k`, atom `a`;
  - if `a < v`, with `q = v div a`, `r = v mod a`: exact factor (`r = 0`, child q); `v = q·a + r` when r is in the dictionary; `v = (q+1)·a − (a − r)` when `a − r` is in the dictionary and the overshoot stays within the limit;
  - if `a` is a leaf and `q > 64`: take the two dictionary values `b` nearest to q in each layer; if the product `a·b` is itself a dictionary entry, child `= |a·b − v|` with the product as atom. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- There is no square-root and no halving move in the base engine. Halving appears only as the power-of-two strip. A later version of the `arsen123` solver adds, behind compile-time switches, a perfect-square move (if `v`, `v − a`, `a − v` or `v + a` is a perfect square, child is its root at cost 1), squares of one-step values in the dictionary, and "exact quotient" moves (`v = d / a` when `v·a` is in the dictionary; `v = a / d`). [src-full] — [arsen_current/recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_current/recovered/solver.cpp)

**Dictionary**

- Built from a leaf list: every leaf at cost 0; every unordered leaf pair combined by `+`, `|−|`, `×` (within the limit) and exact `÷` in either direction at cost 1; every one-step value combined with every leaf at cost 2. First insertion of a value wins. Stored in an open-addressing hash of 2^20 slots plus three sorted arrays by cost. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Refresh: the dictionary is cleared and rebuilt for every target that is not already defined. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Leaf list in the base engine, in this order: a fixed "palette" (see section 4), the start values, earlier targets largest first until 52 leaves, then the most recently created values until 56 leaves. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Size: with n leaves there are at most 4·n(n+1)/2 one-step and 4·n·(one-step count) two-step candidates, about 6,400 and 1.4 million for n = 56, about 15,700 and 5.5 million for n = 88, before de-duplication and the limit filter. [derived]
- The parameterised version makes the table size an argument (INDEX_BITS, 20 by default), refuses inserts above 7/8 load, and with a negative value grows the table on demand; so the table size is in effect a cap on dictionary size. [src-full] — [konbu.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/konbu.cpp)

**Assembling the program**

- Planning state is a map `value → (op, a, b)` plus creation order. `make(op, a, b)` adds a recipe only if the value has none yet, so a value is built once however many targets use it. A found path is unwound from the terminal entry to the target, materialising each dictionary operand recursively. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- `compile()` walks the recipes depth-first from each target in target order, producing a sequence that contains only values some target needs (unused palette or dictionary values are never emitted), then simulates 48 registers (section 5). [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Targets are processed in the order given; the wrappers pass them sorted ascending. [src-full] — [beam.py](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/src/santa2026/beam.py); [rudolph.cpp header](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)

Pseudocode in my own words (base engine):

```
solve(puzzle):
    recipes = {start values}; build palette recipes (not yet emitted)
    for T in targets ascending:
        if T has a recipe: continue
        leaves = palette + starts + largest earlier targets (to 52) + newest values (to 56)
        D = two_step_dictionary(leaves)                 # rebuilt every target
        path = beam(T, D, width)
        if path: materialise path into recipes (each new value once)
        else:    binary doubling for T
    return compile(recipes, targets)                    # 48 registers handled here

beam(T, D, width):
    front = [state(T, cost 0)]; best = infinity
    repeat up to 20 times:
        next = []
        for s in front with s.cost + 3 < best:
            for (child, factor, atom, op) in moves(s.v, D):
                c = s.cost + (factor ? 1 + D.cost(factor) : 0) + (atom ? 1 + D.cost(atom) : 0)
                if child in D: best = min(best, c + D.cost(child)); continue
                if child >= s.v or c + 3 >= best or seen[child] <= c: continue
                insert into next by rank c + ALPHA*log2(child); keep the best `width`
        front = next
    return path of best
```

**Variants of the search in the other engines**

- Rudolph (own implementation of the same mechanism): default width 10, 24 levels, prune at `cost + 2 ≥ best`; additive moves use the 12 nearest entries of the whole dictionary and the 12 nearest among cost ≤ 1 entries ("which the full list crowds out"); at the root the factor may be any dictionary entry (two-step ones only below 2^28), deeper only cost ≤ 1 entries; an optional product link `v = f·Y ± c` with Y a dictionary value near `v/f` (PROD_K, default off, credited to `thisray`); no power-of-two strip; the dictionary also holds `x + x` and `x·x` for one-step x. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- `arsen123` base solver: default width 4, 18 levels, 6 nearest entries per layer, power-of-two strip from k ≥ 5, no quotient-approximation move, generation-stamped hash table capped at 75% load, default 72 leaves. [src-full] — [recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/recovered/solver.cpp)
- Atlas standalone mode: exact breadth-first search for tiny puzzles, then a "Beam DAG" solver called with (width 10, alpha 0.18, 48, 56), a "real-machine" fallback only if that fails, then peephole, cofactor, chain-reversal, window and scaffold-exchange passes. [src-part] — [atlas.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/atlas.cpp)
- `Yukisiooisiiyo/kaggle-santa` is a different design (see section 6): best-first search with a node limit instead of a beam, working on the real register contents.

### Inferences

- (Inference) The public dictionary is two to three orders of magnitude larger than a "thousands of values" catalogue: every operand on the spine may itself be a fresh two-step value, so one beam step can consume up to 6 instructions (multiply + two-step factor, add + two-step atom) and still be found by a hash lookup. A reduction search whose `b` and `c` come only from current register contents or one-step values sees far fewer exact hits per step.
- (Inference) The engine is cheap because the search state is one integer. It cannot represent "two open values that share a sub-result"; all sharing has to come from the leaf list and from value de-duplication (section 2).
- (Inference) Because dictionary costs are tree costs and leaves are priced at zero, the beam's cost is only an estimate of instructions actually added; engines that re-price finished paths by distinct new values (Rudolph's SLACK, the local COUNT_REUSE) are correcting this.

### Gaps

- The original notebooks were not read; `tony.cpp`, `konbu.cpp` and `rudolph.cpp` are copies in a third-party repository, and the last two carry that repository's own changes, which are marked only by a header comment. Parameters defaulting to "off" in those files (LANDMARKS, CLUSTER_WEIGHT, EXACT_JOIN, DISTANCE_GUIDE, RATIONAL_LIFTS, SHARED_INTERVAL, COUNT_REUSE, TARGET_LEAVES, a learned residual model) are treated here as local additions, by inference from the header comments.
- Atlas's beam and real-machine solver bodies (about 6,000 lines) were not read; neither were `arsen_current/solver_depth4.cpp`, `arsen_v7/solver_joint.cpp`, `generative/seed_grammar.cpp` or Juan-Severiano's `rust/construct.rs`.

## 2. Sharing: how by-products are rewarded, what-if rebuilds, target orders

### Takeaway

The base engine has no sharing term at all: sharing arises only because earlier targets and recent intermediates are dictionary leaves and because a value is materialised once. Explicit sharing appears in derivatives as four devices: choosing the next target by measured cost (sometimes compiled cost), re-pricing finished candidates by distinct new values, voting for hidden values that several open targets can reach by exact inversion, and ruin-and-recreate accepted on compiled length. Where results are reported, each device is worth about 1–2% on constructor output and nothing on already-optimised public programs.

### Cited Findings

**Implicit sharing in the base engine**

- Earlier targets (largest first) and the newest intermediates are leaves, so any one- or two-step combination of them is a dictionary entry; `make` refuses to redefine an existing value. Nothing in the rank or cost refers to other targets. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)

**Re-pricing by what is really new**

- Rudolph resets to cost 0 every dictionary entry whose value the program already holds, and keeps all finished paths within SLACK (default 2) of the best estimate, then picks the one with the fewest distinct new values ("a value used twice or already built counts once or not at all; the beam's sum counts it each time"). Reported on the 200 practice puzzles: SLACK 0 → 33,132, 1 → 32,856, 2 → 32,842 (comment dated 2026-11-18). [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- The local COUNT_REUSE switch in `konbu.cpp` does the same inside the beam: a path's cost counts each distinct non-leaf dictionary component once, tracked with a 64-bit fingerprint per state and an exact walk up the parents. [src-full] — [konbu.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/konbu.cpp)

**Leaf selection aimed at open targets**

- Rudolph puts up to 40 recent values below 2^16 into the leaves first ("residuals end small, where the dictionary is sparse"; −6.2% on 32 practice puzzles), then recent targets up to 60 leaves, then recent values up to 80. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- The local TARGET_LEAVES switch scores each existing value x for the current target T by `log2(min residual of T mod x) + 0.35·log2(T div x)` (quotient at most 64), takes the best third of the free leaf slots by that score, the next third by fan-out (how many recipes use x), and fills the rest with the newest values. [src-full] — [konbu.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/konbu.cpp)
- `munhof` ranks recent helper values by the number of pending targets each can reach "directly or as target = helper × fixed_factor ± fixed_offset" (six inverse forms plus `(t ∓ r)/a` over a fixed set), and orders the leaf candidates by that count. [src-full] — [pending_dictionary.hpp](https://raw.githubusercontent.com/munhof/kaggle.1-santa2026/HEAD/elf_calculator/constructors/pending_dictionary.hpp)

**Explicit "values several open targets can reach"**

- `Yukisiooisiiyo`: when no target is one instruction away, every remaining target votes for values within two inverse steps of it (inverse of `+ − × ÷` against each pool value, half and square root, a second inverse against pool values, and one inverse against one-step values). Each candidate x records `cnt` (distinct targets) and `ksum` (sum over those targets of the fewest steps from x to the target). A candidate with `cnt ≥ 2` that an exact search can build in d ≤ 3 instructions is scored `(d + ksum) / cnt`, instructions per target served; a remaining target competes with `cnt + 1`. The lowest score is built, ties to the larger `cnt`; at most 300 candidates are tried. [src-full] — [solver.cpp](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/src/solver.cpp)
- Local `discover_shared` in `rudolph.cpp` (run every SHARED_INTERVAL targets, default off): each remaining target, combined with each cheap atom (leaves, the 128 smallest and about 256 evenly spaced cost ≤ 1 entries), nominates `t − a`, `a − t`, `t + a`, `t/a`, `a/t`, `t·a`; a nominee needs at least two distinct targets; benefit per target is `max(0, 2 + 0.145·log2(t) − 1 − cost(a))`; the top 8 by `benefit − estimated price` are actually searched, and the best is built if `benefit − true cost > 1`. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- Local `promote_landmarks` (LANDMARKS, default 0): greedily builds two-step dictionary values of at least 64 that serve as a factor for at least two targets, scored by factor bits minus 5 per instruction of offset cost plus a bonus when the quotient is in the dictionary, counting only the gain over factors already available. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)

**Target orders**

- Base engine: input order, which the wrappers make ascending. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Rudolph HEAD: for the first HEAD picks, search every remaining target and build the cheapest, then continue ascending. Practice totals: HEAD 0 → 34,560, 1 → 34,181, 2 → 34,628, 3 → 34,283, 4 → 34,237, 6 → 34,876; per-puzzle best of the six → 33,516. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- `Juan-Severiano` order modes: 0 input order; 1 re-plan all unfinished targets against each rebuilt dictionary and build the cheapest; 2 reversed (seed 0) or shuffled; 3 as mode 1 minus an affinity bonus `min(2, 0.25 · Σ 1/(1 + cost(|t − u|)))` over unfinished targets u whose difference to the candidate is in the dictionary; 4 rank each candidate by the compiled length of the prefix program with that target added ("the dictionary treats all selected leaves as free… compile a hypothetical prefix to charge their actual construction and reload costs"); 5 as 4 with leaves restricted to values resident in the 48 registers after compiling the prefix. [src-part] — [beam_search.cpp](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/cpp/beam_search.cpp)
- `arsen123`: orderings 0 input, 1 reversed, 2–99 shuffled with that seed, 100 cheapest remaining target each round, above 100 a shortlist of `ordering − 100` targets ranked first by a width-1 beam and then searched at full width (the shortlist is marked as a local modification). [src-full] — [arsen.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen.cpp); [recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/recovered/solver.cpp)
- `munhof` planner policies: 0 input order; 1 cheapest by true marginal cost (copy the state, build the target, count); 2 one-step lookahead over the 6 cheapest: after taking a candidate, rebuild the dictionary and sum the marginal cost of every remaining target, choose the minimum of `5·immediate + 2·remaining`. [src-full] — [target_planner.inc](https://raw.githubusercontent.com/munhof/kaggle.1-santa2026/HEAD/elf_calculator/constructors/target_planner.inc)
- `Yukisiooisiiyo` `--pick N`: run the reduction search on the N smallest remaining targets and build the shortest plan. [src-full] — [solver.cpp](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/src/solver.cpp)
- Order derived from an existing program (used for regeneration): repeatedly pick the target with the smallest marginal price, where each not-yet-paid value in its dependency closure costs `1 / (1 + strength · log2(number of remaining targets needing it))`. [src-part] — [run_source.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/run_source.py)

**What-if rebuilds inside constructors**

- Rudolph ruin-and-recreate: for each target, delete the values only it needs, rebuild it with leaves drawn from everything else the program holds (small values first, then values closest in bit length), keep the change only if the compiled program is shorter. Practice: 33,604 with against 33,738 without. Accepting by number of needed values instead of compiled length was 60 worse. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- Rudolph pair ruin: the same for a target and the target sharing most dependencies with it, rebuilding the smaller first. Practice: 33,340 against 33,470 at twice the time. On public programs: one-target ruin 141,432 → 141,431, pair ruin 14,362 → 14,362 on 100 puzzles. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- `arsen123` `simplify`: for every node, enumerate one-instruction alternative recipes over the graph's own earlier values (`v = x + (v − x)`, `x − v`, `x · (v/x)`, `x / (x/v)`), accept an alternative when the number of nodes reachable from the targets drops; four passes. "Judge changes by total reachable graph size, not expression-tree cost." [src-full] — [arsen.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen.cpp)

**What authors report did not work**

- Regenerating long puzzles with Rudolph four more times per arm, one arm with fixed random target permutations and one with orders adjusted from the generated dependency graph (postponing targets with many private steps, computing widely shared intermediates first, moving a group of adjacent targets), then merging each arm's five programs with a recipe selector: 799 (random) and 793 (directed) instructions on 4 development puzzles against 791 for the frozen programs. [doc] — [official-heads README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/official-heads/README.md)
- `Juan-Severiano`: MILP, C++ re-planning (the order modes) and compression together took `konbu17`'s 160,175 public programs to 159,737 on 2026-11-18, 438 saved. [doc] — [Juan-Severiano README](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/README.md)
- A constructor by `josecoronel` that scores accumulated benefit reached 150,463 against a 133,790 portfolio, "and bounded rollouts remained above the frontier"; a hub-swap test found no improving move on ten cases. [doc, third-party summary] — [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)
- All-consumer retirement by one-instruction alternatives: over 1,000 puzzles and 31,320 helpers with fan-out at least three, 5,364 consumers had an alternative single-operation recipe but zero helpers had every consumer covered. [doc] — [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)

### Inferences

- (Inference) No public constructor scores a decomposition by its by-products during the beam. The closest are the vote (a separate step before the search) and the affinity bonus on target choice. A beam-internal term "this atom or factor is also one or two steps from k other open targets" is absent from everything read.
- (Inference) The measured effect sizes inside constructors are small: SLACK about 0.9% (33,132 → 32,842), ruin-and-recreate about 0.4%, pair ruin about 0.4%, cheapest-first on the first pick about 1.1% (34,560 → 34,181). The 59% sharing saving quoted by the guide is a property of programs after days of value-graph optimisation, not of constructor output.
- (Inference) Our what-if rebuild and "values shared by several targets" ideas already match what the public derivatives do; the differences worth testing are the dictionary size, re-pricing finished candidates by distinct new values, and ranking the next target by compiled prefix length.

### Gaps

- No measured result was found for COUNT_REUSE, TARGET_LEAVES, LANDMARKS, CLUSTER_WEIGHT, EXACT_JOIN, RATIONAL_LIFTS or `discover_shared`; all default to off in the files read.
- Results of `munhof`'s pending-dictionary and planner ablations (capacity 0/48/128 × policy 0/1/2, practice data) live in an unversioned reports folder and a diary notebook that was not read.
- Per-mode totals for `Juan-Severiano`'s order modes 1–5 were not found; only the combined 438.

## 3. The portfolio of about 50 settings

### Takeaway

The exact 50 settings were not found in any mirror. What varies is known from the source: beam width, ALPHA, the two leaf budgets and the hash-table size, later joined by target order and palette style. The only measured per-puzzle-best gains found are 1.9% over six settings (Rudolph) and 0.9% over three (another repository); `konbu17`'s own single-setting baseline is not documented in anything read.

### Cited Findings

- The parameterised engine reads from the command line: width, ALPHA (default 0.18), N_DONE (leaf count after adding earlier targets, default 52), N_RECENT (leaf count after adding recent intermediates, default 56) and INDEX_BITS (default 20). The header says of the notebook's own change: "the four tunables below are read from the command line". [src-full] — [konbu.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/konbu.cpp)
- A downstream wrapper cycles through eight (width, ALPHA, N_DONE, N_RECENT, INDEX_BITS) tuples: (3, .18, 52, 56, 20), (10, .18, 72, 88, 22), (30, .18, 64, 96, 22), (10, .18, 64, 72, 22), (10, .12, 72, 88, 22), (10, .25, 72, 88, 22), (30, .18, 80, 112, 23), (3, .18, 40, 48, 20); width is multiplied by an effort factor up to 100, and the seed beyond eight selects a target-order seed. [src-full] — [beam.py](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/src/santa2026/beam.py)
- Single settings used by another driver: `tony` width 3; `konbu` (10, .18, 72, 88, 24); `arsen-base` (width 3, 64 leaves, .18, style 0, order 0); `arsen` (3, 128 leaves, .18, style 0, order 100, 32 schedule trials); `rudolph` (width 20, .18, 60, 80, small bits 16, small count 40, HEAD 1). [src-part] — [run_source.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/run_source.py)
- `konbu17` is credited with "wider dictionaries, per-puzzle portfolios, cheapest-target ordering, virtual-register plans and exact graph rewrites". [doc] — [ARSEN-SOURCES.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/ARSEN-SOURCES.md)
- Scores: the notebook title carries 163k; the `konbu17` programs dataset replayed at 160,175 on 2026-11-18. [doc] — [Juan-Severiano README](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/README.md); [THIRD_PARTY.md](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/THIRD_PARTY.md)
- Portfolio gain, Rudolph: six HEAD settings score 34,181 to 34,876 individually on the 200 practice puzzles; per-puzzle best of the six is 33,516, 665 (1.9%) below the best single setting. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- Portfolio gain, `Yukisiooisiiyo`: 32,888 for one setting (`--pick 16 --nodes 100`), 32,580 for the per-puzzle best of three settings on practice (0.9%); the script lists four settings, varying the bits-per-instruction rate, minimum rate, eviction weights and whether voting is on. [doc + src-full] — [README](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/README.md); [portfolio.py](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/tools/portfolio.py)
- `arsen123` adds palette style (two exponent sets) and schedule mode to the portfolio axes, and credits `yuki16` for "heterogeneous per-puzzle portfolios". [src-full + doc] — [recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/recovered/solver.cpp); [ARSEN-SOURCES.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/ARSEN-SOURCES.md)

### Inferences

- (Inference) The gap between the notebook title (163k) and the dataset (160,175) suggests the portfolio, planner and re-allocation steps together were worth about 3,000 on top of a first portfolio, about 2%; this is a guess from two numbers, not a reported ablation.
- (Inference) A portfolio over width, ALPHA and leaf budgets changes which residuals survive and which values are leaves, so it produces structurally different programs. Its direct gain is 1–2%; its indirect use is as a recipe pool for later recombination.
- (Inference) Pure constructor output is around 160–170 thousand: 160,175 for the `konbu17` portfolio; Rudolph's 32,842 on practice scales to about 167,000 using the 26,898 / 5,288 lower-bound ratio quoted in one README. Our 143,891 is already well below any public constructor alone.

### Gaps

- The list of 50 settings, the score of the base engine with one setting on the 1,000 scored puzzles, and `konbu17`'s own portfolio-versus-single comparison were not found. The notebook itself could not be read.

## 4. Bootstrap: what happens before the first target

### Takeaway

The base engine declares a fixed palette of 1, sixteen powers of two and eleven small odd numbers as free leaves, and emits only the members that some target's recipe ends up using; fully used it costs 28 instructions. Rudolph has no palette and instead grows a tiny dictionary by squaring and doubling. Every reported attempt to pre-load a designed or sampled dictionary was neutral or worse.

### Cited Findings

- Palette of the base engine: 1 (a start value divided by itself); `2^k` for k in {1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 20, 24, 32, 40, 48} within the limit, each built as a product of two smaller powers (`2^k = 2^(k div 2) · 2^(k − k div 2)`); and 3, 5, 7, 9, 11, 13, 15, 17, 19, 23, 31 (11, 13 and 19 as `x + 8`, 23 as `7 + 16`, `2^j − 1` by subtraction, others by doubling). [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Cost if every palette value were emitted: 1 + 16 + 11 = 28 instructions, since each power and each odd number takes exactly one instruction given the earlier ones. [derived]
- Palette values are recipes only; `compile()` emits a value only if a target depends on it. The beam nevertheless prices every palette leaf at zero. [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- The `arsen123` solver has a second palette style with exponents {1, 2, 3, 4, 6, 8, 9, 12, 16, 18, 24, 27, 32, 36, 48, 54}. [src-full] — [recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/recovered/solver.cpp)
- Rudolph starts from 1 and the start values only. If a search fails it "grows" the value set (squares of the 3 largest held values, doublings of the 3 smallest), rebuilds the dictionary and retries, up to GROW = 4 rounds before binary doubling. "Unused ones cost nothing: compile() emits only what the targets need." [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- Rudolph's measurements (comments dated 2026-11-18): before growth, the first target on 39 single-start puzzles took 2,107 instructions against 827 in public programs, "all in the binary fallback"; growth rounds took those 39 puzzles from 8,594 to 7,974 in total and practice from 33,340 to 33,153; adding `x + x` and `x·x` of one-step values took them to 7,943 and 33,132. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- `Yukisiooisiiyo`: on the first target that needs the reduction search, if the pool has at most 6 values, build 1, 2, 4, 8, 16 ("seed the pool with 1, 2, 4, … so residues become cheap"). [src-full] — [solver.cpp](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/src/solver.cpp)
- In the 134,568 public set (2026-11-20) every puzzle pays about 21 instructions for its first target, about 4.9 times a later target (4.4): "the small starting values have to be grown into a useful set of registers first". [doc] — [guide notebook v217 mirror](https://raw.githubusercontent.com/AsteriosPanoras/kaggle-portfolio/HEAD/competitions/santa-2026/notebooks/santa-2026-best-public-score-dataset-fails/v217.ipynb)
- Experiments on reducing it:
  - Pinning a dictionary of a base B and its powers (B = 2^8, 2^12, 2^16, 2^20 or the largest start value) in the public reverse beam: no gain (round one recorded 44 to 168 instructions worse over 10 puzzles). [doc] — [guide notebook v217 mirror](https://raw.githubusercontent.com/AsteriosPanoras/kaggle-portfolio/HEAD/competitions/santa-2026/notebooks/santa-2026-best-public-score-dataset-fails/v217.ipynb)
  - Pre-built dictionaries for Rudolph: let the generator run one to several steps from the start values, feed the resulting values as extra inputs; one arm prefers values used by several targets in a normal run, the other samples values of similar bit length and construction cost. All preparatory instructions are really executed and counted. Development (4 puzzles): 790 random, 795 targeted, 791 frozen. Held-out (8 puzzles): 1,370 and 1,371 against 1,349. A further 26 long puzzles regenerated normally: 4,162, down to 4,096 after recipe selection and rewriting, against 4,007 existing, no strict improvement. [doc] — [official-heads README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/official-heads/README.md)
  - A fresh constructor that pays "every bootstrap, temporary and target operation" on a real 48-register bank scored 4,295 then 4,197 instructions on 20 puzzles against 2,837 for the 142k-level reference. [doc] — [Juan-Severiano README](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/README.md)

### Inferences

- (Inference) Part of the "21 instructions for the first target" is accounting: the compile step emits recipes depth-first in target order, so shared infrastructure (1, powers of two, small odd numbers) is billed to whichever target is emitted first. The figure is still about 21 after days of optimisation, which suggests the infrastructure is being used, not that it is waste.
- (Inference) The public palette is deliberately generic and lazily emitted. This is the opposite of our measured loss from building seeds unconditionally: declare many cheap candidates as free leaves, pay only for those a chosen recipe uses.
- (Inference) The power-of-two strip move exists to exploit the palette: it turns `(v − a)` with many trailing zero bits into a multiplication by a palette power.

### Gaps

- No source reports the bootstrap cost of constructor output itself (as opposed to the optimised public set), or an ablation with the palette removed or changed on the scored puzzles.
- `generative/seed_grammar.cpp` (82 lines, apparently a seed-construction experiment) was listed but not read.

## 5. The register-aware planner and eviction

### Takeaway

Two different things are called register-aware. All engines plan on an unbounded value graph and then compile with "evict the value whose next use is farthest, rebuild it from its recipe if it is needed again"; the planner variants go further and choose the next target, or restrict the dictionary leaves, by simulating that compile. Nothing read changes the search itself when the bank is nearly full.

### Cited Findings

- Base compile: emit values in dependency order; to emit a value, ensure both operands are in a register (recursively re-emitting an evicted operand from its recipe, with the first operand's register locked), then write to an empty register or else to the unlocked, non-start register whose value has the farthest next use (values with no further use count as farthest). Registers holding start values are never chosen; the source comment says an evicted value "can always be rebuilt from its expression or a protected seed". [src-full] — [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp)
- Cost-aware eviction (`arsen123`, credited to `mizeroluckygall`): priority = `distance to next use / (1 + min(20, rebuild cost))^1.5`, where rebuild cost is the recipe's tree cost; three schedules are compiled (plain farthest-use; cost-aware in goal order; cost-aware in reversed goal order), later 32 random goal orders, and the shortest program is kept. [src-full] — [recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/recovered/solver.cpp); [arsen.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen.cpp)
- Rudolph compiles four schedules and keeps the shortest: sequence by depth-first target order or by creation order, each with and without permission to overwrite a start value that has no further use. An operand's register may take the result when that operand dies at this step. A schedule that later needs an overwritten start value is discarded. [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)
- Planner by compiled prefix (`Juan-Severiano` modes 4 and 5): for every unfinished target, copy the state, add the target's recipe, compile the prefix program and rank by its length; mode 5 also replays the compiled prefix and admits as leaves only earlier targets and intermediates that are physically in the 48 registers. [src-part] — [beam_search.cpp](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/cpp/beam_search.cpp)
- Virtual-bank planner (`munhof`, described as included inside the base engine's puzzle structure): keeps a resident list of a set capacity (0 = unlimited, 48, or 128); loading a value that is not resident re-derives it recursively, evicts the least recently used unlocked non-start resident and counts one emitted step; with a capacity set, the dictionary leaves are exactly the residents and the cost of a target is the number of emitted steps. [src-full] — [target_planner.inc](https://raw.githubusercontent.com/munhof/kaggle.1-santa2026/HEAD/elf_calculator/constructors/target_planner.inc)
- `Yukisiooisiiyo` works on the real bank from the start: a result goes to an undefined register, else one holding a duplicate value, else the register minimising `last-use time + 300 if value ≤ 65,536 + useW · use count − bitW · log2(value)`, skipping values the rest of the current plan needs. In words: least recently used, small values protected, optionally large values first. [src-full] — [solver.cpp](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/src/solver.cpp)
- Rudolph's acceptance rule counts compiled length "rebuilds included (closure size missed register rebuilds)". [src-full] — [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp)

Pseudocode in my own words (compile with farthest-next-use eviction):

```
compile(recipes, targets):
    seq = values needed by targets, in dependency order (depth-first per target)
    next_use[v] = positions in seq where v is an operand
    bank = start values
    for v in seq: emit(v, locked = {})

emit(v, locked):
    if v in bank: return its register
    ra = emit(recipe(v).a, locked); rb = emit(recipe(v).b, locked + {ra})   # may rebuild evicted operands
    dest = an empty register, else the unlocked non-start register whose value is used farthest ahead
           (cost-aware variant: maximise distance / (1 + rebuild_cost)^1.5)
    write v to dest; append instruction; return dest
```

### Inferences

- (Inference) In all public constructors the 48-register limit shows up as extra rebuild instructions at compile time, never as a failed plan. The planning dictionary is limited to 56–112 leaves by parameter, not by the bank, so plans routinely assume values that are no longer resident; modes 4 and 5 and the virtual bank exist to charge for that.
- (Inference) This "plan on the value graph, compile with rebuilds, accept by compiled length" split is the main architectural difference from a solver that keeps the real bank as its pool. It lets the leaf set exceed 48 and makes the dictionary independent of eviction order.

### Gaps

- No measurement was found of how many instructions in constructor output are rebuilds, or of the gain from cost-aware eviction over plain farthest-use. Round one found that re-allocation alone and a 72-register search both gave zero on later programs.
- `konbu17`'s own planner code was not read; "virtual-register plans" is known from a credit line and from `munhof`'s re-implementation.

## 6. Differences between the public engines, and the fall of the public merge from 132,477 to 128,501

### Takeaway

All beam constructors descend from one base and differ in leaf policy, extra moves, target order and post-passes; alone they score about 160–170 thousand, which is worse than our current 143,891. The public merge reached 142k within a day and 128.5k within a week through value-graph optimisers applied on top, and nothing read describes what produced the 3,976-instruction drop between 2026-11-21 and 2026-11-24.

### Cited Findings

**Lineage and differences**

| Engine | Relation to base | Leaves | Extra moves | Order | Post-pass | Reported score |
|---|---|---|---|---|---|---|
| `tonylica` | base | palette + starts + largest earlier targets to 52 + newest values to 56 | — | input (ascending) | none | not found |
| `konbu17` | same code, parameters exposed; portfolio, planner, re-allocation | 72/88 to 80/112 in the settings seen | — | cheapest-target ordering credited | exact graph rewrites credited | title 163k; dataset 160,175 (2026-11-18) |
| `alexchilton` Rudolph | own implementation of the mechanism | no palette; small values first, 60/80 | wider nearest lists, whole-dictionary factors at the root, optional product link | cheapest first for HEAD picks | ruin-and-recreate, pair ruin, 4 schedules | practice 32,842 (2026-11-18 comments) |
| `arsen123` | own implementation; "conceptual attribution, not copied code" | palette (two styles) + recent goals to 3/4 + newest nodes; 64–128 | later: squares, perfect-square move, exact quotients | input, reversed, shuffled, cheapest, shortlist | one-instruction alternative recipes by reachable size; cost-aware eviction | not found for the constructor alone |
| `Juan-Severiano` `beam_search.cpp` | derived from the two above | as `konbu17`; mode 5 resident-only | — | modes 0–5 | modes 6–9 repair an existing program | 159,737 from 160,175 (2026-11-18) |
| `pablodiegoo` Atlas | separate C++20 program | Beam DAG (10, .18, 48, 56) | real-machine fallback | — | peephole, cofactor cuts, reversal, windows, scaffold exchange | 138,601 → 138,592 as a post-optimiser in one ablation |
| `Yukisiooisiiyo` | independent design | the real register contents | square root, halving, quotient/remainder role swap | 1-step targets, vote, cheapest of N smallest | dead-code removal | practice 32,580; README estimates about 165,000 scored |
| `munhof` | own digit/window constructors; planner experiment inside the base engine | residents of a virtual bank | — | policies 0–2 | — | own constructors 724,927; 0 saved on a 130,922 public reference |

Sources for the table: [tony.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/tony.cpp), [konbu.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/konbu.cpp), [rudolph.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/rudolph.cpp), [recovered/solver.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/recovered/solver.cpp), [arsen_current/SOURCES.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/arsen_current/SOURCES.md), [beam_search.cpp](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/cpp/beam_search.cpp), [atlas.cpp](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/generative/atlas.cpp), [Yukisiooisiiyo solver.cpp](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/src/solver.cpp) and [README](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/README.md), [munhof README](https://raw.githubusercontent.com/munhof/kaggle.1-santa2026/HEAD/README.md), [Juan-Severiano README](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/README.md). Tags: src-full or src-part as in the table at the top; scores are [doc] except Rudolph's, which are source comments.

- `Yukisiooisiiyo` reduction search in detail: best-first on `g + log2(v)/5.5` with at most 200 expansions (100 in the portfolio); each popped value is first tried by an exact search to depth 3 (4 with a two-step table, 5 at the root at the highest effort); moves are square root and halving (cost 1), `v = q·b + r` or `(q+1)·b − r'` with b in the pool and the remainder within two instructions, the same with roles swapped (recurse on the remainder when the quotient is within two instructions), `v = child·b ± c` with both b and c in the pool, the same with b a one-step value of at least 16, and `v = child ± a` with a in the pool or one of the 8 nearest one-step values; a move must remove at least 2.5 bits per instruction. A second pass relaxes that to 0.3 bits with 2,000 expansions, and a quotient-remainder recursion on the largest usable base is the last resort. [src-full] — [solver.cpp](https://raw.githubusercontent.com/Yukisiooisiiyo/kaggle-santa/HEAD/src/solver.cpp)
- `Juan-Severiano`'s own digit and window construction reached 233,968 (2026-11-18), and its Rust ports "retain the dictionary, backward search, graph repair and 48-register allocator; they do not introduce a new search algorithm". [doc] — [README](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/README.md); [THIRD_PARTY.md](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/THIRD_PARTY.md)
- The `goodpjw2008` dataset code is not a constructor: `elfopt.cpp` is a value-DAG search crediting `prvsiyan`'s neighbourhood design, and the dataset also redistributes `atakanaldemir`'s multiplier-frontier sources unchanged. [doc] — [THIRD_PARTY.md](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/THIRD_PARTY.md); [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)
- A Rudolph programs dataset (version 51) scored 135,806, the same total as a merged public release of that time, with zero rows shorter than a 135,161 parent. A total at that level cannot be constructor output alone (the constructor's practice figures correspond to about 167,000), so the published dataset includes merged or optimised programs. [doc; the last sentence is an inference] — [methods.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/methods.md)

**How fast public programs left constructor level**

- 2026-11-18: `konbu17` programs 160,175; `hanifnoerrofiq` "peephole programs" version 4 at 144,248; `atakanaldemir` "Joint Recipes for Large Puzzles" version 2 at 142,272 and version 8 at 141,394. [doc] — [Juan-Severiano README](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/README.md); [THIRD_PARTY.md](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/THIRD_PARTY.md)
- Gains the author of the joint-recipes notebook attributes to algorithms and not to imported programs: 138,905 → 138,769 (multiplier lanes, 88 of 635 cases), 138,769 → 138,681 (multiplier frontier, 60 of 238 cases), 138,681 → 138,667 (block rebuild of four to eight targets, 13 cases), 138,280 → 138,273 (interface rebuilding). [doc, third-party summary] — [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)

**The fall from 132,477 to 128,501**

- The log has consecutive entries "2026-11-21 21:18 BJT: 132,477" and "2026-11-24 10:12 BJT: 700 puzzles saved 3,976 in total, combined candidate 128,501", with nothing in between and no description of the cause; both link to the same reconstruction note. [src-part] — [PROGRESS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/PROGRESS.md)
- The current reconstruction note names three inputs (`goodpjw2008` dataset version 239, the `submission.csv` of `ozertuu`'s notebook run 373317540, `asteriospanoras` dataset version 373) and credits the last single-instruction change (128,492 → 128,491, puzzle 93) to `ozertuu`. Its metadata file holds only hashes and that one credit, no per-source counts. [doc] — [portfolio.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/releases/portfolio.md); [portfolio.json](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/releases/portfolio.json)
- Intermediate public checkpoints from other repositories: `goodpjw2008` dataset version 50 = 132,543 and version 55 = 132,516 (both 2026-11-21, the latter read about 15:00 UTC); version 169 = 130,922, called the shortest public program for every puzzle in a README last committed 2026-11-22 23:36 UTC; `avazaku` "Elf Calc Backward Frontier Rewrite" version 30 = 130,943. Round one's notes add version 72 = 130,976 from another repository's README, which was not re-read here. [doc] — [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md); [munhof README](https://raw.githubusercontent.com/munhof/kaggle.1-santa2026/HEAD/README.md)
- Earlier on 2026-11-21 the same log's merges moved by a few instructions per public release (for example 133,816 → 133,798 → 133,772 over a morning, each from named dataset versions and re-run public searches). [doc] — [releases README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/releases/README.md)

### Inferences

- (Inference) The premise that public constructors spend 4.4 instructions per later target is not supported. That figure is from the optimised 134,568 set. The constructors score about 160–170 thousand, roughly 6 instructions per missing target overall (160,175 / 26,898); the drop from 160k to 142k took one day and came from peephole rewriting and joint recipe re-pricing, and the rest from value-graph search and recombination over the following days.
- (Inference) What the public constructors do offer us is a different candidate space, not a better constructor: a multi-million-entry two-step dictionary rebuilt per target over 56–112 leaves that include all earlier targets, lazy palette values, planning on a value graph with rebuild-on-demand compilation. Their programs would be new raw material for our value-graph search and recipe pool.
- (Inference) The 3,976 drop was not uniform in time: about 1,550 between 2026-11-21 13:18 UTC and 2026-11-22 23:36 UTC (132,477 → 130,922), then about 2,420 in the next 27 hours. The `goodpjw2008` dataset moved only 54 between versions 72 and 169 (130,976 → 130,922), so the second part looks like a step change entering the public pool on 2026-11-23 or early 2026-11-24 UTC, either in versions 170–239 of that dataset or through the `ozertuu` run. With 700 puzzles improved by 5.7 on average, it was a broad change across most puzzles, not a handful of special cases.
- (Inference) The dataset's version count (55 on 2026-11-21 about 15:00 UTC, 239 by 2026-11-24 05:21 UTC, one version about every 20 minutes) indicates an automated loop that optimises and re-uploads continuously. A constructor change would not produce that pattern; an optimiser running on existing programs would.

### Gaps

- What produced the drop is not described in anything read. The `goodpjw2008` dataset pages for versions 170–239, the `ozertuu` notebook and the `asteriospanoras` dataset version 373 could not be read, and their standalone scores were not found. A web search for the notebook was refused by the organisation's content policy because the query contained an account handle.
- `elfopt.cpp` was not read in this round (no copy under that name in the files listed; a Rust adaptation exists at `rust/lns.rs` in the `Juan-Severiano` repository, not read).
- `tonylica`'s single-setting score on the 1,000 scored puzzles was not found, so the table has no baseline for the base engine.
- GitHub code search for engine file names and for newer repositories was not possible: the unauthenticated API was rate-limited throughout.
