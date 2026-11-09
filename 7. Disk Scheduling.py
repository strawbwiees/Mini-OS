"""Operating System Simulator - Disk Scheduling (console version, no GUI, single file).

Needs only Python 3.8+ - no other files or packages.
Run:   python cli_07_disk_scheduling.py
"""
from __future__ import annotations

import random
import re
from bisect import bisect_left
from dataclasses import dataclass
from typing import List, Tuple


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
# Algorithm logic: Disk Scheduling
# ============================================================================
# Disk scheduling: FCFS, SSTF, SCAN, C-SCAN, LOOK and C-LOOK.
#
# Conventions
#   * Cylinders are numbered 0 .. disk_size-1.
#   * SCAN / C-SCAN always travel to the physical end of the disk;
#     LOOK / C-LOOK only go as far as the last request in that direction.
#   * C-SCAN / C-LOOK "return jump" distance is counted by default (option).
#   * SSTF ties are broken toward the lower cylinder.

ALGORITHMS = ["FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK", "C-LOOK"]


@dataclass
class DiskResult:
    algorithm: str
    order: List[int]                         # requests in the order they are served
    steps: List[Tuple[int, int, int, str]]   # (from, to, distance counted, note)
    total_movement: int
    average_seek: float
    path: List[int]


class _Head:
    def __init__(self, start, count_jump):
        self.pos, self.total, self.count_jump = start, 0, count_jump
        self.steps, self.order, self.path = [], [], [start]

    def go(self, to, served=False, jump=False, note=""):
        dist = abs(to - self.pos)
        counted = 0 if (jump and not self.count_jump) else dist
        self.total += counted
        if not note:
            note = "serve request" if served else "move"
        if jump:
            note += " (return jump counted)" if self.count_jump else " (return jump NOT counted)"
        self.steps.append((self.pos, to, counted, note))
        self.pos = to
        self.path.append(to)
        if served:
            self.order.append(to)


def _validate(requests, head, disk_size):
    if disk_size < 1:
        raise InputError("Disk Scheduling: the disk size must be at least 1 cylinder.")
    if not requests:
        raise InputError("Disk Scheduling: enter at least one request.")
    top = disk_size - 1
    if not 0 <= head <= top:
        raise InputError(f"Disk Scheduling: the head position must be between 0 and {top}.")
    bad = [r for r in requests if r < 0 or r > top]
    if bad:
        raise InputError(f"Disk Scheduling: request {bad[0]} is outside the disk range 0..{top}.")


def run_algorithm(name, requests, head, disk_size, direction="up", count_jump=True) -> DiskResult:
    _validate(requests, head, disk_size)
    top = disk_size - 1
    up = direction == "up"
    h = _Head(head, count_jump)
    if name == "FCFS":
        for r in requests:
            h.go(r, served=True)
    elif name == "SSTF":
        pending = sorted(requests)
        while pending:
            i = bisect_left(pending, h.pos)
            left = pending[i - 1] if i > 0 else None
            right = pending[i] if i < len(pending) else None
            if right is None or (left is not None and h.pos - left <= right - h.pos):
                h.go(pending.pop(i - 1), served=True, note="serve nearest request")
            else:
                h.go(pending.pop(i), served=True, note="serve nearest request")
    elif name in ("SCAN", "LOOK"):
        if up:
            first = sorted(r for r in requests if r >= head)
            second = sorted((r for r in requests if r < head), reverse=True)
            end = top
        else:
            first = sorted((r for r in requests if r <= head), reverse=True)
            second = sorted(r for r in requests if r > head)
            end = 0
        for r in first:
            h.go(r, served=True)
        if name == "SCAN" and h.pos != end:
            h.go(end, note="reach end of disk")
        for r in second:
            h.go(r, served=True)
    elif name in ("C-SCAN", "C-LOOK"):
        if up:
            first = sorted(r for r in requests if r >= head)
            second = sorted(r for r in requests if r < head)
            end, wrap = top, 0
        else:
            first = sorted((r for r in requests if r <= head), reverse=True)
            second = sorted((r for r in requests if r > head), reverse=True)
            end, wrap = 0, top
        for r in first:
            h.go(r, served=True)
        if name == "C-SCAN":
            if h.pos != end:
                h.go(end, note="reach end of disk")
            if second:
                h.go(wrap, jump=True, note="jump to other end")
                for r in second:
                    h.go(r, served=True)
        elif second:
            h.go(second[0], served=True, jump=True, note="jump to farthest request")
            for r in second[1:]:
                h.go(r, served=True)
    else:
        raise InputError(f"Unknown disk scheduling algorithm: {name}")
    return DiskResult(name, h.order, h.steps, h.total, h.total / len(requests), h.path)


# ============================================================================
# Program: Disk Scheduling
# ============================================================================
# Disk Scheduling - console version (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK).

SAMPLE = [98, 183, 37, 122, 14, 124, 65, 67]


def main():
    banner("OPERATING SYSTEM SIMULATOR - DISK SCHEDULING")
    print("SCAN/C-SCAN go to the disk end; LOOK/C-LOOK stop at the last request; SSTF ties go to the lower cylinder.")
    while True:
        src = ask_source()
        if src == 3:
            print("Goodbye.")
            return
        size = ask_int("Disk size (number of cylinders)", 1, default=200 if src != 2 else 10000)
        if src == 0:
            reqs = ask_int_list("Request queue (cylinder numbers separated by spaces)", 0, size - 1)
            head = ask_int("Initial head position", 0, size - 1)
        elif src == 1:
            reqs, head = list(SAMPLE), 53
            print("Requests: " + " ".join(map(str, reqs)) + "   head = 53")
        else:
            reqs = [random.randrange(size) for _ in range(ask_int("How many requests", 1, 1_000_000, 1000))]
            head = random.randrange(size)
            print(f"Random requests generated, head = {head}")
        direction = ("up", "down")[ask_choice("Initial head direction", ["up (toward higher cylinders)", "down"], 0)]
        jump = ask_yes_no("Count the C-SCAN / C-LOOK return jump in the total?", True)
        algos = ask_multi("Algorithms to run", ALGORITHMS)
        try:
            results = [run_algorithm(a, reqs, head, size, direction, jump) for a in algos]
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        for r in results:
            banner(f"{r.algorithm}  (head {head}, {len(reqs)} requests)")
            order = " -> ".join(map(str, r.order[:30])) + (" ..." if len(r.order) > 30 else "")
            print("Service order: " + order)7.
            print_table(["Move", "From", "To", "Distance", "Note"],
                        [[i + 1, a, b, d, n] for i, (a, b, d, n) in enumerate(r.steps)],
                        None if len(r.steps) <= 30 else 15)
            print(f"Total head movement = {r.total_movement}   Average seek = {r.average_seek:.2f}")
        banner("Comparison")
        print_table(["Algorithm", "Total head movement", "Average seek"],
                    [[r.algorithm, r.total_movement, f"{r.average_seek:.2f}"] for r in results])
        best = min(results, key=lambda r: r.total_movement)
        print(f"Least head movement: {best.algorithm} ({best.total_movement})")


if __name__ == "__main__":
    run(main)
