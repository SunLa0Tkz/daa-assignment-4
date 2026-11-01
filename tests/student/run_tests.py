"""Own tests: fixtures, independent brute-force oracles, full-domain stress runs.

Run from the repository root: python tests/student/run_tests.py
Every request goes through Python/source/main.py, the real JSON Lines interface.
The oracles below do not import the implementation, so they do not share its bugs.
"""
import itertools
import json
import pathlib
import random
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAIN = ROOT / 'Python' / 'source' / 'main.py'
FIXTURES = pathlib.Path(__file__).with_name('fixtures.jsonl')
SEED = 20261101
TIME_LIMIT = 20.0
failures = 0


def run(requests):
    data = ''.join(json.dumps(r, separators=(',', ':')) + '\n' for r in requests)
    started = time.perf_counter()
    done = subprocess.run([sys.executable, str(MAIN)], input=data, capture_output=True,
                          text=True, encoding='utf-8', timeout=120)
    elapsed = time.perf_counter() - started
    if done.returncode:
        raise RuntimeError(done.stderr[:2000])
    lines = done.stdout.splitlines()
    assert len(lines) == len(requests), 'one result line per request'
    return [json.loads(line) for line in lines], elapsed


def report(name, passed, detail=''):
    global failures
    failures += not passed
    print(f"{'PASS' if passed else 'FAIL'} {name}{' ' + detail if detail else ''}")


def is_subsequence(s, text):
    it = iter(text)
    return all(c in it for c in s)


def oracle_lcs(a, b):
    # Plain exhaustive search over the subsets of the shorter string.
    if len(a) > len(b):
        a, b = b, a
    for size in range(len(a), 0, -1):
        for picked in itertools.combinations(a, size):
            if is_subsequence(picked, b):
                return size
    return 0


def oracle_merge(sizes):
    # Tries every order of adjacent merges on the list of current block totals.
    if len(sizes) <= 1:
        return 0
    best = None
    for i in range(len(sizes) - 1):
        joined = sizes[i] + sizes[i + 1]
        cost = joined + oracle_merge(sizes[:i] + [joined] + sizes[i + 2:])
        if best is None or cost < best:
            best = cost
    return best


def oracle_tree(n, weights, edges):
    best = 0
    for mask in range(1 << n):
        if all(not (mask >> u & 1 and mask >> v & 1) for u, v in edges):
            best = max(best, sum(weights[v] for v in range(n) if mask >> v & 1))
    return best


def oracle_positions(text, pattern):
    return [i for i in range(len(text) + 1) if text.startswith(pattern, i)]


def oracle_sa_lcp(text):
    sa = sorted(range(len(text)), key=lambda i: text[i:])
    lcp = [0] * len(text)
    for index in range(1, len(sa)):
        x, y = text[sa[index - 1]:], text[sa[index]:]
        while lcp[index] < min(len(x), len(y)) and x[lcp[index]] == y[lcp[index]]:
            lcp[index] += 1
    return sa, lcp


def oracle_repeat_length(text):
    for size in range(len(text) - 1, 0, -1):
        seen = set()
        for i in range(len(text) - size + 1):
            part = text[i:i + size]
            if part in seen:
                return size
            seen.add(part)
    return 0


def oracle_count(text, pattern):
    return sum(text.startswith(pattern, i) for i in range(len(text)))


def valid_merge_plan(sizes, plan):
    blocks = [(i, i) for i in range(len(sizes))]
    cost = 0
    for l, k, r in plan:
        j = blocks.index((l, k))
        if blocks[j + 1] != (k + 1, r):
            return None
        blocks[j:j + 2] = [(l, r)]
        cost += sum(sizes[l:r + 1])
    return cost if len(blocks) <= 1 and len(plan) == max(0, len(sizes) - 1) else None


def random_tree(rng, n):
    return [[rng.randrange(v), v] for v in range(1, n)]


def fixture_tests():
    cases = [json.loads(line) for line in FIXTURES.read_text(encoding='utf-8').splitlines() if line.strip()]
    answers, _ = run([case['input'] for case in cases])
    for case, answer in zip(cases, answers):
        expected = case['expected']
        passed = all(answer.get(key) == value for key, value in expected.items())
        report(f"fixture {case['name']}", passed, '' if passed else f'got {answer}')


def oracle_tests(rng):
    for task_name, requests, verify in generated_cases(rng):
        answers, _ = run(requests)
        bad = sum(not verify(x, y) for x, y in zip(requests, answers))
        report(f'oracle {task_name}', bad == 0, f'{len(requests)} random cases, {bad} wrong')


def generated_cases(rng):
    def word(max_length, alphabet='ab '):
        return ''.join(rng.choice(alphabet) for _ in range(rng.randint(0, max_length)))

    def verify_lcs(x, y):
        return (y['length'] == oracle_lcs(x['a'], x['b']) == len(y['sequence'])
                and is_subsequence(y['sequence'], x['a']) and is_subsequence(y['sequence'], x['b']))

    def verify_merge(x, y):
        return y['cost'] == oracle_merge(x['sizes']) == valid_merge_plan(x['sizes'], y['plan'])

    def verify_tree(x, y):
        chosen = set(y['selected'])
        return (len(chosen) == len(y['selected'])
                and not any(u in chosen and v in chosen for u, v in x['edges'])
                and sum(x['weights'][v] for v in chosen) == y['weight']
                == oracle_tree(x['n'], x['weights'], x['edges']))

    def verify_search(x, y):
        return y['positions'] == oracle_positions(x['text'], x['pattern'])

    def verify_suffix(x, y):
        sa, lcp = oracle_sa_lcp(x['text'])
        size = oracle_repeat_length(x['text'])
        return (y['sa'] == sa and y['lcp'] == lcp and len(y['repeated']) == size
                and (size == 0 or oracle_count(x['text'], y['repeated']) >= 2))

    def verify_aho(x, y):
        return y['counts'] == [[oracle_count(t, p) for p in x['patterns']] for t in x['texts']]

    yield 'lcs', [{'task': 'lcs', 'a': word(9), 'b': word(9)} for _ in range(300)], verify_lcs
    yield 'merge', [{'task': 'merge', 'sizes': [rng.randint(0, 20) for _ in range(rng.randint(0, 6))]}
                    for _ in range(200)], verify_merge
    trees = []
    for _ in range(300):
        n = rng.randint(0, 11)
        trees.append({'task': 'tree', 'n': n, 'weights': [rng.randint(-6, 10) for _ in range(n)],
                      'edges': random_tree(rng, n)})
    yield 'tree', trees, verify_tree
    for task in ('naive', 'kmp', 'rk'):
        yield task, [{'task': task, 'text': word(25), 'pattern': word(4)} for _ in range(500)], verify_search
    yield 'suffix', [{'task': 'suffix', 'text': word(30)} for _ in range(300)], verify_suffix
    yield 'aho', [{'task': 'aho',
                   'patterns': [word(3) or 'a' for _ in range(rng.randint(0, 6))],
                   'texts': [word(20) for _ in range(rng.randint(0, 4))]} for _ in range(300)], verify_aho


def stress_tests(rng):
    n = 100000
    random_letters = ''.join(rng.choice('abcd') for _ in range(1000))

    def timed(name, request, verify):
        answers, elapsed = run([request])
        report(f'stress {name}', verify(answers[0]) and elapsed < TIME_LIMIT, f'{elapsed:.2f}s')

    timed('lcs 1000x1000 equal', {'task': 'lcs', 'a': 'a' * 1000, 'b': 'a' * 1000},
          lambda y: y['length'] == 1000 and y['sequence'] == 'a' * 1000)
    timed('lcs 1000x1000 random', {'task': 'lcs', 'a': random_letters, 'b': random_letters[::-1]},
          lambda y: y['length'] == len(y['sequence']) and is_subsequence(y['sequence'], random_letters)
          and is_subsequence(y['sequence'], random_letters[::-1]))
    big = [10 ** 9] * 200
    timed('merge n=200 max sizes', {'task': 'merge', 'sizes': big},
          lambda y: y['cost'] == valid_merge_plan(big, y['plan']) and y['cost'] == 1544 * 10 ** 9)
    chain = {'task': 'tree', 'n': n, 'weights': [10 ** 9] * n, 'edges': [[v - 1, v] for v in range(1, n)]}
    timed('tree deep chain n=100000', chain,
          lambda y: y['weight'] == 50000 * 10 ** 9 and len(y['selected']) == 50000)
    star = {'task': 'tree', 'n': n, 'weights': [-1] + [10 ** 9] * (n - 1), 'edges': [[0, v] for v in range(1, n)]}
    timed('tree star n=100000', star, lambda y: y['weight'] == (n - 1) * 10 ** 9)
    timed('naive 3000/1500 repetitive', {'task': 'naive', 'text': 'a' * 3000, 'pattern': 'a' * 1500},
          lambda y: y['positions'] == list(range(1501)))
    timed('kmp 200000/100000 repetitive', {'task': 'kmp', 'text': 'a' * 200000, 'pattern': 'a' * 100000},
          lambda y: y['positions'] == list(range(100001)))
    timed('kmp near-match', {'task': 'kmp', 'text': 'a' * 199999 + 'b', 'pattern': 'a' * 99999 + 'b'},
          lambda y: y['positions'] == [100000])
    timed('rk 10000/2000 all candidates', {'task': 'rk', 'text': 'a' * 10000, 'pattern': 'a' * 2000},
          lambda y: y['positions'] == list(range(8001)))
    equal_text = 'a' * 50000
    timed('suffix all equal n=50000', {'task': 'suffix', 'text': equal_text},
          lambda y: y['sa'] == list(range(49999, -1, -1)) and y['lcp'] == [0] + list(range(1, 50000))
          and y['repeated'] == 'a' * 49999)
    periodic = 'ab' * 25000
    timed('suffix periodic n=50000', {'task': 'suffix', 'text': periodic},
          lambda y: sorted(y['sa']) == list(range(50000)) and max(y['lcp']) == 49998
          and len(y['repeated']) == 49998)
    random_text = ''.join(chr(rng.randint(32, 126)) for _ in range(50000))
    timed('suffix random n=50000', {'task': 'suffix', 'text': random_text},
          lambda y: y['sa'] == sorted(range(50000), key=lambda i: random_text[i:i + 64]))
    timed('aho chain of suffix patterns', {'task': 'aho', 'patterns': ['a' * size for size in range(1, 447)],
                                           'texts': ['a' * 200000]},
          lambda y: y['counts'] == [[200001 - size for size in range(1, 447)]])
    timed('aho 100000 states 100 texts', {'task': 'aho', 'patterns': ['x' * 100000],
                                          'texts': ['x' * 2000 for _ in range(100)]},
          lambda y: y['counts'] == [[0]] * 100)
    timed('aho 10000 duplicates', {'task': 'aho', 'patterns': ['ab'] * 10000, 'texts': ['ab' * 100000]},
          lambda y: y['counts'] == [[100000] * 10000])
    mixed = [{'task': 'aho', 'patterns': ['a'], 'texts': ['aa']}, {'task': 'lcs', 'a': 'ab', 'b': 'b'},
             {'task': 'aho', 'patterns': ['a'], 'texts': ['aa']}, {'task': 'suffix', 'text': 'aa'}]
    answers, _ = run(mixed)
    report('mixed tasks in one process', answers[0] == answers[2] == {'counts': [[2]]}
           and answers[1]['length'] == 1 and answers[3]['repeated'] == 'a')


def main():
    rng = random.Random(SEED)
    fixture_tests()
    oracle_tests(rng)
    stress_tests(rng)
    print(f'{failures} failure(s)')
    return int(bool(failures))


if __name__ == '__main__':
    sys.exit(main())
