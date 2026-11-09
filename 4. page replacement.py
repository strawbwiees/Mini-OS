

Needs only Python 3.8+ - no other files or packages.
Run:   python cli_04_page_replacement.py
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import List, Optional


# ============================================================================
# Input validation
# ============================================================================
# Shared input-validation helpers.
#
# Every module raises ``InputError`` for bad user input.  The GUI catches it and
# shows the message in a dialog, so invalid data never crashes the program.

class InputError(ValueError):
    """Raised for blank, malformed, negative or inconsistent user input."""


_SPLIT = re.compile(r"[,;\s]+")


def parse_int(text, label, minimum=None, maximum=None):
    """Convert ``text`` to an int, or raise InputError with a helpful message."""
    s = "" if text is None else str(text).strip()
    if s == "":
        raise InputError(f"{label}: the field is blank.")
    try:
        value = int(s)
    except ValueError:
        raise InputError(f"{label}: '{s}' is not a valid whole number.") from None
    if minimum is not None and value < minimum:
        if minimum == 0:
            raise InputError(f"{label}: negative values are not allowed (got {value}).")
        raise InputError(f"{label}: must be at least {minimum} (got {value}).")
    if maximum is not None and value > maximum:
        raise InputError(f"{label}: must be at most {maximum} (got {value}).")
    return value


def parse_int_list(text, label, minimum=None, maximum=None, min_count=1):
    """Parse a list of integers separated by commas, spaces, semicolons or newlines."""
    s = "" if text is None else str(text).strip()
    if not s:
        raise InputError(f"{label}: the field is blank.")
    parts = [p for p in _SPLIT.split(s) if p != ""]
    if len(parts) < min_count:
        raise InputError(f"{label}: enter at least {min_count} value(s).")
    return [parse_int(p, f"{label} (item {k})", minimum, maximum)
            for k, p in enumerate(parts, 1)]


# ============================================================================
# Console helpers
# ============================================================================
# Console helpers: validated prompts, row entry, aligned text tables and a text Gantt chart.

def banner(title):
    print("\n" + "=" * 72)
    print("  " + title)
    print("=" * 72)


def ask_text(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        raise SystemExit(0)


def run(main):
    """Run a program's main() and exit politely on Ctrl+C."""
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye.")


def ask_int(prompt, minimum=None, maximum=None, default=None):
    """Ask until a valid whole number is typed (blank = default when one is given)."""
    while True:
        shown = prompt + (f" [{default}]" if default is not None else "") + ": "
        text = ask_text(shown)
        if text == "" and default is not None:
            return default
        try:
            return parse_int(text, "Input", minimum, maximum)
        except InputError as exc:
            print("  ! " + str(exc))


def ask_int_list(prompt, minimum=None, maximum=None, min_count=1):
    while True:
        try:
            return parse_int_list(ask_text(prompt + ": "), "Input", minimum, maximum, min_count)
        except InputError as exc:
            print("  ! " + str(exc))


def ask_vector(prompt, size, minimum=0):
    """A list of exactly ``size`` whole numbers."""
    while True:
        values = ask_int_list(prompt, minimum)
        if len(values) == size:
            return values
        print(f"  ! please enter exactly {size} value(s) (you gave {len(values)}).")


def ask_choice(title, options, default=None):
    """Numbered menu; returns the 0-based index of the choice."""
    print(f"\n{title}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        hint = f" [{default + 1}]" if default is not None else ""
        text = ask_text(f"Choose 1-{len(options)}{hint}: ")
        if text == "" and default is not None:
            return default
        try:
            return parse_int(text, "Choice", 1, len(options)) - 1
        except InputError as exc:
            print("  ! " + str(exc))


def ask_multi(title, options):
    """Pick several options (numbers separated by spaces); Enter = all of them."""
    print(f"\n{title}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        text = ask_text("Choose numbers separated by spaces (Enter = all): ")
        if text == "":
            return list(options)
        try:
            picks = parse_int_list(text, "Choice", 1, len(options))
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        return [options[i - 1] for i in sorted(set(picks))]


def ask_yes_no(prompt, default=True):
    while True:
        text = ask_text(f"{prompt} ({'Y/n' if default else 'y/N'}): ").lower()
        if text == "":
            return default
        if text in ("y", "yes"):
            return True
        if text in ("n", "no"):
            return False
        print("  ! please answer y or n.")


def ask_source():
    return ask_choice("Where does the data come from?",
                      ["Type it in", "Use sample data", "Generate random data (large test)", "Quit"])


def read_rows(title, hint, convert, min_rows=1):
    """Read rows (any number) until a blank line.  ``convert(tokens, row_no)`` builds
    one item or raises InputError; a bad row is explained and asked again."""
    print(f"\n{title}\n  Format: {hint}\n  One row per line - press Enter on an empty line to finish.")
    rows = []
    while True:
        line = ask_text(f"  row {len(rows) + 1}> ")
        if line == "":
            if len(rows) >= min_rows:
                return rows
            print(f"  ! enter at least {min_rows} row(s).")
            continue
        try:
            rows.append(convert([t for t in re.split(r"[,;\s]+", line) if t], len(rows) + 1))
        except InputError as exc:
            print("  ! " + str(exc))


def print_table(headers, rows, limit=None):
    rows = [[str(c) for c in r] for r in rows]
    shown = rows if limit is None else rows[:limit]
    widths = [len(str(h)) for h in headers]
    for r in shown:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))
    line = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    print(line)
    print("| " + " | ".join(str(h).center(w) for h, w in zip(headers, widths)) + " |")
    print(line)
    for r in shown:
        print("| " + " | ".join(c.center(w) for c, w in zip(r, widths)) + " |")
    print(line)
    if len(shown) < len(rows):
        print(f"  ... {len(rows) - len(shown)} more row(s) not shown")


def text_gantt(segments, per_line=12, limit=96):
    """Print (label, start, end) segments as a text Gantt chart."""
    shown = segments[:limit]
    for i in range(0, len(shown), per_line):
        chunk = shown[i:i + per_line]
        print("|" + "|".join(f" {str(n)[:5]:^5} " for n, _, _ in chunk) + "|")
        print("".join(str(s).ljust(8) for _, s, _ in chunk) + str(chunk[-1][2]))
    if len(segments) > limit:
        print(f"  ... {len(segments) - limit} more segment(s) not shown")


# ============================================================================
# Algorithm logic: Page Replacement
# ============================================================================
# Page replacement: FIFO, LRU, Optimal and Second Chance (Clock).
#
# Each step records the frame contents, whether it was a HIT or FAULT and which
# page (if any) was evicted.

ALGORITHMS = ["FIFO", "LRU", "Optimal", "Second Chance (Clock)"]


@dataclass
class ReplacementStep:
    index: int
    page: int
    frames: List[Optional[int]]
    hit: bool
    victim: Optional[int]


@dataclass
class ReplacementResult:
    algorithm: str
    frame_count: int
    steps: List[ReplacementStep]
    hits: int
    faults: int

    @property
    def hit_ratio(self) -> float:
        return self.hits / len(self.steps) if self.steps else 0.0

    @property
    def fault_ratio(self) -> float:
        return self.faults / len(self.steps) if self.steps else 0.0


def _validate(refs, frames):
    if not refs:
        raise InputError("Page Replacement: the reference string is empty.")
    if frames < 1:
        raise InputError("Page Replacement: the number of frames must be at least 1.")
    if any(r < 0 for r in refs):
        raise InputError("Page Replacement: page numbers cannot be negative.")


def _finish(name, F, steps):
    hits = sum(1 for s in steps if s.hit)
    return ReplacementResult(name, F, steps, hits, len(steps) - hits)


def fifo(refs, F):
    _validate(refs, F)
    frames, where, steps = [None] * F, {}, []
    used = ptr = 0
    for i, p in enumerate(refs):
        if p in where:
            steps.append(ReplacementStep(i, p, list(frames), True, None)); continue
        victim = None
        if used < F:
            slot = used; used += 1
        else:
            slot = ptr; ptr = (ptr + 1) % F
            victim = frames[slot]; del where[victim]
        frames[slot] = p; where[p] = slot
        steps.append(ReplacementStep(i, p, list(frames), False, victim))
    return _finish("FIFO", F, steps)


def lru(refs, F):
    _validate(refs, F)
    frames, where, last, steps = [None] * F, {}, {}, []
    used = 0
    for i, p in enumerate(refs):
        if p in where:
            last[p] = i
            steps.append(ReplacementStep(i, p, list(frames), True, None)); continue
        victim = None
        if used < F:
            slot = used; used += 1
        else:
            victim = min(where, key=lambda q: last[q])      # least recently used
            slot = where.pop(victim)
        frames[slot] = p; where[p] = slot; last[p] = i
        steps.append(ReplacementStep(i, p, list(frames), False, victim))
    return _finish("LRU", F, steps)


def optimal(refs, F):
    _validate(refs, F)
    n = len(refs)
    nxt, seen = [0] * n, {}                    # nxt[i] = next index where refs[i] is used
    for i in range(n - 1, -1, -1):
        nxt[i] = seen.get(refs[i], float("inf")); seen[refs[i]] = i
    frames, where, next_use, steps = [None] * F, {}, {}, []
    used = 0
    for i, p in enumerate(refs):
        if p in where:
            next_use[p] = nxt[i]
            steps.append(ReplacementStep(i, p, list(frames), True, None)); continue
        victim = None
        if used < F:
            slot = used; used += 1
        else:                                  # evict the page used farthest in the future
            victim = max(where, key=lambda q: (next_use[q], -where[q]))
            slot = where.pop(victim)
        frames[slot] = p; where[p] = slot; next_use[p] = nxt[i]
        steps.append(ReplacementStep(i, p, list(frames), False, victim))
    return _finish("Optimal", F, steps)


def second_chance(refs, F):
    _validate(refs, F)
    frames, where, bits, steps = [None] * F, {}, [0] * F, []
    used = hand = 0
    for i, p in enumerate(refs):
        if p in where:
            bits[where[p]] = 1
            steps.append(ReplacementStep(i, p, list(frames), True, None)); continue
        victim = None
        if used < F:
            slot = used; used += 1
        else:
            while bits[hand] == 1:             # give a second chance
                bits[hand] = 0; hand = (hand + 1) % F
            slot = hand; hand = (hand + 1) % F
            victim = frames[slot]; del where[victim]
        frames[slot] = p; where[p] = slot; bits[slot] = 1
        steps.append(ReplacementStep(i, p, list(frames), False, victim))
    return _finish("Second Chance (Clock)", F, steps)


_FUNCS = {"FIFO": fifo, "LRU": lru, "Optimal": optimal, "Second Chance (Clock)": second_chance}


def run_algorithm(name, refs, frames) -> ReplacementResult:
    if name not in _FUNCS:
        raise InputError(f"Unknown page replacement algorithm: {name}")
    return _FUNCS[name](refs, frames)


# ============================================================================
# Program: Page Replacement
# ============================================================================
# Page Replacement - console version (FIFO, LRU, Optimal, Second Chance).

SAMPLE = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]


def main():
    banner("OPERATING SYSTEM SIMULATOR - PAGE REPLACEMENT")
    while True:
        src = ask_source()
        if src == 3:
            print("Goodbye.")
            return
        if src == 0:
            refs = ask_int_list("Reference string (numbers separated by spaces or commas)", 0)
        elif src == 1:
            refs = list(SAMPLE)
            print("Reference string: " + " ".join(map(str, refs)))
        else:
            n = ask_int("Length of the reference string", 1, 1_000_000, 1000)
            k = ask_int("Number of distinct pages", 1, 1_000_000, 20)
            refs = [random.randrange(k) for _ in range(n)]
        frames = ask_int("Number of frames", 1, default=3)
        algos = ask_multi("Algorithms to run", ALGORITHMS)
        try:
            results = [run_algorithm(a, refs, frames) for a in algos]
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        limit = None if len(refs) <= 40 else 20
        for r in results:
            banner(f"{r.algorithm}  -  {len(refs)} references, {frames} frames")
            print_table(["Step", "Page", "Frames", "Result", "Evicted"],
                        [[s.index + 1, s.page, " ".join("-" if x is None else str(x) for x in s.frames),
                          "HIT" if s.hit else "FAULT", "" if s.victim is None else s.victim] for s in r.steps], limit)
            print(f"Hits = {r.hits}   Faults = {r.faults}   Hit ratio = {r.hit_ratio:.1%}   Fault ratio = {r.fault_ratio:.1%}")
        banner("Comparison")
        print_table(["Algorithm", "Hits", "Faults", "Hit ratio", "Fault ratio"],
                    [[r.algorithm, r.hits, r.faults, f"{r.hit_ratio:.1%}", f"{r.fault_ratio:.1%}"] for r in results])
        best = min(results, key=lambda r: r.faults)
        print(f"Fewest faults: {best.algorithm} ({best.faults})")


if __name__ == "__main__":
    run(main)
