# Control layer around the LNS moves: operator selection, acceptance rule, compute allocation

Evidence labels used on every cited finding:
- **[text]**: I read the passage in the source's full text (PDF converted to text locally, or the HTML page).
- **[text, via summary]**: the full page was fetched, but I only saw the fetch tool's extraction of it, not the raw text.
- **[abstract]**: abstract or bibliographic record only.
- **[snippet]**: search-result snippet only. Treat as unverified.

"Our units" conversions use the total of 140,526 nodes: 0.1% is about 140 nodes.

Sources that could not be opened in this run: the Springer pages (login redirect), the HAL page for Fialho et al. (bot protection), one University of Évora PDF (certificate error), and Kaggle discussion pages (not attempted, searches returned no write-ups).

---

## 1. Operator selection: do adaptive weights, bandits or hyper-heuristics help?

### Takeaway
The only meta-analysis found puts the average benefit of the adaptive weight layer in ALNS at 0.14% of the objective, and its authors recommend leaving selection probabilities equal or tuned offline once useless operators have been removed. Which operators are in the set matters far more than how they are chosen online; the adaptive layer earns its place mainly when slow, mostly useless operators are present or when operators are specialised to subsets of instances.

### Cited Findings
- Scope of the meta-analysis: 134 studies identified, 63 eligible, results for 25 ALNS implementations pooled with a random-effects model. **[text]** — [Turkeš, Sörensen & Hvattum, working paper full text](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- Pooled effect of the adaptive layer: 0.14292% improvement in objective value, standard error 0.03738, 95% confidence interval 0.06819 to 0.21764, p = 0.00018. The abstract rounds this to 0.07–0.22%; the companion data paper prints 0.06–0.21%, which is the same interval truncated. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf); [data paper](https://repository.uantwerpen.be/docstore/d:irua:3523); [journal record, EJOR 292(2) 2021](https://econpapers.repec.org/RePEc:eee:ejores:v:292:y:2021:i:2:p:423-442)
- What was compared: ALNS against the same code with the reaction factor set to 0 (weights stay equal), stopped at the same number of iterations. The authors note the non-adaptive variant is cheaper per iteration (no score bookkeeping, no memory of visited solutions), so an equal-time comparison would shrink the adaptive advantage further. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- Spread across studies (rows I read in the forest-plot table): CVRP −0.00%, CMST 0.01%, QAP −0.02%, one study 0.00% (sample size 1,455), one −0.03% (sample size 11,705), others −0.32%, −0.40%, −0.50%. Three outliers: +15.46%, +6.54% and −9.52%. Dropping the three outliers leaves the pooled effect at 0.137%. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- The largest positive outlier is a study with slow, weak operators and a time-aware weight update; with the standard update the adaptive version beat equal probabilities by 10.69%. The authors read this as: adaptiveness matters "if there are less useful heuristics which also take a lot of computation time". In that same study, plain LNS with the single best destroy–repair pair beat every adaptive and non-adaptive variant. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- The +6.54% outlier (10 destroy and 8 repair operators, timetabling with integer penalties): the equal-probability variant restricted to the 4 best repair operators beat ALNS on that same restricted set. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- Offline selection beats online adaptation: in one cited study ALNS was "clearly worse" than a configuration whose operators were chosen offline by irace; where irace had already narrowed the set (10 and 5 operators down to 5 and 4) the adaptive effect was −0.03%. Authors' wording: "adaptiveness cannot effectively compensate for a poor offline selection of heuristics". **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- Significant weight differences do not imply benefit: one study found statistically significant differences among learned weights and an adaptive effect of 0.00%. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- Known failure of the weight dynamics: operators that succeed early gain weight and are then over-selected later when they no longer succeed; selection probabilities "look completely different" in two runs on the same instance; the most-used operators are not the ones with the highest success rate. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- Authors' recommendation: when the instances are known and no operator targets a particular subset, "the adaptive layer will probably not have a major impact" and "the heuristic selection probabilities can be tuned, or even left equal". Cases where they would keep it: an operator that is poor on most instances but important on a subset; too few test instances to know the instance properties. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- No moderator analysis exists: the authors say the number of studies is too small for subgroup analysis or meta-regression on number of operators, reaction factor, scores or stopping criterion. One data point: scoring destroy and repair operators separately instead of in pairs cost 0.23–0.29% in one study. **[text]** — [working paper](https://repository.uantwerpen.be/docman/irua/d9a052/163609.pdf)
- Bandit-based selection with extreme-value credit: the operator's reward is the best fitness improvement seen in a sliding window for that operator, not the average; the dynamic multi-armed bandit is UCB plus a change-detection restart. **[snippet]** — [Fialho et al., PPSN 2008, HAL record](https://hal.archives-ouvertes.fr/inria-00287355v1). The page was blocked; benchmark and effect sizes are not verified.

### Inferences
- Our move set is small (four to eight hand-built moves, each measured separately), which is the "already narrowed down" regime where the meta-analysis finds an effect near zero. The supported action is offline: measure accepted savings per CPU-second for each move, by puzzle family and by score level, drop moves with zero yield, and fix the mix. This is the irace-style selection that beat online adaptation.
- In our units 0.14% is about 197 nodes, roughly four times the 51 nodes of the second pass. It should not be read as 197 extra nodes: the figure is solution quality at a fixed iteration count from scratch. Once passes are repeated to stagnation, faster convergence saves compute, not final score.
- Two of our conditions match the cases where the authors would keep adaptivity. Move costs are very unequal (one bounded search per move against microsecond swaps), and puzzles fall into families where different moves pay. Both are handled without an online layer: credit per CPU-second, and fixed weights per puzzle family.
- A within-run roulette wheel has almost no signal here. A puzzle sees zero or one improving event per run, so weights updated inside a run are noise. If anything is learned, learn it across passes and across puzzles of the same family, because the 1,000 instances are fixed and revisited. That design is not covered by the ALNS literature read here.
- The standard ALNS score also rewards accepted, previously unseen, non-improving solutions. On our plateaus that reward fires constantly and would steer weight towards whichever move produces the most equal-cost changes. Use improvement-only credit (extreme-value style) if any credit is kept.
- The observation that a move saves hundreds at 140,000 and about zero at 130,000 is the non-stationarity the meta-analysis warns about ("past success implies future success might be very wrong"). Weights measured at one score level should be re-measured after each large drop.

### Gaps
- Effect sizes for UCB, Thompson sampling, dynamic bandits and extreme-value credit against a uniform or offline-tuned baseline were not verified; only a search snippet was available.
- No hyper-heuristic survey was read. No source was found that tests operator selection with rewards as sparse as ours (integer gains, most runs with none).
- Reinforcement-learning operator selection for ALNS (for example [DR-ALNS, arXiv 2211.00759](https://arxiv.org/pdf/2211.00759)) appeared in search results but was not read.
- Lead, not checked: Christiaens and Vanden Berghe's single-operator ruin-and-recreate for vehicle routing is usually cited as evidence that one well-designed operator can beat multi-operator ALNS. The outlier study above points the same way.

---

## 2. Acceptance criteria inside LNS

### Takeaway
In the one large controlled comparison, the acceptance rule mattered (more than 0.5 percentage points among sensible rules, more than 2 between best and worst), and a linearly decreasing record-to-record threshold ending at zero was never significantly beaten in three of four test sets while needing one parameter. Late-acceptance hill climbing landed in the middle group, and on an objective with few integer values it loses its mechanism; the "length cap over the best" used by the public engine is a record-to-record rule, which is the family the evidence favours.

### Cited Findings
- Setup: 21 variants of 9 criteria (hill climbing, random walk, late acceptance, threshold accepting, simulated annealing, great deluge, non-linear great deluge, record-to-record travel, and a new "worse accept"), each tuned on six instances per problem, then run for 150,000 iterations with 10 reruns on 104 CMST, 159 CVRP and 136 QAP instances, with a full ALNS and a simple LNS for CVRP. **[text]** — [Santini, Ropke & Hvattum, author PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- Average gap to best known, best rule against late acceptance, strict hill climbing and random walk **[text]** — [same PDF, Table 4](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf):

| Test set | Best rule | Best | Linear record-to-record, end fixed at 0 | Late acceptance | Hill climbing | Random walk |
|---|---|---|---|---|---|---|
| CMST, ALNS | Linear SA | 0.399% | 0.514% | 0.655% | 2.226% | 2.824% |
| CVRP, ALNS | Linear record-to-record (fixed end) | 0.391% | 0.391% | 0.716% | 1.163% | 2.583% |
| CVRP, simple LNS | Linear record-to-record (fixed end) | 0.754% | 0.754% | 1.870% | 2.595% | 3.946% |
| QAP, ALNS | Linear worse accept (fixed end) | 0.136% | 0.164% | 0.504% | 0.666% | 0.370% |

- Ranking in the authors' words: simulated annealing, record-to-record and threshold accepting "performed best"; late acceptance, great deluge, non-linear great deluge and worse accept were "better than HC and RW but worse than SA, RRT, and TA". In three of four test sets no rule was significantly better than one record-to-record version; in the fourth it was beaten only by another record-to-record version. **[text]** — [same PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- Effect size: differences "easily" exceed 0.5 percentage points of average gap even without hill climbing and random walk. **[text]** — [same PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- Recommendation: use SA, threshold accepting or record-to-record; "if time permits, it may pay off to attempt all three, and otherwise, RRT should be preferred"; use a linear schedule ending at zero, which removes one parameter "without sacrificing the solution quality". **[text]** — [same PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- Record-to-record as tested: accept the candidate if its relative gap to the best solution so far (not the current one) is below a threshold that decreases over the run. Tuned starting thresholds for the fixed-end linear version were 5.0% (CMST) and 1.67% (CVRP). **[text]** — [same PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- Late acceptance needed long histories after tuning: 4,166 to 22,500 iterations of a 150,000-iteration run. **[text]** — [same PDF, Tables 2–3](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- Run statistics associated with better results (regression): no long streaks of rejected moves, and a long maximum distance between accepted solutions. **[text]** — [same PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- "Worse accept" (accept an improving candidate, or any candidate with a probability that decays over the run) was introduced for objectives that hold "a few discrete values" where moving to the next better value is rare, with vertex colouring as the example. In this study it was among the best only on QAP, and two of its three variants were near the bottom for the simple LNS on CVRP (2.461% and 2.516%; the third reached 1.270%). None of the three test problems has such an objective. **[text]** — [same PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- Stated limits: the conclusions are expected to hold best for problems close to CVRP, CMST and QAP, and "the relative merit of the move acceptance criteria may also change based on the number of iterations that can be run". **[text]** — [same PDF](https://santini.in/files/papers/santini-ropke-hvattum-2018.pdf)
- Late acceptance, original claim: compared with SA, threshold accepting and great deluge on travelling salesman and exam timetabling, it was better on most instances, especially large ones, and is insensitive to the scale of the objective. **[abstract]** — [Burke & Bykov, EJOR 258(1) 2017, record](https://ideas.repec.org/a/eee/ejores/v258y2017i1p70-78.html)
- A second comparison reports the Metropolis rule and late acceptance "among the choices that obtain the best results", with results depending on the problem. This conflicts with the middle-group placing above. **[abstract]** — [Franzin & Stützle, Artificial Evolution 2017](https://link.springer.com/10.1007/978-3-319-78133-4_2)
- Weakness of late acceptance on repeated values: after a new local optimum "often the same fitness value is stored many times in the array", and once all entries equal the best value no worsening move is accepted, so it behaves as hill climbing. Measured share of hill-climbing-like iterations: about half on TSP, about 10% on QAP. **[text, via summary]** — [Namazi et al., Diversified Late Acceptance Search](https://ar5iv.labs.arxiv.org/html/1806.09328)
- The proposed fix accepts a candidate equal to the current cost or strictly below the maximum of the history, with a history of 5 (TSP) or 10 (QAP) against 50,000 for late acceptance. It was better on 20 of 23 TSP instances (17 significant) and 15 of 24 QAP instances (10 significant). No single percentage is given. Step-counting hill climbing was a baseline in the same tables; its numbers were not extracted. **[text, via summary]** — [same paper](https://ar5iv.labs.arxiv.org/html/1806.09328)

### Inferences
- The public engine's length cap of best + 1, + 2, 0 is record-to-record travel with an integer threshold on a repeating sawtooth. On a 140-node program, +1 and +2 are 0.7% and 1.4%, at or below the low end of the tuned starting thresholds (1.67% and 5%, about +2 to +7 nodes). A cheap test is a larger starting cap (+3 to +5) decreasing to 0 within each epoch, with a return to the best snapshot at the end of the epoch.
- With integer costs the other rules lose their distinguishing features. Threshold accepting is measured against the current solution, so a threshold above 1 allows unbounded upward drift and a threshold of 1 or less is plain plateau hill climbing. Simulated annealing reduces to "accept +1 with probability p, +2 with p squared". Only the bound relative to the best has a natural integer parameter and bounded drift.
- Late acceptance and step-counting hill climbing are a poor fit. On our plateaus the history holds one integer almost all the time, so the rule becomes "accept equal or better", which we already have. It grants a +1 allowance only for a short time after an improvement, the opposite of when it is needed. The tuned history lengths of thousands of iterations are also out of reach when one move is one search.
- Strict hill climbing was the worst or second-worst rule in all four test sets. SA, threshold accepting and record-to-record (while the threshold is positive) accept equal-cost candidates with certainty. Our fixed probability below 1 for equal-cost moves has no counterpart among the rules that performed well, so probability 1 is worth one comparison run.
- Two of the regression findings are checkable in our logs: longest streak of rejected moves, and distance (number of differing values) between accepted programs. If streaks are long and distance is small, the acceptance rule is too tight.
- In our units, 0.5 percentage points is about 700 nodes. That is an upper-end reading: the study ran from scratch on smooth objectives, and our programs are already polished.

### Gaps
- No controlled comparison of acceptance rules on an objective with few integer values and large plateaus was found. "Worse accept" was motivated by that case but not tested on it.
- The equal-cost acceptance probability is not studied in any source read; all sources treat equal-cost moves as always accepted or do not discuss them.
- The original late-acceptance and step-counting papers were not read in full, so the claim of scale independence is abstract-level only.
- Whether a sawtooth cap (the public engine) beats a single linear decrease is untested in the literature read; the source compares linear with exponential decrease only.

---

## 3. Compute allocation across 1,000 instances with a summed score

### Takeaway
No published source was found that tests a time-allocation rule across fixed instances with a summed objective, and the one winners' paper read does not describe one. The nearest formal model is the "rotting" bandit, where an arm's reward only falls as it is pulled; its algorithm ranks arms by averages over recent pulls. With gains as rare as ours, a single puzzle's own history is too thin to drive allocation, so estimates must be pooled by puzzle family and by known gap.

### Cited Findings
- Rotting bandits: each arm's reward can only decrease with the number of times it has been pulled. The FEWA algorithm builds moving averages over windows of increasing length to find arms likely to pay if pulled again, and achieves problem-independent regret of order √(KT) without knowing how arms decay, improving on the earlier K^(1/3)·T^(2/3) bound. **[abstract]** — [Seznec et al., arXiv 1811.11043](https://arxiv.org/abs/1811.11043)
- A fixed-instance geometry contest with 180 instances and per-instance scores: the winning team (best solution on 75 of 180 instances, 14 teams) ran its solvers on "several desktop and laptop computers" plus two laboratory clusters over months, and reports still improving "several of the smallest competition instances" late on. The paper gives no rule for dividing time among instances and no stagnation criterion; local search runs "until a specified time limit is reached". **[text, via summary]** — [Shadoks, CG:SHOP 2024, arXiv 2403.20123](https://arxiv.org/html/2403.20123v3)
- What that paper does document is a choice of starting method by instance class: integer-programming starts were better on small instances and greedy starts followed by local search on large ones ("as the instances grow larger, the situation reverses"); one figure uses 12 independent executions of greedy plus local search. **[text, via summary]** — [same paper](https://arxiv.org/html/2403.20123v3)
- The 2020 edition of the same contest allowed "any computing device, any amount of computing time". **[snippet]** — [CG:SHOP 2020 survey, arXiv 2004.04207](https://arxiv.org/pdf/2004.04207)
- Luby's universal restart sequence, tested as a way to divide a fixed time budget among runs of a local-search solver on travelling salesman and vertex cover instances, "turned out inferior" to 40 short runs followed by continuing the best one. **[text]** (as reported by the follow-up paper) — [Weise, Wu & Wagner, arXiv 1806.08984](https://arxiv.org/pdf/1806.08984)

### Inferences
- Our problem is a rotting bandit with 1,000 arms: pulling a puzzle (spending CPU on it) can only lower its future gain rate. The matching policy is to estimate each arm's current rate from its most recent pulls only, never the lifetime average, and to spend on the highest optimistic estimate. A lifetime average would keep rewarding puzzles for the 2,371-node first pass.
- A single puzzle's record cannot support that estimate. After an exposure t with zero gains, the 95% upper bound on a Poisson rate is 3/t. The second pass averaged 51/150 = 0.34 nodes per puzzle per pass, so a puzzle needs about 3/0.34 ≈ 9 consecutive empty passes before its own history says it is below the fleet average. One or two empty passes are not evidence of stagnation.
- Therefore pool. Estimate gain per CPU-second for groups defined by puzzle family, program length, passes since last gain, and above all the gap between our program and the best known program for that puzzle. That gap averages 12 nodes per puzzle (140,526 against 128,491) and is known per puzzle; it is proof that a shorter program exists, which no allocation model in the literature has. Time proportional to that gap is the natural first prior. Whether public programs may be used directly is a rules question outside this note.
- For sum objectives with diminishing returns, greedy allocation by current marginal gain is the textbook optimum (stated from general knowledge, not checked against a source in this run). Successive halving and Hyperband answer a different question: they find the single best arm and discard the rest, whereas every puzzle counts in our sum. Their useful part is the schedule: short slices for all, then longer slices for the groups that paid.
- Keep a floor. The rotting-bandit analysis assumes rewards only decrease; ours jump back up for a puzzle whenever a new move type or a new starting program appears. After each such change, reset the estimates for the affected puzzles and give every puzzle a short slice again.
- The contest paper suggests where practitioners put the decision: not in a time-allocation rule but in which starting method to use for which instance class.

### Gaps
- No write-up was found that describes how compute was spread across instances for Santa competitions, Al Zimmermann's contests, ICFP contests, AtCoder long contests or ROADEF/EURO challenges. Three searches returned nothing relevant; Kaggle discussion pages were not opened. This is absence of findings in a short search, not evidence that no such write-up exists.
- The Hyperband and successive-halving papers and the Luby and Gomes–Selman papers were not read; Luby appears only through the follow-up paper above.
- Lead, not checked: the "max k-armed bandit" (Cicirello and Smith; Streeter and Smith) models allocation when only the best outcome matters, which fits allocation among starting points for one puzzle better than allocation among puzzles.

---

## 4. Parallel search organisation

### Takeaway
One survey with measured tables shows that sharing an elite pool turned sub-linear speedups from independent runs into roughly linear or better ones (on job-shop scheduling, 5.9 times against 16.9 times on 16 processors), but only in a method that has a recombination step to consume the pool. The same source gives a cheap test for whether independent runs are already as good as they can be: check whether the time to reach a target is exponentially distributed. Nothing verified was found on island migration settings, parallel tempering or diversity filters at equal total compute.

### Cited Findings
- Independent runs: if the time to reach a target value is exponentially distributed, ρ independent processors reach it with probability 1 − e^(−ρt/λ), a linear speedup. With a shifted exponential (minimum time μ) the speedup is approximately linear only while ρ·μ is much smaller than λ. Proposed test: 200 sequential runs, then a quantile plot against the exponential. **[text]** — [Resende & Ribeiro, Parallel GRASP (survey chapter)](https://optimization-online.org/wp-content/uploads/2004/12/1011.pdf)
- Three-index assignment, GRASP with path-relinking, averages of 60 runs, time to a fixed target: independent threads gave average speedups 1.94, 3.95, 7.3 and 12.21 on 2, 4, 8 and 16 processors; cooperative threads sharing an elite pool gave 1.88, 4.24, 8.78 and 17.10. **[text]** — [same chapter, Tables 2–3](https://optimization-online.org/wp-content/uploads/2004/12/1011.pdf)
- Job-shop scheduling, same protocol: independent 1.79, 2.67, 4.15 and 5.91 (efficiency 0.37 at 16 processors; instance mt10 reached only 4.05); cooperative 2.12, 4.54, 9.05 and 16.93 (efficiency 1.06; mt10 reached 16.97). **[text]** — [same chapter, Tables 5–6](https://optimization-online.org/wp-content/uploads/2004/12/1011.pdf)
- With total iterations fixed, the independent strategy shows "a clear degradation in solution quality" as processors are added, because each processor does fewer iterations and its own elite pool gets poorer; the cooperative version is "more robust". Cost noted by the authors: more programming effort. **[text]** — [same chapter](https://optimization-online.org/wp-content/uploads/2004/12/1011.pdf)
- The run time of parallel local search for satisfiability "can be predicted by a model based on order statistics" from the sequential run-time distribution (exponential, shifted exponential or lognormal), checked on hardware with up to 384 cores. **[abstract]** — [arXiv 2403.08790](https://arxiv.org/abs/2403.08790)
- In cooperative parallel local search on QAP, badly chosen cooperation settings can do much worse than independent runs, while well-tuned ones can do significantly better. **[snippet]** — [CPLS papers, for example](https://dspace.uevora.pt/rdpc/bitstream/10174/24749/1/PPSN.pdf). The source page was not opened.

### Inferences
- Our current scheme (independent passes, then merge the per-puzzle best and restart everything from it) is a cooperative scheme with the most elitist migration possible and no diversity. The measured benefit of cooperation came from an elite pool feeding a recombination step. Our counterpart is the crossover move over near-best programs, so the pool should hold several programs per puzzle that differ in their value sets, not only the shortest.
- Without a pool-consuming move, sharing has nothing to act on, and independent runs are the right baseline. The earlier reports' finding that crossover paid only with structurally different parents is the same statement from the other side.
- The exponential test transfers directly, because our natural target is "one node shorter than now". For a sample of puzzles, run the search 50 to 200 times from the same program with different seeds and record the time to the first improvement. If the times look exponential, eight short runs equal one run eight times as long, and seeds versus run length does not matter. If there is a large minimum time before any improvement (table building, warm-up), many short runs waste it each time, so prefer fewer, longer runs. If the tail is heavy, prefer restarts.
- The speedups above are times to reach a target. In a fixed-budget setting like ours they translate into more puzzles improved per CPU-day, not a guaranteed lower final score.

### Gaps
- No verified numbers on island models (migration interval and size), parallel tempering applied to local search, or diversity filtering in elite pools against independent restarts at equal total compute. The questions remain open after this run.
- The cooperative-search evidence is from GRASP with path-relinking on two problems, from a 2004-era survey; no recent replication was read.
- The earlier report noted a public repository with parallel-tempering experiment folders for this competition whose results were not read; that is still the case.

---

## 5. Restart from a different starting solution, or keep polishing the incumbent

### Takeaway
The best-supported recipe is "bet and run": start many runs, give each a small share of the budget, and continue only the best. In the cited tests the configuration of 40 runs at 1% each, then 60% on the best, beat both a single long run and plain restarts in many cases, the simple "continue the current best" rule proved hard to improve on, and the right split still varied by instance and budget from "many short runs" to "one long run".

### Cited Findings
- Expected regimes: a single run is best for small budgets and independent restarts for large budgets; budgets in between fall in neither. **[text]** — [Weise, Wu & Wagner, arXiv 1806.08984](https://arxiv.org/pdf/1806.08984)
- Best earlier configuration (Friedrich, Kötzing and Wagner, on travelling salesman and minimum vertex cover): 40 runs, each with 1% of the total time, then the remaining 60% on the best of them. **[text]** (as reported by the follow-up) — [same paper](https://arxiv.org/pdf/1806.08984); original: [AAAI 2017](https://ojs.aaai.org/index.php/AAAI/article/view/10645), not read
- Continuing after the selection phase helps when total time is short: both even restarts and Luby-scheduled restarts are "beaten significantly and often". The bet-and-run benchmark beats a single run when the total budget is large. **[text]** — [same paper](https://arxiv.org/pdf/1806.08984)
- How often the early leader is the wrong pick, from one million resampled sets of runs on 86 vertex-cover and 113 travelling-salesman data sets (total 100 s, selection phase 40 s): with 40 runs, some other run would have finished better with mean probability 0.23 (vertex cover) and 0.12 (travelling salesman); with 4 runs, 0.11 and 0.03. On the two example instances shown, the probability ranged from 0.01 to 0.93. **[text]** — [same paper, Table 1](https://arxiv.org/pdf/1806.08984)
- For smarter selection (curve extrapolation, small neural predictors) the authors expect an advantage of "a few percent" averaged over instances; continuing the current best is "a very robust basic strategy that performs the best in many situations". Continuing two runs instead of one paid only at the largest budget tested. **[text]** — [same paper](https://arxiv.org/pdf/1806.08984)
- No universal setting: "the best BET-AND-RUN configuration varies depending on total runtime budget t and instance", from "make many short runs" to "just make a single run". **[text]** — [same paper](https://arxiv.org/pdf/1806.08984)
- Starting method matters after local search, by instance class: in the geometry contest paper, integer-programming starts won on small instances and greedy starts won on large ones once local search had been applied to both. **[text, via summary]** — [Shadoks, arXiv 2403.20123](https://arxiv.org/html/2403.20123v3)

### Inferences
- Apply bet-and-run per puzzle across structurally different starting programs (other constructive methods, rebuilt programs within a few nodes of the best, other lineages), not across seeds of the same start. The second pass with a new seed (51 nodes) shows that seed diversity alone is nearly exhausted, while the earlier reports' largest crossover gain came from differently built parents.
- The 40 × 1% then 60% split is a starting point, not a constant: the source itself says the best split depends on instance and budget. With only a handful of distinct starts per puzzle, the 4-run figures apply, where the early leader was wrong only 3–11% of the time.
- The selection signal is weaker for us. After a short slice most starts will tie on an integer length, so "current best" needs a tie-break; distance from the incumbent's value set is the obvious one, since it also serves the crossover pool. Losing starts should stay in the pool, not be discarded.
- A start that is 2 or 3 nodes longer than the incumbent can still be the better bet if its recent gain rate is higher. This is the rotting-bandit view from section 3 applied within one puzzle, and it argues against judging starts by current length alone.
- Restarting from scratch is unlikely to pay at our level: the earlier reports measured about 1% from random restarts of the constructive solver, and every source here that favours restarts does so at budgets where single runs have converged. The supported form of restart is a new start near the incumbent's quality, then local search.

### Gaps
- No source compares "restart from a different constructive method" with "continue the incumbent" under equal compute on a problem like ours; the contest paper only shows that the better starting method differs by instance size.
- The iterated-local-search literature on perturbation against random restart, and Gomes and Selman's heavy-tail restart results, were not read in this run.
- Bet-and-run was tested on problems where a short slice already separates runs by quality; no test on objectives with frequent ties was found.
