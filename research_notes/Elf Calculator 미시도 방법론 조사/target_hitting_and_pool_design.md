# Target hitting from a 48-value pool and pool design: methods not yet tried

Scope: algorithms for (a) deriving one 40–60-bit target from a pool of at most 48 integers in few instructions and (b) designing the pool. Everything in `notes/research.md` and the "already tried" list is excluded. Research date 2026-11-24.

Evidence tags used on every claim:

- **[V]** checked against the fetched source text (abstract, page, or PDF page).
- **[S]** seen only in a search-result summary; the source itself was not opened.
- **[U]** recalled from memory; the source could not be fetched (URL given for follow-up).
- **[C]** my own computation for these notes (exact enumeration with numpy on synthetic pools, or arithmetic on verified numbers). Not a measurement on competition data.
- Everything under "Inferences" is my mapping onto the competition and is not stated by any source.

Shared notation: P = pool (48 values), F_k = set of valid values reachable from P with at most k instructions (positive integers ≤ value_limit), N = size of the target range (2^48 for a 49-bit target), r = list size in k-list problems.

## 1. k-list and generalized-birthday algorithms, Schroeppel–Shamir, Howgrave-Graham–Joux: can they find 3–5 operation expressions deeper or faster than two-level hash-table meet-in-the-middle?

### Takeaway
No for "deeper", marginal for "faster". These algorithms are fast only when many solutions exist; a minimum-instruction derivation sits in the sparse regime (about one solution), where sort-and-match in Õ(r^⌈k/2⌉) is conjectured optimal, so the only thing the literature offers is lower memory (Schroeppel–Shamir, dissection). Exact expression counts show that a 49-bit target cannot average below about 6 instructions from any 48-value pool, so the measured 6.3 is already at the counting limit and the single-target search is saturated.

### Cited Findings
- A sort-and-match (meet-in-the-middle) algorithm finds a k-SUM solution in T = Õ(r^⌈k/2⌉), and the k-SUM conjecture states that no algorithm does substantially better in standard models. [V] — [Dinur, Keller, Klein, "Fine-Grained Cryptanalysis: Tight Conditional Bounds for Dense k-SUM and k-XOR", p.1](https://arxiv.org/abs/2111.00486)
- Sparse regime (r^k ≈ N, only a few solutions on average): Conjecture 1.2 says any algorithm needs expected time Ω(r^(⌈k/2⌉−o(1))). For N much larger than r^k a solution exists only with probability o(1). [V] — [arXiv:2111.00486, p.1](https://arxiv.org/abs/2111.00486)
- Dense regime (r^k ≫ N, many solutions): k = 3 is solved in Õ(N/r) for N^(1/3) ≤ r ≤ N^(1/2); Wagner's k-tree algorithm finds a k-XOR solution in Õ(N^(1/(1+⌊log2 k⌋))) when r is of similar size; the Minder–Sinclair generalisation gives a trade-off for N^(1/k) ≤ r ≤ N^(1/(1+⌊log2 k⌋)); for k = 4 the curve is T = Õ(N/r²) for N^(1/4) ≤ r ≤ N^(1/3). The algorithm also applies to modular k-SUM in Z_N and to average-case integer k-SUM. [V] — [arXiv:2111.00486, p.2](https://arxiv.org/abs/2111.00486)
- Assuming the sparse conjecture, the known dense-regime algorithms are essentially optimal for k = 3, 4, 5; for k > 5 optimality of the k-tree algorithm is proved only for a limited parameter range. [V] — [arXiv:2111.00486, abstract](https://arxiv.org/abs/2111.00486)
- The representation technique for subset sum "crucially relies on variants of the [k-tree] algorithm for small values of k to find one out of many representations of a solution". [V] — [arXiv:2111.00486, p.2](https://arxiv.org/abs/2111.00486)
- Wagner's own page carries only a note that Camion and Patarin had significant prior work; the paper text (k lists of n-bit values, time and space O(k·2^(n/(1+lg k))), 2^(n/3) for k = 4) could not be opened. [V for the note, U for the complexity; consistent with the verified restatement above] — [Wagner, "A Generalized Birthday Problem"](https://people.eecs.berkeley.edu/~daw/papers/genbday.html)
- The extended k-tree algorithm works when lists are shorter than Wagner's threshold, as a trade-off between list length and running time. [S] — [Minder & Sinclair, J. Cryptology 2012](https://link.springer.com/doi/10.1007/s00145-011-9097-y)
- Schroeppel–Shamir solves knapsacks of n elements in Õ(2^(n/2)) time and Õ(2^(n/4)) memory. [V] — [Howgrave-Graham & Joux, ePrint 2010/189, abstract](https://eprint.iacr.org/2010/189)
- Howgrave-Graham–Joux: "hard knapsacks" of density close to 1, where lattice low-density attacks "are not an option". The ePrint abstract states Õ(2^(0.3113n)); Becker–Coron–Joux cite the same work as Õ(2^(0.337n)) time and Õ(2^(0.256n)) memory and improve it to Õ(2^(0.291n)); Bonnetain–Bricout–Schrottenloher–Shen reach Õ(2^(0.283n)) for random subset-sum instances with representations in {−1,0,1,2}. [V for each abstract; the 0.3113 vs 0.337 discrepancy is between the two abstracts and was not resolved] — [ePrint 2010/189](https://eprint.iacr.org/2010/189); [ePrint 2011/474](https://eprint.iacr.org/2011/474); [ePrint 2020/168](https://eprint.iacr.org/2020/168)
- Dissection (Dinur, Dunkelman, Keller, Shamir): problems with "bicomposite" structure admit "much better time/memory tradeoffs"; for knapsacks it gives "better time complexities (for small memory complexities)"; the one concrete figure in the abstract is T = 2^(4n), M = 2^n for 7-fold multiple encryption. The knapsack trade-off points themselves were not verified (PDF returned 403). [V for the abstract] — [ePrint 2012/217](https://eprint.iacr.org/2012/217)
- 3SUM: conjectured to need Ω(n²) deterministic time; Grønlund–Pettie O(n²/(log n/log log n)^(2/3)); Chan O(n²(log log n)^O(1)/log² n); matching Ω(n^⌈k/2⌉) lower bounds for k-SUM are known in specialised models. The page as fetched also reports 2026 preprints claiming O(n^1.9992) for polynomially bounded integers and n^(1.9945+o(1)); I did not check these. [V as page text] — [Wikipedia, 3SUM](https://en.wikipedia.org/wiki/3SUM)
- Number of inequivalent expressions on n distinct operands with binary + − × / and parentheses: 1, 6, 68, 1170, 27142, 793002, 27914126, 1150212810, 54326011414, … with a(n) ~ (n/(e·b))^n·√b·c/n, b ≈ 0.16142418, c ≈ 1.87722131. (a−b and b−a count separately; (a−b)/(c−d) and (b−a)/(d−c) are identified.) [V] — [OEIS A140606](https://oeis.org/A140606)
- Countdown numbers game (the same problem at 6 inputs): duplicate-free generation needs n-ary operator nodes that alternate between "+" and "×" from root to leaf, unordered children, subtraction and division represented as "inverted" children with at least one non-inverted child per node, and abandoning any branch with a non-positive-integer intermediate or a multiplication by 1; there are 3020 such trees with up to six leaves; on one instance an RPN solver returned 15 "essentially the same" solutions where the tree form returned 1. [V] — [Ben North, Countdown numbers solver](https://bennorth.github.io/countdown-numbers-solver)
- Alliot's analysis of the Countdown numbers round includes a complexity analysis, a comparison of existing algorithms and a new algorithm that "increases resolution speed by a factor of 20"; details are in the PDF, not opened. [V for the abstract] — [Alliot, "The (Final) Countdown", arXiv:1502.05450](https://arxiv.org/abs/1502.05450)
- The Oxford (Spivey) solver stores expressions by value in a hash table together with a bitmap of the inputs used, and drops duplicates with the same value and inputs. [S] — [Oxford CS Countdown demo](https://cs.ox.ac.uk/admissions/undergraduate/courses/countdown.html)

### Inferences

**1a. Counting limit for one target from a 48-value pool [C, using A140606].** Upper bound on distinct values of tree expressions with k instructions and k+1 distinct pool leaves: N_k = C(48, k+1)·A140606(k+1).

| k (instructions) | log2 N_k | cumulative count ÷ 2^38 (39-bit target) | ÷ 2^48 (49-bit) | ÷ 2^59 (60-bit) |
|---|---|---|---|---|
| 3 | 27.8 | 0.0008 | 8e-7 | 4e-10 |
| 4 | 35.4 | 0.17 | 1.7e-4 | 8e-8 |
| 5 | 43.1 | 36 | 0.035 | 1.7e-5 |
| 6 | 50.9 | 7,500 | 7.3 | 0.0036 |
| 7 | 58.6 | 1.6e6 | 1,550 | 0.76 |
| 8 | 66.3 | 3.3e8 | 3.3e5 | 159 |

- log2 N_k ≈ 5.0 + 7.65·k, so one more instruction buys about 7.65 bits. Even if every expression were valid, in range and distinct, at most 3.5% of 49-bit targets are reachable in 5 instructions; a 49-bit target needs ≥ 6, a 39-bit target ≥ 5 (17% could be 4), a 60-bit target ≥ 7–8.
- Synthetic pools are far below this bound. Exact enumeration on synthetic 48-value pools [C] gave |F_1| ≈ 2,400–3,500 (bound 6,768), |F_2| ≈ 80,000–310,000 (bound 1.2e6), |F_3| ≈ 2·10^6–3·10^7 (bound 2.3e8), and only 0.3–2% of the 3-instruction bound landing as distinct values in [2^48, 2^49). The measured probability that a random 49-bit target is reachable in ≤ 4 instructions was 7·10^-8 to 2.6·10^-6 depending on pool shape, growing by a factor of about 100 per instruction (about 20 for a pool of old targets, about 180 for a pool of 14–18-bit values; tables in 4c). Extrapolated two more levels, a 6-instruction derivation exists for roughly 0.003%–9% of targets, so the mean cost is about 7 for the best synthetic pools and 7.5–8 for the others.
- The brief's 6.3 is better than any synthetic pool I tried, so either real pools are well matched to their targets or that measurement used more than 48 values (see Gaps). Against the hard bound above (at most 3.5% of 49-bit targets in 5 instructions, so a mean of at least 5.97) a measured 6.3 leaves at most about 5%. No algorithm for the fixed-pool single-target problem can gain more than that.

**1b. Why Wagner / extended k-tree / representation technique do not transfer.**
- Mapping: a k-list instance would be t = x_1 ± x_2 ± … ± x_k with x_i drawn from F_1 or F_2. With N = 2^48–2^49 and k = 4, Wagner needs r ≥ N^(1/3) ≈ 2^16.3 ≈ 83,000 per list and the Minder–Sinclair range starts at N^(1/4) ≈ 2^12.2 ≈ 4,900.
- |F_1| ≈ 3,000 is below even N^(1/4): four F_1 lists hold about 0.14 expected solutions. That instance (4 + 3 = 7 instructions) is sparse, so Õ(r²) ≈ 10^7 operations is optimal and already trivial.
- |F_2| ≈ 2·10^5 is in the dense range, and the k-tree would find one of roughly 3·10^6 solutions in about 10^5 list operations, but a sum of four F_2 values costs 4·2 + 3 = 11 instructions. Dense means expensive: the algorithm trades instruction count for search time, which is the wrong direction here.
- Representation technique (HGJ, BCJ, BBSS): designed for subset sum with n ≈ log2 N items and weight about n/2. From 48 pool values a signed subset sum needs weight 13 before C(48,w)·2^w exceeds 2^49 [C], i.e. at least 12 additions. Not competitive with 6.
- Mixed operators break the k-tree's partial-bit filtering (it needs a group operation such as XOR or modular addition).
- Expected benefit: none on instruction count.

**1c. Concrete operation counts for exhaustive "is t reachable in ≤ k instructions" from a 48-value pool.** Sizes from [C]: |F_1| ≈ 3·10^3, |F_2| ≈ 2·10^5, |F_3| ≈ 10^7 (measured 2·10^6–3·10^7). β ≈ 100–290 = number of valid inverse images of t under one pool element (t−p, t+p, p−t, t·p, t/p, p/t). c_k = hash probes, root split written (left instructions | right instructions).

| k | without an F_3 table | with an F_3 hash table (≈10^7 entries) | dominant split |
|---|---|---|---|
| 3 | ≈ 1.2·10^4 | 1 | (1 \| 1): 4·\|F_1\| probes into F_1 |
| 4 | ≈ 2·10^6 | ≈ 1.2·10^4 | (3 \| 0): β·c_3 |
| 5 | ≈ 4·10^8 | ≈ 3·10^6 | (4 \| 0) and (3 \| 1) |
| 6 | ≈ 9·10^10 | ≈ 5·10^8 | (5 \| 0): β·c_5 |
| 7 | infeasible | ≈ 10^11 | (6 \| 0) and (5 \| 1) |

- Building the F_3 table costs about |F_2|·β + |F_1|²·2 ≈ 5·10^7 operations per pool state; adding one pool element changes only the expressions that contain it.
- So a guaranteed-optimal ≤ 5 search is about 3·10^6 probes per target (tens of milliseconds), ≤ 6 about 5·10^8 (seconds), ≤ 7 about 10^11 (not routine). These counts cover tree-shaped expressions; reuse of a subresult inside one derivation is not covered.
- Expected benefit: bounded by how often the current search misses an existing 5- or 6-instruction derivation. The brief reports < 0.5% from widening, consistent with 1a.

**1d. Schroeppel–Shamir and dissection.**
- Mapping: any 4-leaf-group shape (a∘b)∘(c∘d) with a monotone operator pattern (+ and × are monotone on positive integers) can be enumerated in sorted order with a heap of size r instead of storing r² values, then merged against a second sorted stream. This removes the F_3 (or F_2∘F_2) table at the same time cost.
- Complexity: time unchanged (size of the larger side times a log factor), memory from ~10^7–10^9 entries to ~10^5.
- Expected benefit: only if memory, not time, limits the (3 | 3) or (4 | 3) splits. At 48 values an F_3 table fits in RAM, so the benefit is nil for ≤ 6 and it does not make ≤ 7 affordable.
- Dissection needs more than four independent sub-lists to beat Schroeppel–Shamir; derivations of ≤ 6 instructions do not have them.

**1e. Canonical-form enumeration (Countdown literature).**
- Mapping: generate each inequivalent expression once (alternating n-ary sum/product nodes with inverted children) instead of every binary tree. The ratio between raw binary trees and A140606 classes grows with depth, so the same time budget reaches slightly deeper, and forward tables stop storing duplicate derivations.
- Complexity: constant-factor saving; for 5 leaves the raw count Catalan(4)·4^4·5! = 430,080 ordered trees per leaf set versus 27,142 classes, a factor of about 16 [C].
- Expected benefit: speed only. It matters if the short-window exhaustive resynthesis is time-limited; it does not change which targets are reachable.
- Might not transfer: a hash table keyed by value already removes most duplicates at the cost of memory.

**1f. Where "many solutions" really exist: collisions across targets, not within one target.** The dense regime appears when all ~30 remaining targets and all alternative derivations are considered together (a derivation's by-product that lies in another target's backward set). This is developed in section 5 because it is a joint-structure method.

### Gaps
- Wagner's paper, the dissection knapsack trade-off points and Alliot's algorithmic details were not opened (403 or PDF-only). The Wagner complexity is corroborated by arXiv:2111.00486; the dissection numbers are not.
- I found no source treating k-list problems with mixed operators (+, −, ×, exact ÷) or with a per-element cost; the mapping above is entirely mine.
- The discount between the A140606 bound and real in-range distinct values was measured only on synthetic pools and only to depth 3–4 (see section 4). It should be measured on a real solver pool.
- Whether the brief's 6.3 was measured on a pool of exactly 48 values or on all values a solution ever computes is not stated; the comparison with my synthetic-pool estimate of about 7 or more depends on it.

## 2. Lattice methods (LLL/BKZ, closest vector, knapsack lattices, PSLQ): small-coefficient combinations t = Σ c_i·p_i or t = p_i·p_j ± small remainder

### Takeaway
Lattice reduction finds short but dense integer combinations, while the score charges per nonzero term and per coefficient that is not already in a register, so for unstructured targets every lattice representation costs more than the 6 instructions it must beat. The useful role is detection: LLL on the relation or orthogonal lattice of a puzzle's targets is a millisecond test for hidden linear generators, and returns only generic-size vectors when no structure exists.

### Cited Findings
- Lagarias–Odlyzko solves almost all subset-sum problems of density < 0.6463 if given a shortest-vector oracle; Coster, Joux, LaMacchia, Odlyzko, Schnorr, Stern raise the bound to 0.9408. [S] — [Lagarias & Odlyzko, JACM 1985](https://web.stevens.edu/algebraic/Files/SubsetSum/p229-lagarias.pdf); [Coster et al., EUROCRYPT '91](https://link.springer.com/chapter/10.1007/3-540-46416-6_4)
- Low-density lattice attacks "are not an option" for knapsacks of density close to 1. [V] — [ePrint 2010/189, abstract](https://eprint.iacr.org/2010/189)
- Siegel's lemma: a system of M linear equations in N > M unknowns with integer coefficients bounded by B has a nonzero integer solution with all entries bounded by (NB)^(M/(N−M)). [V] — [Wikipedia, Siegel's lemma](https://en.wikipedia.org/wiki/Siegel%27s_lemma)
- Integer relation algorithms: for n = 2 the Euclidean algorithm (continued fraction of x_1/x_2); LLL (1982) was the first with complete proofs; HJLS (1986) and PSLQ (1992) are polynomial time and "essentially equivalent"; given inputs to a known precision the algorithm "will either find an integer relation between them, or will determine that no integer relation exists" with coefficients below a bound. [V] — [Wikipedia, Integer relation algorithm](https://en.wikipedia.org/wiki/Integer_relation_algorithm)
- Hidden subset sum problem: a subset-sum variant "where the n weights are also hidden". The Nguyen–Stern algorithm starts with an orthogonal lattice attack using LLL; its last step (a very short basis of an n-dimensional lattice) makes it exponential in n; Coron–Gini replace that step with a multivariate technique and reach n = 250 in a few hours on one PC. [V] — [Coron & Gini, ePrint 2020/461](https://eprint.iacr.org/2020/461)

### Inferences

**2a. Dense versus sparse, with numbers [C].**
- Siegel's lemma with one equation: among the ~30 targets of a 49-bit puzzle there is always a relation Σ c_j·t_j = 0 with |c_j| ≤ (30·2^49)^(1/29) ≈ 3.6. LLL finds it instantly. Using it to build one target from the other 29 costs ~29 additions plus small multiplications. Useless.
- Restricting to 3 values: coefficients up to (3·2^49)^(1/2) ≈ 2^25. Each such coefficient is itself a 25-bit number costing about 3 instructions (rule 5.0 + 7.65·k bits from 1a), so t = c_1·p_1 + c_2·p_2 costs about 3 + 2·3 = 9.
- Signed 0/±1 combinations of the 48 pool values need weight 13 (section 1b). Subset-sum lattices solve this "density ≈ 1" instance badly and the answer would cost 12 instructions anyway.
- General rule: a d-term combination costs (d − 1) additions + up to d multiplications + the coefficients, and the total coefficient information is at least 49 − (information already in the pool choice) bits. This is the same counting as 1a; lattices do not escape it.

**2b. t = p_i·p_j ± small remainder.**
- This is a nearest-neighbour search in a sorted list (for each x in F_1 or F_2, binary-search t/x), not a lattice problem. It is the already tried v = q·b ± c reduction.
- A 2-dimensional lattice (Gauss reduction, equivalently continued fractions) solves t = c_1·p_1 − c_2·p_2 for fixed p_1, p_2: the solutions form a one-parameter family c_1 = c_1⁰ + k·p_2/g, c_2 = c_2⁰ + k·p_1/g. One can pick k so that c_1 is a value already in F_1, but c_2 is then a forced number of about bits(t) − bits(p_2) bits. Net cost again ≥ 6–7.

**2c. Where a lattice helps: hidden-generator detection (new, cheap, structure-dependent).**
- What it does: if a puzzle's targets are t_j = Σ_{i ≤ r} a_ij·X_i with a few hidden large X_i (not in the pool, not targets) and small coefficients a_ij (r = 2–4, a_ij up to ~11 bits, optionally X_r = 1 to absorb small additive offsets), then the orthogonal lattice {c : Σ c_j·t_j = 0} contains a rank m − r sublattice of unusually short vectors (orthogonal to every coefficient vector). LLL exposes it; the orthogonal complement gives the coefficient lattice, and a second LLL in rank r gives candidate a_i and then the X_i by solving a linear system. This is step 1 of Nguyen–Stern applied over the integers with tiny r, so the exponential last step does not arise.
- Complexity: one LLL in dimension ≤ 32 with 60-bit entries per puzzle, milliseconds; 1,000 puzzles in seconds.
- Signal test: for unstructured targets the reduced basis vectors all have norm near the Siegel/Minkowski size (≈ 2^(49/29) ≈ 3 for 30 targets of 49 bits). A block of much shorter vectors followed by a jump is the structure signal.
- Expected benefit: zero on the "independent" family by construction. On "shared" or "mixed" puzzles it could replace per-target derivations by cost(X_i) once plus about 2r − 1 + cost(coefficients) per target; with r = 2 and coefficients from start values that is 3–5 per target. Whether such structure exists in the data is unknown.
- Might not transfer: the existing "relations between targets" and "factor sharing" passes may already capture every structure the generator produced; coefficients may not be small; with r ≥ 4 the per-target cost exceeds the direct 5–6.

**2d. PSLQ.** For integer inputs it offers nothing beyond LLL on the relation lattice; for two numbers it reduces to the continued fraction of t_i/t_j (section 3).

### Gaps
- The Lagarias–Odlyzko and Coster et al. thresholds are from search summaries only.
- I did not find any source on lattice problems with a cost per nonzero coefficient ("sparse CVP with priced coefficients") that would match the scoring rule.
- The Nguyen–Stern condition relating coefficient size, r and target size was not read; the detection thresholds in 2c are my estimate from Siegel's lemma.

## 3. Number-theoretic representations: sums or differences of two products, near-squares, Euclid/continued fractions, smooth neighbours, exact-division tricks

### Takeaway
None of these beats the counting limit for unstructured targets: each replaces one b-bit number by two or three numbers of about b/2 bits that are not in the pool. Two items are still worth having: factoring t ± δ to enumerate every product-rooted derivation in time independent of the table size, and smooth-neighbour or continued-fraction scans as detectors of generator structure.

### Cited Findings
- Dickman function: Ψ(x, y) counts y-smooth integers below x and the proportion with y = x^(1/u) is estimated by ρ(u); ρ(2) = 0.3069, ρ(3) = 0.0486, ρ(4) = 0.00491, ρ(5) = 3.55e-4, ρ(6) = 1.96e-5; first approximation ρ(u) ≈ u^(−u). [V] — [Wikipedia, Dickman function](https://en.wikipedia.org/wiki/Dickman_function)
- Rabin and Shallit gave randomized polynomial-time algorithms computing one representation n = x_1² + x_2² + x_3² + x_4² in expected time O(log² n); Pollack and Treviño improved it in 2018; a positive integer is a sum of three squares iff it is not of the form 4^k(8m + 7). [V] — [Wikipedia, Lagrange's four-square theorem](https://en.wikipedia.org/wiki/Lagrange%27s_four-square_theorem)
- Dirichlet: for real α and N ≥ 1 there are integers p, q with 1 ≤ q ≤ N and |qα − p| < 1/N; simultaneous version: for α_1..α_d there are p_1..p_d and 1 ≤ q ≤ N with |α_i − p_i/q| ≤ 1/(q·N^(1/d)). [V] — [Wikipedia, Dirichlet's approximation theorem](https://en.wikipedia.org/wiki/Dirichlet%27s_approximation_theorem)
- Double-base number system (n = Σ ±2^a·3^b): the greedy algorithm terminates after O(log n / log log n) terms and this is sharp for greedy (Θ(log n / log log n)); the best lower bound on minimal weight is of order log n / (log log n · log log log n). [S] — [arXiv:1808.06330](https://arxiv.org/pdf/1808.06330); [arXiv:2104.06222](https://arxiv.org/pdf/2104.06222)
- Expression counts by number of operands (A140606), as in section 1. [V] — [OEIS A140606](https://oeis.org/A140606)

### Inferences

**3a. Sum or difference of two products, t = a·b ± c·d.**
- Mapping: a 4-list problem over F_0 = P or F_1. Counting [C]: all four from P gives C(48,2)²·2 ≈ 2.5·10^6 values (3 instructions); two from F_1 and two from P gives about 4·10^10 (5 instructions); all four from F_1 about 10^13–10^14 (7 instructions). Against 2^48–2^49 targets the first two are sparse by 4–8 orders of magnitude.
- Complexity: sorted product lists plus a two-pointer merge, ≤ 10^7 operations. Already inside any exhaustive ≤ 5 search (shape (1|0)·… ± (1|0)·…).
- Expected benefit: none beyond 1c. It is one of the shapes, with no special density.

**3b. Near-squares and sums of squares.**
- t = s² ± r with s = ⌊√t⌋ leaves s (25 bits) and r (≤ 26 bits), both unrelated to the pool: 2 + 3 + 3 ≈ 8 instructions. Choosing s from F_2 instead (about 10^4–10^5 values near √t) leaves a remainder of about 33 bits: 2 + 1 + 1 + 4 ≈ 8.
- Two or four squares (Rabin–Shallit): the roots are 24.5-bit numbers with essentially no freedom, so the cost is 3 + 2·3 = 9 for two squares and ≥ 19 for four.
- Expected benefit: none. Squares of pool values are already in F_1.

**3c. Continued fractions between two values (Euclid).**
- Mapping: convergents p/q of t_i/t_j (or t/p for a pool value p) give q·t_i − p·t_j = e, i.e. t_i = (p·t_j + e) ÷ q using an exact division. Cost 3 + cost(p) + cost(q) + cost(e).
- By Dirichlet, |e| ≈ t_j/q_next, so bits(p) + bits(e) ≈ bits(t_i) and the three numbers together carry at least bits(t_i) + bits(q) bits. No gain for unstructured pairs.
- Use as a detector: a partial quotient ≥ 2^10 in the continued fraction of t_i/t_j means an unusually good small-denominator relation. All 435 pairs of a puzzle cost about 435·30 division steps. This finds every two-term relation with small p, q, e optimally, which a difference-only or ratio-only relation scan can miss (for example 3·t_i − 5·t_j = small).
- Expected benefit: zero on independent targets; unknown but cheap on shared/mixed puzzles.

**3d. Factoring t ± δ: smooth neighbours and divisor enumeration.**
- Smooth neighbours: with start values ≤ 1998 (11 bits), a 49-bit number is 2^11-smooth with probability about ρ(4.45) ≈ 1.5·10^-3 [C from the Dickman table], so some offset among ~700 gives a smooth neighbour. But a 2^11-smooth 49-bit number has ≥ 5 prime factors: ≥ 4 multiplications + the primes + the offset + 1 addition ≈ 11 or more instructions. Not useful as a construction.
- Divisor enumeration (useful as a search accelerator): for each δ in P or F_1 (48–3,000 values) factor t − δ and t + δ, list every divisor pair (A, B), and look both up in the F_1/F_2/F_3 tables. This returns every derivation t = A·B ± δ with A, B at any table depth in about 6,000 factorizations of ≤ 60-bit numbers plus the divisor lookups, instead of iterating A over F_2 or F_3 (2·10^5–10^7 divisibility tests per δ). Pollard rho on 60-bit numbers takes about 2^15 modular multiplications in the worst case [U, standard estimate], i.e. tens of microseconds, so roughly 0.1–0.5 s per target in compiled code.
- Expected benefit: speed for the product-rooted shapes (k_A + k_B + k_δ ≤ 4 within a 6-instruction budget); it finds nothing that an exhaustive ≤ 6 search would not.
- Generator detection: if targets were produced by a short hidden program over the start values, t ± (start value or small constant) will be smooth or share a large factor with another target's neighbour far more often than chance. The chance rate for a shared prime factor above 2^30 among 10^5 neighbour values of one puzzle is about 0.2 pairs [C: 5·10^9 pairs × Σ_{p>2^30} p^-2 ≈ 4.5·10^-11]. Any excess is structure. Cost about 10^5 factorizations per puzzle.
- Might not transfer: if the generator did not use products of mid-size values, nothing is found.

**3e. Exact-division tricks.**
- Because value_limit is 1–5 times the largest target, a target that is g bits smaller than the largest one can be reached as (X ∘ Y) ÷ q with q up to about 2^g·(1–5). This turns "hit t" into "hit any of the multiples q·t for q in P or F_1" at the price of one division plus cost(q): about 5.6 extra bits of freedom for one instruction with q in P, less than the 7.65 bits a generic instruction buys.
- It is therefore just the root operator "÷" in a backward search (inverse image t·p). Worth checking only that the existing backward step includes t·p for all p with t·p ≤ value_limit; it matters for small targets inside puzzles with a 60-bit largest target.
- No modular trick was found that changes the count: fixing a divisor a and solving c ≡ −t·d (mod a) produces a small c but leaves a quotient as large and as random as t.

**3f. Double-base and multi-base representations.** A 49-bit number needs roughly 9–10 greedy {2,3}-terms [C estimate: about 760 numbers 2^a·3^b below 2^49, about 5 bits gained per term], each term a product. Far above 6, and the grid of 2^a·3^b values does not fit in 48 registers. Equivalent in spirit to the already tried approximation/Bos–Coster reductions.

### Gaps
- No source was found for "sum of two products" or "near-square" representations with priced operands; the estimates are mine.
- The Pollard-rho timing is a standard estimate, not benchmarked here.
- How the organisers generated targets is unknown; 3c and 3d are only as useful as the hidden structure is real.

## 4. Pool design: additive bases, postage-stamp problem, multiplicative and sum–product bases, geometric pools, Sidon sets, universal bases

### Takeaway
I found no construction or theory for pools that maximise four-operation reachability; the additive theory (postage stamp) shows a 48-element pool covers only an interval of length about 0.29–0.48·48² ≈ 670–1,100 with one addition, and sum–product theory says unstructured ("random-like") sets already maximise the number of distinct sums and products. What does matter is the size profile of the pool: in exact enumeration on synthetic pools, pools of values between one third and one half of the target's bit length made a random 49-bit target about 10 times more likely to be reachable in 4 instructions than a log-uniform pool and about 35 times more likely than a pool of old targets, which is worth roughly 0.5–0.75 instruction per target.

### Cited Findings
- Postage-stamp problem: given m and a set V, find the smallest z that is not a sum of at most m elements of V; brute force takes time proportional to |V|^m; polynomial for fixed m and NP-hard for arbitrary m. [V] — [Wikipedia, Postage stamp problem](https://en.wikipedia.org/wiki/Postage_stamp_problem)
- Extremal range with n denominations and 2 stamps: 2, 4, 8, 12, 16, 20, 26, 32, 40, 46, 54, 64, 72, 80, 92, 104, 116, 128, 140, 152, 164, 180, 196, 212 for n = 1..24. [V] — [OEIS A001212](https://oeis.org/A001212)
- An additive 2-basis with range n is a set A whose sumset A + A contains 0..n but not n + 1; explicit bases with n/k² ≥ 2/7 were known and Kohonen improves this to 85/294 > 0.2891. [V] — [Kohonen, arXiv:1606.04770](https://arxiv.org/abs/1606.04770)
- Upper bound limsup n(2,k)/k² ≤ 0.4789 (Güntürk–Nathanson, improving Rohrbach's 0.4992); computing the limits is open; Robinson's computed 2-bases suggest about 5k²/16. [S] — [Güntürk & Nathanson, arXiv:math/0503241](https://arxiv.org/abs/math/0503241); [Robinson, J. Integer Sequences 12](https://cs.uwaterloo.ca/journals/JIS/VOL12/Robinson/robinson4.html)
- Erdős–Szemerédi: max(|A+A|, |A·A|) ≥ c|A|^(1+ε) for finite sets of integers; best exponent over the reals 1/3 + 2/951 (Bloom 2025). {1..n} has |A+A| = 2|A| − 1; a geometric progression has |A·A| = 2|A| − 1; for random sets both the sumset and the product set have size about n²/2 with high probability. The page reports a 2026 disproof of the |A|^(2−o(1)) conjecture over the reals (still open over the integers); I did not check that. Lower bounds for A·A + A, A·(A + A) and A·A + A·A exceed |A|^(3/2). Bourgain–Chang: for every b there is k with max(|kA|, |A^(k)|) ≥ |A|^b for all A ⊂ Z. [V as page text] — [Wikipedia, Erdős–Szemerédi theorem](https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93Szemer%C3%A9di_theorem)
- A multiplicative basis of order h is a set whose h-fold products reach every positive integer. [S] — [arXiv:2204.00412](https://arxiv.org/pdf/2204.00412)
- Pippenger's algorithm computes p products of powers of q inputs with exponents below N in about min{p,q}·lg N + H/lg H multiplications, H = pq·lg N, which is optimal up to lower-order terms; in additive language this is the cost of an addition sequence for p integers. The source could not be fetched (parse error twice). [U] — [Bernstein, "Pippenger's exponentiation algorithm"](https://cr.yp.to/papers/pippenger.pdf)
- The Lim–Lee and BGMW fixed-base precomputation methods are parts of Pippenger's 1976 algorithm. [S] — [Bernstein, notes on US patent 5299262](https://cr.yp.to/patents/us/5299262.html)
- A search for sets A with every integer up to N representable as a·b + c (a, b, c in A) returned no relevant result. [no source found]

### Inferences

**4a. Additive bases are irrelevant for large targets and marginal for small ones.**
- With all 48 registers used as an additive 2-basis, one addition covers a contiguous range of only about 670 (Kohonen constant) to at most about 1,100 (upper bound) [C: constants × 48²]; A001212 gives 212 for 24 elements. Exact 4-operation coverage from 48 generic values is |F_1| ≈ 3,000 distinct values in total [C].
- A small additive basis (8–12 registers, range 32–64 by A001212) could serve as a digit set for the "tiny" family or for small multipliers, but it costs registers that the measurements below say are better spent on mid-size values.

**4b. Structure in the pool lowers coverage.** By the sum–product results, arithmetic progressions collapse the sumset and geometric progressions collapse the product set, while random-like sets keep both near n²/2. Radix pools ({d·B^j}), power-of-two ladders and similar designed families therefore reduce the number of distinct one- and two-instruction values compared with the irregular values a solver produces anyway. Do not regularise the pool. (Sidon-type distinctness of sums is automatic for irregular 20–50-bit values.)

**4c. Size profile of the pool: exact enumeration [C].** Synthetic pools of 48 values, value_limit = 2.24·2^49, target window [2^48, 2^49), all four operations with validity rules, three random seeds each. D_k = number of distinct values in the window reachable in ≤ k instructions.

| pool shape | \|F_1\| | \|F_2\| | D_1 | D_2 | D_3 |
|---|---|---|---|---|---|
| A: log-uniform over 1–49 bits | 2,970 | 191,000 | 112 | 9,600 | 853,000 |
| B: all 48 values at 23–26 bits (≈ √target) | 3,310 | 245,000 | 329 | 51,700 | 4,580,000 |
| C: 8 start-like (≤ 1998) + 40 log-uniform 11–49 bits | 2,990 | 183,000 | 84 | 7,900 | 711,000 |
| D: 8 start-like + 40 "old targets" at 44–49 bits | 2,390 | 80,800 | 585 | 22,800 | 633,000 |
| E: 8 start-like + 20 at 20–30 bits + 20 at 40–49 bits | 2,690 | 125,000 | 195 | 12,400 | 693,000 |
| F: 16 at 8–13 bits + 16 at 22–27 bits + 16 at 36–49 bits | 2,900 | 165,000 | 78 | 10,000 | 957,000 |
| G: 8 start-like + 16 at 14–20 bits + 24 at 28–36 bits | 3,090 | 201,000 | 42 | 8,400 | 949,000 |

Depth 4, one seed per shape, measured in the lowest 1/256 of the window, so noisy by a factor of about 2–3. ρ_k = fraction of the window reachable in ≤ k instructions = probability that a random 49-bit target is hit. Growth uses ρ_3 from the same sub-window.

| pool shape | \|F_3\| | ρ_3 (full window) | ρ_4 | growth 3→4 |
|---|---|---|---|---|
| A: log-uniform over 1–49 bits | 9.5·10^6 | 2.8e-9 | 2.4e-7 | ×99 |
| B: all 48 values at 23–26 bits | 1.9·10^7 | 1.6e-8 | 9.7e-7 | ×96 |
| D: 8 start-like + 40 "old targets" at 44–49 bits | 2.1·10^6 | 2.2e-9 | 7.3e-8 | ×21 |
| H: 8 start-like + 16 at 10–14 bits + 24 at 22–27 bits | 2.6·10^7 | 6.8e-9 | 2.2e-6 | ×97 |
| I: all 48 values at 14–18 bits (≈ one third of the target's bits) | 3.2·10^7 | 7.0e-9 | 2.6e-6 | ×184 |

- Reading: the best profile depends on the remaining depth. At 3 instructions a pool concentrated at half the target's bit length (B) leads by 5–7 times. At 4 instructions pools of smaller values overtake it: 14–18-bit values (I) and the small/mid mixture (H) reach 2.2–2.6·10^-6, against 1.0·10^-6 for B, 2.4·10^-7 for log-uniform and 7·10^-8 for old targets. Since one instruction multiplies the count by roughly 100, the factor of about 10 between the best shapes and a log-uniform pool is worth about 0.5 instruction per target, and the factor of about 35 against an old-target pool about 0.75.
- A pool dominated by old targets (D) has the most 1-instruction hits (differences and sums of large values) but the slowest growth (×28 from 2 to 3 and ×21 from 3 to 4, against about ×100 elsewhere) and the smallest F_2 and F_3: values near value_limit cannot be multiplied, so each contributes only ± combinations. Keeping finished targets in registers is the least productive use of a register for multiplicative reach.
- Practical rules that follow: (i) evict large stale values first and keep values between about b/3 and b/2 bits of the remaining targets (repository B's "evict large, least recently used, keep small" rule points the same way); (ii) among equal-cost derivations prefer balanced products x·y ± z whose factors stay in the pool over unbalanced q·b ± c with a tiny b, because the by-products are the future pool; (iii) order targets so that those of similar bit length are processed together while the matching √-scale values are resident.
- Might not transfer: the pool must serve targets of 1–60 bits at once; mid-size values are not free and must arise as by-products; the extrapolation from depth 3–4 to depth 6 is unverified; real solver pools may already look like shape B.

**4d. Counting bound for a whole puzzle [C].** Number of distinct value-DAGs with m instructions from n_0 start values is at most (2(n_0+m)²)^m / m!, and a DAG covers C(m, T) target sets. Requiring this to reach (2^(b−1))^T / T! for T = 30 random b-bit targets gives, with unlimited registers:

| target bits | minimum instructions per target (n_0 = 3) | (n_0 = 8) |
|---|---|---|
| 30 | 2.63 | 2.60 |
| 39 | 3.47 | 3.40 |
| 45 | 4.00 | 3.97 |
| 49 | 4.37 | 4.30 |
| 55 | 4.87 | 4.83 |
| 60 | 5.33 | 5.27 |

- The brief's 3.15 corresponds to targets a little under the 39-bit median. For a puzzle of 30 random 49-bit targets the same argument gives 4.3–4.4, and this bound ignores validity, value_limit and the 48-register limit, each of which raises it. At one target from a 48-value pool the analogous DAG bound says 5 while the tree count says 6 and enumeration says about 7, so the bound is optimistic by 1–2 instructions per target at that scale.
- Consequence: on unstructured 49-bit puzzles the true optimum is probably between 5 and 6 per target, not near 3. A per-family, per-bit-length table of "our instructions per target minus (bits − 5)/7.65" would show where the 147,310 → 125,650 gap actually sits; I expect it mostly in structured families and small or mid-size targets, not in 49-bit independent targets.

**4e. Additive-only universal constructions do not compete.** Pippenger's bound [U] for 30 integers below 2^49 is about 49 + 1470/lg(1470) ≈ 189 additions, 6.3 per target before lower-order terms, against the measured 8.6 for Bos–Coster and 5.5 for the current multiplicative solver. An optimal addition-only method would at best match what multiplication already gives.

### Gaps
- No literature was found on extremal or universal pools under mixed +, −, ×, ÷ with a fixed number of operations. Countdown analyses (6 inputs) and A140606 are the nearest.
- The Güntürk–Nathanson and Robinson constants are from search summaries; A001212 lists values only up to 24 elements, so the 48-element figure is an extrapolation of asymptotic constants.
- The Pippenger statement is from memory.
- The pool-shape experiment used synthetic pools and a single target window; the depth-4 figures are from one seed and a 1/256 sub-window. Depths 5–7 were extrapolated, not measured. It should be repeated on real register contents and on the actual mix of target sizes.
- Not reached before the wrap-up request: Yu's upper bound for additive 2-bases, the planted k-SUM literature (ECCC 2023/060), and any check of Kaggle discussion threads for pool-design ideas.

## 5. Simultaneous structure: small sets of intermediates shared by about 30 targets (approximate common divisors, simultaneous Diophantine approximation, clustering by quotient or difference)

### Takeaway
Approximate-common-divisor and simultaneous-approximation lattices are cheap, exact tools for finding an unknown value B such that many targets are q_j·B + small; they can only help where the generator planted such structure. For unstructured targets the remaining lever is deep sharing: choosing derivations so that a 2–4-instruction intermediate lies on the derivations of two or more targets. Counting says this could save up to about 0.5 instruction per target, at a search cost of 10^9–10^11 table probes per puzzle.

### Cited Findings
- The approximate common divisor (ACD) problem underlies several homomorphic encryption schemes; the lattice algorithms compared are simultaneous Diophantine approximation, the orthogonal lattice method, and the multivariate polynomial (Coppersmith) method of Cohn and Heninger; "the multivariate polynomial approach is not better than the orthogonal lattice algorithm for practical cryptanalysis". [V] — [Galbraith, Gebregiyorgis, Murphy, ePrint 2016/215](https://eprint.iacr.org/2016/215)
- Cohn–Heninger: in the m-variable case with modulus N and approximate common divisor of size N^β, the tolerated error improves from N^(β²) to N^(β^((m+1)/m)), under a commonly used heuristic assumption. [V] — [Cohn & Heninger, arXiv:1108.2714](https://arxiv.org/abs/1108.2714)
- Simultaneous Dirichlet theorem: for α_1..α_d there is 1 ≤ q ≤ N with |α_i − p_i/q| ≤ 1/(q·N^(1/d)). [V] — [Wikipedia, Dirichlet's approximation theorem](https://en.wikipedia.org/wiki/Dirichlet%27s_approximation_theorem)
- Orthogonal-lattice first step of Nguyen–Stern and its polynomial-time completion. [V] — [Coron & Gini, ePrint 2020/461](https://eprint.iacr.org/2020/461)
- In the dense regime of k-SUM (many solutions) one solution is found much faster than in the sparse regime. [V] — [arXiv:2111.00486](https://arxiv.org/abs/2111.00486)

### Inferences

**5a. Approximate common divisor among targets.**
- What it does: finds an unknown B (not in the pool, not a target) such that t_j = q_j·B + r_j with small r_j for several targets j.
- Mapping: targets are the ACD samples, r_j are offsets a puzzle can supply cheaply (start values ≤ 1998, or small F_1 values). After B is found, each participating target costs 1 multiplication + 1 addition + cost(q_j) + cost(r_j), and B is paid once.
- Tolerated error from the Cohn–Heninger exponent, with N = 2^49 and 11-bit offsets [C]: β^((m+1)/m) > 11/49 = 0.224 requires B ≥ 23 bits with m = 1 (two targets), ≥ 18 bits with m = 2, ≥ 15 bits with m = 4, ≥ 13 bits with m = 9.
- Complexity: lattice dimension m + 1 ≤ 10, LLL in microseconds to milliseconds; trying all subsets is unnecessary because a wrong sample only weakens the lattice, so run on sliding groups of targets sorted by size. A non-lattice alternative with the same output: factor t_j − δ for δ in P ∪ small F_1 and hash the large divisors across targets (section 3d), about 10^5 factorizations per puzzle.
- Expected benefit: for a cluster of g targets sharing B with q_j cheap, roughly cost(B) + g·(2 + cost(q_j)) instead of g·6. Zero on unstructured puzzles: for random targets a common B of β·49 bits with 11-bit offsets exists by chance only when 2^(β·49)·(2^11)^g ≳ 2^(β·49·g), which fails for every g ≥ 2 once B exceeds about 22 bits [C].
- Might not transfer: the existing factor-sharing and q·b ± c passes find B only when B is already a pool value or an exact divisor; ACD adds something only if the generator used hidden multipliers with small additive noise. If q_j is as random as a 25-bit number (3 instructions) the saving per target is about 1.

**5b. Simultaneous Diophantine approximation of target ratios.**
- Mapping: a common denominator q with q·t_j/t_0 all near integers p_j gives t_j = (p_j·t_0 + e_j) ÷ q.
- By the simultaneous Dirichlet bound the generic error with d ratios is t_0/Q^(1/d): for d = 2 and Q = 2^16 the remainders are still about 41 bits. Generic targets gain nothing; an error far below that bound is a structure signal. This is the ratio-space view of 5a and of the hidden-generator lattice in 2c; run one of them, not all three.

**5c. Clustering by quotient or difference.** Sorting targets and taking differences finds additive clusters (already tried). The continued-fraction scan of all pairs (section 3c) is the complete version for rational relations q·t_i − p·t_j = e with small p, q, e. Cost about 13,000 division steps per puzzle.

**5d. Deep shared intermediates for unstructured targets: collision search across targets.**
- What it is: find x with cost c from the pool, and two targets t_1, t_2 reachable from pool ∪ {x} in a and b further instructions with x used in both. Total c + a + b instead of (c + a) + (c + b). This is a generalized-birthday problem across targets and across alternative derivations, and unlike the single-target problem it is in the dense regime because there are 435 target pairs and thousands of candidate x.
- Counting [C, nominal A140606 bound]: with singles at 6 instructions, the expected number of bundles with c + a + b = 11 is 2.0 per pair of 49-bit targets (889 per puzzle), and with total 10 it is 0.0086 per pair (3.7 per puzzle). Applying the measured validity/in-range discount (0.3–2% per target-hitting expression) shifts everything by about one instruction per target: singles at about 7, bundles at 13 common, bundles at 12 for a few percent of pairs.
- Why it can work: one instruction buys about 7.65 bits, a single target needs a fractional 5.6–6.4 instructions and rounds up alone; a joint derivation pools the rounding slack of both targets. The gain is therefore at most about 0.5 instruction per target from pairs, more from triples, converging toward the DAG bound of 4d.
- Search procedure and cost: enumerate candidate x in F_2 (≈ 2·10^5); for each x form the ≈ 3·10^4 values reachable from x in ≤ 2 further instructions and probe a merged backward table {t_j ∘⁻¹ w : w in F_2, all j} (30 × 8·10^5 ≈ 2.4·10^7 entries). About 6·10^9 probes per puzzle, minutes per core. With x in F_3 it is about 10^11–10^12 probes, hours per core, so that depth needs filtering.
- Cheaper variant: enumerate all derivations of each target with optimum and optimum + 1 instructions (tens to thousands of alternatives), collect their by-products, and test each by-product against the other targets' backward sets. This chooses, among near-optimal derivations of t_i, the one whose by-products make another target cheaper. The existing "shared intermediates first" greedy looks only two steps ahead from x; the counting says the valuable sharings are 3–5 steps from x to each target.
- Expected benefit: at most about 8% on unstructured puzzles, realistically a fraction of that after matching conflicts between pairs and register pressure; unknown share of the total score because the family mix is unknown to me.
- Might not transfer: the discount factors are from synthetic pools; if singles on real pools already average 6.3, the slack to pool is smaller; large-neighbourhood search on the value DAG may already find the shallow cases; holding x until both targets are built uses a register.

### Gaps
- The ACD parameter conditions in Galbraith et al. (lattice dimension as a function of γ, η, ρ) were not read (PDF 403); the thresholds in 5a come from the Cohn–Heninger abstract formula only.
- No source addresses joint short derivations of many unstructured integers with multiplication beyond the counting bounds already in `notes/research.md`; 5d is my construction and its benefit is an estimate, not a measurement.
- Whether "shared" and "mixed" puzzles contain hidden common multipliers with small offsets was not tested on the data (out of scope for this literature task). A one-off run of 2c, 3c, 3d or 5a over all 1,000 puzzles would settle it.
