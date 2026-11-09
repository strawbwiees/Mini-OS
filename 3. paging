"""Operating System Simulator - Paging (console version, no GUI, single file).

Needs only Python 3.8+ - no other files or packages.
Run:   python cli_03_paging.py
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


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
# Algorithm logic: Paging
# ============================================================================
# Paging: page-to-frame mapping and logical -> physical address translation.
#
#     page number     = logical address // page size
#     offset          = logical address %  page size
#     physical address = frame number * page size + offset
# Internal fragmentation of a process = pages * page size - process size.

SEQUENTIAL = "Sequential (first free frames)"
SCATTERED = "Scattered (random free frames)"


@dataclass
class PagingState:
    page_size: int
    total_frames: int
    os_frames: int
    frame_table: List[Optional[Tuple[str, int]]]   # None = free, ("OS", k) = reserved
    page_tables: Dict[str, List[int]]
    sizes: Dict[str, int]
    rows: List[Dict]


def allocate_memory(page_size, total_frames, os_frames, processes, mode=SEQUENTIAL,
                    seed=None) -> PagingState:
    """``processes`` is a list of (name, size_in_bytes)."""
    if page_size < 1:
        raise InputError("Page size must be at least 1.")
    if total_frames < 1:
        raise InputError("Number of frames must be at least 1.")
    if not 0 <= os_frames <= total_frames:
        raise InputError("OS-reserved frames must be between 0 and the total number of frames.")
    if not processes:
        raise InputError("Paging: add at least one process.")
    if len({p[0] for p in processes}) != len(processes):
        raise InputError("Paging: process names must be unique.")
    table: List[Optional[Tuple[str, int]]] = [None] * total_frames
    for f in range(os_frames):
        table[f] = ("OS", f)
    free = list(range(os_frames, total_frames))
    if mode == SCATTERED:
        random.Random(seed).shuffle(free)
    ptr = 0
    page_tables, sizes, rows = {}, {}, []
    for name, size in processes:
        if not name:
            raise InputError("Paging: a process has a blank name.")
        if size < 1:
            raise InputError(f"{name}: process size must be at least 1.")
        pages = -(-size // page_size)
        internal = pages * page_size - size
        if pages > len(free) - ptr:
            rows.append({"name": name, "size": size, "pages": pages, "internal": internal,
                         "status": f"REJECTED (needs {pages} frames, {len(free) - ptr} free)"})
            continue
        frames = free[ptr:ptr + pages]
        ptr += pages
        for pg, fr in enumerate(frames):
            table[fr] = (name, pg)
        page_tables[name], sizes[name] = frames, size
        rows.append({"name": name, "size": size, "pages": pages, "internal": internal,
                     "status": "LOADED"})
    return PagingState(page_size, total_frames, os_frames, table, page_tables, sizes, rows)


def translate(state: PagingState, name: str, address: int) -> dict:
    out = {"process": name, "logical": address, "page": None, "offset": None,
           "frame": None, "physical": None, "ok": False, "calc": "", "message": ""}
    if name not in state.page_tables:
        out["message"] = "INVALID: process is not loaded in memory"
        return out
    if address < 0:
        out["message"] = "INVALID: negative logical address"
        return out
    size = state.sizes[name]
    if address >= size:
        out["message"] = f"TRAP: beyond process size ({size})"
        return out
    page, offset = divmod(address, state.page_size)
    frame = state.page_tables[name][page]
    phys = frame * state.page_size + offset
    out.update(page=page, offset=offset, frame=frame, physical=phys, ok=True,
               calc=f"{frame} x {state.page_size} + {offset} = {phys}", message="VALID")
    return out


# ============================================================================
# Program: Paging
# ============================================================================
# Paging - console version (page tables and logical -> physical address translation).

SAMPLE_PROCS = [("P1", 3000), ("P2", 5000), ("P3", 2048)]
SAMPLE_ADDR = [("P1", 0), ("P1", 2100), ("P2", 4999), ("P3", 2047), ("P1", 3000), ("P9", 5)]


def to_process(tok, n):
    if len(tok) != 2:
        raise InputError(f"Row {n}: expected 'name size'.")
    return tok[0], parse_int(tok[1], f"Row {n} size", 1)


def to_address(tok, n):
    if len(tok) != 2:
        raise InputError(f"Row {n}: expected 'process address'.")
    return tok[0], parse_int(tok[1], f"Row {n} address")


def main():
    banner("OPERATING SYSTEM SIMULATOR - PAGING")
    print("page = address // page size | offset = address % page size | physical = frame x page size + offset")
    while True:
        src = ask_source()
        if src == 3:
            print("Goodbye.")
            return
        page_size = ask_int("Page size in bytes", 1, default=1024)
        frames = ask_int("Number of physical frames", 1, default=16 if src != 2 else 5000)
        os_frames = ask_int("Frames reserved for the OS", 0, frames, 2)
        scattered = ask_choice("Frame placement", [SEQUENTIAL, SCATTERED], 0) == 1
        seed = ask_int("Random seed", 0, default=1) if scattered else None
        if src == 0:
            procs = read_rows("Enter the processes", "name size_in_bytes   e.g.  P1 3000", to_process)
        elif src == 1:
            procs = list(SAMPLE_PROCS)
        else:
            procs = [(f"P{i + 1}", random.randint(100, 20000)) for i in range(ask_int("How many processes", 1, 100000, 200))]
        try:
            state = allocate_memory(page_size, frames, os_frames, procs,
                                       SCATTERED if scattered else SEQUENTIAL, seed)
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        limit = None if len(procs) <= 30 else 15
        banner("Processes")
        print_table(["Process", "Size", "Pages", "Internal fragmentation", "Status"],
                    [[r["name"], r["size"], r["pages"], r["internal"], r["status"]] for r in state.rows], limit)
        banner("Page tables")
        print_table(["Process", "Page -> Frame"],
                    [[n, "  ".join(f"{p}->{f}" for p, f in enumerate(t[:12])) + (" ..." if len(t) > 12 else "")]
                     for n, t in state.page_tables.items()], limit)
        if frames <= 48:
            banner("Frame map")
            print("  ".join(f"[{i}:{'free' if e is None else e[0] + ('' if e[0] == 'OS' else ':' + str(e[1]))}]"
                            for i, e in enumerate(state.frame_table)))
        free = sum(1 for e in state.frame_table if e is None)
        print(f"\nFrames: {frames} total, {os_frames} for OS, {free} free.")
        if src == 0:
            addrs = read_rows("Enter logical addresses to translate", "process address   e.g.  P1 2100",
                              to_address, min_rows=0)
        else:
            addrs = list(SAMPLE_ADDR) if src == 1 else [(random.choice(list(state.page_tables) or ["P1"]), random.randint(0, 25000)) for _ in range(20)]
        if addrs:
            rows = []
            for who, a in addrs:
                t = translate(state, who, a)
                rows.append([who, a, t["page"] if t["ok"] else "-", t["offset"] if t["ok"] else "-",
                             t["frame"] if t["ok"] else "-", t["physical"] if t["ok"] else "-", t["message"], t["calc"]])
            banner("Address translation")
            print_table(["Process", "Logical", "Page", "Offset", "Frame", "Physical", "Result", "Calculation"], rows)


if __name__ == "__main__":
    run(main)
