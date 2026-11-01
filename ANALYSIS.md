# Assignment 4 — analysis

## Environment and commands

- **Language/runtime:** Python 3.14.3 locally (the launcher requirement is 3.12+; GitHub Actions uses 3.12).
- **Hardware/OS:** Intel Core Ultra 9 275HX, 31.4 GiB RAM, Windows 11 Education.
- **Build:** none, Python is interpreted. Setup check: `python tools/run.py --setup`
- **Run:** `python tools/run.py --input examples/lcs.jsonl`
- **Public checks:** `python tools/run.py --check`
- **Own tests:** `python tests/student/run_tests.py` (saved log: `tests/student/test_log.txt`)
- **Search comparison:** `python tests/student/benchmark.py` (saved output: `tests/student/benchmark_results.md`)

The final commit URL is recorded in Moodle. All numbers below come from actual runs of these commands.

## Algorithm explanations

### lcs

- **State:** `dp[i][j]` is the LCS length of the first `i` characters of `a` and the first `j` characters of `b`.
- **Transition/base:** row 0 and column 0 are 0. If `a[i-1]==b[j-1]`, then `dp[i][j]=dp[i-1][j-1]+1`; otherwise `dp[i][j]=max(dp[i-1][j],dp[i][j-1])`.
- **Order:** rows, then columns increase, so the upper, left and diagonal states are ready.
- **Correctness:** on a match, an optimal solution can be exchanged to pair these two last characters, so taking them is safe. On a mismatch, the two last characters cannot be paired with each other, so at least one is unused, which is exactly the two options of the `max`.
- **Reconstruction/ties:** walk from `(n,m)`. A match appends the character and moves diagonally. Otherwise move to a neighbour with value equal to `dp[i][j]`, preferring `i-1` on ties. Each step preserves the remaining optimum, so the reversed string has optimal length and is a subsequence of both inputs. Any optimum is accepted.
- **Complexity:** O((n+1)(m+1)) time and auxiliary memory (list of integer rows); output O(min(n,m)+1).
- **Boundary test:** `lcs-not-contiguous` (`tea_time`, `team`, expected 4) detects a longest-common-substring implementation that would answer 3.

### merge

- **State:** `dp[l][r]` is the minimum cost to merge original blocks `l..r` into one; `split[l][r]` is the best last split `k`.
- **Transition/base:** `dp[i][i]=0`. For `l<r`, `dp[l][r]=min(dp[l][k]+dp[k+1][r])+sum(l..r)` over `l<=k<r`. The sum comes from prefix sums in O(1).
- **Order:** increasing interval length, so both strictly shorter parts are ready.
- **Correctness:** the last merge of `l..r` joins some `[l,k]` and `[k+1,r]` and always costs the sum of the whole interval. The two parts are independent, so each must be optimal, and all `k` are tried.
- **Reconstruction/ties:** from `(0,n-1)`, a stack generates each merge before its two children; reversing the list puts both child merges before their parent, so every merged block exists when it is used. Ties keep the smallest `k`. For `n>1` the plan has exactly `n-1` merges.
- **Complexity:** O(n³) time, O(n²) auxiliary memory, O(n+1) output; `n<=1` returns immediately in O(1). Python integers hold the costs exactly.
- **Boundary test:** `merge-adjacent-not-greedy` (`[5,100,5]`, expected 215) detects merging the two smallest non-adjacent blocks, which would give 120.

### tree

- **State:** `take[v]`/`skip[v]` is the best weight in the subtree of `v` with `v` selected/not selected. The root is vertex 0; rooting only orders the calculation.
- **Transition/base:** a vertex starts with `take[v]=weights[v]`, `skip[v]=0`. Each child `c` adds `skip[c]` to `take[v]` and `max(take[c],skip[c])` to `skip[v]`.
- **Order:** an explicit stack produces a preorder; its reverse handles each child before its parent. No recursion is used, so a 100000-vertex chain is safe.
- **Correctness:** given the state of `v`, the subtrees of its children are independent. Selecting `v` forbids selecting its children; not selecting `v` leaves each child free. The answer is `max(take[0],skip[0])`, at least 0 because the empty set is allowed.
- **Reconstruction/ties:** in preorder the parent is decided first. A child of a selected vertex must be skipped; otherwise a vertex is selected only if `take[v]>skip[v]`, so a tie and all-negative inputs skip it.
- **Complexity:** O(n+1) time and auxiliary memory using adjacency lists; output O(n+1).
- **Boundary test:** `tree-parent-restricts-child` (`[4,9,6]` on a path, expected 10 with `{0,2}`) detects a greedy heaviest-vertex choice, which gives 9.

### naive

- **Invariant:** before start `i`, all earlier starts have been decided; `j` counts characters matched at start `i`.
- **Update/base:** the empty pattern returns every boundary `0..n`. Otherwise for `i=0..n-m` compare `text[i+j]` with `pattern[j]` for `j=0..m-1`, and report `i` if all `m` match.
- **Order/correctness:** starts are tested in increasing order, each independently, so all starts (including overlaps) are reported in strictly increasing order. `n-m` is the last start where the pattern fits; when `m>n` the range is empty.
- **Complexity:** O(n·m+n+1) time, O(1) auxiliary memory, O(z+1) output.
- **Boundary test:** `naive-last-start` (`abab`, `ab`, expected `[0,2]`) detects an off-by-one that misses the last valid start.

### kmp

- **State:** `pi[i]` is the length of the longest proper prefix of `pattern[0..i]` that is also its suffix. During the search, `matched` is the length of the longest pattern prefix that is a suffix of the text read so far.
- **Update/base:** `pi[0]=0`. On a mismatch, fall back `matched=pi[matched-1]` until the character matches or `matched=0`; then extend on equality. After a full match report `i-m+1` and set `matched=pi[m-1]`, which keeps overlaps. The empty pattern returns `0..n` before any indexing and `m>n` returns `[]`.
- **Order:** `pi` values depend only on smaller indices; the text is read from left to right.
- **Correctness:** the borders of a prefix are exactly the chain `pi[matched-1], pi[pi[matched-1]-1], ...`. Fallback therefore tries every shorter candidate in decreasing order and skips none that could match.
- **Complexity:** `matched` grows by at most 1 per character and each fallback lowers it, so the total is O(n+m+z+1). O(m+1) auxiliary memory, O(z+1) output.
- **Boundary test:** `kmp-overlap-fallback` (`abababa`, `aba`, expected `[0,2,4]`) detects resetting to 0 after a match, which gives `[0,4]`.

### rk

- **Invariant:** before testing start `i`, `window_hash` is `sum(ord(text[i+t])·31^(m-1-t)) mod 101`, with the highest power on the leftmost character.
- **Update/base:** the empty pattern returns `0..n` and `m>n` returns `[]`, both before forming a window. The first hashes use Horner's rule, and `high=31^(m-1) mod 101`. The roll is `((window_hash-ord(text[i])·high)·31+ord(text[i+m])) mod 101`. Python's `%` gives a non-negative result for a positive modulus, so the negative remainder is normalized by the language; a fixture exercises this.
- **Order/correctness:** equal strings always have equal hashes, so no real match is rejected. Equal hashes do not imply equal strings, so each candidate is verified on actual characters and no false position is reported. For example `ab` and `dj` both hash to 75.
- **Complexity:** for `1<=m<=n`, O(n+m+c·m) time, where `c` is the number of equal-hash candidate windows. This can be quadratic, as with `a`-only inputs where every window is a candidate, so linear worst-case time is not claimed. The all-input bound is O(n·m+n+m+1). Rolling needs O(1) state plus an O(m) temporary slice for verification, so O(m+1) auxiliary; O(z+1) output.
- **Boundary test:** `rk-collision-only` (`dj`, `ab`, expected `[]`) detects trusting a hash without verification.

### suffix

**Doubling.**

- **Invariant:** after a round with step `s`, `rank` orders suffixes by their first `2s` characters; equal rank means those prefixes are equal.
- **Update/base:** initial ranks are ASCII codes. Each round sorts by the pair `(rank[i],rank[i+s])`, encoded as one integer, where a suffix that ended gets the smallest second value 0 instead of a sentinel character. Then it reassigns dense ranks.
- **Order/correctness:** comparing the first `2s` characters is the same as comparing two `s`-length parts, whose order is already known. A shorter suffix sorts before a longer one sharing its prefix. The loop stops when all ranks differ. No suffix string is ever created and no sentinel appears in the output.
- **Complexity:** at most ⌈log₂n⌉+1 rounds of Python's comparison sort (Timsort with a precomputed key list), O(n log²(n+1)) time, O(n+1) auxiliary memory.

**Kasai.**

- **Invariant:** if the suffix at `i` has LCP `h` with its predecessor in `sa`, the suffix at `i+1` has LCP at least `h-1` with its own predecessor.
- **Update/base:** `lcp[0]=0`. Process text positions in order, extend `h` by character comparison, store it, then decrement it. Reset `h` to 0 at rank 0.
- **Correctness:** dropping the first character of two suffixes that share `h` characters leaves two suffixes sharing `h-1`, and sorted order makes the adjacent one at least as close.
- **Complexity:** `h` rises at most `2n` times overall, so O(n) time and O(n+1) auxiliary memory.

**Longest repeat.** Any two suffixes share a prefix equal to the minimum LCP between them in sorted order, so the best pair is adjacent and `max(lcp)` is the longest repeat. Ties take the first maximum in `sa` order. Maximum 0 gives `""`, and overlaps are allowed.

**Boundary test:** `suffix-all-equal-overlap` (`aaaa`, expected `sa=[3,2,1,0]`, `lcp=[0,1,2,3]`, `aaa`) detects a sentinel, wrong handling of ended suffixes, or a ban on overlaps.

### aho

- **State:** one state per distinct dictionary prefix. `fail[s]` is the state of the longest proper suffix of `s` that is also in the trie. After reading a text prefix, the current state is its longest suffix present in the trie.
- **Update/base:** insert patterns into a flat 95-column table, `goto[state*95+code]`; duplicates reach the same terminal state, and `terminal[index]` stores it per dictionary position. Root missing edges stay at root.
- **Order:** BFS by depth. A failure state is strictly shallower, so its row is already complete when `s` is handled. A child's failure is `goto[fail[s]][code]`, and a missing edge copies `goto[fail[s]][code]`.
- **Correctness/suffix-pattern counts:** a pattern ends at a text position exactly when its terminal state is on the failure chain of the current state. Each step adds 1 to the current state's `visits`. Then in reverse BFS (deepest first) each state adds its total to its failure state, so every state's total is the number of end positions where it is a suffix. This counts overlaps and suffix patterns, for example `he` inside `she`.
- **Duplicates/reset:** each dictionary position reads the count of its shared terminal state, so duplicates get equal counts. A new `visits` array and state 0 per text keep repeated texts independent. The automaton is built per request, so nothing leaks between requests. An empty dictionary gives an empty row per text; empty `texts` gives `[]`.
- **Complexity:** with total pattern length `L`, dictionary size `p`, and `S` states: construction O(L+95·S+p) time, O(95·S+p) auxiliary memory. Each text takes O(|text|+S+p). Output O(q·(p+1)+1) for `q` texts. No per-match traversal or output lists are used, so dense matches do not slow it.
- **Boundary test:** `aho-duplicates-and-suffix` (`he,she,he` on `sheshe,sheshe,""`, expected `[[2,2,2],[2,2,2],[0,0,0]]`) detects missing suffix counts, lost duplicates and counts carried between texts.

## Own tests

Files: `tests/student/fixtures.jsonl` (33 fixed cases with expected results) and `tests/student/run_tests.py`. All requests pass through the real JSON Lines program. Saved log: `tests/student/test_log.txt`, final line `0 failure(s)`. `python tools/run.py --check` printed PASS for all 44 public cases and for the repeated two-batch state check.

|Command|Input or fixture path|Expected result|Actual result / log|What it checks|
|---|---|---|---|---|
|lcs|`lcs-both-empty`, `lcs-one-empty`|0, `""`|PASS|Empty inputs|
|lcs|`lcs-not-contiguous`|4, `team`|PASS|Subsequence versus substring|
|lcs|`lcs-case-sensitive`|0, `""`|PASS|No case folding|
|lcs|300 random, seed 20261101|Length equals brute force; valid witness|0 wrong|Optimum and alternative witnesses|
|lcs|`a`×1000 and random 1000×1000|1000; valid witness|PASS, 0.14 s and 0.16 s|Scale|
|merge|`merge-empty`, `merge-one`|0, `[]`|PASS|n≤1|
|merge|`merge-all-zero`|0|PASS|Zero sizes|
|merge|`merge-adjacent-not-greedy`|215|PASS|Adjacency versus greedy|
|merge|200 random, seed 20261101|Cost equals all-orders brute force; plan replays to the same cost|0 wrong|Chronological plan, ties|
|merge|n=200, sizes 10⁹|1544·10⁹; valid plan|PASS, 0.18 s|Large total cost|
|tree|`tree-empty`, `tree-single-*`|0 `[]`; 0 `[]`; 5 `[0]`|PASS|0/1 vertices|
|tree|`tree-all-negative`|0, `[]`|PASS|Empty set allowed|
|tree|300 random, seed 20261101|Weight equals subset brute force; independent, no repeats|0 wrong|Optimum, zero/ties, witness|
|tree|Chain and star, n=100000, weights 10⁹|5·10¹³ and 99999·10⁹|PASS, 0.18 s and 0.16 s|No recursion failure; large sum|
|naive|`naive-empty-pattern`|`[0,1,2,3]`|PASS|n+1 boundaries|
|naive|`naive-last-start`, `naive-longer-pattern`|`[0,2]`; `[]`|PASS|Last start; m>n|
|kmp|`kmp-both-empty`|`[0]`|PASS|Empty text and pattern|
|kmp|`kmp-case-punctuation`|`[2,5]`|PASS|Ordinary punctuation, case|
|kmp|`a`×200000 / `a`×100000; near-match|100001 starts; `[100000]`|PASS, 0.10 s each|Scale, overlaps, fallback|
|rk|`rk-collision-not-reported`, `rk-collision-only`|`[0]`; `[]`|PASS|ab/dj collision verification|
|rk|`rk-negative-remainder`|`[1,3]`|PASS|Rolling with subtraction below zero|
|rk|`rk-empty-text`|`[]`|PASS|Empty text|
|rk|`a`×10000 / `a`×2000|8001 starts|PASS, 0.07 s|Every window is a candidate|
|naive, kmp, rk|500 random each, seed 20261101|Same as `str.startswith` oracle at all starts|0 wrong|Identical outputs over the contract|
|suffix|`suffix-empty`, `suffix-one-char`|Empty; `[0]`, `[0]`, `""`|PASS|Small sizes, no sentinel|
|suffix|`suffix-all-distinct`|`""`|PASS|No repeat|
|suffix|`suffix-banana-no-sentinel`|Published result|PASS|Order and overlap|
|suffix|300 random, seed 20261101|`sa`, `lcp` equal to direct sort; repeat length equal to brute force|0 wrong|Independent small check, ties|
|suffix|n=50000: all equal, periodic, random|Correct `sa`/`lcp`/length|PASS, 0.23 s, 0.23 s, 0.14 s|Worst round count; scale|
|aho|`aho-empty-dictionary`, `aho-empty-texts`|`[[],[]]`; `[]`|PASS|Empty rows|
|aho|`aho-overlaps`, `aho-prefix-pattern`|`[[3,4]]`; `[[2,2,2,2]]`|PASS|Overlaps, suffix chain|
|aho|300 random, seed 20261101|Equal to per-pattern direct count|0 wrong|Duplicates, empties, independent texts|
|aho|Chain patterns on `a`×200000; 100000 states with 100 texts; 10000 duplicates|Exact counts|PASS, 0.09 s, 1.62 s, 0.10 s|Dense matches, largest automaton|
|mixed|`aho`, `lcs`, `aho`, `suffix` in one process|Repeated request gives the same answer|PASS|Stale state|

The oracles do not import the implementation. The stress times are for one process on the machine above, including interpreter start and JSON, and are not official grading times.

## Search comparison

**Method.** Generator: `tests/student/benchmark.py`, `random.Random(20261101)`.

- `random`: uniform lowercase text; the pattern is a substring of it at a random start.
- `repetitive`: text `a`×n, pattern `a`×(m−1)+`b` (no match).
- `repetitive-match`: text `a`×n, pattern `a`×m (all windows match).

Before timing, each output is compared with an independent `str.startswith` oracle ("yes" below). **Timing scope:** only the algorithm call inside one process, using `time.perf_counter`; JSON and process start are excluded. **Warm-up:** one unmeasured call per combination. Python 3.14.3 has no JIT enabled here, and there is no compilation step. Each combination has three measured runs. **Unit:** milliseconds.

|Case|n|m|Seed/generator|Algorithm|Run 1|Run 2|Run 3|Median|Correct outputs checked|
|---|---:|---:|---|---|---:|---:|---:|---:|---|
|random|500|50|20261101/benchmark.py|naive|0.038|0.037|0.037|0.037|yes (z=1)|
|random|500|50|20261101/benchmark.py|kmp|0.043|0.037|0.037|0.037|yes (z=1)|
|random|500|50|20261101/benchmark.py|rk|0.087|0.087|0.098|0.087|yes (z=1)|
|repetitive|500|50|20261101/benchmark.py|naive|1.258|1.254|1.249|1.254|yes (z=0)|
|repetitive|500|50|20261101/benchmark.py|kmp|0.072|0.072|0.071|0.072|yes (z=0)|
|repetitive|500|50|20261101/benchmark.py|rk|0.085|0.089|0.086|0.086|yes (z=0)|
|repetitive-match|500|50|20261101/benchmark.py|naive|1.305|1.309|1.300|1.305|yes (z=451)|
|repetitive-match|500|50|20261101/benchmark.py|kmp|0.075|0.079|0.074|0.075|yes (z=451)|
|repetitive-match|500|50|20261101/benchmark.py|rk|0.133|0.134|0.130|0.133|yes (z=451)|
|random|1500|150|20261101/benchmark.py|naive|0.115|0.111|0.110|0.111|yes (z=1)|
|random|1500|150|20261101/benchmark.py|kmp|0.106|0.106|0.105|0.106|yes (z=1)|
|random|1500|150|20261101/benchmark.py|rk|0.289|0.283|0.295|0.289|yes (z=1)|
|repetitive|1500|150|20261101/benchmark.py|naive|11.862|12.326|12.080|12.080|yes (z=0)|
|repetitive|1500|150|20261101/benchmark.py|kmp|0.222|0.220|0.223|0.222|yes (z=0)|
|repetitive|1500|150|20261101/benchmark.py|rk|0.283|0.276|0.279|0.279|yes (z=0)|
|repetitive-match|1500|150|20261101/benchmark.py|naive|11.424|11.705|11.712|11.705|yes (z=1351)|
|repetitive-match|1500|150|20261101/benchmark.py|kmp|0.233|0.237|0.230|0.233|yes (z=1351)|
|repetitive-match|1500|150|20261101/benchmark.py|rk|0.410|0.411|0.397|0.410|yes (z=1351)|
|random|3000|300|20261101/benchmark.py|naive|0.236|0.240|0.235|0.236|yes (z=1)|
|random|3000|300|20261101/benchmark.py|kmp|0.216|0.217|0.216|0.216|yes (z=1)|
|random|3000|300|20261101/benchmark.py|rk|0.558|0.555|0.556|0.556|yes (z=1)|
|repetitive|3000|300|20261101/benchmark.py|naive|49.689|47.172|48.455|48.455|yes (z=0)|
|repetitive|3000|300|20261101/benchmark.py|kmp|0.486|0.483|0.477|0.483|yes (z=0)|
|repetitive|3000|300|20261101/benchmark.py|rk|0.530|0.518|0.519|0.519|yes (z=0)|
|repetitive-match|3000|300|20261101/benchmark.py|naive|49.180|49.313|48.659|49.180|yes (z=2701)|
|repetitive-match|3000|300|20261101/benchmark.py|kmp|0.486|0.488|0.511|0.488|yes (z=2701)|
|repetitive-match|3000|300|20261101/benchmark.py|rk|0.891|0.887|0.876|0.887|yes (z=2701)|

**Observations.**

- On random text most naive attempts fail at the first character, so naive and KMP are nearly equal, and naive even looks close to linear. RK is about 2.5 times slower here because it does arithmetic for every window.
- On repetitive inputs naive does about (n−m+1)·m character comparisons. Multiplying both n and m by 2 (1500/150 to 3000/300) raised its median about fourfold, from 12.080 ms to 48.455 ms, while KMP and RK about doubled. This fits the bounds on these inputs but does not prove them: timings describe this machine, runtime and these three sizes.
- `repetitive` versus `repetitive-match` shows the candidate effect on RK: the median at 3000/300 rose from 0.519 ms to 0.887 ms when every window became a candidate.
- **Implementation constant:** RK's verification uses Python slice comparison, which runs in C, while naive compares characters in a Python loop. That makes RK's verification look cheaper than the same number of comparisons in naive, so these constants should not be taken as a comparison of the algorithms themselves. RK with many candidates is still Θ(c·m) in comparisons.

**Modulus 101.** With only 101 possible hash values, unrelated windows collide often (on the order of 1 in 101 for well-mixed text), which makes verification visibly necessary. The collision pair `ab`/`dj` (both hash to 75) is a correctness test in `rk-collision-not-reported` and `rk-collision-only`. This deliberately small modulus is a teaching laboratory and does not describe every production hash implementation, which may use much larger moduli or several hashes to make accidental candidates much rarer.

## Sources and AI assistance

- **Sources:** this repository's specification, contracts, testing guide and algorithm notes; course lectures for weeks 8–10 as referenced there. No external code was copied.
- **AI assistance:** Claude Code (Anthropic, model Claude Opus 5.5) wrote the implementation in `Python/source/algorithms.py`, the tests and benchmark in `tests/student`, and this analysis.
- **Verification:** the public checks, 33 fixed cases, random cases against independent brute-force oracles, and stress cases at the published limits were run, with results in `tests/student/test_log.txt` and `tests/student/benchmark_results.md`.
