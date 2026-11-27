# Santa 2026 – The Elf Calculator: competition rules and public developments, 2026-11-21 to 2026-11-24

All reading was done on 2026-11-24 between about 16:10 and 16:45 local time. Scores are total instructions, lower is better. BJT is Beijing time (UTC+8), as written in the source. Kaggle authors are identified by account handle or by notebook title, not by personal name.

Read-level tags used on every finding:

- **[page]** the page itself was read
- **[archive]** an archived copy was read
- **[quote-elsewhere]** a verbatim quotation of the page in another document
- **[analogue]** a different competition's rules or a general template, never this competition's rules
- **[search-summary]** a search engine's summary or result title; the page was not read
- **[file-full]** / **[file-part]** a public GitHub file read in full / in part
- **[fetch-summary]** a page read through a summarising fetch tool, not verbatim

Access summary. The competition Rules page returned only its title to the fetch tool. One Wayback Machine capture of the Rules page exists (2026-11-23 01:12:55 UTC); the fetch tool refuses `web.archive.org`, so the raw capture was fetched once from the shell with that host declared, and it is an empty application shell with no rules text. The fetch tool also refuses `archive.ph`; that was not pursued. No Kaggle API was queried, nothing was logged in to, no credentials on this machine were used, and no solution or program file was downloaded (only Markdown logs and JSON provenance manifests that hold hashes and attributions). GitHub's core API was rate-limited, so commit history was read from the GitHub web page instead.

## 1. What the Santa 2026 rules say (external data and tools, public and private sharing, winner licences, automated tools and LLMs, submissions per day, team size, starting from others' public submissions)

### Takeaway

The text of the Santa 2026 rules was not obtained at any read-level: not from the page, not from an archive, and not from a verbatim quotation. Nothing below is a statement of the rules; the only material found is what participants publicly do and what licences they attach to what they publish.

### Cited Findings

**The rules page itself**

- 2026-11-24: the Rules page returns only the title "Santa 2026 - The Elf Calculator | Kaggle" to the fetch tool; no rules text. [page, title only] — [Kaggle Rules page](https://www.kaggle.com/competitions/santa-2026/rules)
- No search result quotes the rules of this competition. The search engine's own summary states that it found nothing identifying this competition's rules. [search-summary] — [Kaggle Rules page](https://www.kaggle.com/competitions/santa-2026/rules)

**What participants publish about licences and reuse (participant statements, not rules)**

- The merged public dataset by `asteriospanoras` (versions 196 and 370) and the `goodpjw2008` dataset (version 239) are recorded with licence "Apache 2.0" in a third party's provenance manifests. The entry for version 373 of the merged dataset and the entry for the `ozertuu` notebook run carry no licence field. [file-full] — [manifest at 128,491](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/releases/portfolio.json); [manifest at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.json); [manifest at 132,477](https://raw.githubusercontent.com/Hansen0223/Santa_2026/5b76ad0/public-assisted/releases/portfolio.json)
- The attribution notice of that dataset, as copied by the third party: "The programs are public work released under the Apache License 2.0, re-verified here; `source` names the origin of each one". [quote-elsewhere, of a dataset description, not of the rules] — [Hansen0223 public-assisted NOTICE](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/NOTICE.md)
- The `pardheev` dataset "santa-2026-elf-calculator-132997" (version 1) marks its terms as "Other (specified in description)", and its publisher says the data may be used directly to enter the competition or as a starting point for further search. This is a third party's report in Chinese of the dataset page, not a reading of the page. [file-full, reported] — [Hansen0223 pardheev README](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/pardheev/README.md)
- The `ishankarnick` dataset "santa-2026-frontier-programs" version 18 (retrieved 2026-11-22) declares Apache-2.0 for its own work, while "the embedded Alex Chilton Rudolph programs retain CC0-1.0". [file-full] — [yobi369 THIRD_PARTY.md](https://raw.githubusercontent.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/HEAD/THIRD_PARTY.md)
- One public portfolio (`kindasomethin`, "exact portfolio checkpoints" version 23) "documents mixed upstream licensing and keeps the original terms for its inputs"; `romanrozen` "invites reuse of the verified IceFire output". [file-full] — [Hansen0223 public-assisted NOTICE](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/NOTICE.md)
- A participant's research note dated 2026-11-21 states that Apache 2.0 was "verified directly" on the owning pages of the `atakanaldemir` notebook "Joint Recipes for Large Puzzles" (V26) and the `josecoronel` notebook "everything I tried and learned" (V1), and through "the official API and its owning page" for `goodpjw2008` dataset versions 49 and 55. [file-part] — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)
- Two repositories say explicitly that the rules still have to be checked before they choose a licence or publish: "Before publication or prize submission, the current official competition rules and applicable licensing requirements must be checked" and "To be selected after reviewing the competition rules and any third-party solver code used". Neither quotes the rules. [file-part] — [Ambetazam README](https://raw.githubusercontent.com/Ambetazam/santa-cloud/HEAD/README.md); [yobi369 README](https://raw.githubusercontent.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/HEAD/README.md)

**Public practice with LLMs and automated pipelines (practice, not permission)**

- A public Kaggle notebook titled "Santa 2026: Claude Coding | LB: 128524" (`wilan`) is credited as the source of 531 programs in the merged public dataset version 370; other credited notebook titles are "Bah Humbug! Agents not Working" (`jazivxt`) and "Sorry for my leakage!!! It's all my AI's fault!" (`tkm2261`). Only the titles were read. [file-full, titles as credited in a manifest] — [manifest at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.json)
- A public pipeline "runs daily on GitHub Actions and uses Codex to investigate how to reproduce public Kaggle Santa 2026 solutions"; "each successful run submits once". [file-part] — [t-kabaya README](https://raw.githubusercontent.com/t-kabaya/santa-2026-codex-pipeline/HEAD/README.md)
- Another public repository retains "the latest AI-generated optimizer" and feeds it back as "an untrusted parent for the next model-generated mutation", and reports previous score 128,504 and new score 128,504. [file-part] — [hp87689 README](https://raw.githubusercontent.com/hp87689/santa_swarm_v1/HEAD/README.md)
- The open collaboration repository lists "Codex" as the worker on several of its tasks in its status table. [file-part] — [Hansen0223 STATUS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/STATUS.md)

**Submissions and teams (indirect evidence only)**

- A public guide notebook "submits itself, one submission per version" and moved from version 217 to version 218 within minutes on 2026-11-20; this shows frequent submission by one account but states no limit. [file-part] — [kaggle-portfolio santa-2026 README](https://raw.githubusercontent.com/AsteriosPanoras/kaggle-portfolio/HEAD/competitions/santa-2026/README.md)
- A search summary of the discussion board mentions posts recruiting teammates and a post described as "Team merge: ~132.07k"; no rule text on team size is shown. [search-summary] — [Kaggle discussion listing](https://www.kaggle.com/competitions/santa-2026/discussion)
- Dates supplied by a participant from a paste of the Overview: start 2026-11-18, entry and team-merger deadline 2027-01-21, final submission 2027-01-28, "Deadlines are 23:59 UTC unless updated by the organizers". The same file says it holds the overview and evaluation text, not the rules. [quote-elsewhere, Overview paraphrase] — [halchemylab docs/competition.md](https://raw.githubusercontent.com/halchemylab/kaggle-santa-2026-elf-calculator/HEAD/docs/competition.md)

**A repository that describes itself as private**

- `radjapov/santa2026` is publicly reachable but its README opens by describing it as the team's private working repository. It was not read further and nothing from it is used here. Disclosure: a batch script printed the top of that README before the (Russian-language) marker was recognised. [existence only] — [radjapov/santa2026](https://github.com/radjapov/santa2026)

### Inferences

- (Inference) Starting from public programs is at least widespread and open: per-puzzle merges of other authors' programs are published as Kaggle datasets with per-row credits, labelled Apache 2.0, and several publishers invite reuse. That shows what participants believe is allowed; it is not evidence of what the rules say, and the user's decision should rest on the Rules page.
- (Inference) LLM-driven solver development is being done in public view, in a notebook whose title names the model, and that notebook's programs were absorbed into the main public dataset within about two days. No sign of removal was seen, and no sign of host approval either. Again this is practice, not a rule.
- (Inference) Licences in the public pool are mixed (Apache-2.0, CC0-1.0, "Other (specified in description)", and portfolios that keep "original terms"). If the rules impose a licence on winning solutions, a submission built on the public pool inherits all of these; the per-row source column in the public datasets is what makes that traceable.

### Gaps

- The rules on external data and tools, private versus public sharing, winner licence, automated tools and LLMs, submissions per day, team size, and any rule on building on other participants' public submissions: **not read at any level**. Each point remains open.
- The most reliable way to close this is for the user to open the Rules tab while signed in. An earlier report notes that a Kaggle CLI is configured in this project; it was deliberately not used here because the task forbids using credentials found on the machine.
- Whether the Data page or Overview repeats any of these points was not checked; neither page could be read.

## 2. Archived copies, mirrors and analogues (Santa 2025, Santa 2024, Kaggle's general terms)

### Takeaway

One archived capture of the Santa 2026 Rules page exists, but it contains only the empty application shell; no mirror or verbatim quotation was found, and the rules of Santa 2025 and Santa 2024 were not obtained either. The analogue evidence is limited to one search-result heading from a 2016 Kaggle competition.

### Cited Findings

- The Wayback Machine availability service reports one capture of the Rules page, status 200, timestamp 20261123011255 (2026-11-23 01:12:55 UTC). [page, API response via fetch tool] — [Wayback availability query](https://archive.org/wayback/available?url=kaggle.com/competitions/santa-2026/rules)
- The raw capture is 5,791 bytes of HTML after decompression: page title, the meta description "Write arithmetic programs to build large target numbers from small starting values in the fewest steps", Open Graph tags, script tags, and an empty `<div id="root">`. It contains no rules text. The Open Graph image URL carries the competition number 177055. [archive, read in full] — [Wayback capture](http://web.archive.org/web/20261123011255/https://www.kaggle.com/competitions/santa-2026/rules)
- GitHub repository search (README text) on 2026-11-24: 0 repositories for `"santa 2026" "private sharing"`, 0 for `"elf calculator" "external data"`, 6 for `"elf calculator" "competition rules"`. None of the six quotes the rules; they link to the Rules page or say the rules must be followed. [file-full, search API] — [GitHub search: private sharing](https://api.github.com/search/repositories?q=%22santa+2026%22+%22private+sharing%22+in:readme); [GitHub search: competition rules](https://api.github.com/search/repositories?q=%22elf+calculator%22+%22competition+rules%22+in:readme)
- One repository's README lists a file `docs/competition-rules.md` in its planned layout; the file returns HTTP 404. [file-part] — [Ambetazam README](https://raw.githubusercontent.com/Ambetazam/santa-cloud/HEAD/README.md)
- One repository's "Competition rules incorporated" section and another's "README that explains every rule" cover the calculator's rules only (operators, positivity, exact division, value limit, register count), not the participation rules. [file-part] — [Joe-You-Know README](https://raw.githubusercontent.com/Joe-You-Know/PRTA-Elf-Calculator/HEAD/README.md); [Chih-Kai-Wang verifier README](https://raw.githubusercontent.com/Chih-Kai-Wang/santa-2026-submission-verifier/HEAD/README.md)
- **Analogue, not this competition:** a search-result summary of the rules page of a 2016 Kaggle competition gives the heading "No private sharing outside teams" and summarises that code may be shared if made available to all participants on the forums. The page was not read, and it is ten years older than this competition. [analogue, search-summary] — [2016 Kaggle competition rules page](https://kaggle.com/c/bnp-paribas-cardif-claims-management/rules)
- **Analogue, not this competition:** a search-result summary of Kaggle's site terms says a user may not run more than one active account. The page was not read. [analogue, search-summary] — [Kaggle terms](https://kaggle.com/terms)

### Inferences

- (Inference) Kaggle pages are rendered in the browser, so web archives that store the raw response capture only the shell. Captures of the Santa 2025 and Santa 2024 Rules pages would almost certainly be empty in the same way, which is why none was fetched.
- (Inference) An archive that stores the rendered page (the kind `archive.ph` keeps) could hold the text, but it is unreachable from this environment.

### Gaps

- Santa 2025 and Santa 2024 rules: not read, not quoted anywhere found. No statement about them is made here.
- Kaggle's general competition terms: not read beyond the single search summary above.
- From model memory only, unverified and not read in this session, and **not to be taken as the rules of this competition**: recent Kaggle rule pages usually open with competition-specific terms (team size, daily submission limit, number of final submissions, winner licence type) and then carry general sections titled along the lines of "External Data and Tools" (including a clause on automated machine learning tools), "Private Sharing" and "Public Sharing" of competition code, and "Winners' Obligations". These are the headings to look for when the user opens the page; the numbers and wording for Santa 2026 are unknown.

## 3. Host statements in discussion threads about sharing solution files publicly

### Takeaway

No host statement was found. Discussion thread bodies could not be read; only thread titles and a search summary are available, and the summary says no host reply was visible.

### Cited Findings

- A search summary of the discussion board lists a thread with a cautionary tone, "A word of caution before you team up", and a thread asking whether there are plans to keep the competition fair; "neither excerpt shows the thread contents or any host response". [search-summary] — [Kaggle discussion listing](https://www.kaggle.com/competitions/santa-2026/discussion)
- The competition's citation line, as pasted by one participant, names two authors; no statement by either was found in any source read. [quote-elsewhere, citation line] — [halchemylab docs/competition.md](https://raw.githubusercontent.com/halchemylab/kaggle-santa-2026-elf-calculator/HEAD/docs/competition.md)
- A public notebook is titled "Sorry for my leakage!!! It's all my AI's fault!" (`tkm2261`); its programs were taken up by the merged public dataset version 370 on 55 puzzles. The notebook body, any discussion around it and any host reaction were not read. [file-full, title as credited in a manifest] — [manifest at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.json)

### Inferences

- (Inference) The "leakage" title suggests an unintended publication of programs by an automated agent, followed by a public apology. If so, it is the one place where the hosts would have had reason to comment on sharing during 11-22 to 11-24. This reading rests on the title alone.

### Gaps

- Whether the hosts have posted anything on public sharing of solution files, on LLM agents, or on the fairness thread is unknown. Thread bodies are unreadable from here.
- The author, date and content of the fairness thread and of "A word of caution before you team up" are unknown.

## 4. What entered the public pool between 2026-11-21 and 2026-11-24, and what explains the fall from 132,477 to 128,501

### Takeaway

The fall of 3,976 is explained: it comes entirely from version 370 of the merged public dataset (`asteriospanoras`), which by itself replays at 128,501, and 75% of the saving (2,983 instructions on 531 puzzles) is credited to one public notebook, "Santa 2026: Claude Coding | LB: 128524" by `wilan`. No public source claims a score below 128,000; the lowest public figure is 128,491.

### Cited Findings

**The step from 132,477 to 128,501**

- At 132,477 (2026-11-21 21:18 BJT) the rebuilt candidate used the tracking repository's own file, merged public dataset version 196 (which replays at 132,584 by itself) and one notebook run. [file-full] — [manifest at 132,477](https://raw.githubusercontent.com/Hansen0223/Santa_2026/5b76ad0/public-assisted/releases/portfolio.json); [portfolio note at 132,477](https://raw.githubusercontent.com/Hansen0223/Santa_2026/5b76ad0/public-assisted/releases/portfolio.md)
- The tracking repository has no log entry and no commit to its portfolio file on 11-22 or 11-23. Its next entry is 2026-11-24 10:12 BJT (02:12 UTC): "700 puzzles save 3,976 in total, the combined candidate falls to 128,501". [file-full; fetch-summary for the commit list] — [Hansen0223 PROGRESS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/PROGRESS.md); [commit history of portfolio.md](https://github.com/Hansen0223/Santa_2026/commits/main/public-assisted/releases/portfolio.md)
- At 128,501 the only external input is merged public dataset version 370 (`best_programs.csv`, licence recorded as Apache 2.0), which replays at exactly 128,501. All 700 improved puzzles are taken from it. [file-full] — [manifest at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.json)
- Credits for the 700 improved puzzles, tallied from that manifest (the credit strings are the dataset's own per-row source labels):

  | Credited source (notebook title, handle) | Puzzles | Instructions saved | Share |
  | --- | --- | --- | --- |
  | "Santa 2026: Claude Coding \| LB: 128524" (`wilan`) | 531 | 2,983 | 75.0% |
  | "Sorry for my leakage!!! It's all my AI's fault!" (`tkm2261`) | 55 | 394 | 9.9% |
  | "Santa 2026 \| Starter Notebook!" (`ozertuu`) | 21 | 85 | 2.1% |
  | "Bah Humbug! Agents not Working" (`jazivxt`) | 5 | 41 | 1.0% |
  | All others (more than 36 distinct labels) | 88 | 473 | 11.9% |

  [file-full, tallied locally] — [manifest at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.json)
- The remaining labels are notebooks whose titles carry their own scores: `ishankarnick` "Frontier Programs" at 132,318, 132,220, 131,053, 130,187, 130,131 and 128,507; `goodpjw2008` "Source-Aware Frontier" from LB 132,207 down to LB 130,892 and "Fresh-Program Re-Search" from LB 130,201 and 130,132 down to LB 128,522 … 128,502; `pardheev` "Best Public Score" from 132,474 down to 130,844; "Deep Cone Rebuilds | 131,020"; "Fresh-Program Re-Search, Explained"; "Every Value, Zero Savings (and Why)"; "Santa 2026 Verified Merge 128521"; and "public merge". [file-full] — [manifest at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.json)
- Shape of the saving: median 4 instructions per improved puzzle, maximum 25; 348 puzzles saved 5 or more, 113 saved 10 or more, 99 saved exactly 1. By previous program length: 250 puzzles of 180 or more instructions saved 1,892; 218 puzzles of 120–179 saved 1,247; 225 puzzles of 60–119 saved 823; 7 puzzles under 60 saved 14. [file-full, tallied locally] — [manifest at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.json)
- Largest single improvements listed: puzzle 182 from 143 to 118 (`ishankarnick`, "Frontier Programs | 130,131"); puzzle 932 from 226 to 203, puzzle 174 from 138 to 117, puzzle 759 from 196 to 175 and puzzle 819 from 225 to 204 (all `wilan`); puzzle 203 from 214 to 194 and puzzle 208 from 226 to 207 (`tkm2261`). [file-full] — [portfolio note at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.md)

**Intermediate public checkpoints, 11-21 to 11-22**

- 2026-11-21 about 15:00 UTC: `goodpjw2008` dataset version 55 replays at 132,516; a participant's merge with one private row gave 132,515, "accepted by Kaggle as submission 58675401". [file-part] — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md); [yobi369 README](https://raw.githubusercontent.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/HEAD/README.md)
- 2026-11-22: merging `ishankarnick` dataset version 18 with that 132,515 file gives 131,052. Of the 360 rows taken from version 18, the dataset's source table records 224 as "Ishan graph-search/solver programs", 125 as Rudolph programs (`alexchilton`) and 11 as `goodpjw2008` DAG-LNS programs. [file-full] — [yobi369 THIRD_PARTY.md](https://raw.githubusercontent.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/HEAD/THIRD_PARTY.md)
- 2026-11-22: `goodpjw2008`'s "source-aware v72 frontier" replays at 130,976; merged with a separate full LNS output (131,045) it gives 130,974, with only two rows improved. [file-part] — [yobi369 README](https://raw.githubusercontent.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/HEAD/README.md)
- Release counters between the two dates: merged public dataset version 196 (11-21) to 370 and 373 (11-24); `goodpjw2008` dataset version 41 (11-21 18:53 BJT) to 239 (11-24); Rudolph dataset (`alexchilton`) version 126 on 11-21 20:09 BJT, and an `alexchilton` public candidate numbered 264 on 11-24 (the log does not say which dataset the number belongs to). [file-full] — [Hansen0223 PROGRESS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/PROGRESS.md); [manifest at 128,491](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/releases/portfolio.json)

**After the step, on 2026-11-24**

- 128,500 at 10:54 BJT (one puzzle); 128,494 at 11:18 BJT (six puzzles); 128,492 at 12:03 BJT (two programs from `ozertuu`'s notebook run 373317540, puzzles 106 and 170); 128,491 at 13:21 BJT (puzzle 93, credited to `ozertuu` in merged dataset version 373). [file-full] — [Hansen0223 PROGRESS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/PROGRESS.md)
- Standalone replays of the three inputs to the 128,491 merge: `goodpjw2008` dataset version 239 = 128,494; `ozertuu` notebook run 373317540 = 128,492; merged public dataset version 373 = 128,491. This closes a gap left open in round one. [file-full] — [manifest at 128,491](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/releases/portfolio.json)
- A further public candidate (`alexchilton`, numbered 264) "brought no shorter per-puzzle program", and recombining 21 puzzles from its different formulations shortened nothing (14:32 BJT). A recombination of 553 puzzles from two near-equal public files, plus extra search on the 57 that differed most, left the total at 128,494 (11:40 BJT). [file-full] — [Hansen0223 PROGRESS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/PROGRESS.md)

**Techniques named in the window**

- Named by title only: "Source-Aware Frontier" and "Fresh-Program Re-Search" (`goodpjw2008`), "Frontier Programs" (`ishankarnick`), "Deep Cone Rebuilds", "Claude Coding" (`wilan`). No description of the method inside the `wilan` notebook was found in any source. [file-full, titles] — [manifest at 128,501](https://raw.githubusercontent.com/Hansen0223/Santa_2026/37d94f2/public-assisted/releases/portfolio.json)
- A participant's survey of public methods on 2026-11-21 about 15:00 UTC judged the "strongest new evidence" to be `atakanaldemir`'s "coordinated multiplier packets", followed by multi-target block rebuilding, while noting those comparisons "start from substantially weaker portfolios". The participant's own bounded factor-packet test on a 132,542 portfolio found no improvement: all 1,000 puzzles, 20,345 new-factor families, 11,949 pair-union evaluations, "zero smaller value graphs and zero physical wins". [file-part] — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)
- The same note summarises a public negative-results notebook (`josecoronel`, "everything I tried and learned", V1): fixed-universe CP extraction found no bound below the incumbent on 973 cases; adding helper pairs did not improve a 99-case sample; a hub-swap test found no improving move on ten cases; an accumulated-benefit generator reached 150,463 against a 133,790 portfolio. [file-part, second-hand] — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md)

**Claims below 128,000**

- None found. The lowest public figures are 128,491 (replay of merged dataset version 373) and notebook titles between 128,502 and 128,524. A public LLM-evolution repository starts from "128,504" and reports no improvement. [file-full; file-part] — [manifest at 128,491](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/public-assisted/releases/portfolio.json); [hp87689 README](https://raw.githubusercontent.com/hp87689/santa_swarm_v1/HEAD/README.md)

### Inferences

- (Inference) The public pool moved in two steps, not gradually. Notebook-title scores cluster at about 132.1k, then about 131.0k (coinciding with `ishankarnick`'s graph-search programs on 11-22), then about 130.1k, then about 128.5k (coinciding with the `wilan` notebook at 128,524). `goodpjw2008`'s "Fresh-Program Re-Search" titles jump from 130,132 straight to 128,522, which fits importing those programs and then shaving a few instructions.
- (Inference) Three quarters of the three-day public gain therefore came from one notebook whose programs were about 1,600 better than everything else public, and whose title says it was coded with an LLM. The 55 puzzles credited to the "leakage" notebook average 7.2 instructions saved each, above the 5.6 average for the `wilan` rows, which fits programs from a stronger private pool.
- (Inference) The gain is concentrated where programs are long: puzzles of 120 or more instructions supply 79% of the saving (3,139 of 3,976). The new programs are not marginal polish; half the improved puzzles lost 5 or more instructions.
- (Inference) Since the step, known public recombination and search operators have recovered only 10 instructions in half a day (128,501 to 128,491), so the public pool is again at a plateau until another private result is published.
- (Inference) Against our 140,526, the public floor is now 12,035 lower, and the leader is 2,841 below the public floor (it was 5,277 below on 11-21).

### Gaps

- The `wilan` notebook itself: publication date and time, method, whether it ships solver source or only programs, and its licence were not read. Web search does not index it yet. This is the single most valuable unread public item.
- What the "leakage" notebook is and where its programs came from is unknown beyond the title.
- Exact timing inside the window is known only to the level "after 2026-11-22 (public references near 130.9k) and before 2026-11-24 02:12 UTC".
- No Kaggle notebook, dataset page or discussion thread was read directly; all titles and scores above come through third-party manifests and READMEs.
- The Juan-Severiano note was read in part (opening sections and keyword lines), not in full.

## 5. Leaderboard movement after 2026-11-24 05:15 UTC

### Takeaway

One later mirror snapshot exists, taken at 06:37:04 UTC. First place is unchanged at 125,650; second place improved by 119 to 125,768, and eighth and ninth improved slightly.

### Cited Findings

- Snapshot checked at 2026-11-24T06:37:04Z, top ten: 125,650 / 125,768 / 126,151 / 126,154 / 126,241 / 126,285 / 126,673 / 126,748 / 126,870 / 127,030. [file-full] — [Hansen0223 leaderboard.json](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/leaderboard.json)
- Compared with the 05:15:21Z snapshot recorded in round one (125,650 / 125,887 / 126,151 / 126,154 / 126,241 / 126,285 / 126,673 / 126,754 / 126,956 / 127,030): rank 2 went from 125,887 to 125,768, rank 8 from 126,754 to 126,748, rank 9 from 126,956 to 126,870; the other seven are unchanged. [file-full] — [Hansen0223 leaderboard.json](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/collaboration/leaderboard.json)
- The tracking log gives the gap from the 128,491 public merge to first place as 2,841 at 14:37 BJT (06:37 UTC), which matches 125,650. [file-full] — [Hansen0223 PROGRESS.md](https://raw.githubusercontent.com/Hansen0223/Santa_2026/HEAD/PROGRESS.md)
- Two additional leader readings fill in the earlier timeline: 126,900 on 2026-11-21 at about 15:00 UTC (with 127,069 and 128,300 in second and third), and "near 126,659" on 2026-11-22. [file-part] — [Juan-Severiano public-methods note](https://raw.githubusercontent.com/Juan-Severiano/santa-2026/HEAD/docs/research/2026-11-21-public-methods.md); [yobi369 README](https://raw.githubusercontent.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/HEAD/README.md)

### Inferences

- (Inference) The leader's path is now 130,600 (11-19), 128,330 (11-20), 127,200 then 126,900 (11-21), about 126,659 (11-22), 125,650 (11-24): roughly 400 to 1,000 per day, slowing. The top ten span 1,380.
- (Inference) The second-place move of 119 within 82 minutes shows that teams near the top are still finding three-digit gains in a single update.

### Gaps

- No snapshot later than 06:37 UTC on 2026-11-24 was found. The mirror file is overwritten in place, so earlier snapshots are only available through its git history, which was not read.
- Team count at 06:37 UTC was not extracted. Team names were deliberately not recorded.
- A repository that describes itself as a daily leaderboard watcher (`EAnge1o/kaggle-lb-watch`) was found by search; whether it tracks this competition was not checked.
