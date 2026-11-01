"""Implement algorithm bodies. See docs/guide/CONTRACTS.md; inputs and outputs are dictionaries."""
BASE = 31
MOD = 101
ALPHABET_START = 32
ALPHABET_SIZE = 95


def lcs(request):
    """Compare two versions of a sequence while preserving the order of shared characters."""
    a, b = request['a'], request['b']
    n, m = len(a), len(b)
    # dp[i][j] = LCS length of the first i characters of a and the first j characters of b.
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        previous, current = dp[i - 1], dp[i]
        ca = a[i - 1]
        for j in range(1, m + 1):
            if ca == b[j - 1]:
                current[j] = previous[j - 1] + 1
            elif previous[j] >= current[j - 1]:
                current[j] = previous[j]
            else:
                current[j] = current[j - 1]
    # Walk back from (n, m), moving only to a state that preserves the optimum.
    i, j = n, m
    sequence = []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            sequence.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    sequence.reverse()
    return {'length': dp[n][m], 'sequence': ''.join(sequence)}


def merge(request):
    """Plan the cheapest sequence of adjacent block merges when the original order must be preserved."""
    sizes = request['sizes']
    n = len(sizes)
    if n <= 1:
        return {'cost': 0, 'plan': []}
    prefix = [0] * (n + 1)
    for i, size in enumerate(sizes):
        prefix[i + 1] = prefix[i] + size
    # dp[l][r] = minimum cost to merge blocks l..r; split[l][r] = last split k: [l,k] + [k+1,r].
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length - 1
            row = dp[l]
            best = None
            best_k = l
            for k in range(l, r):
                candidate = row[k] + dp[k + 1][r]
                if best is None or candidate < best:
                    best = candidate
                    best_k = k
            row[r] = best + prefix[r + 1] - prefix[l]
            split[l][r] = best_k
    # Root-right-left preorder reversed gives left-right-root: children precede their parent.
    plan = []
    stack = [(0, n - 1)]
    while stack:
        l, r = stack.pop()
        if l == r:
            continue
        k = split[l][r]
        plan.append([l, k, r])
        stack.append((l, k))
        stack.append((k + 1, r))
    plan.reverse()
    return {'cost': dp[0][n - 1], 'plan': plan}


def tree(request):
    """Choose a maximum-value set when neighbouring vertices are incompatible and conflicts form a tree."""
    n = request['n']
    if n == 0:
        return {'weight': 0, 'selected': []}
    weights = request['weights']
    adjacency = [[] for _ in range(n)]
    for u, v in request['edges']:
        adjacency[u].append(v)
        adjacency[v].append(u)
    # An explicit stack gives a preorder, so deep chains cannot overflow the call stack.
    parent = [-1] * n
    order = []
    stack = [0]
    while stack:
        v = stack.pop()
        order.append(v)
        for u in adjacency[v]:
            if u != parent[v]:
                parent[u] = v
                stack.append(u)
    # take[v] / skip[v] = best weight in the subtree of v with v selected / not selected.
    take = list(weights)
    skip = [0] * n
    for v in reversed(order):
        p = parent[v]
        if p >= 0:
            take[p] += skip[v]
            skip[p] += max(take[v], skip[v])
    # Preorder visits a parent first, so its decision is known when a child is decided.
    chosen = [False] * n
    selected = []
    for v in order:
        p = parent[v]
        if (p < 0 or not chosen[p]) and take[v] > skip[v]:
            chosen[v] = True
            selected.append(v)
    return {'weight': max(take[0], skip[0]), 'selected': selected}


def naive(request):
    """Establish a simple exact-search baseline against which the other two searches can be checked."""
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    if m == 0:
        return {'positions': list(range(n + 1))}
    positions = []
    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pattern[j]:
            j += 1
        if j == m:
            positions.append(i)
    return {'positions': positions}


def kmp(request):
    """Reuse information about matched prefixes to avoid restarting the search after every mismatch."""
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    if m == 0:
        return {'positions': list(range(n + 1))}
    if m > n:
        return {'positions': []}
    # pi[i] = length of the longest proper prefix of pattern[0..i] that is also its suffix.
    pi = [0] * m
    matched = 0
    for i in range(1, m):
        c = pattern[i]
        while matched > 0 and pattern[matched] != c:
            matched = pi[matched - 1]
        if pattern[matched] == c:
            matched += 1
        pi[i] = matched
    positions = []
    matched = 0
    for i in range(n):
        c = text[i]
        while matched > 0 and pattern[matched] != c:
            matched = pi[matched - 1]
        if pattern[matched] == c:
            matched += 1
        if matched == m:
            positions.append(i - m + 1)
            matched = pi[m - 1]
    return {'positions': positions}


def rk(request):
    """Reject windows with unequal fingerprints and verify every equal-hash candidate."""
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    if m == 0:
        return {'positions': list(range(n + 1))}
    if m > n:
        return {'positions': []}
    pattern_hash = 0
    window_hash = 0
    high = 1  # BASE^(m-1) mod MOD: the weight of the leftmost window character.
    for i in range(m):
        pattern_hash = (pattern_hash * BASE + ord(pattern[i])) % MOD
        window_hash = (window_hash * BASE + ord(text[i])) % MOD
        if i > 0:
            high = high * BASE % MOD
    positions = []
    for i in range(n - m + 1):
        # Equal hashes are only candidates: the slice comparison checks the real characters.
        if window_hash == pattern_hash and text[i:i + m] == pattern:
            positions.append(i)
        if i < n - m:
            # Python % already returns a non-negative remainder for a positive modulus.
            window_hash = ((window_hash - ord(text[i]) * high) * BASE + ord(text[i + m])) % MOD
    return {'positions': positions}


def suffix(request):
    """Order the text suffixes and use adjacent common prefixes to find repeated substrings."""
    text = request['text']
    n = len(text)
    if n == 0:
        return {'sa': [], 'lcp': [], 'repeated': ''}
    # Prefix doubling: after a round, rank orders suffixes by their first 2*step characters.
    rank = [ord(c) for c in text]
    sa = list(range(n))
    scale = max(n, 127) + 2
    step = 1
    while True:
        # A combined integer key encodes the pair (rank[i], rank[i+step]); -1 becomes 0 for "past the end".
        keys = [rank[i] * scale + (rank[i + step] + 1 if i + step < n else 0) for i in range(n)]
        sa.sort(key=keys.__getitem__)
        rank[sa[0]] = 0
        distinct = 0
        for index in range(1, n):
            if keys[sa[index]] != keys[sa[index - 1]]:
                distinct += 1
            rank[sa[index]] = distinct
        if distinct == n - 1 or step >= n:
            break
        step *= 2
    # Kasai: moving to the next text position loses at most one matched character.
    lcp = [0] * n
    position = [0] * n
    for index, start in enumerate(sa):
        position[start] = index
    h = 0
    for i in range(n):
        index = position[i]
        if index > 0:
            j = sa[index - 1]
            while i + h < n and j + h < n and text[i + h] == text[j + h]:
                h += 1
            lcp[index] = h
            if h > 0:
                h -= 1
        else:
            h = 0
    best = max(lcp)
    best_index = lcp.index(best)
    repeated = text[sa[best_index]:sa[best_index] + best] if best > 0 else ''
    return {'sa': sa, 'lcp': lcp, 'repeated': repeated}


def aho(request):
    """Build one dictionary automaton and count its patterns in several independent texts."""
    patterns, texts = request['patterns'], request['texts']
    # Flat transition table: goto[state * ALPHABET_SIZE + code]; 0 in the trie phase means "no child".
    goto = [0] * ALPHABET_SIZE
    states = 1
    terminal = [0] * len(patterns)  # Duplicates share one terminal state.
    for index, pattern in enumerate(patterns):
        state = 0
        for c in pattern:
            slot = state * ALPHABET_SIZE + ord(c) - ALPHABET_START
            following = goto[slot]
            if following == 0:
                following = states
                states += 1
                goto[slot] = following
                goto.extend([0] * ALPHABET_SIZE)
            state = following
        terminal[index] = state
    # BFS sets failure links shallow-first and completes missing edges into a full automaton.
    fail = [0] * states
    bfs = []
    for slot in range(ALPHABET_SIZE):
        if goto[slot]:
            bfs.append(goto[slot])
    head = 0
    while head < len(bfs):
        state = bfs[head]
        head += 1
        base = state * ALPHABET_SIZE
        fail_base = fail[state] * ALPHABET_SIZE
        for code in range(ALPHABET_SIZE):
            child = goto[base + code]
            if child:
                fail[child] = goto[fail_base + code]
                bfs.append(child)
            else:
                goto[base + code] = goto[fail_base + code]
    counts = []
    for text in texts:
        # A fresh visit array per text keeps the texts independent.
        visits = [0] * states
        state = 0
        for c in text:
            state = goto[state * ALPHABET_SIZE + ord(c) - ALPHABET_START]
            visits[state] += 1
        # Deepest first: every visit also counts for all suffixes along the failure chain.
        for s in reversed(bfs):
            visits[fail[s]] += visits[s]
        counts.append([visits[s] for s in terminal])
    return {'counts': counts}
