# Register fit and repair inside a local search: fast order checks, local reordering and recomputation for a 150–250 node value DAG under 48 registers

Research date: 2026-11-24. Scope: only material that is not in the round-one notes (`register_constrained_scheduling.md`) or the three reports. Round-one results (Belady optimality for a fixed order, Chen's CP-SAT, Moccasin/Checkmate, Bouchez–Darte–Rastello, Farach–Liberatore, Austrin et al.) are referred to as "round one" and not re-described.

Verification labels on every claim:

- **[V]** verified by me against the source's full text (PDF downloaded, text extracted, passage read).
- **[A]** only the abstract was verified.
- **[U]** unverified: from a search summary or a secondary description.
- **[inference]** my own mapping, derivation or estimate; no source states it. All microsecond/millisecond figures for our setting are estimates of this kind and are unmeasured.

Model used throughout [inference, consistent with round one]. An order is a topological order σ of the value DAG. Start values sit at position 0. `last[u]` is the position of the last consumer of u. A value occupies a register on the gaps between its definition and its last use. Because an instruction may overwrite one of its own operands, the register need of step t is

    need(t) = live_before(t) + (0 if some operand of σ[t] has its last use at t, else 1)

and the order fits iff max need ≤ 48. A target with no consumers has an empty interval and costs only the transient "+1". The decision problem "does some order fit" is the one-shot black pebble game with the slide move.

Headline answer: no published method decides width 48 on about 200 nodes exactly in milliseconds, and none is close. What the literature does supply is (a) a set of pruning and locality ideas that make a heuristic check cheap and incremental, (b) two safe dominance rules that shrink the search to the real decisions, and (c) a clean way to treat recomputation as a DAG edit. Sound cheap lower bounds are weak at this width; the quick-reject step has to be mostly statistical.

## 1. Memory-aware scheduling of computation graphs in ML compilers: what sizes are solved exactly, how fast, and what survives with unit sizes

### Takeaway
The exact dynamic program over frontiers (Serenity) is infeasible beyond roughly 20–35 nodes per independent partition, and every later system (HMCOS, Zhong et al., MODeL) gets its speed from structure our DAGs lack: hourglass cut points, cells, long linear chains and narrow ASAP/ALAP windows. The ideas that survive at unit size are the state signature (the set of scheduled nodes), pruning against a fixed budget, re-scheduling only the part of the graph that touches the peak, and fusing nodes that are provably safe to run immediately.

### Cited Findings

**Serenity (Ahn et al., MLSys 2020), details not in round one**
- [V] The DP memoises on the "zero-indegree set" z (the set of nodes ready to run) as the signature of a partial schedule and keeps, per signature, only the partial schedule with the lowest peak; complexity is O(|V|·2^|V|) against O(|V|!) for enumeration. — [Ahn et al., arXiv:2003.02369](https://arxiv.org/abs/2003.02369)
- [V] Table 2, SwiftNet: the DP alone on the 62-node graph is "N/A" ("infeasible within practical time"); with divide-and-conquer into partitions of 21, 19 and 22 nodes it takes 56.5 s; adding adaptive soft budgeting, 37.9 s. After graph rewriting (92 nodes, partitions 33, 28, 29) divide-and-conquer alone takes 7.2 hours and with soft budgeting 111.9 s. — [same](https://arxiv.org/abs/2003.02369)
- [V] Adaptive soft budgeting: the peak of a Kahn-order schedule is the "hard budget" τ_max; partial schedules whose peak exceeds a soft budget τ are pruned; τ is found by binary search with a per-step time limit T ('no solution' raises τ to (τ_new + τ_old)/2, 'timeout' halves it) and the search stops at the first 'solution'. — [same](https://arxiv.org/abs/2003.02369)
- [V] Average scheduling time over the benchmark networks: 40.6 s without rewriting, 48.8 s with. Among the possible schedules of SwiftNet Cell A, "only 0.04% would achieve the optimal peak memory". — [same](https://arxiv.org/abs/2003.02369)
- [V] The same DP, written as a memoised recursion over the set of tensors that must be in memory ("undoing" the operator that produced one of them), with complexity O(|V|·2^|V|), is given for microcontroller inference. — [Liberis & Lane, arXiv:1910.05110](https://arxiv.org/abs/1910.05110)

**HMCOS (Wang et al., DAC 2022)**
- [V] Stated limits of Serenity: it "only works for hourglass-shaped networks where cells are sequentially concatenated" and "usually takes hours to produce a schedule for a network". — [Wang et al., DAC 2022, PDF](https://chengcheng-wan.github.io/paper/22-DAC.pdf)
- [V] Two hierarchy levels. A *sequence* is a chain of operators (each with one predecessor and one successor inside the chain) whose transient footprints are non-increasing; such a sequence "is always safe to schedule as a whole". A *group* is built from the cells given by the architecture search, refined with a dominator tree. — [same](https://chengcheng-wan.github.io/paper/22-DAC.pdf)
- [V] Iterative scheduling: schedule the hierarchical graph (Serenity-style DP on groups), locate the peak, and disassemble "only the peak-related vertices of the hierarchical graph"; repeat until no group is disassembled. The budget of each iteration is the peak of the previous one (no hyperparameter), and optimal group schedules are memoised under a key describing the group's context. Footprints are computed incrementally from per-step differences. — [same](https://chengcheng-wan.github.io/paper/22-DAC.pdf)
- [V] Table 1 scheduling times (row grouping read from a text extraction): CIFAR-10 NASNet-A 40.05 s, AmoebaNet-A 1.57 s, DARTS 0.97 s; ImageNet NASNet-A 0.207 s, AmoebaNet-A 0.065 s, DARTS 0.042 s; RandWire 1–3: 20, 39, 68 s against 5,659, 5,358 and 10,247 s for the authors' re-implementation of Serenity (137–283× faster). Peak memory is 8.7–42.4% below reverse postorder. All CIFAR-10 networks finish in three iterations, ImageNet ones in two, and "at most 20% of the sequences are freed from their original groups". — [same](https://chengcheng-wan.github.io/paper/22-DAC.pdf)

**Zhong et al. (ICCAD 2023)**
- [V] Both Serenity and HMCOS need "more than 10 hours" on multi-scale networks such as HRNet. Table III: HMCOS 30000+ s on three HRNets against 0.96, 5.01 and 3.20 s for the new method; on the other networks 0.09–23 s against 0.18–73 s for HMCOS (NASNet-A is slower: 4.62 s against 1.51 s). — [Zhong et al., arXiv:2308.13898](https://arxiv.org/abs/2308.13898)
- [V] Method: (1) iterative sub-graph fusion with an optimality guarantee: a sub-graph is replaced by one hypernode when its footprint profile satisfies stated conditions. Theorem IV.1 (linear sequence): transient footprints are monotonically non-decreasing along the sequence (t^i ≤ t^j for i < j) and no stable footprint exceeds the last one. Theorem IV.2 (isolated sub-graph): the transient footprint inside never drops below the entry level or the exit level (t^i ≥ t^0 and t^i ≥ t^n), so nothing is gained by pausing inside it. (2) Acyclic partitioning (dagP). (3) An ILP solved only on the partitions that contain the operators at the peak of a reverse-postorder schedule, the other partitions keeping reverse postorder. (4) Variable pruning from topology, e.g. operator i cannot run in the first |anc(i)| steps. The ILP time limit is 30 s and the incumbent is taken. Average peak reduction over prior methods 13.4%. — [same](https://arxiv.org/abs/2308.13898)
- [V, column headers garbled in extraction] Table IV: pruning and partitioning remove roughly 55–91% of ILP variables depending on network and configuration, and the leading time column reads ">3600" s for all three example networks, which I read as the baseline without these reductions. — [same](https://arxiv.org/abs/2308.13898)

**MODeL / OLLA (Steiner et al., ICML 2023), full text**
- [V] Ordering ILP with 2·|E|·|V| binary variables (tensor created / preserved at each step). Each node may run only inside [ASAP(v), ALAP(v)]; variables outside the span are fixed. Solver: Gurobi 9.1.1. — [Steiner et al., arXiv:2210.12924](https://arxiv.org/abs/2210.12924)
- [V] Graphs from 118 operators (AlexNet) to 2,007 (XLM-R). Node-ordering time: median 1.4 ± 0.2 s, best case 100 ms, worst case 5.2 s excluding EfficientNet, which needs 2 minutes for the optimum at batch size 1 and 5 minutes to get within 1% at batch size 32. — [same](https://arxiv.org/abs/2210.12924)

**Conflict between sources**
- [V] HMCOS's own table gives 40.05 s (CIFAR-10) and 0.207 s (ImageNet) for NASNet-A; Zhong et al. report 1.51 s for HMCOS on "NASNet-A". Different network variants and machines; the two papers' absolute times should not be compared with each other. — [Wang et al.](https://chengcheng-wan.github.io/paper/22-DAC.pdf); [Zhong et al.](https://arxiv.org/abs/2308.13898)

### Inferences
All [inference].

| Idea | Survives with unit sizes and budget 48? | How it maps | Why it might not transfer |
|---|---|---|---|
| Signature = set of scheduled nodes; one schedule kept per signature | Yes, and it simplifies: with unit sizes the live set is a function of the scheduled set, so the decision problem is reachability over down-sets whose boundary is ≤ 48. | Memo table keyed by a 256-bit mask in any exact or beam search (section 7, tiers 3). | The number of reachable down-sets is exponential in the DAG's width (antichain size); our DAGs have ~30 nearly independent targets, so the unpruned state space is hopeless (cf. 62 nodes "N/A"). |
| Soft budget τ | Yes, trivially: we have a decision problem, so τ = 48 is fixed and no binary search is needed. Every partial order whose need exceeds 48 is cut at once. | Hard pruning in all search tiers. | Pruning only bites when the budget is tight; when it is tight the instance is also likely infeasible, and proving that still needs the whole space. |
| Divide-and-conquer at hourglass points | Mostly no. A cut point is a single value through which everything flows; a 30-target DAG with shared helpers has none. | Replace by a *time window*: fix the prefix and suffix of the current order and re-schedule only a window of 20–60 consecutive nodes exactly. | A window of 20–30 nodes is at the edge of what Serenity solves in tens of seconds; in our case budget pruning and the safe rules below must carry it, which is unmeasured. |
| HMCOS sequences / Zhong fusion | Yes, as a principle (nodes that are provably safe to run at once need no decision). With unit sizes its role is played by two rules I derive separately: a ready node that kills one of its operands can be run immediately (rule R1), and a ready target with no consumers can be run as soon as one register is free (rule R2). Proof sketches in section 7; they do not rely on the papers' theorems. | Applied as a closure after every decision; the search branches only on nodes that open a new register. | None structural; the exchange arguments rely only on unit sizes and one-shot semantics. |
| Peak-focused re-scheduling (HMCOS iterations, Zhong's "ILP only where the peak is") | Yes. | Only values whose interval covers an overfull step, and nodes whose slack window meets the overfull region, are move candidates. | HMCOS reports ≤ 20% of sequences touched on cell-structured networks; on our DAGs the overfull region may span most of the program. |
| ASAP/ALAP span pruning (MODeL, Zhong) | Weakly. | A node's legal positions are (last operand, first consumer); use this as the move range for insertion moves. | ML graphs are near-linear, so spans are short and the ILP collapses; in a DAG with 30 targets and little depth the spans are a large fraction of the program, so the ILP pruning that makes MODeL fast gives little. |
| Size-driven heuristics, concat rewriting, arena placement | No. | — | Unit sizes; register assignment for intervals is trivial (round one). |

- Speed conclusion: the fastest exact figures on a few hundred nodes are MODeL's 0.1–5 s (commercial ILP, near-linear graphs) and HMCOS/Zhong's 0.04–70 s (cell-structured graphs). Nothing in this literature runs in milliseconds on an unstructured 200-node DAG, and each system's failure cases (Serenity on 62 nodes unpartitioned, HMCOS and Serenity > 10 h on HRNet, unpartitioned ILP > 1 h) are exactly the unstructured ones.

### Gaps
- The operator counts of the HMCOS and Zhong benchmark networks were not in the text I extracted, so "seconds on a few hundred nodes" cannot be stated per network.
- Serenity is not public (HMCOS re-implemented it); its timings may be dominated by implementation language. No source gives a C++ timing of the frontier DP.
- No ML-compiler paper tests unit sizes with a tight budget on unstructured DAGs.
- Not searched: TelaMalloc and other placement-only planners (irrelevant with unit sizes); a 2023–2026 follow-up to HMCOS/Zhong may exist that I did not find.

## 2. Peak-memory scheduling theory for trees, series-parallel graphs and general DAGs

### Takeaway
The polynomial cases are in-trees/out-trees (Liu, O(n²)) and series-parallel graphs (Kayaaslan et al., O(n³)); for general DAGs the authors only suggest converting to series-parallel first and report no measured gap. The transferable content is the hill–valley principle (interleave independent sub-computations only at local minima, taking first the segment with the largest hill minus valley) and the dominant-schedule/linearization result that lets a locally optimal sub-order be frozen into a chain.

### Cited Findings
- [V] Liu's algorithm for in-trees: recursively compute an optimal traversal of each child subtree, cut each into *segments* ending at *valleys* (particular local minima of the memory profile; the maximum inside a segment is its *hill*), then merge the segment lists by repeatedly taking the available segment with the largest (hill − valley). An optimal traversal "may switch from one subtree to another", but only at valleys. Worst-case O(n²). An out-tree is handled by reversing edges and reversing the schedule. — [Kayaaslan, Lambert, Marchal & Uçar, TCS 707 (2018), PDF](https://perso.ens-lyon.fr/loris.marchal/docs-data-aware/tcs18-series-parallel-memory.pdf)
- [V] The problem is a weighted variant of minimum cut linear arrangement; the paper extends the polynomial class from rooted trees to series-parallel graphs. Parallel-chain graphs are solved by removing a minimum-weight edge from each chain, which leaves an in-tree and an out-tree, and calling Liu's algorithm twice; the general SP algorithm recurses on the decomposition and runs in O(n³). — [same](https://perso.ens-lyon.fr/loris.marchal/docs-data-aware/tcs18-series-parallel-memory.pdf)
- [V] For general graphs the paper only says the algorithm "may be applied to general graphs, if we first transform them into series-parallel graphs, for example using the SP-ization process"; no experiment is given. — [same](https://perso.ens-lyon.fr/loris.marchal/docs-data-aware/tcs18-series-parallel-memory.pdf)
- [V] Every DAG has a *dominant schedule*: "For any directed acyclic graph G = (V, E) with node weights w_v ∈ R, there exists a schedule σ of G that dominates all schedules of G" (lower peaks and lower valleys simultaneously). Given an oracle for a peak-minimising schedule, "a linear number of calls to it suffices to compute a dominant schedule". — [Jin, Purohit, Svitkina, Vee & Wang, arXiv:2312.13526](https://arxiv.org/abs/2312.13526)
- [V] Linearization: "replacing an isolated subgraph with the directed path induced by its dominant schedule results in a (simpler) graph whose optimal peak memory is identical to the original". For series-parallel graphs this gives an algorithm in 2^O(d log d)·poly(n) time, d the maximum out-degree; the exponential dependence on d is necessary (hardness already for out-trees and "pumpkins"). — [same](https://arxiv.org/abs/2312.13526)
- [V] In the model where every edge carries its own data item, the *maximum* peak memory over all schedules (the "maximum topological cut") is computable in polynomial time, by a linear program or by one max-flow computation plus linear work. For each parallel execution there is a sequential schedule with equal peak (Theorem 1). — [Marchal, Simon & Vivien, JPDC 2019, PDF](https://perso.ens-lyon.fr/loris.marchal/docs-data-aware/jpdc18-bertrand-memory.pdf)
- [V] Shared outputs (one value used by several successors, which is the pebble game and our model) are handled by a transformation with twice as many nodes. The transformation preserves what can be achieved when *minimising* memory, but it "overestimates the maximal peak memory", and "the complexity of computing maximal peak memory with shared data is different"; the authors settle for the upper bound, which "guarantees that the maximum peak memory of the original graph is also below the prescribed bound". The shared-data result is "inspired and adapted from the work of Touati … which studies the maximum number of registers". — [same](https://perso.ens-lyon.fr/loris.marchal/docs-data-aware/jpdc18-bertrand-memory.pdf)
- [V] Deciding whether a DAG can be scheduled within a memory limit is NP-complete in that model (Theorem 4, by reduction from the pebble game). — [same](https://perso.ens-lyon.fr/loris.marchal/docs-data-aware/jpdc18-bertrand-memory.pdf)

### Inferences
All [inference].

- Tree part of our DAG. A value with a single consumer hangs in an in-tree fragment below that consumer. For such fragments the Sethi–Ullman/Liu order is exact, and with unit sizes and in-degree 2 it is the usual rule "evaluate the operand whose sub-tree needs more registers first". This is already implied by rule R1 plus a depth-first priority, so nothing new has to be coded for it.
- Hill–valley rule for interleaving targets. Treat "everything still missing to complete target T from the currently live values" as a segment with hill = extra registers needed at its worst step and valley = net change in live count once T is emitted and its private values are dead. Liu's rule then says: among segments that can be started, prefer the largest (hill − valley), i.e. do first the work that has a high transient need but leaves little behind. This is a principled priority for the greedy constructor in section 7 (priority P3). It is exact only for trees; with shared helpers the segments are not independent, so it is a heuristic.
- Linearization as a cache. If a sub-DAG is isolated (its internal values are not used outside except through its outputs) and has been scheduled well once, it can be frozen into a chain and treated as one unit in later checks. In a local search this means: after a move touches one target's private cone, only that cone needs re-ordering; the others keep their frozen chains and the chains are re-merged at valleys.
- Maximum topological cut as an accept test. If an upper bound on the largest possible live set over all orders is ≤ 48, every order fits and the check can be skipped. In our shared-value model the polynomial algorithm gives only such an upper bound (it counts a value once per consumer), and the exact maximum is the register-saturation problem. For 150–250 node DAGs with 30 targets the bound will almost always exceed 48, so its only use is on small sub-DAGs or windows.
- Why it might not transfer: SP-ization adds synchronisation constraints that can only raise the peak, and no source measures by how much; our DAGs are far from series-parallel (helpers shared by many targets form dense bipartite-like sharing).

### Gaps
- No measured optimality gap of any Marchal/Vivien-group heuristic on general DAGs was found in the texts read. I recall that an implementation of the series-parallel approach for general DAGs exists and is used in later workflow-mapping papers, but I did not locate or verify it.
- Liu's 1987 paper itself was not read; its content is taken from the description in Kayaaslan et al.
- A 2026 JPDC paper from the same group on average (not peak) memory appeared in search results and was not read: [Obrecht et al., publication page](https://perso.ens-lyon.fr/adrien.obrecht/publications/2026-07-jpdc/) [U].

## 3. Exact methods that are fast at small width: branch and bound, live-set DP, pathwidth and vertex-separation solvers. Is width 48 on about 200 nodes within reach in milliseconds?

### Takeaway
No. Published exact solvers for vertex separation and pathwidth close instances of 10–80 vertices with widths of 4–12 in seconds to minutes, the frontier DP dies at about 60 nodes without decomposition, and fixed-parameter methods are exponential in the width, which makes 48 unreachable. Exactness is only affordable on a window of a few dozen nodes, or offline with the round-one CP-SAT model.

### Cited Findings
- [V] Vertex separation: for an ordering of the vertices, the *guards* of a prefix S are the vertices of S with a neighbour outside S; a graph has vertex separation number ≤ ω iff some ordering has at most ω guards for every prefix, and "G has vertex separation number at most ω if and only if G has pathwidth at most ω". — [Lodha, Ordyniak & Szeider, "SAT-Encodings for Special Treewidth and Pathwidth", TU Wien AC-TR-17-012](https://www.ac.tuwien.ac.at/files/tr/ac-tr-17-012.pdf)
- [V] Same report, experiments: each SAT call has a 1,000 s timeout (8 GB memory, Minisat/Glucose/MapleSAT). On the named-graph benchmark (10–78 vertices) the pathwidth encodings give, for example (column assignment inferred from the extracted table): Petersen (10 vertices) pathwidth 5 in about 0.3 s; Paley17 (17 vertices, 68 edges) pathwidth 12 in 27–107 s; Holt (27 vertices) pathwidth 10 in 386 s with one encoding and only an interval 8–10 with the other; Watsin (50 vertices) 7 in 77 s; B10Cage (70 vertices) left open at 8–16; Ellingham (78 vertices) 6 in 23 s. The best pathwidth encoding reaches square grids of 81 vertices. — [same](https://www.ac.tuwien.ac.at/files/tr/ac-tr-17-012.pdf)
- [U] Branch and bound for pathwidth / directed vertex separation with preprocessing and prefix-based cuts: the 2014 version computes "the exact pathwidth of any graph with less than 60 nodes in a reasonable running-time (≤ 10 min.)", and works well as a heuristic under a time limit. Still unread: both the HAL and the CORE copies refused automated download. — [Coudert, Mazauric & Nisse, ACM JEA 21 (2016), HAL record](https://hal.archives-ouvertes.fr/hal-01266496)
- [V] Frontier DP: O(|V|·2^|V|); infeasible on 62 nodes unpartitioned; 38–57 s when split into three parts of about 20 nodes (section 1). — [Ahn et al., arXiv:2003.02369](https://arxiv.org/abs/2003.02369)
- [V] 0-1 model for vertex separation with O(m·n²) variables and O(m·n³) constraints, "impractical for relatively large instances": CPLEX obtains the optimum only for the smallest instances within a 5,400 s limit and runs out of memory on others, while the metaheuristic reaches the known optima of the instances the text refers to in 0.36 s on average. — [Duarte et al., "Variable neighborhood search for the Vertex Separation Problem", Computers & OR 39 (2012), PDF](https://jesussanchezoro.github.io/publications/duarte2012a.pdf)
- [U] A search for a PACE challenge track on pathwidth or vertex separation found none; the PACE treewidth tracks (2016, 2017) are the nearest, and the search summary describes exact width solvers as limited to "about hundred vertices". Absence of a search hit is not proof that no such track exists. — [SAT-based local improvement paper found in the search](https://www.cs.uni-potsdam.de/wv/publications/DBLP_conf/sat/FichteLS17.pdf)

### Inferences
All [inference].

- Relation to our problem. For a topological order of the value DAG, the live set after each step is exactly the guard set of the prefix in the underlying undirected graph. So register need ≥ pathwidth of the underlying graph, with equality not guaranteed because pathwidth may use non-topological orderings. A generic pathwidth solver therefore solves a relaxation: it can certify infeasibility but its orderings are usually not valid programs. Directed pathwidth is of no use (it is 0 for any DAG).
- Milliseconds at width 48: out of reach by two to three orders of magnitude in size and by the nature of the parameter. The decision is one-sided, though: any order that fits is a certificate, so heuristics give exact "yes" answers; only "no" answers are uncertain. In a local search a false "no" costs one lost move, so the right question is not exactness but the false-rejection rate per microsecond spent.
- Where exactness is affordable. (1) A window of W consecutive nodes with prefix and suffix fixed: states are down-sets of the window's sub-DAG; with pruning at 48 and rules R1/R2 the reachable set is usually far below 2^W. A cap on states per layer turns it into a beam search that is exact whenever the cap is not hit. (2) Offline, on the few rejected candidates per puzzle with the largest gain, the round-one CP-SAT model in decision form.
- Dominance rules worth having in any branch and bound over orders (the two safe ones are proved in section 7): R1 kill-first, R2 emit-free-targets, plus signature memoisation. With R1 and R2 the remaining branching is over "which value to open next", which is the real combinatorial core.

### Gaps
- Coudert–Mazauric–Nisse remains unread; their cut rules (which may include further dominance tests usable here) are known to me only by title-level description.
- I found no implementation or paper for an exact one-shot pebbling decision procedure restricted to topological orders that reports timings at width > 15.
- The SAT-encoding numbers come from a 2017 report; newer solvers may shift the limits somewhat but not by the two orders of magnitude needed.

## 4. Incremental repair: fixing an existing order locally when a few nodes change

### Takeaway
Three published mechanisms combine into an incremental check: dynamic topological ordering confines re-ordering to the "affected region" between the two endpoints of a violated edge; in vertex-separation local search a move between positions p and q changes the cut values only inside [p, q), with an efficient insert-move implementation reported about 1,000 times faster than full re-evaluation; and ML schedulers re-solve only the part of the graph that touches the peak. I found no paper that does incremental peak-memory re-scheduling under DAG edits as such.

### Cited Findings
- [V] Dynamic topological order: for an inserted edge x → y that violates the current order, the affected region is {k : ord(y) ≤ ord(k) ≤ ord(x)}; "One feature common to all the algorithms we will consider is that they only reorder vertices within the affected region", and only the vertices in the region that reach x or are reachable from y need to move. The authors' algorithm is, in their experiments on random DAGs, "the best for sparse digraphs and only a constant factor slower than the best on dense digraphs". — [Pearce & Kelly, ACM JEA 11 (2006), preprint PDF](https://whileydave.com/publications/PK07_JEA_preprint.pdf)
- [V] Vertex-separation local search, incremental evaluation: evaluating a layout directly is O(n²) in the worst case, but after Move(φ, p, q) "all vertices with label r for 1 ≤ r < p or q ≤ r ≤ n do not change their Cut-values", so only positions p ≤ s < q are updated. — [Duarte et al. 2012, PDF](https://jesussanchezoro.github.io/publications/duarte2012a.pdf)
- [V] Insert moves implemented as a sequence of adjacent swaps with incremental update: "about 40 times faster than the incremental computation described in [the 2012 paper] and … about 1000 times faster than the direct computation of the objective function"; the 2012 incremental scheme itself was about 25 times faster than direct computation. — [Sánchez-Oro, Pantrigo & Duarte, Computers & OR 52 (2014), PDF](https://jesussanchezoro.github.io/publications/sanchezoro2014a.pdf)
- [V] Same paper: because vertex separation is a min–max objective, plain local search stalls on plateaus; the authors compare solutions with an extended evaluation that also counts how many positions attain each separation value, so a move that lowers the number of positions at the maximum counts as an improvement. Benchmarks: 62 Harwell–Boeing graphs, 50 grids (25–2,916 vertices), 50 trees (22–202 vertices); all grids are solved to the known optimum, 40 of 50 trees by the best variant, and local search runs take seconds per instance (e.g. 0.78–6.94 s average in the neighbourhood comparison). — [same](https://jesussanchezoro.github.io/publications/sanchezoro2014a.pdf)
- [V] Greedy constructors for vertex separation are 11–16% above the best known on average in the 2012 experiments (C1 11.24%, C2 15.66%), i.e. the same order of error as the list-scheduling figures of round one. — [Duarte et al. 2012, PDF](https://jesussanchezoro.github.io/publications/duarte2012a.pdf)
- [V] Peak-focused re-scheduling: HMCOS disassembles only groups related to the peak and touches at most 20% of sequences; Zhong et al. run the ILP only on partitions containing the peak operators and keep reverse postorder elsewhere. — [Wang et al.](https://chengcheng-wan.github.io/paper/22-DAC.pdf); [Zhong et al.](https://arxiv.org/abs/2308.13898)
- [V] Linearization (section 2) justifies freezing an isolated sub-DAG's order. — [Jin et al., arXiv:2312.13526](https://arxiv.org/abs/2312.13526)

### Inferences
All [inference].

- Incremental check for a local-search move. Keep the parent's fitting order. Delete removed nodes; insert each new node inside its slack window (after its last operand, before its first consumer); if a rewired consumer now precedes its new operand, repair precedence with a Pearce–Kelly shift inside the affected region. The live profile changes only between the smallest and largest touched position, because a value's interval changes only if its definition or its last consumer moved. At n ≤ 250 a full O(n) profile recomputation is already about a microsecond, so the locality matters less for speed than for *search focus*: it tells which steps became overfull and which nodes can relieve them.
- Insertion ("sift") moves on a topological order. Moving node v one position across an independent neighbour changes the live count at exactly one gap and the need of exactly two steps, so walking v across its whole slack window costs O(window). Sweeping all candidate nodes once costs at most O(n²) elementary updates (about 60,000 at n = 250), i.e. tens of microseconds.
- Objective for the sift. Use the plateau-breaking idea from the 2014 paper adapted to a threshold: primary key E = Σ_t max(0, need(t) − 48) ("excess area"), secondary key the number of steps at need = 48. E = 0 means the order fits.
- Why it might not transfer: the vertex-separation results are for undirected graphs with free orderings; our slack windows may be short for exactly the nodes that matter (a helper used early and late cannot move), in which case sifting cannot help and only recomputation (section 5) or a DAG change can.

### Gaps
- No source measures incremental re-scheduling for peak memory under graph edits; the combination above is mine.
- I did not check incremental register-allocation literature (e.g. re-allocation after small code edits in JIT compilers); it mostly concerns assignment, which is trivial here.
- The extended evaluation function of the 2014 paper was read from a partly garbled extraction; its exact formula should be taken from the PDF before re-use.

## 5. Recomputation as repair: which values to drop and rebuild for a fixed order, dropped operands, and when it pays

### Takeaway
Nothing new was found beyond round one on the exact side (uniform reload cost: farthest next use; fixed unequal costs: min-cost flow; dependent costs: hard). The practical additions are a constant-time approximation of "what it really costs to rebuild this value given what else is gone" from the DTR runtime, and a reformulation: one recomputation is a *node clone* in the value DAG, after which the ordinary one-shot check applies. A move that saves s instructions is worth keeping whenever it can be made to fit with fewer than s clones.

### Cited Findings
- [V] DTR's eviction score uses the *evicted neighbourhood* e*(t): the evicted tensors that would have to be recomputed along with t. Tracking it exactly is costly because "each new eviction can expand a given tensor's evicted neighborhood and each rematerialization can shrink it", so the runtime approximates it with "an undirected relaxation tracked by a union-find data structure that uses a constant-time approximation for splitting": evicted components are merged with running cost sums, and when a tensor is rematerialised its cost is simply subtracted from its component's sum and the tensor is mapped to a new empty component. — [Kirisame et al., arXiv:2006.09616](https://arxiv.org/abs/2006.09616)
- [V, sentence read only in part] Same paper: three variants are compared, the exact evicted-neighbourhood score, the equivalence-class (union-find) approximation, and a "local" score that uses only each tensor's own cost, the last serving to "assess the importance of tracking evicted neighborhoods". The text says the more complex scores "also introduce more runtime overhead" and that a cheaper variant "incurring much less runtime overhead suggests that it would be more effective in practice"; I did not extract the figures behind that sentence. — [same](https://arxiv.org/abs/2006.09616)
- [V] In the scheduling papers read for this round (HMCOS, Zhong et al., MODeL, the two vertex-separation local searches) a budget violation is handled by re-ordering only; none of them considers recomputation. Recomputation appears only in the rematerialisation line covered in round one (Checkmate, Moccasin, DTR, Kumar et al.). — [Wang et al.](https://chengcheng-wan.github.io/paper/22-DAC.pdf); [Zhong et al.](https://arxiv.org/abs/2308.13898); [Sánchez-Oro et al. 2014](https://jesussanchezoro.github.io/publications/sanchezoro2014a.pdf)

### Inferences
All [inference]. The exact results they lean on are in round one.

- Clone formulation. Recomputing value u before one of its later consumers is the same as adding a node u′ with the same two operands and moving a suffix of u's consumers to u′. Cost: one instruction. Effect: u's interval is cut into two pieces with a hole between a use and the rebuild. After the edit the DAG is again a one-shot instance, so every tool in this note still applies, and the local search can later delete the clone if room appears. This also means "recomputation repair" needs no separate simulator: it is one more move type.
- Fixed order, free rebuilds. Call a hole *free* if both operands of u are held at the rebuild point anyway. If only free holes are used, each hole costs 1 and relieves one register on a contiguous range of steps, and the task is to cover every overfull step t by at least need(t) − 48 holes. Constraint rows are intervals, so this is the totally unimodular interval case of round one: solvable exactly by min-cost flow, and with unit costs by a left-to-right sweep that, at each still-overfull step, drops the eligible value whose next use is farthest. That is Belady's rule restricted to values with free rebuilds.
- Dropped operands. The rebuild of u is a new use of u's operands. If an operand a is not held at the rebuild point, either a's interval is extended to that point (which costs a register on the extension and is useless if the extension crosses the overfull region) or a is cloned too (cost +1, recursively). For a repair budget of one or two clones the exact recursive cost can be computed by brute force to depth 1–2; the union-find approximation from DTR is only needed if repairs of many clones are attempted. A cost-aware score in the spirit of DTR and of the public compiler described in the brief is (distance to next use) / (1 + number of operands not held)^α; α = 0 is plain Belady.
- When it pays. Let s be the instructions the move saves before repair and k the clones needed. Accept iff s − k ≥ 1, or s − k ≥ 0 where equal-length moves are accepted. A move saving 2 with one clone is a net gain of 1; a move saving 1 can never be rescued by cloning and should stop after the re-ordering tiers. Cap k at s − 1 and at a small constant (2 or 3): the trade-off theorems of round one say that below the one-shot register need the cost can grow very fast, so a repair that has not succeeded after two or three clones is evidence of a structural deficit, not of a local one.
- Good clone candidates are recognisable before any search: values one instruction away from operands that stay alive for the whole program (start values still in use, small constants, values used by many later targets), with one early use and one late use and a long hole between them covering the overfull steps.
- Why it might not transfer: (a) the public experiments quoted in the reports found no gain from searching with more registers and compiling back to 48, which suggests that in well-optimised programs the values worth dropping are rarely cheap to rebuild; (b) our DAGs come from a search that already minimises instruction count, so values with a single-instruction rebuild from always-alive operands may be scarce; (c) a clone makes the program longer by one, which can push the candidate out of the acceptance band even if it fits.

### Gaps
- No new source on optimal spilling as min-cost flow was read in this round; the statements rest on round one.
- I found no published heuristic specifically for "rebuild needs operands that were also dropped" on straight-line code other than DTR's evicted-neighbourhood score (a runtime heuristic for tensors with sizes).
- Whether cheap-rebuild values exist in our programs in useful numbers is an empirical question nobody has measured; it should be counted before tier 4 is built.

## 6. Quick lower bounds on register need for rejecting hopeless candidates in microseconds

### Takeaway
I found no published cheap lower bound that is strong at width 48 on sparse in-degree-2 DAGs: degree-based pathwidth bounds are capped at 2 for such graphs, and the one-shot problem is hard to approximate (round one). The literature offers the opposite test, the maximum topological cut, which certifies that *every* order fits. A sound bound specific to our model (a clique of values whose lifetimes are forced to overlap) is cheap to compute but of unknown strength; the working quick-reject should be a calibrated, unsound threshold on the excess of the cheapest order.

### Cited Findings
- [V] Maximum topological cut (largest memory any schedule can reach) is polynomial when each edge carries its own data: LP, or one max-flow plus linear work. With shared outputs (our model) the same computation on the transformed graph only gives an upper bound on the maximum, which the authors use as a safe certificate; the exact shared-data problem has a different complexity and corresponds to Touati's register saturation. — [Marchal, Simon & Vivien, JPDC 2019, PDF](https://perso.ens-lyon.fr/loris.marchal/docs-data-aware/jpdc18-bertrand-memory.pdf)
- [V] Vertex separation equals pathwidth, so any pathwidth or treewidth lower bound applies to the minimum over *all* orderings of the guard count. — [Lodha, Ordyniak & Szeider, AC-TR-17-012](https://www.ac.tuwien.ac.at/files/tr/ac-tr-17-012.pdf)
- [U] Standard cheap treewidth lower bounds are degree-based: the degeneracy (maximum over subgraphs of the minimum degree, "MMD"), and the contraction degeneracy (maximum over minors of the minimum degree), approximated by the MMD+ heuristic that contracts a minimum-degree vertex into a neighbour instead of deleting it; computing contraction degeneracy exactly is NP-complete; the heuristics give "considerable improvements" in practice but "can perform arbitrarily bad". — [Bodlaender, Koster & Wolle, "Contraction and Treewidth Lower Bounds", JGAA 2006](https://jgaa.info/index.php/jgaa/article/download/paper117/2845); [Koster, Wolle & Bodlaender, ZIB report 04-29](https://opus4.kobv.de/opus4-zib/files/804/ZR-04-29.pdf)
- [V] The solver's lower bound from the 0-1 vertex-separation model can be poor: for one instance the text reports a lower bound of 1 at the time limit against an optimum of 3. — [Duarte et al. 2012, PDF](https://jesussanchezoro.github.io/publications/duarte2012a.pdf)

### Inferences
All [inference], with proof sketches; none is measured.

- Degree-based bounds are useless here. In any induced subgraph of our DAG the topologically last node has no successor inside the subgraph and at most two predecessors, so its degree is ≤ 2: the degeneracy is ≤ 2. MMD+ can exceed that, but there is no reason to expect it near 48 on a graph with about two edges per node.
- Sound bound A (ancestor cut). When node v is computed, every ancestor of v is computed and no descendant is. So every value u that is an ancestor of v (or a start value) and has a consumer in {v} ∪ Desc(v) is live. LB_A = max_v |(Anc(v) ∪ Starts) ∩ Ops({v} ∪ Desc(v))|, where Ops(X) is the set of operands of nodes in X. With 256-bit masks this is two passes over the DAG, about a microsecond. It is strong on deep chain-like DAGs and nearly useless for targets without descendants.
- Sound bound B (forced-overlap clique), which contains A. Two values u, w are live at a common moment in *every* order if u is an ancestor of some consumer of w and w is an ancestor of some consumer of u (each is then defined before the other dies; start values count as ancestors of everything). Lifetimes are intervals on a line, and pairwise-overlapping intervals share a common point (Helly property in one dimension), so any clique in this "forced overlap" graph must be simultaneously live: register need ≥ clique size. Any clique found greedily is a valid bound. Construction: A(w) = union of Anc(c) over consumers c of w; Q(w) = operands of all descendants of w; the neighbours of w are A(w) ∩ Q(w). Cost: O(m) mask operations plus a greedy clique, a few to a few tens of microseconds. If the bound exceeds 48 there is no one-shot order at all and only cloning (or rejection) remains.
- Expected strength. Both bounds certify only overlaps forced by precedence. The overloads that matter in practice come from *choice*: helpers shared by targets that could be emitted in many orders, which is a pathwidth-type quantity on the sharing structure and is exactly what is hard to approximate. I expect bound B to sit well below 48 on most rejected candidates. It should be computed anyway (it is nearly free and exact when it fires), but not relied on.
- Practical quick-reject: a calibrated gate. After the O(n) spliced-order profile, record the excess e = max need − 48 and the number of overfull steps. Log, over a few thousand candidates, how often the later tiers rescue a candidate as a function of (e, overfull length, gain). Reject immediately the cells of that table whose rescue probability times net gain does not justify the tier's time. This is unsound by design; the false rejects it causes are bounded by the measured table.
- Accept-side certificate. If the (upper bound on the) maximum topological cut of the touched window, with everything outside fixed, is ≤ the slack available in that window, no re-ordering can break the order and the profile check can be skipped. At n ≤ 250 this saves nothing over the O(n) profile; it is listed for completeness.

### Gaps
- No source gives a lower bound for one-shot pebbling of sparse DAGs that is both cheap and empirically tight at widths of several dozen; bounds A and B are mine and untested.
- The contraction-degeneracy papers were not read in full (the ZIB server returned a non-PDF page); statements are from the search summary.
- Touati's register-saturation papers were not read; only the mention in Marchal et al. is verified.

## 7. Recommended procedure, cheapest to most expensive (synthesis)

### Takeaway
Use a tiered check: splice into the parent's order and recompute the profile (about a microsecond); a sound forced-overlap bound; peak-focused sifting; a greedy constructor closed under two safe rules, with limited discrepancy and an exact window search; then clone repair capped at gain − 1; and log what still fails for an offline exact solver. Gate every tier by the move's gain and by rescue rates measured on our own rejected moves.

### Cited Findings
The procedure is built from these verified elements; everything else in this section is inference.
- [V] Signature memoisation and budget pruning. — [Ahn et al., arXiv:2003.02369](https://arxiv.org/abs/2003.02369)
- [V] Sequences that are safe to schedule as a whole; re-scheduling only peak-related parts; budget carried over from the previous iteration. — [Wang et al., DAC 2022](https://chengcheng-wan.github.io/paper/22-DAC.pdf)
- [V] Fusion with optimality guarantee; exact solve only where the peak is; time-limited solve with incumbent. — [Zhong et al., arXiv:2308.13898](https://arxiv.org/abs/2308.13898)
- [V] Hill–valley merge order. — [Kayaaslan et al., TCS 2018](https://perso.ens-lyon.fr/loris.marchal/docs-data-aware/tcs18-series-parallel-memory.pdf)
- [V] Affected region for order repair. — [Pearce & Kelly, JEA 2006](https://whileydave.com/publications/PK07_JEA_preprint.pdf)
- [V] Incremental evaluation of insert moves and plateau-breaking evaluation. — [Duarte et al. 2012](https://jesussanchezoro.github.io/publications/duarte2012a.pdf); [Sánchez-Oro et al. 2014](https://jesussanchezoro.github.io/publications/sanchezoro2014a.pdf)
- [V] Evicted-neighbourhood cost for rebuilds. — [Kirisame et al., arXiv:2006.09616](https://arxiv.org/abs/2006.09616)

### Inferences
All [inference]. Time figures are estimates for C++ with 256-bit masks at n ≤ 250 and must be benchmarked.

**Two safe rules (exchange arguments, unit sizes, one-shot).**
- R1, kill-first. If a ready node v is the last unscheduled consumer of one of its operands a, scheduling v now is never worse. Take any fitting completion in which v runs later at step t′ and move v to now: between now and t′ the register that held a now holds v (or nothing, if v has no consumers or both operands die), so the live count is pointwise ≤ the original; the step itself needs no extra register because v overwrites a; after t′ the two schedules coincide. This is the exact version of HMCOS's "safe sequences", Zhong's monotone fusion and the RP-reduction heuristic of round one.
- R2, emit-free-targets. If a ready node v has no consumers and at most 47 values are live, scheduling v now is never worse: it leaves the live set unchanged, and removing v from a later position can only shorten its operands' lifetimes.
- Consequence: after closing under R1 and R2, every remaining ready node opens a new register. If 48 are live at that point the partial order is dead. The search decides only the order in which values are *opened*.

**Tiers.**

| Tier | What it does | Estimated cost | Outcome |
|---|---|---|---|
| 0 | Splice the move into the parent's order (Pearce–Kelly shift if precedence breaks; new nodes placed where they kill an operand if possible, else just before their first consumer), then O(n) profile | 1–3 µs | fits → accept |
| 1 | Sound bounds A/B | 2–50 µs | bound > 48 → skip to tier 4 or reject |
| gate | Look up (excess, overfull length, gain) in the measured rescue table | ~0 | hopeless cell → reject |
| 2 | Peak-focused sifting, 1–3 sweeps, key = (excess area, steps at 48) | 20–200 µs | fits → accept |
| 3a | Greedy constructor closed under R1/R2 with 3–4 priorities, then limited discrepancy (≤ 1–2 deviations) | 0.1–2 ms | fits → accept |
| 3b | Exact window search around the overfull region, state cap | 0.2–3 ms | fits → accept |
| 4 | Clone repair on the best order so far, at most gain − 1 clones, then one sifting sweep | 20–300 µs | fits → accept with net gain = gain − clones |
| 5 | Log (DAG, gain, excess, bound); offline, run the round-one CP-SAT decision model on the few highest-gain rejects per puzzle | seconds to minutes, outside the loop | calibrates the false-reject rate |

Starting thresholds (guesses to be tuned): tier 2 for every candidate with excess ≤ 4; tier 3 only if gain ≥ 1 and excess ≤ 3; tier 4 only if gain ≥ 2. A candidate with gain 1 stops after tier 3.

**Pseudocode.**

```
# σ[1..n]: order; pos[v]; start values have pos 0
# last[u]: position of the last consumer of u (0 if none)
# need[t] = live_before(t) + (1 if no operand of σ[t] has last = t else 0); fits iff max need ≤ 48

function PROFILE(σ):                                   # tier 0, O(n)
    live ← number of start values with a consumer
    for t in 1..n:
        v ← σ[t]
        d ← number of distinct operands u of v with last[u] = t
        need[t] ← live + (d = 0 ? 1 : 0)
        live ← live − d + (last[v] > t ? 1 : 0)
    return need

function FORCED_OVERLAP_BOUND(G):                      # tier 1, sound
    for v in topological order:   Anc[v] ← operands(v) ∪ ⋃ Anc[o] for o in operands(v)
    for v in reverse order:       Q[v]   ← ⋃ (operands(c) ∪ Q[c]) for c in consumers(v)
    for each value w with a consumer:
        A[w] ← Starts_in_use ∪ ⋃ Anc[c] for c in consumers(w)
        F[w] ← A[w] ∩ Q[w]                              # values forced to overlap w
    best ← 0
    for a few seeds w with the largest |F[w]|:
        K ← {w};  cand ← F[w] \ {w}
        while cand ≠ ∅:
            x ← element of cand maximising |F[x] ∩ cand|
            K ← K ∪ {x};  cand ← cand ∩ F[x] \ {x}
        best ← max(best, |K|)
    return best

function SIFT(σ, sweeps):                              # tier 2
    repeat sweeps times:
        H ← steps with need > 48;  if H = ∅: return σ
        C ← nodes positioned within H ± margin, plus producers and consumers of values live across H
        for v in C, values covering the most overfull steps first:
            lo ← 1 + max pos of operands(v);  hi ← (min pos of consumers(v)) − 1
            walk v through [lo, hi] by adjacent swaps, updating need[] at the two touched steps each time
            key(position) = (Σ max(0, need − 48), number of steps with need = 48)
            leave v at the position with the smallest key (ties: keep, or move with small probability)
    return σ

function CLOSURE_GREEDY(G, priority, deviations):      # tier 3a
    live ← start values with a consumer;  ready ← nodes whose operands are available
    while unscheduled nodes remain:
        if some ready v is the last unscheduled consumer of one of its operands: schedule v; continue   # R1
        if live ≤ 47 and some ready v has no consumers:                          schedule v; continue   # R2
        if live ≥ 48: return FAIL(prefix)               # every ready node needs a 49th register
        rank ready nodes by priority; schedule the first (or the second, where `deviations` says so)
    return σ
# priorities to try:
#   P1  position in the parent's order (stability)
#   P2  fewest still-missing nodes until some live value dies (look ahead 1–2 levels)
#   P3  hill − valley of the cheapest target that v helps complete (Liu's rule), largest first
#   P4  P2 with random tie-breaks

function WINDOW_SEARCH(σ, i, j, cap):                  # tier 3b; exact if cap is never hit
    W ← nodes at positions i..j (|W| ≤ 64); prefix and suffix stay fixed
    layer ← { (S = ∅, live = live_before(i)) }
    for k in 1..|W|:
        next ← empty hash map keyed by S
        for (S, live) in layer:
            R ← nodes of W \ S whose operands inside W are all in S
            if R contains a node allowed by R1 or R2: R ← {that node}
            for v in R:
                d ← operands of v all of whose consumers lie in prefix ∪ S ∪ {v}
                if live + (d = ∅ ? 1 : 0) ≤ 48:
                    insert (S ∪ {v}, live − |d| + (v has a consumer outside prefix ∪ S ∪ {v} ? 1 : 0)) with parent pointer
        if next = ∅: return FAIL
        if |next| > cap: keep the cap states with the smallest live
        layer ← next
    return order rebuilt from parent pointers

function CLONE_REPAIR(σ, max_clones):                  # tier 4
    k ← 0
    while k < max_clones and some step has need > 48:
        g ← first such step;  best ← none
        for each non-start value u live across g and not an operand of σ[g]:
            r ← position of u's next consumer after g
            x ← number of operands of u not held just before r
            if x > 0 and holding them until r would cross a step with need ≥ 48: continue
            score ← (r − g) / (1 + x)^α                 # α = 0: farthest next use
            best ← argmax score
        if best = none: return FAIL
        insert u′ (same operation as u) just before r; consumers of u at positions ≥ r read u′
        update last[] for u, u′ and the operands; recompute need on the touched range; k ← k + 1
    return (σ, k) if max need ≤ 48 else FAIL

function FIT(G, σ_parent, gain):
    σ ← SPLICE(σ_parent, G);  need ← PROFILE(σ)
    if max(need) ≤ 48: return ACCEPT(σ, clones = 0)
    lb ← FORCED_OVERLAP_BOUND(G)
    if lb ≤ 48 and not GATE_REJECTS(excess, overfull_length, gain):
        σ ← SIFT(σ, 2);  if fits: return ACCEPT(σ, 0)
        if gain ≥ 1:
            for p in priorities, then single deviations: τ ← CLOSURE_GREEDY(G, p, ·); keep the best by excess area
            if some τ fits: return ACCEPT(τ, 0)
            τ ← WINDOW_SEARCH(best order, overfull window ± margin, cap);  if fits: return ACCEPT(τ, 0)
    if gain ≥ 2:
        (τ, k) ← CLONE_REPAIR(best order, gain − 1)
        if fits: return ACCEPT(τ, k)                    # net gain = gain − k ≥ 1
    LOG(G, gain, excess, lb)                            # tier 5, offline CP-SAT on the top few
    return REJECT
```

**Prose notes on the procedure.**
- Why splice first: the parent fits, the move changes a handful of nodes, so the spliced order usually exceeds 48 by a small integer over a short stretch. That stretch is the only place the later tiers need to look, which is the HMCOS/Zhong lesson.
- Why a closed greedy instead of "20 alternative orders": random alternative orders waste almost all their freedom on steps that R1 and R2 decide for free. Varying only the opening decisions explores the part of the space that can change the answer.
- Why cap clones at gain − 1: it guarantees a strict improvement and stops the repair before the regime where recomputation cost explodes. A dead end inside CLOSURE_GREEDY can call the same eviction rule online (drop the eligible value with the farthest next use, rebuild on demand); that is the scheme the brief attributes to the public compiler, here restricted to values with free or one-level rebuilds and to a clone budget.
- What to measure before building tiers 3–4 (one afternoon): for each improving move currently discarded, log gain, excess of the spliced order, number of overfull steps, bound B, and whether a value with a free rebuild spans the overfull steps. If most discarded moves have excess 1–2 and gain 1, tiers 2–3 are the whole story; if many have gain ≥ 2, tier 4 matters; if bound B often exceeds 48, the losses are structural and only cloning or different moves can recover them.
- Reasons the whole approach may recover little: the reports record that the public register experiments (search with 72 registers, compile back to 48; re-assignment only) gained nothing; our own "register-aware" restriction also did not help. Both are consistent with a picture in which the rejected moves fail for structural reasons (too many shared values that must overlap), in which case re-ordering cannot help and each rescue costs clones that eat the gain. The measurement above distinguishes the two pictures cheaply.

### Gaps
- None of the tiers has been timed or scored on our DAGs; every cost and threshold above is an estimate.
- The rescue-rate table for the gate does not exist yet and is the first thing to produce.
- The correctness of rules R1 and R2 rests on my exchange arguments; they should be checked against the round-one CP-SAT model on a few hundred small DAGs (closure applied versus not applied must give the same feasibility answer).
- The interaction between clones and later local-search moves (does the search remove clones again, or accumulate them) is unknown.
