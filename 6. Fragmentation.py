"""Operating System Simulator - Fragmentation (console version, no GUI, single file).

Needs only Python 3.8+ - no other files or packages.
Run:   python cli_06_fragmentation.py
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


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
# Algorithm logic: Fragmentation
# ============================================================================
# Fragmentation: First/Best/Worst/Next Fit allocation with internal and external
# fragmentation analysis.
#
# Two models are supported
#   * Fixed partitions   - each block holds at most ONE process; the unused part of
#                          the block is INTERNAL fragmentation.
#   * Dynamic partitions - a block is a hole that is split; the left-over holes
#                          are the source of EXTERNAL fragmentation.
# External fragmentation is reported when a waiting process is smaller than the
# total free memory yet no single free block can hold it.

STRATEGIES = ["First Fit", "Best Fit", "Worst Fit", "Next Fit"]
FIXED = "Fixed partitions"
DYNAMIC = "Dynamic partitions"
MODES = [FIXED, DYNAMIC]


@dataclass
class Block:
    bid: int
    start: int
    size: int
    owner: Optional[str] = None
    used: int = 0

    @property
    def free(self) -> bool:
        return self.owner is None


@dataclass
class FragResult:
    strategy: str
    mode: str
    blocks: List[Block]
    rows: List[dict]
    total_memory: int
    used_total: int
    internal_total: int
    free_total: int
    largest_free: int
    external_total: int
    notes: List[str]


def allocate(block_sizes: List[int], processes: List[Tuple[str, int]], strategy: str,
             mode: str = FIXED) -> FragResult:
    if not block_sizes:
        raise InputError("Fragmentation: enter at least one memory block.")
    if not processes:
        raise InputError("Fragmentation: enter at least one process.")
    if strategy not in STRATEGIES:
        raise InputError(f"Unknown allocation strategy: {strategy}")
    if any(s < 1 for s in block_sizes):
        raise InputError("Fragmentation: block sizes must be at least 1.")
    if any(sz < 1 for _, sz in processes):
        raise InputError("Fragmentation: process sizes must be at least 1.")
    if len({n for n, _ in processes}) != len(processes):
        raise InputError("Fragmentation: process names must be unique.")

    blocks, addr = [], 0
    for i, s in enumerate(block_sizes, 1):
        blocks.append(Block(i, addr, s)); addr += s
    last_start, rows = 0, []
    for name, size in processes:
        # single pass over the blocks: find the position of the chosen block
        pick = -1
        for pos, c in enumerate(blocks):
            if c.owner is not None or c.size < size:
                continue
            if strategy == "First Fit":
                pick = pos; break
            if strategy == "Next Fit":
                if c.start >= last_start:
                    pick = pos; break
                if pick < 0:
                    pick = pos                     # fallback: wrap around to the first fit
                continue
            if pick < 0 or (strategy == "Best Fit" and c.size < blocks[pick].size) or \
                    (strategy == "Worst Fit" and c.size > blocks[pick].size):
                pick = pos                         # ties keep the lower address
        if pick < 0:
            rows.append({"name": name, "size": size, "status": "WAITING", "bid": None,
                         "start": None, "block_size": None, "internal": 0})
            continue
        b = blocks[pick]
        last_start = b.start
        if mode == DYNAMIC and b.size > size:              # split the hole
            blocks.insert(pick + 1, Block(b.bid, b.start + size, b.size - size))
            b.size = size
        b.owner, b.used = name, size
        rows.append({"name": name, "size": size, "status": "ALLOCATED", "bid": b.bid,
                     "start": b.start, "block_size": b.size, "internal": b.size - size})

    free_blocks = [b for b in blocks if b.free]
    free_total = sum(b.size for b in free_blocks)
    largest = max((b.size for b in free_blocks), default=0)
    internal = sum(r["internal"] for r in rows)
    used_total = sum(b.used for b in blocks if not b.free)
    notes, external = [], 0
    for r in rows:
        if r["status"] != "WAITING":
            continue
        if r["size"] <= free_total:
            external = free_total
            notes.append(f"{r['name']} (size {r['size']}) is waiting: total free = {free_total} "
                         f"but the largest single block is only {largest} -> EXTERNAL fragmentation.")
        else:
            notes.append(f"{r['name']} (size {r['size']}) is waiting: not enough total free "
                         f"memory ({free_total}).")
    return FragResult(strategy, mode, blocks, rows, addr, used_total, internal,
                      free_total, largest, external, notes)


# ============================================================================
# Program: Fragmentation
# ============================================================================
# Fragmentation - console version (First/Best/Worst/Next Fit, internal & external fragmentation).

SAMPLE_BLOCKS = [100, 500, 200, 300, 600]
SAMPLE_PROCS = [("P1", 212), ("P2", 417), ("P3", 112), ("P4", 426)]


def to_process(tok, n):
    if len(tok) != 2:
        raise InputError(f"Row {n}: expected 'name size'.")
    return tok[0], parse_int(tok[1], f"Row {n} size", 1)


def memory_line(blocks):
    return " ".join(f"[{'free' if b.free else b.owner}:{b.size}]" for b in blocks[:40]) + \
           (" ..." if len(blocks) > 40 else "")


def main():
    banner("OPERATING SYSTEM SIMULATOR - FRAGMENTATION")
    print("FIXED partitions: unused part of a block = INTERNAL fragmentation.")
    print("DYNAMIC partitions: leftover holes that cannot hold a waiting process = EXTERNAL fragmentation.")
    while True:
        src = ask_source()
        if src == 3:
            print("Goodbye.")
            return
        if src == 0:
            sizes = ask_int_list("Memory block sizes (numbers separated by spaces)", 1)
            procs = read_rows("Enter the processes", "name size   e.g.  P1 212", to_process)
        elif src == 1:
            sizes, procs = list(SAMPLE_BLOCKS), list(SAMPLE_PROCS)
        else:
            sizes = [random.randint(20, 600) for _ in range(ask_int("How many memory blocks", 1, 100000, 500))]
            procs = [(f"P{i + 1}", random.randint(10, 450)) for i in range(ask_int("How many processes", 1, 100000, 500))]
        mode = MODES[ask_choice("Memory model", MODES, 0)]
        shown = STRATEGIES[ask_choice("Show full details for", STRATEGIES, 1)]
        try:
            results = {s: allocate(sizes, procs, s, mode) for s in STRATEGIES}
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        res = results[shown]
        banner(f"{shown} / {mode}")
        print_table(["Process", "Size", "Status", "Block #", "Start", "Block size", "Internal frag."],
                    [[r["name"], r["size"], r["status"], "-" if r["bid"] is None else r["bid"],
                      "-" if r["start"] is None else r["start"], "-" if r["block_size"] is None else r["block_size"],
                      r["internal"]] for r in res.rows], None if len(procs) <= 30 else 15)
        print("\nMemory map: " + memory_line(res.blocks))
        print(f"Total {res.total_memory} | allocated {res.used_total} | internal fragmentation {res.internal_total} | "
              f"free {res.free_total} (largest {res.largest_free}) | external fragmentation {res.external_total}")
        for note in res.notes[:8]:
            print("  - " + note)
        banner("Strategy comparison")
        print_table(["Strategy", "Allocated", "Waiting", "Internal frag.", "Free", "Largest free", "External frag."],
                    [[s, sum(r["status"] == "ALLOCATED" for r in x.rows), sum(r["status"] == "WAITING" for r in x.rows),
                      x.internal_total, x.free_total, x.largest_free, x.external_total] for s, x in results.items()])


if __name__ == "__main__":
    run(main)
