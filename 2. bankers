"""Operating System Simulator - Banker's Algorithm (console version, no GUI, single file).

Needs only Python 3.8+ - no other files or packages.
Run:   python cli_02_bankers_algorithm.py
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import List


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
# Algorithm logic: Banker's Algorithm
# ============================================================================
# Banker's Algorithm: Need matrix, safety check, safe sequence, resource requests.
#
#     Need[i][j] = Max[i][j] - Allocation[i][j]
# Safety algorithm: Work = Available.  Repeatedly find an unfinished process whose
# Need <= Work; pretend it finishes (Work += Allocation) and record it.  If every
# process can finish, the state is SAFE and the order found is a safe sequence.

@dataclass
class SafetyStep:
    process: str
    work_before: List[int]
    need: List[int]
    work_after: List[int]


@dataclass
class BankerResult:
    names: List[str]
    need: List[List[int]]
    safe: bool
    sequence: List[str]
    steps: List[SafetyStep]
    stuck: List[str]          # processes that could never finish (when UNSAFE)


def resource_names(m: int) -> List[str]:
    return [chr(65 + j) for j in range(m)] if m <= 26 else [f"R{j + 1}" for j in range(m)]


def validate_system(names, available, allocation, maximum) -> None:
    n, m = len(names), len(available)
    if n == 0:
        raise InputError("Banker's Algorithm: add at least one process.")
    if m == 0:
        raise InputError("Banker's Algorithm: add at least one resource type.")
    if len(set(names)) != n:
        raise InputError("Banker's Algorithm: process names must be unique.")
    if len(allocation) != n or len(maximum) != n:
        raise InputError(f"Banker's Algorithm: Allocation has {len(allocation)} row(s) and "
                         f"Maximum has {len(maximum)} row(s); both must have {n}.")
    rn = resource_names(m)
    if any(x < 0 for x in available):
        raise InputError("Banker's Algorithm: Available values cannot be negative.")
    for i in range(n):
        if len(allocation[i]) != m or len(maximum[i]) != m:
            raise InputError(f"{names[i]}: every row needs exactly {m} value(s).")
        for j in range(m):
            a, mx = allocation[i][j], maximum[i][j]
            if a < 0 or mx < 0:
                raise InputError(f"{names[i]}: negative values are not allowed.")
            if a > mx:
                raise InputError(f"Inconsistent data: {names[i]} holds {a} of resource "
                                 f"{rn[j]} but its maximum demand is only {mx}.")


def compute_need(allocation, maximum):
    return [[mx - a for a, mx in zip(ar, mr)] for ar, mr in zip(allocation, maximum)]


def check_safety(names, available, allocation, need) -> BankerResult:
    n, m = len(names), len(available)
    work = list(available)
    finished = [False] * n
    sequence, steps = [], []
    progress = True
    while progress and len(sequence) < n:
        progress = False
        for i in range(n):
            if not finished[i] and all(need[i][j] <= work[j] for j in range(m)):
                before = list(work)
                work = [work[j] + allocation[i][j] for j in range(m)]
                steps.append(SafetyStep(names[i], before, list(need[i]), list(work)))
                finished[i] = True
                sequence.append(names[i])
                progress = True
    return BankerResult(list(names), need, len(sequence) == n, sequence, steps,
                        [names[i] for i in range(n) if not finished[i]])


def analyse(names, available, allocation, maximum) -> BankerResult:
    validate_system(names, available, allocation, maximum)
    return check_safety(names, available, allocation, compute_need(allocation, maximum))


def resource_request(names, index, request, available, allocation, maximum) -> dict:
    """Resource-request algorithm: would granting ``request`` to process ``index``
    leave the system in a safe state?"""
    validate_system(names, available, allocation, maximum)
    m = len(available)
    if len(request) != m:
        raise InputError(f"The request needs exactly {m} value(s).")
    if any(r < 0 for r in request):
        raise InputError("Request values cannot be negative.")
    need = compute_need(allocation, maximum)
    name = names[index]
    if any(request[j] > need[index][j] for j in range(m)):
        return {"granted": False, "result": None,
                "message": f"DENIED: {name} asked for more than its remaining need "
                           f"{need[index]} (request {list(request)})."}
    if any(request[j] > available[j] for j in range(m)):
        return {"granted": False, "result": None,
                "message": f"DENIED (must wait): request {list(request)} exceeds "
                           f"Available {list(available)}."}
    new_avail = [available[j] - request[j] for j in range(m)]
    new_alloc = [list(r) for r in allocation]
    new_need = [list(r) for r in need]
    for j in range(m):
        new_alloc[index][j] += request[j]
        new_need[index][j] -= request[j]
    res = check_safety(names, new_avail, new_alloc, new_need)
    if res.safe:
        return {"granted": True, "result": res,
                "message": f"GRANTED: the system stays SAFE. Safe sequence: "
                           f"{' -> '.join(res.sequence)}"}
    return {"granted": False, "result": res,
            "message": "DENIED: granting this request would leave the system UNSAFE."}


def generate_safe_system(n: int, m: int, seed=None, max_alloc: int = 4):
    """Random test data that is guaranteed safe (used for large-dataset tests)."""
    rng = random.Random(seed)
    avail = [rng.randint(3, 9) for _ in range(m)]
    work = list(avail)
    rows = []
    for _ in range(n):
        alloc = [rng.randint(0, max_alloc) for _ in range(m)]
        need = [rng.randint(0, work[j]) for j in range(m)]
        rows.append((alloc, [a + d for a, d in zip(alloc, need)]))
        work = [work[j] + alloc[j] for j in range(m)]
    rng.shuffle(rows)
    names = [f"P{i}" for i in range(n)]
    return names, avail, [r[0] for r in rows], [r[1] for r in rows]


# ============================================================================
# Program: Banker's Algorithm
# ============================================================================
# Banker's Algorithm - console version (Need matrix, safety check, safe sequence, requests).

SAMPLE_AVAIL = [3, 3, 2]
SAMPLE_ALLOC = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
SAMPLE_MAX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]


def main():
    banner("OPERATING SYSTEM SIMULATOR - BANKER'S ALGORITHM")
    print("Need = Max - Allocation.  Safety check: repeatedly find a process whose Need <= Work.")
    while True:
        src = ask_source()
        if src == 3:
            print("Goodbye.")
            return
        if src == 1:
            names, avail, alloc, mx = [f"P{i}" for i in range(5)], SAMPLE_AVAIL, SAMPLE_ALLOC, SAMPLE_MAX
        else:
            n = ask_int("Number of processes", 1, 5000)
            m = ask_int("Number of resource types", 1, 60)
            if src == 2:
                names, avail, alloc, mx = generate_safe_system(n, m)
            else:
                names = [f"P{i}" for i in range(n)]
                avail = ask_vector(f"Available instances ({m} values)", m)
                alloc = [ask_vector(f"Allocation of {names[i]} ({m} values)", m) for i in range(n)]
                mx = [ask_vector(f"Maximum of {names[i]} ({m} values)", m) for i in range(n)]
        m = len(avail)
        try:
            res = analyse(names, avail, alloc, mx)
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        limit = None if len(names) <= 30 else 15
        rn = resource_names(m)
        banner("Need matrix")
        print_table(["Process"] + [f"Alloc {c}" for c in rn] + [f"Max {c}" for c in rn] + [f"Need {c}" for c in rn],
                    [[names[i]] + alloc[i] + mx[i] + res.need[i] for i in range(len(names))], limit)
        banner("Safety algorithm steps")
        print_table(["Step", "Process", "Work (before)", "Need", "Work (after)"],
                    [[k, s.process, s.work_before, s.need, s.work_after] for k, s in enumerate(res.steps, 1)], limit)
        if res.safe:
            seq = " -> ".join(res.sequence)
            print("\nRESULT: the system is in a SAFE state.")
            print("Safe sequence: <" + (seq if len(seq) < 400 else seq[:400] + " ...") + ">")
        else:
            print("\nRESULT: the system is UNSAFE (possible deadlock).")
            print("Processes that can never finish: " + ", ".join(res.stuck[:40]))
        while ask_yes_no("\nTest a resource request?", False):
            who = ask_text("Process name: ")
            if who not in names:
                print(f"  ! unknown process '{who}'.")
                continue
            req = ask_vector(f"Request vector ({m} values)", m)
            print("  " + resource_request(names, names.index(who), req, avail, alloc, mx)["message"])


if __name__ == "__main__":
    run(main)
