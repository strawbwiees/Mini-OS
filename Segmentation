"""Operating System Simulator - Segmentation (console version, no GUI, single file).

Needs only Python 3.8+ - no other files or packages.
Run:   python cli_05_segmentation.py
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
# Algorithm logic: Segmentation
# ============================================================================
# Segmentation: segment table, base/limit checking and address translation.
#
# A logical address is (segment number, offset).  It is valid when the segment
# exists and 0 <= offset < limit; then physical address = base + offset.
# Otherwise the hardware raises a trap (addressing error).

@dataclass
class Segment:
    seg_id: int
    base: int
    limit: int

    @property
    def end(self) -> int:               # last valid physical address
        return self.base + self.limit - 1


@dataclass
class Translation:
    seg: int
    offset: int
    valid: bool
    physical: Optional[int]
    message: str


def validate_segments(segments: List[Segment]) -> List[str]:
    """Raise InputError for impossible data; return warnings for overlaps."""
    if not segments:
        raise InputError("Segmentation: define at least one segment.")
    if len({s.seg_id for s in segments}) != len(segments):
        raise InputError("Segmentation: segment numbers must be unique.")
    for s in segments:
        if s.seg_id < 0 or s.base < 0:
            raise InputError(f"Segment {s.seg_id}: segment number and base cannot be negative.")
        if s.limit < 1:
            raise InputError(f"Segment {s.seg_id}: limit must be at least 1.")
    warnings, max_end, owner = [], -1, None
    for s in sorted(segments, key=lambda s: (s.base, s.seg_id)):
        if s.base <= max_end:
            warnings.append(f"Segments {owner} and {s.seg_id} overlap in physical memory.")
        if s.end > max_end:
            max_end, owner = s.end, s.seg_id
    return warnings


def translate_all(segments: List[Segment], requests: List[Tuple[int, int]]) -> List[Translation]:
    table: Dict[int, Segment] = {s.seg_id: s for s in segments}
    out = []
    for seg, off in requests:
        s = table.get(seg)
        if s is None:
            out.append(Translation(seg, off, False, None, f"TRAP: segment {seg} is not defined"))
        elif off < 0:
            out.append(Translation(seg, off, False, None, "TRAP: negative offset"))
        elif off >= s.limit:
            out.append(Translation(seg, off, False, None,
                                   f"TRAP: offset {off} >= limit {s.limit} (out of range)"))
        else:
            out.append(Translation(seg, off, True, s.base + off,
                                   f"VALID: {s.base} + {off} = {s.base + off}"))
    return out


# ============================================================================
# Program: Segmentation
# ============================================================================
# Segmentation - console version (segment table, base/limit checks, address translation).

SAMPLE_SEGS = [(0, 1400, 1000), (1, 6300, 400), (2, 4300, 400), (3, 3200, 1100), (4, 4700, 1000)]
SAMPLE_REQS = [(2, 53), (3, 852), (0, 1222), (1, 399), (1, 400), (9, 10)]


def to_segment(tok, n):
    if len(tok) != 3:
        raise InputError(f"Row {n}: expected 'segment base limit'.")
    return Segment(parse_int(tok[0], f"Row {n} segment", 0), parse_int(tok[1], f"Row {n} base", 0),
                      parse_int(tok[2], f"Row {n} limit", 1))


def to_request(tok, n):
    if len(tok) != 2:
        raise InputError(f"Row {n}: expected 'segment offset'.")
    return parse_int(tok[0], f"Row {n} segment"), parse_int(tok[1], f"Row {n} offset")


def main():
    banner("OPERATING SYSTEM SIMULATOR - SEGMENTATION")
    print("Valid when the segment exists and 0 <= offset < limit; physical = base + offset.")
    while True:
        src = ask_source()
        if src == 3:
            print("Goodbye.")
            return
        if src == 0:
            segs = read_rows("Enter the segment table", "segment base limit   e.g.  0 1400 1000", to_segment)
            reqs = read_rows("Enter logical addresses", "segment offset   e.g.  2 53", to_request)
        elif src == 1:
            segs, reqs = [Segment(*s) for s in SAMPLE_SEGS], list(SAMPLE_REQS)
        else:
            n = ask_int("How many segments", 1, 100000, 500)
            base, segs = 0, []
            for i in range(n):
                lim = random.randint(50, 900)
                segs.append(Segment(i, base, lim))
                base += lim + random.randint(0, 200)
            reqs = [(random.randint(0, n + 5), random.randint(0, 1000)) for _ in range(ask_int("How many requests", 1, 1_000_000, 2000))]
        try:
            warnings = validate_segments(segs)
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        limit = None if len(segs) <= 30 else 15
        banner("Segment table")
        print_table(["Segment", "Base", "Limit", "Last valid address"],
                    [[s.seg_id, s.base, s.limit, s.end] for s in sorted(segs, key=lambda s: s.seg_id)], limit)
        for w in warnings[:5]:
            print("  WARNING: " + w)
        out = translate_all(segs, reqs)
        banner("Address translation")
        print_table(["Segment", "Offset", "Physical address", "Result"],
                    [[t.seg, t.offset, "-" if t.physical is None else t.physical, t.message] for t in out],
                    None if len(out) <= 40 else 20)
        ok = sum(t.valid for t in out)
        print(f"{len(out)} request(s): {ok} valid, {len(out) - ok} trapped.")


if __name__ == "__main__":
    run(main)
