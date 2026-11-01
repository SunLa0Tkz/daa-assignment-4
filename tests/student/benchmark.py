"""Reproducible naive/KMP/RK comparison. Run from the repository root: python tests/student/benchmark.py

Timing scope: only the algorithm call, inside one process, after inputs are built; no JSON and no
process start. One unmeasured warm-up call precedes the three measured runs of each combination.
"""
import pathlib
import random
import statistics
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'Python' / 'source'))
import algorithms  # noqa: E402

SEED = 20261101
SIZES = [(500, 50), (1500, 150), (3000, 300)]
METHODS = [('naive', algorithms.naive), ('kmp', algorithms.kmp), ('rk', algorithms.rk)]


def cases(rng):
    for n, m in SIZES:
        text = ''.join(rng.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(n))
        start = rng.randrange(n - m + 1)
        yield 'random', n, m, text, text[start:start + m]
        yield 'repetitive', n, m, 'a' * n, 'a' * (m - 1) + 'b'
        yield 'repetitive-match', n, m, 'a' * n, 'a' * m


def oracle(text, pattern):
    return [i for i in range(len(text) - len(pattern) + 1) if text.startswith(pattern, i)]


def main():
    rng = random.Random(SEED)
    print('|Case|n|m|Seed/generator|Algorithm|Run 1|Run 2|Run 3|Median|Correct outputs checked|')
    print('|---|---:|---:|---|---|---:|---:|---:|---:|---|')
    for case, n, m, text, pattern in cases(rng):
        request = {'text': text, 'pattern': pattern}
        expected = oracle(text, pattern)
        for name, method in METHODS:
            correct = method(request)['positions'] == expected
            method(request)  # Warm-up, not measured.
            runs = []
            for _ in range(3):
                started = time.perf_counter()
                method(request)
                runs.append((time.perf_counter() - started) * 1000)
            values = '|'.join(f'{value:.3f}' for value in runs)
            print(f'|{case}|{n}|{m}|{SEED}/benchmark.py|{name}|{values}|{statistics.median(runs):.3f}|'
                  f'{"yes" if correct else "NO"} (z={len(expected)})|')


if __name__ == '__main__':
    main()
