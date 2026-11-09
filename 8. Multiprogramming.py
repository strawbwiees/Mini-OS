"""Operating System Simulator - Multiprogramming (console version, no GUI, single file).

Needs only Python 3.8+ - no other files or packages.
Run:   python cli_08_multiprogramming.py
"""
from __future__ import annotations

import random
import re
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple


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
# Algorithm logic: Multiprogramming
# ============================================================================
# Multiprogramming: several programs share main memory, one CPU and one I/O device.
#
# Model (time advances in 1-unit ticks)
#   * A program ARRIVES and waits in the job queue until enough free memory exists
#     (and the degree of multiprogramming limit, if any, is not reached).
#   * ADMITTED programs hold their memory until they finish.
#   * The CPU is shared by Round Robin (time quantum).  After its CPU burst a
#     program uses the single I/O device (FCFS) for its I/O burst, then terminates.
#   * While one program does I/O another can use the CPU - this overlap is what
#     raises CPU utilisation compared with running one program at a time.
# Programs that need more memory than the whole system are rejected.

MAX_WORK = 3_000_000          # safety limit on total simulated time units


@dataclass
class Program:
    name: str
    arrival: int
    memory: int
    cpu: int
    io: int = 0


@dataclass
class MPResult:
    rows: List[Dict]
    rejected: List[Program]
    cpu_segments: List[Tuple[str, int, int]]
    io_segments: List[Tuple[str, int, int]]
    mem_samples: List[Tuple[int, int, int]]       # (time, memory used, programs in memory)
    log: List[str]
    metrics: Dict[str, float]


def _add_seg(segs, name, s, e):
    if segs and segs[-1][0] == name and segs[-1][2] == s:
        segs[-1] = (name, segs[-1][1], e)
    else:
        segs.append((name, s, e))


def simulate(programs: List[Program], total_memory: int, quantum: int,
             max_degree: int = 0) -> MPResult:
    if total_memory < 1:
        raise InputError("Multiprogramming: total memory must be at least 1.")
    if quantum < 1:
        raise InputError("Multiprogramming: the time quantum must be at least 1.")
    if max_degree < 0:
        raise InputError("Multiprogramming: the degree limit cannot be negative (0 = unlimited).")
    if not programs:
        raise InputError("Multiprogramming: add at least one program.")
    if len({p.name for p in programs}) != len(programs):
        raise InputError("Multiprogramming: program names must be unique.")
    for p in programs:
        if not p.name:
            raise InputError("Multiprogramming: a program has a blank name.")
        if p.arrival < 0 or p.memory < 1 or p.cpu < 1 or p.io < 0:
            raise InputError(f"{p.name}: arrival/I-O must be >= 0 and memory/CPU burst >= 1.")
    rejected = [p for p in programs if p.memory > total_memory]
    jobs = [p for p in programs if p.memory <= total_memory]
    if not jobs:
        raise InputError("Multiprogramming: every program needs more memory than the system has.")
    if sum(p.cpu + p.io for p in jobs) > MAX_WORK:
        raise InputError(f"Multiprogramming: total CPU+I/O time exceeds {MAX_WORK:,} units; "
                         "please reduce the burst times.")

    n = len(jobs)
    order = sorted(range(n), key=lambda i: (jobs[i].arrival, i))
    rem_cpu = [p.cpu for p in jobs]
    rem_io = [p.io for p in jobs]
    admit, first_cpu, finish = [None] * n, [None] * n, [None] * n
    waiting, ready, ioq = [], deque(), deque()
    cpu_cur = io_cur = None
    slice_used = 0
    in_mem = mem_used = 0
    ptr = done = 0
    t = t0 = jobs[order[0]].arrival
    cpu_busy = io_busy = mem_area = deg_area = max_deg = 0
    cpu_seg, io_seg, samples, log = [], [], [(t, 0, 0)], []
    dirty = True

    def complete(i):
        nonlocal in_mem, mem_used, done, dirty
        finish[i] = t
        in_mem -= 1
        mem_used -= jobs[i].memory
        done += 1
        dirty = True
        log.append(f"t={t}: {jobs[i].name} finished; memory freed "
                   f"({mem_used}/{total_memory} used)")
        samples.append((t, mem_used, in_mem))

    while done < n:
        while ptr < n and jobs[order[ptr]].arrival <= t:
            i = order[ptr]; ptr += 1
            waiting.append(i); dirty = True
            log.append(f"t={t}: {jobs[i].name} arrived (needs {jobs[i].memory} memory)")
        if dirty and waiting:
            still = []
            for i in waiting:
                if (max_degree == 0 or in_mem < max_degree) and \
                        mem_used + jobs[i].memory <= total_memory:
                    in_mem += 1; mem_used += jobs[i].memory
                    admit[i] = t; ready.append(i)
                    log.append(f"t={t}: {jobs[i].name} admitted to memory "
                               f"({mem_used}/{total_memory} used, degree={in_mem})")
                    samples.append((t, mem_used, in_mem))
                else:
                    still.append(i)
            waiting = still
        dirty = False
        max_deg = max(max_deg, in_mem)

        if cpu_cur is None and not ready and io_cur is None and not ioq:
            if ptr < n:                                   # system idle: jump to next arrival
                t = jobs[order[ptr]].arrival
                samples.append((t, mem_used, in_mem))
                continue
            break

        if cpu_cur is not None and slice_used >= quantum:  # quantum expired -> back of queue
            ready.append(cpu_cur); cpu_cur = None
        if cpu_cur is None and ready:
            cpu_cur = ready.popleft(); slice_used = 0
            if first_cpu[cpu_cur] is None:
                first_cpu[cpu_cur] = t
        if io_cur is None and ioq:
            io_cur = ioq.popleft()

        mem_area += mem_used
        deg_area += in_mem
        cpu_i, io_i = cpu_cur, io_cur
        if cpu_i is not None:
            rem_cpu[cpu_i] -= 1; slice_used += 1; cpu_busy += 1
            _add_seg(cpu_seg, jobs[cpu_i].name, t, t + 1)
        if io_i is not None:
            rem_io[io_i] -= 1; io_busy += 1
            _add_seg(io_seg, jobs[io_i].name, t, t + 1)
        t += 1

        if cpu_i is not None and rem_cpu[cpu_i] == 0:
            cpu_cur = None
            if jobs[cpu_i].io > 0:
                ioq.append(cpu_i)
                log.append(f"t={t}: {jobs[cpu_i].name} finished CPU burst, waiting for I/O")
            else:
                complete(cpu_i)
        if io_i is not None and rem_io[io_i] == 0:
            io_cur = None
            complete(io_i)

    horizon = max(t - t0, 1)
    rows = []
    for i, p in enumerate(jobs):
        tat = finish[i] - p.arrival
        rows.append({"name": p.name, "arrival": p.arrival, "memory": p.memory,
                     "cpu": p.cpu, "io": p.io, "admitted": admit[i],
                     "mem_wait": admit[i] - p.arrival, "first_cpu": first_cpu[i],
                     "finish": finish[i], "turnaround": tat,
                     "waiting": tat - p.cpu - p.io})
    metrics = {
        "makespan": horizon,
        "cpu_utilization": 100.0 * cpu_busy / horizon,
        "io_utilization": 100.0 * io_busy / horizon,
        "memory_utilization": 100.0 * mem_area / (horizon * total_memory),
        "throughput": n / horizon,
        "avg_turnaround": sum(r["turnaround"] for r in rows) / n,
        "avg_mem_wait": sum(r["mem_wait"] for r in rows) / n,
        "avg_degree": deg_area / horizon,
        "max_degree": max_deg,
    }
    return MPResult(rows, rejected, cpu_seg, io_seg, samples, log, metrics)


# ============================================================================
# Program: Multiprogramming
# ============================================================================
# Multiprogramming - console version (programs sharing memory, CPU and one I/O device).

SAMPLE = [("J1", 0, 120, 6, 4), ("J2", 1, 200, 5, 3), ("J3", 2, 150, 8, 2),
          ("J4", 3, 300, 4, 6), ("J5", 4, 250, 7, 0), ("J6", 5, 900, 3, 1)]


def to_program(tok, n):
    if len(tok) not in (4, 5):
        raise InputError(f"Row {n}: expected 'name arrival memory cpu [io]'.")
    return Program(tok[0], parse_int(tok[1], f"Row {n} arrival", 0), parse_int(tok[2], f"Row {n} memory", 1),
                      parse_int(tok[3], f"Row {n} CPU burst", 1),
                      parse_int(tok[4], f"Row {n} I/O burst", 0) if len(tok) == 5 else 0)


def main():
    banner("OPERATING SYSTEM SIMULATOR - MULTIPROGRAMMING")
    print("Programs wait for memory, share one Round-Robin CPU, then use one FCFS I/O device.")
    while True:
        src = ask_source()
        if src == 3:
            print("Goodbye.")
            return
        total = ask_int("Total memory", 1, default=1024 if src != 2 else 4096)
        quantum = ask_int("Time quantum", 1, default=2)
        degree = ask_int("Max degree of multiprogramming (0 = unlimited)", 0, default=0)
        if src == 0:
            progs = read_rows("Enter the programs", "name arrival memory cpu_burst [io_burst]   e.g.  J1 0 120 6 4", to_program)
        elif src == 1:
            progs = [Program(*row) for row in SAMPLE]
        else:
            n = ask_int("How many programs", 1, 100000, 500)
            progs = [Program(f"J{i + 1}", random.randint(0, max(10, n // 2)), random.randint(20, 300),
                                random.randint(1, 15), random.randint(0, 10)) for i in range(n)]
        try:
            res, base = simulate(progs, total, quantum, degree), simulate(progs, total, quantum, 1)
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        m, b = res.metrics, base.metrics
        banner("Utilization summary")
        print_table(["Metric", "This run", "Baseline (one program at a time)"], [
            ["CPU utilization %", f"{m['cpu_utilization']:.1f}", f"{b['cpu_utilization']:.1f}"],
            ["I/O device utilization %", f"{m['io_utilization']:.1f}", f"{b['io_utilization']:.1f}"],
            ["Memory utilization %", f"{m['memory_utilization']:.1f}", f"{b['memory_utilization']:.1f}"],
            ["Throughput (programs/unit)", f"{m['throughput']:.4f}", f"{b['throughput']:.4f}"],
            ["Average turnaround", f"{m['avg_turnaround']:.2f}", f"{b['avg_turnaround']:.2f}"],
            ["Average wait for memory", f"{m['avg_mem_wait']:.2f}", f"{b['avg_mem_wait']:.2f}"],
            ["Average / max degree", f"{m['avg_degree']:.2f} / {m['max_degree']}", f"{b['avg_degree']:.2f} / {b['max_degree']}"],
            ["Total time", m["makespan"], b["makespan"]]])
        if res.rejected:
            print("REJECTED (need more than total memory): " + ", ".join(f"{p.name}({p.memory})" for p in res.rejected[:20]))
        banner("Programs")
        print_table(["Program", "Arrival", "Memory", "CPU", "I/O", "Admitted", "Wait for mem.", "First CPU", "Finish", "Turnaround"],
                    [[r["name"], r["arrival"], r["memory"], r["cpu"], r["io"], r["admitted"], r["mem_wait"],
                      r["first_cpu"], r["finish"], r["turnaround"]] for r in res.rows], None if len(progs) <= 30 else 15)
        banner("CPU timeline")
        text_gantt(res.cpu_segments, limit=48)
        banner("I/O timeline")
        text_gantt(res.io_segments, limit=48)
        if ask_yes_no("\nShow the event log?", False):
            for line in res.log[:60]:
                print("  " + line)
            if len(res.log) > 60:
                print(f"  ... {len(res.log) - 60} more event(s) not shown")


if __name__ == "__main__":
    run(main)
