# Structured construction: joint small-value sets and k·a·b + r families (Santa 2026 Elf Calculator)

Researcher notes, 2026-11-24. Scope: only material not already in `notes/research.md` and the three reports in `reports/`. Not repeated here: Bos–Coster reduction, windowing, Thurber–Clift exact search, Hcub, MCM integer programming (Garcia–Volkova), approximate-common-divisor lattices as a detector (Cohn–Heninger, Coron–Gini), the public Pippenger-bucket loss, the helper-budget exact enumeration, recipe-pool ILP/CP-SAT, and the multiplier-lane score line 138,905 → 138,769.

Evidence tags used on every claim:

- **[text]** verified against the source text that I read (paper body, repository file, or a fetch of the raw file).
- **[abstract]** abstract, landing page, or a summariser's reading of the page only.
- **[unverified]** search snippet or memory; the source was not opened.
- **[estimate]** my own computation (formula plug-in or a small synthetic simulation; scripts in the session scratchpad, not project data).
- **[inference]** my transfer of a source to the competition's cost model. Every cited theory assumes "no multiply instruction, start from 1, unlimited registers"; all transfers are inferences.

Access notes. `cr.yp.to` could not be read by the fetch tool; I downloaded the public PDF of Bernstein's survey and read the extracted text. The AIMS paper was read the same way. Kaggle pages were not read. In `Hansen0223/Santa_2026` the README does not describe the repository as private or internal (it says the repository holds solver code, candidate submissions and verification records, and is where developers "take over tasks and see what others have tried") [abstract]; I read README-level documents and two solver source files through a summariser, and downloaded no solution or program files. The `Juan-Severiano/santa-2026` document reads like an internal research memo inside a public repository; I read that single page only (it was already cited in the earlier report).

## 1. Small-set problem: shortest program for a whole set of 30–100 small integers when +, −, × (and exact ÷) each cost one

### Takeaway
No published algorithm targets this exact cost model; the classical addition-sequence bounds (Yao, Pippenger) are 3–7 additions per element at our sizes and are the wrong tool, while a plain "closure plus best helper" greedy already reaches about 1.1–1.7 instructions per element on random 12-bit sets in simulation. The useful imports are structural: treat the scalars as one addition-multiplication sequence problem, minimise helpers (cost = set size + helpers), and use exact helper-budget search only for the last few helpers.

### Cited Findings
- Yao (1976): there is an addition chain containing n1,…,np of length at most lg B + (p + o(1))·lg B / lg lg B for fixed p and B → ∞; the union of Yao's chains has length j(k + p) + (2^k − 2)p when all lg n_i < (j+1)k [text] — [Bernstein, "Pippenger's exponentiation algorithm"](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- Pippenger's special case for a set S of exponents of one base costs about (#S + 2^c)(lg B)/c multiplications; "If c ≈ lg #S − lg lg #S and #S is large then this special case … uses about #S(lg B)/lg #S multiplications, while Yao's algorithm uses about #S(lg B)/lg lg B" [text] — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- Lower bound: Pippenger showed that almost all exponent matrices require min{p,q}·lg B + (1 + o(1))·pq·lg B / lg(pq·lg B) multiplications; Erdős: for almost all n the shortest chain is lg n + (1 + o(1))·lg n / lg lg n [text] — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- The whole theory assumes no multiply instruction. Bernstein quotes Pippenger: "If we have no MULTIPLY instruction in our machine, we must simulate scalar multiplication by addition" and "This problem would be more realistic if we allowed negative coefficients, subtractions, and short shifts. These changes would not affect our analysis or results in any significant way" [text] — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- "Limit the precomputation": the digit table 1,2,…,2^k − 1 of a window method "can be replaced by any addition chain that contains c0, c1, …, cj" (Thurber); "One could use Yao's algorithm or Pippenger's algorithm to find an addition chain containing c0,…,cj. Or one can spend more time searching for a better chain" (pointing to Bos–Coster pp. 405–406). This is exactly the small-set sub-problem, and the survey offers no dedicated method for it [text] — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- Bergeron–Berstel–Brlek: a unifying continued-fraction framework for short addition chains; binary and factor methods are special cases; generating chains for all integers up to n costs O(n log² n · γ_n) where γ_n is the cost of computing the strategy's choice set; an analogue of the Scholz–Brauer conjecture is proved [abstract] — [Efficient computation of addition chains, J. Théor. Nombres Bordeaux 6 (1994)](http://www.numdam.org/item/JTNB_1994__6_1_21_0/)
- Structured dense sets can cost about one operation per element: the first N exponents of theta/eta series are reachable with N + o(N) multiplications; every generalised pentagonal number c can be written c = 2a + b with a, b smaller generalised pentagonal numbers; a baby-step giant-step scheme uses O(N / log^r N) multiplications for the sum [abstract] — [Enge, Hart, Johansson, "Short addition sequences for theta functions"](https://arxiv.org/abs/1608.06810)
- Addition-multiplication chains (each term a sum or product of two earlier terms): ℓ_AM(n) ≤ ℓ_A(n); the only integers with no "small step" are 2^(2^A); "the computational complexity of generating a shortest AM-chain remains an open problem"; the 2026 paper bounds chain elements by the number of squaring steps and classifies all chains with exactly one small step. It mentions addition sequences for sets only as a different generalisation and gives no result for sets [text, introduction and theorem list] — [Tarek, Bahig, Anwar, AIMS Mathematics 11(6), 2026](https://www.aimspress.com/aimspress-data/math/2026/6/PDF/math-11-06-667.pdf)
- Bahig (2008) introduced the AM-chain generalisation and shows addition-chain notions carry over [unverified, search summary] — [On a generalization of addition chains: addition–multiplication chains](https://www.bohrium.com/paper-details/on-a-generalization-of-addition-chains-addition-multiplication-chains/812000378634633216-992)
- Kumm's ILP for optimal constant multiplication (IEEE TCAS-II 65(5), 2018); the companion book chapter states that optimal methods only scale to relatively small problems, which is why heuristics such as RPAG remain necessary [unverified, search summary] — [Kumm 2018 record](https://researchr.org/publication/Kumm18/bibtex), [chapter](https://www.springerprofessional.de/en/optimally-solving-mcm-related-problems-using-integer-linear-prog/10012336)

### Inferences
- **Classical bounds at our size are far from 1 per element [estimate].** For 60 exponents below 2^12: Yao's union is at least 430 additions (k = 2, j = 5), 7.2 per element; Pippenger's special case is 221–228 (c = 4 or 5), 3.7–3.8 per element; for 100 elements about 317 (3.2 each); for 30 about 138 (4.6 each). The asymptotic lower-bound formula with p = 1, q = 60 gives about 88 (1.46 each), but its o(1) term is uncontrolled at this size. This explains from the formulas why a Pippenger-style bucket synthesis lost on real puzzles: buckets pay (lg B)/c per element, and with lg B = 12 that is 2–4, while dense small sets admit about 1.
- **The true floor is exactly 1 per element** (every non-start value needs its own instruction), so the quantity to minimise is the number of helper values. Cost per element = 1 + helpers/n.
- **Simulation [estimate; synthetic uniform sets, start values 16, 29, 33, four trials each, simple greedy, value cap 2^17].** "Joint" = add every target that is one operation from the pool; when stuck, buy the one-step helper that unlocks the most targets. "Sequential" = targets in arbitrary order, each built alone with at most one helper.

  | Set | n | Joint | Sequential |
  |---|---|---|---|
  | all below 2^12 | 30 | 1.67 | 2.23 |
  | all below 2^12 | 60 | 1.28 | 1.83 |
  | all below 2^12 | 100 | 1.13 | 1.54 |
  | 85% below 2^12, 15% below 2^16 | 60 | 1.44 | 1.92 |
  | all below 2^9 | 60 | 1.02 | not run |
  | additions only from 1, below 2^12 | 60 | 1.74 | not run |
  | additions and subtractions from 1, below 2^12 | 60 | 1.46 | not run |

  Joint ordering saves 0.4–0.55 instructions per element against the crude sequential baseline (17, 33 and 41 instructions at n = 30, 60, 100). Our real solvers are smarter than this baseline, so the realisable gain is smaller. Below 2^9 there is almost nothing left to gain.
- **Continued-fraction method maps to a rule we already have.** A step n = q·k + r costs ℓ(q) + 1 in addition chains but 2 instructions here when q, k, r are stored. For a set, the set-level version is: choose one or two shared radices k so that all quotients and remainders fall in a tiny dense range, where each costs about 1. For 12-bit values and k near 64 this is 2 instructions per element plus the digits actually used; the simulated joint greedy (1.1–1.7) is already better, so the radix scheme is a fallback, not the plan.
- **Exact MCM solvers do not adapt directly.** Their linear models work because one operand is a variable and the other a shift constant. A product of two stored values is bilinear. Because the scalars here are at most 16 bits, a CP-SAT model with multiplication constraints is representable (products fit in 32 bits), but the earlier finding that even linear MCM proofs stall around 12-bit coefficients argues against a monolithic model. The workable exact tool is the helper-budget enumeration already documented in the earlier report, applied to the scalar sub-problem alone, where the universe is small.

### Gaps
- I found no paper on addition-multiplication *sequences* (several targets, + and × both unit cost), no integer-complexity result for sets, and no table of ℓ_AM beyond single integers. OEIS integer-complexity entries were not opened this round.
- Not opened: Knuth 4.6.3 itself (only Bernstein's citations of its exercises 9, 32, 39), Olivos (1981) directly, Bleichenbacher–Flammenkamp, Aksoy et al., Kumm's paper body, the body of Bergeron–Berstel–Brlek (so the n = q·k + r description above is from general knowledge of the method [unverified]).
- The simulation uses uniform random sets; the real multiplier/offset sets are unknown to me. The first measurement to make is the per-puzzle histogram of distinct k and r values and their bit sizes from our decoder output.

## 2. Family problem: about 30 targets k_j·P + r_j as vectors (k_j, r_j) over the basis (P, 1)

### Takeaway
Vector-addition-chain theory prices the purely additive route at roughly 3.3 additions per target for random 12-bit (k, r) and proves that re-association (Straus-like versus Yao-like) cannot change that cost; a multiply instruction changes the model, so the family reduces to the scalar-set problem plus glue. Storing k and multiplying wins when k is reused across lanes; building k·P inside the lane ("lifted") wins when k is used once, by up to about 0.6 instructions per target in simulation.

### Cited Findings
- Straus computes one product of p powers, i.e. the vector (n1,…,np) from unit vectors, with j(k+1) + 2^(pk) − p − 1 additions when jk ≤ lg B ≤ (j+1)k; for fixed p this is lg B + (p + o(1))·lg B / lg lg B. Example: x^31415 costs 19, x^27182 costs 18, the pair 21, the product x1^31415·x2^27182 22 [text] — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- General Pippenger: q products of powers of p inputs cost at most p·lg B + (1 + o(1))·pq·lg B / lg(pq·lg B), and the transposed algorithm q·lg B + the same second term; the matching lower bound holds for almost all matrices [text] — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- Transposition: "The transpose of a Brauer-Straus-type algorithm is a Yao-type algorithm, and vice versa." Olivos: the minimum number of vector additions for (n1,…,np) from unit vectors is p − 1 more than the shortest addition chain containing n1,…,np. Knuth–Papadimitriou: computing the column vectors of a p×q matrix costs p − q more than computing its row vectors [text, as reported by Bernstein] — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- Yao's chain is "mostly independent of n": after the shared powers are computed, each further exponent costs j + 2^k − 2 [text] — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf)
- Multi-scalar multiplication practice: one library uses Straus below 50 points and Pippenger above; one implementation notes a Straus/Pippenger crossover at 232 points. Both are for scalars of about 253 bits and are implementation-specific [unverified, search summary] — [generic-ec multiscalar source](https://docs.rs/generic-ec/0.4.5/src/generic_ec/multiscalar.rs.html), [Monero multiexp source](https://cdn.jsdelivr.net/npm/react-native-mymonero-core@0.3.4/android/src/main/cpp/monero-core-custom/ringct/multiexp.cc)
- Public "shared quotient" experiment: write t = q·k ± r with base k from the retained set and r from the set or a one-step value up to 512, rebuild q directly or split once more. On 36 puzzles it saved one instruction on 4 independent-line puzzles and 1 public-line puzzle (141,438 → 141,434; 135,077 → 135,076); on 80 planted cases it rebuilt 80 groups against 0 for the baseline [abstract] — [shared-quotients](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/shared-quotients/README.md)
- Public "joint Euclid" experiment: a two-target reverse chain (A, B) → (B, |A − kB|) for up to eight rounds, and a shared scale/intercept rewrite u = k·h + e, v = l·h + e with h recovered from v − u = (l − k)·h. Both shorten planted examples (18 → 6 and 8 → 6) and save nothing on 24 strong parents; of 13,615 node pairs, 87 scale/intercept combinations survived algebraic screening and 8 constructions in 3 puzzles were built, none shorter (173 vs 170, 140 vs 139, 196 vs 196) [abstract] — [joint-euclid](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/joint-euclid/README.md)
- Public "affine elimination" (solve two anchors z = ax + by + c, w = dx + ey + f for hidden x, y): 188 new inverse paths, zero attributable gain on 24 frozen rows [abstract] — [affine-elimination](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/affine-elimination/README.md)

### Inferences
- **Additive price of the family [estimate].** With p = 2 inputs (P and 1), q = 30 targets and B = 2^12, the Pippenger formula gives 2·12 + 720 / lg 720 ≈ 100 additions, about 3.3 per target, excluding the cost of P. The 2×30 matrix transposes to two 30-term multi-products, and by Knuth–Papadimitriou the two costs differ by exactly 28, so no re-association trick lowers the additive cost. Any saving must come from the multiply instruction or from structure in the (k, r) pairs.
- **With multiply, the family is the scalar-set problem plus glue.** Given stored k_j and r_j, each target costs 2 (multiply, add). Total = cost(K ∪ R as a set) + distinct k + q.
- **Stored multiplier versus lifted lane [estimate; 10 trials, q = 30, P given, uniform random scalars].** Option A stores every k and multiplies. Option B builds each k·P inside the lane with additions/subtractions of stored multiples of P and multiplication of a stored multiple by any stored scalar (the offsets are stored anyway), never materialising k.

  | Scalars below | Distinct k / r | A: stored k | B: lifted lane |
  |---|---|---|---|
  | 2^12 | 29.9 / 30.0 | 4.55 per target | 4.32 |
  | 2^9 | 29.3 / 29.6 | 3.91 | 3.27 |
  | 2^6 | 23.4 / 24.3 | 3.02 | 2.56 |
  | 2^4 | 12.1 / 13.1 | 1.89 | 1.84 |

  Lifting saves up to one multiplication per single-use k; the measured saving is 0.05–0.65 per target, largest at 6–9 bits (14–19 instructions on a 30-target lane).
- **Decision rule.** Store k as a scalar when it has at least two uses: it multiplies two or more different bases, or it also serves as an offset or as an ingredient of other scalars. Otherwise build k·P in the lane. Exact division gives a third option for an expensive k that is needed elsewhere: k = (k·P)/P costs one instruction.
- **Sibling relations give the only route to 1 per target.** t_j = t_i ± s (same k, stored offset difference), t_j = t_i ± m·P (same r, stored multiple), t_j = c·t_i ± s. Our measured 2.86 per target on a multiplicative puzzle is already below the 3.0 of option A at 6 bits before hub costs, so the real programs must rely on such relations and on small repeated scalars; the constructor has to model them explicitly.
- **Why bucket methods lost.** The crossover evidence from multi-scalar multiplication (50–232 points at 253 bits) and the formula plug-ins above agree: 30 outputs with 12-bit scalars are far below the regime where Pippenger-style bucketing pays.
- **Public experiments say single- and pair-level rewrites are exhausted on strong parents.** Shared quotient, shared intercept, dual Euclid and affine elimination all work on planted cases and save 0–1 per puzzle on 134k–141k programs. The only matched comparison that showed a gain from structure is grouping several roots by a common factor (earlier report: 5 for single roots versus 10 for same-factor packets). This points to whole-lane construction, not more pairwise identities.

### Gaps
- No source treats vector chains with a unit-cost scalar multiplication. The additive estimate of 3.3 per target is an asymptotic formula at a size where its error term is not controlled; whether a two-dimensional Bos–Coster-style reduction with scalar-multiply steps beats options A/B on real (k, r) data is untested.
- The simulation assumes one base P and uniform scalars. With several products sharing the same multiplier set, option A amortises and should win; this needs the real data.

## 3. Where the offset goes: k·(a·b) + r versus (k·a + r′)·b + r″ and other nested forms

### Takeaway
An offset inserted before a multiplication is scaled by every later multiplier, so the choice of form is a mixed-radix digit expansion of the offset in the radices k, a, b; the public structure solver implements exactly two such forms. Polynomial-evaluation theory with preprocessing does not transfer as a cost result, because it counts only non-scalar multiplications, but its principle (choose the form whose constants are already paid for) is the right selection rule.

### Cited Findings
- The public structure scanner accepts a target only if t = k·a·b + r **and** r = k·d + e with a, b among the recovered hub integers, i.e. the recovered model is t = k·(a·b + d) + e. By default it scans only puzzles whose largest start value is at most 35 and that have at least 6 targets. The search itself is in a compiled binary that I did not see, so its tolerances are unknown [abstract of source file] — [matrix_scan.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/solvers/matrix/matrix_scan.py)
- The public constructor builds, per target, a single-stage route P = a·b; c = x ± |s|; M = c·m; t = M ± |e|, where the origin x is P or another target on the same P, m = k/q, and s is tried at round(gap/m), its neighbours, and ±1, ±2 when |gap| < 8192. A two-stage route (when m ≥ 4, m = outer·inner) is mid0 = c·inner; mid = mid0 ± |u|; last = mid·outer; t = last ± |tail|, with the correction round(e/outer) tried at −1, 0, +1. Source comments: "Insert a correction between consecutive multiplications." and "Prefer shared centers and constants." Routes are ranked by how many targets share their nodes and leaves; one route per target is chosen by up to 8 greedy passes in shuffled order with a small random tie-break; a leaf not in the start values is priced 1 + max(0, log2 v − 3)/6 [abstract of source file] — [matrix_construct.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/solvers/matrix/matrix_construct.py)
- The repository README states that the solver builds several targets from the multiplication table of the recovered integers "while comparing the instruction count of adding the deviation before or after the multiplication", and that the cost of constructing those integers must still be paid; it gives no separate measured gain for these tools [abstract] — [Hansen0223 README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/README.md)
- Multivariate Horner schemes leave the variable order open; the usual greedy is "most-occurring variable first"; Monte Carlo tree search over orders reduces evaluation cost "sometimes by factors up to two" [abstract] — [Kuipers, Vermaseren, Plaat, van den Herik](https://arxiv.org/abs/1207.7079)
- Paterson–Stockmeyer evaluate a degree-n polynomial with about √n non-scalar multiplications, counting scalar multiplications and additions as free [unverified, from memory] — [SIAM J. Comput. 2(1), 1973](https://doi.org/10.1137/0202007)

### Inferences
- **Algebra of the forms.** k·(a·b) + r leaves r unscaled. k·(a·b + d) + e gives r = k·d + e. (k·a + r′)·b + r″ gives r = r′·b + r″. ((P + s)·inner + u)·outer + tail gives r = s·k + u·outer + tail. In each case r is written in mixed radix with the later multipliers as radices, and the form is usable when every digit is a cheap scalar.
- **Instruction counts given the scalars and a·b.** After: multiply + add = 2, plus building r if it is not in the pool (at least 2 for r = k·d + e). Before: (a·b + d) once per (a, b, d), then multiply, then add e unless e = 0 = 2–3, and the shifted centre is shared by all targets with the same d. Nested: k·a once per (k, a), + r′, × b, + r″ = 3–4, and it is the only form that makes an offset of the size of a hub integer cheap.
- **Association order is a small covering problem.** k·a·b can be formed as k·(a·b), (k·a)·b or (k·b)·a; each creates a different shareable intermediate. Choosing the fewest pair intermediates so that every target's triple contains a chosen pair is a hitting-set instance with at most 30 triples and 90 candidate pairs, small enough for exact search. This is the multi-output version of the Horner-order choice; "most-occurring first" is the natural greedy start.
- **Preprocessing theory transfers as a rule, not a bound.** In Paterson–Stockmeyer and adapted-coefficient schemes constants are free; here a constant costs one instruction once and nothing afterwards. The rule that carries over is to pick, for each target, the form whose digits coincide with scalars that are already paid for, and to let that choice feed back into which scalars are bought.

### Gaps
- No measured comparison of before/after/nested placement is published; the public repository reports only that both are tried.
- Knuth 4.6.4 (adaptation of coefficients) and the Paterson–Stockmeyer text were not opened; the statement above is from memory.

## 4. Decoding two-level structure t = (k1·h + r1)·k2 + r2

### Takeaway
I found no literature on approximate common divisors with product-form offsets; the general lattice comparison says the orthogonal-lattice method is the practical one, but at our sizes exhaustive enumeration is cheaper and exact. A two-level target is a one-level sample with multiplier k1·k2 and offset k2·r1 + r2, so it is detectable only when h is large and the inner residue r1 is small; the practical decoder enumerates k2 (or divisors of the rounded quotient) and accepts by construction cost, and applies the one-level detector recursively to recovered integers.

### Cited Findings
- Galbraith, Gebregiyorgis and Murphy compare the simultaneous-Diophantine-approximation lattice, the orthogonal lattice and the Cohn–Heninger multivariate method for the approximate common divisor problem and conclude that the multivariate approach "is not better than the orthogonal lattice algorithm for practical cryptanalysis"; sample amplification and a BKW-style pre-processing do not help. The page mentions only the general problem, no structured-noise variant [abstract] — [Algorithms for the Approximate Common Divisor Problem](https://eprint.iacr.org/2016/215)
- The public scanner's accepted identity already has a two-level shape, t = k·(a·b + d) + e, with the inner offset d applied to the hub product; nothing in the visible file handles (k1·h + r1)·k2 + r2 with a multiplier inside [abstract of source file] — [matrix_scan.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/solvers/matrix/matrix_scan.py)
- A difference-based detector for a shared offset: for u = k·h + e and v = l·h + e, v − u = (l − k)·h recovers h; 13,615 node pairs yielded 87 combinations after screening [abstract] — [joint-euclid](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/joint-euclid/README.md)

### Inferences
- **Reduction.** t = (k1·h + r1)·k2 + r2 = (k1·k2)·h + (k2·r1 + r2). When |k2·r1 + r2| < h/2, K = round(t/h) equals k1·k2 exactly and the residue ρ = t − K·h equals k2·r1 + r2; then k2 divides K, r2 ≡ ρ (mod k2) and r1 = (ρ − r2)/k2. When the offset can exceed h/2, try K + δ for δ in −2…2.
- **Enumeration given a candidate h.** Either loop over divisors k2 of K (cheapest), or loop over k2 in the scalar pool and small integers, take r2 as the centred residue of t mod k2 (and pool values in the same residue class), set M = (t − r2)/k2, r1 = centred M mod h, k1 = (M − r1)/h. About |pool|² steps per (t, h), trivial for 30 targets and tens of candidates.
- **Selectivity [estimate].** Small k2 always fits (k2 = 2 fits every target), so "fit" is not evidence; accept only when the four scalars are cheap. With k2 between 2^8 and 2^12 and |r2| ≤ 4, a random target has about 9·ln 16 ≈ 25 accidental (k2, r2) pairs; requiring |r1| ≤ 8 against h near 2^20 cuts this to about 4·10^-4 per (target, h). The decoder is therefore selective only for hidden integers of roughly 16 bits or more and inner residues of a few bits.
- **Shared middle values come for free.** If several targets share M = k1·h + r1, then M itself is an approximate common divisor of those targets with small noise, and the existing one-level decoder finds it as a hidden integer. The missing step is recursion: run the same detector on the set of recovered integers and on the quotients (t − r2)/k2. With only 4–10 recovered values of 18–22 bits and h near 2^10, tolerance 8 gives a per-value false-hit rate near 1.7%, so require at least four hits or confirm by construction cost.
- **One-level detection can be exhaustive.** For hidden integers below 2^23, testing every a against 30 targets is about 10^8 modular reductions per puzzle. With offsets below 2^12 and a near 2^20 the false-hit rate per (a, t) is about 2^-7, so five or six agreeing targets are significant; three suffice when offsets are below 2^8. Lattices are not needed at this size.
- **Lattice feasibility for larger offsets [unverified formula from memory of the paper body].** The lattice methods need roughly more than (γ − ρ)/(η − ρ) samples (γ target bits, η divisor bits, ρ noise bits). For γ = 44, η = 20 and a two-level offset of 16 bits this is 7 targets sharing h; it fails entirely when the offset reaches the size of h.

### Gaps
- No source on approximate common divisors with offsets of the form k2·r1 + r2, nor on recursive ("tower") recovery. The fetched page of the survey is the abstract only.
- How many currently unexplained targets become explained by the two-level form is unknown; it needs a scan of our data with acceptance by what-if cost.

## 5. Public evidence in this competition: multiplication-table recovery, offset placement, multiplier lanes

### Takeaway
Public material confirms the mechanisms (hub recovery with t = k·(a·b + d) + e, single- and two-stage correction routes, factor-grouped "lane" rewrites) but every measured gain on programs at or below about 141k is small, and nothing public measures a dedicated joint constructor for the small multipliers and offsets.

### Cited Findings
- The experiment directory of the public repository lists, beyond what the earlier reports read, the folders affine-elimination, joint-euclid, residue-joint, shared-intercept, shared-quotients, positional-sums, goal-differences, subset-capacity and factor; none is named for multiplication tables, lanes, nested forms or small-value sets [text, directory listing] — [collaboration directory](https://api.github.com/repos/Hansen0223/Santa_2026/contents/collaboration)
- Multiplier lanes (attributed to a public notebook, version 14): "Build an arithmetic atlas and propose factors from existing multipliers, quotients, common divisors"; proposed one-write factors must be constructible; "Group root rewrites by factor, intern each constructed value once", then price unions of recipes against the full reachable graph. Reported 138,905 → 138,769 (136 saved in 88 of 635 cases); single-root rewrites saved 5 and same-factor packets 10 on matched cases [abstract; second-hand description of a notebook; the score line was already in the earlier report] — [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)
- An independent probe of factor packets ("Each packet tries two roots of t = f*q ± r") over 1,000 puzzles evaluated 20,345 constructible factor families and 11,949 pair unions and found "zero smaller value graphs and zero physical wins" on a 132.5k baseline; adding helper pairs did not improve a 99-case sample [abstract] — [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)
- Frontier search (version 15): "Generate translated products and near products from congruent differences and recurring divisors", going beyond "target mod factor" with small residuals; 138,769 → 138,681 (88 saved in 60 of 238 cases) [abstract; already in the earlier report] — [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)
- Joint CP-SAT synthesis over residues (mod 5, or mod 5, 7, 11) of two small private segments: 99,375 and 8,609 topologies examined, no shorter full program on 32 puzzles of a 140,727 parent [abstract] — [residue-joint](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/residue-joint/README.md)
- Offset placement and hub recovery details are in sections 3 and 4 (scanner identity, single- and two-stage routes) — [matrix_construct.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/solvers/matrix/matrix_construct.py)

### Inferences
- The public structure solver treats the small constants as leaves with a size-based price and hands their synthesis to a general planner ("Include the previous pass's best small constants, then synthesize all"). It does not optimise the scalar set jointly with form choice beyond greedy passes. That is the gap a dedicated constructor would fill, and it is also why no public number exists for it.
- Gains from structure were large when programs were weak (the earlier report's 636 and 155 at about 150k) and zero to one instruction per puzzle on strong parents. Expect the dedicated constructor to pay mainly on puzzles where our current program is still far from the public merge, and to be judged per puzzle by what-if adoption.

### Gaps
- The `shared-intercept` README returned 404; `positional-sums`, `goal-differences`, `subset-capacity` and `factor` were not opened for budget reasons.
- The compiled recovery binary and the notebook sources behind "multiplier lanes" were not read; the lane description is second-hand.
- I could not verify any figure on Kaggle itself.

## 6. Design sketch for a dedicated constructor (own design; all of it inference)

### Takeaway
Build structured puzzles in three coupled layers: a jointly optimised scalar set, per-base lanes that decide for each multiplier between "stored and multiplied" and "lifted", and per-target form selection (after / before / nested / sibling) priced against the scalars actually bought, iterated to a fixed point and adopted only when shorter than the incumbent.

### Cited Findings
- Cost floor and helper framing, classical bounds, transposition, and the "limit the precomputation" remark — [Bernstein](https://cr.yp.to/papers/pippenger-20020118-retypeset20220327.pdf) [text]
- Route forms, popularity ranking and greedy re-selection passes used by the public structure solver — [matrix_construct.py](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/solvers/matrix/matrix_construct.py) [abstract of source file]
- Factor-grouped rewriting beats root-by-root rewriting 10 to 5 on matched cases — [public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md) [abstract]

### Inferences
**Objective.** Program length = targets + helpers. Helpers are hub integers and their build chains, hub products, lifted multiples, and scalars that are not themselves targets. The constructor minimises helpers.

**Layer 0, decode with alternatives.** For every target keep all cheap explanations, not only the best: after (k·P + r), before (k·(P + d) + e), nested ((k·a + r′)·b + r″ and the two-stage route), sibling (t′ ± s, t′ ± m·P, c·t′ ± s), and the two-level form from section 4. Each form lists the scalars and lifted values it needs.

**Layer 1, scalar set.** Closure plus helper search on the union of demanded scalars, seeded with the start values and with free by-products (quotients (k·P)/P, differences of targets on one lane). Finish with the existing helper-budget exact search when at most three or four helpers remain. Return a marginal price per scalar: 1 if it joined by closure, more if helpers were bought for it alone.

**Layer 2, lanes.** For each base (hub or hub product), choose the association order by hitting set, then for each multiplier: stored if it has two or more uses, lifted otherwise. Lifted closure uses sums and differences of stored multiples, multiplication of a stored multiple by any stored scalar, and exact division.

**Layer 3, form selection.** Re-choose each target's form against current prices, in shuffled order, until no change; restart a few times with random tie-breaks and keep the shortest. Scalars priced above 1 are the ones worth avoiding by switching form.

**Emit and adopt.** Order lanes so that scalars die early (registers), verify, hand to the value-graph local search, and keep the result only if shorter than the incumbent for that puzzle.

```
function BUILD_STRUCTURED(puzzle, hubs):
    forms[t]  = ENUMERATE_FORMS(t, hubs, puzzle.starts)   for every target t
    choice[t] = form with the lowest static price            # leaf price grows with bit size
    best = none
    repeat for restart in 1..RESTARTS:
        repeat until choice is stable or MAX_ROUNDS:
            need_scalars, need_lifted = DEMAND(choice)
            S = SMALL_SET(puzzle.starts + free_byproducts(choice), need_scalars)
            L = for each base P: LANE(P, need_lifted[P], S.pool, uses_across_lanes)
            price = MARGINAL_PRICES(S, L)
            for t in shuffled(targets):
                choice[t] = argmin over f in forms[t] of
                            glue(f) + sum(price of values in f not yet paid) + tiebreak_noise
        program = SCHEDULE(hub_chains, S, L, glue(choice))    # register-aware order
        if VERIFY(program) and length(program) < length(best): best = program
    return best if shorter than incumbent else incumbent

function SMALL_SET(pool0, wanted):
    pool = pool0;  remaining = wanted - pool;  steps = []
    loop:
        while some s in remaining is one operation (+, -, *, exact /) from pool:
            add s (smallest first);  record step
        if remaining is empty: break
        candidates = values one operation from pool, not in pool
        shortlist  = top M candidates by number of remaining values they make one-step
        for h in shortlist: unlocked[h] = size of closure(pool + h) within remaining
        if max unlocked >= 1:
            add the h with the largest unlocked (ties: also demanded by an alternative form, then smaller)
        else:
            try pairs (h1, h2) with h2 one operation from pool + h1
            if none: mark the smallest remaining value "expensive" and build it with the general solver
    if helpers bought <= EXACT_LIMIT: replace by the helper-budget exact search result if shorter
    return steps, pool

function LANE(P, multipliers, scalar_pool, uses):
    lifted = {1·P};  remaining = multipliers
    for k in remaining with uses[k] >= 2 or k in scalar_pool:
        emit k·P by one multiplication;  remove k          # stored-multiplier case
    loop on the rest with the SMALL_SET scheme, where one operation means:
        l1 + l2,  l1 - l2,  s·l  (s in scalar_pool),  l / s exact
        and a helper may be a lifted value or one new scalar
    return steps

function TWO_LEVEL_FORMS(t, h, pool):
    for delta in -2..2:
        K = round(t / h) + delta;  rho = t - K·h
        for k2 in divisors(K) with k2 > 1:
            r2 = centred residue of rho mod k2;  r1 = (rho - r2) / k2;  k1 = K / k2
            if |r1| < h and price(k1) + price(k2) + price(r1) + price(r2) < incumbent cost of t:
                yield form (k1·h + r1)·k2 + r2
```

**Expected benefit.** From the simulations: up to 0.4–0.55 instructions per scalar from joint ordering and up to 0.6 per target from lifting single-use multipliers, both against crude baselines and both shrinking to almost nothing when scalars are below about 2^9 or heavily repeated. A cautious expectation is a few instructions per structured puzzle on top of the 8–11 already obtained from seeds, concentrated in puzzles whose scalars are 10–16 bits; it must be measured on about 50 puzzles before committing.

**Reasons it might not transfer.** (1) Our measured 2.86 per target is already below the simulated stored-multiplier cost at 6 bits, which suggests the real scalars are small and shared, the regime with the least headroom. (2) Every public pairwise structure rewrite saved 0–1 per puzzle on strong parents. (3) The value-graph local search may already find the same sharings after seeding. (4) Hub build cost is untouched by this design and may dominate. (5) Forty-eight registers: a large stored scalar set plus lifted values can exceed the limit unless lanes are scheduled one after another.

### Gaps
- All benefit numbers are from synthetic uniform data with a simple greedy; none is measured on competition puzzles.
- Needed before implementation: per-puzzle counts of distinct multipliers and offsets and their bit sizes, how often a multiplier recurs across hub products, and a cost breakdown of current programs into hubs, products, scalars and glue.
