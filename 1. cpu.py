import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

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
# Algorithm logic: CPU Scheduling
# ============================================================================
# CPU Scheduling: FCFS, SJF, SRTF, Priority (both modes) and Round Robin.
#
# Formulas used for every algorithm
#     Turnaround Time = Completion Time - Arrival Time
#     Waiting Time    = Turnaround Time - Burst Time
#     Response Time   = First Start Time - Arrival Time
# The Gantt chart starts at the earliest arrival time; gaps appear as IDLE.

IDLE = "IDLE"

ALGORITHMS = [
    "FCFS",
    "SJF (Non-Preemptive)",
    "SRTF (Preemptive SJF)",
    "Priority (Non-Preemptive)",
    "Priority (Preemptive)",
    "Round Robin",
]


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int = 0


@dataclass
class ScheduleResult:
    algorithm: str
    timeline: List[Tuple[str, int, int]]      # (pid or IDLE, start, end)
    rows: List[Dict]
    avg_waiting: float
    avg_turnaround: float
    avg_response: float
    cpu_utilization: float                    # percent
    throughput: float                         # processes per time unit
    context_switches: int
    start_time: int
    end_time: int


def validate_processes(procs: List[Process]) -> None:
    if not procs:
        raise InputError("CPU Scheduling: add at least one process.")
    seen = set()
    for p in procs:
        if not p.pid:
            raise InputError("CPU Scheduling: a process has a blank ID.")
        if p.pid in seen:
            raise InputError(f"CPU Scheduling: duplicate process ID '{p.pid}'.")
        seen.add(p.pid)
        if p.arrival < 0:
            raise InputError(f"{p.pid}: arrival time cannot be negative.")
        if p.burst < 1:
            raise InputError(f"{p.pid}: burst time must be at least 1.")
        if p.priority < 0:
            raise InputError(f"{p.pid}: priority cannot be negative.")


def _merge(timeline):
    merged = []
    for name, s, e in timeline:
        if e <= s:
            continue
        if merged and merged[-1][0] == name and merged[-1][2] == s:
            merged[-1] = (name, merged[-1][1], e)
        else:
            merged.append((name, s, e))
    return merged


def _build_result(name, procs, timeline, completion) -> ScheduleResult:
    timeline = _merge(timeline)
    first_start: Dict[str, int] = {}
    for pid, s, _ in timeline:
        if pid != IDLE and pid not in first_start:
            first_start[pid] = s
    rows = []
    for p in procs:
        c = completion[p.pid]
        tat = c - p.arrival
        rows.append({
            "pid": p.pid, "arrival": p.arrival, "burst": p.burst,
            "priority": p.priority, "start": first_start[p.pid],
            "completion": c, "turnaround": tat, "waiting": tat - p.burst,
            "response": first_start[p.pid] - p.arrival,
        })
    n = len(procs)
    begin, end = timeline[0][1], timeline[-1][2]
    busy = sum(e - s for pid, s, e in timeline if pid != IDLE)
    span = max(end - begin, 1)
    switches = sum(1 for a, b in zip(timeline, timeline[1:])
                   if a[0] != IDLE and b[0] != IDLE and a[0] != b[0])
    return ScheduleResult(
        algorithm=name, timeline=timeline, rows=rows,
        avg_waiting=sum(r["waiting"] for r in rows) / n,
        avg_turnaround=sum(r["turnaround"] for r in rows) / n,
        avg_response=sum(r["response"] for r in rows) / n,
        cpu_utilization=100.0 * busy / span, throughput=n / span,
        context_switches=switches, start_time=begin, end_time=end)


def _arrival_order(procs):
    return sorted(range(len(procs)), key=lambda i: (procs[i].arrival, i))


def _nonpreemptive(name, procs, key):
    """Generic non-preemptive scheduler: when the CPU frees up, pick the ready
    process with the smallest ``key`` (ties: earlier arrival, then input order)."""
    n = len(procs)
    order = _arrival_order(procs)
    ptr, done = 0, 0
    time = procs[order[0]].arrival
    heap, timeline, completion = [], [], {}
    while done < n:
        while ptr < n and procs[order[ptr]].arrival <= time:
            i = order[ptr]
            heapq.heappush(heap, (key(procs[i]), procs[i].arrival, i))
            ptr += 1
        if not heap:                                  # CPU idle until next arrival
            nxt = procs[order[ptr]].arrival
            timeline.append((IDLE, time, nxt))
            time = nxt
            continue
        _, _, i = heapq.heappop(heap)
        p = procs[i]
        timeline.append((p.pid, time, time + p.burst))
        time += p.burst
        completion[p.pid] = time
        done += 1
    return _build_result(name, procs, timeline, completion)


def _preemptive(name, procs, key):
    """Event-driven preemptive scheduler.  ``key(p, remaining)`` is minimised.
    A running process can only be preempted when a new process arrives."""
    n = len(procs)
    order = _arrival_order(procs)
    rem = [p.burst for p in procs]
    ptr, done = 0, 0
    time = procs[order[0]].arrival
    heap, timeline, completion = [], [], {}
    while done < n:
        while ptr < n and procs[order[ptr]].arrival <= time:
            i = order[ptr]
            heapq.heappush(heap, (key(procs[i], rem[i]), procs[i].arrival, i))
            ptr += 1
        if not heap:
            nxt = procs[order[ptr]].arrival
            timeline.append((IDLE, time, nxt))
            time = nxt
            continue
        _, _, i = heapq.heappop(heap)
        next_arrival = procs[order[ptr]].arrival if ptr < n else float("inf")
        run = int(min(rem[i], next_arrival - time))
        timeline.append((procs[i].pid, time, time + run))
        time += run
        rem[i] -= run
        if rem[i] == 0:
            completion[procs[i].pid] = time
            done += 1
        else:
            heapq.heappush(heap, (key(procs[i], rem[i]), procs[i].arrival, i))
    return _build_result(name, procs, timeline, completion)


def round_robin(procs: List[Process], quantum: int) -> ScheduleResult:
    if quantum < 1:
        raise InputError("Round Robin: the time quantum must be at least 1.")
    n = len(procs)
    order = _arrival_order(procs)
    rem = [p.burst for p in procs]
    queue, timeline, completion = deque(), [], {}
    ptr, done = 0, 0
    time = procs[order[0]].arrival
    while done < n:
        while ptr < n and procs[order[ptr]].arrival <= time:
            queue.append(order[ptr]); ptr += 1
        if not queue:
            nxt = procs[order[ptr]].arrival
            timeline.append((IDLE, time, nxt)); time = nxt
            continue
        i = queue.popleft()
        run = min(quantum, rem[i])
        timeline.append((procs[i].pid, time, time + run))
        time += run
        rem[i] -= run
        # processes that arrived during this slice enter the queue BEFORE the preempted one
        while ptr < n and procs[order[ptr]].arrival <= time:
            queue.append(order[ptr]); ptr += 1
        if rem[i] > 0:
            queue.append(i)
        else:
            completion[procs[i].pid] = time
            done += 1
    return _build_result(f"Round Robin (q={quantum})", procs, timeline, completion)


def run_algorithm(name: str, procs: List[Process], quantum: int = 4,
                  lower_priority_is_higher: bool = True) -> ScheduleResult:
    validate_processes(procs)
    sign = 1 if lower_priority_is_higher else -1
    if name == "FCFS":
        return _nonpreemptive(name, procs, lambda p: 0)
    if name == "SJF (Non-Preemptive)":
        return _nonpreemptive(name, procs, lambda p: p.burst)
    if name == "SRTF (Preemptive SJF)":
        return _preemptive(name, procs, lambda p, r: r)
    if name == "Priority (Non-Preemptive)":
        return _nonpreemptive(name, procs, lambda p: sign * p.priority)
    if name == "Priority (Preemptive)":
        return _preemptive(name, procs, lambda p, r: sign * p.priority)
    if name == "Round Robin":
        return round_robin(procs, quantum)
    raise InputError(f"Unknown CPU scheduling algorithm: {name}")


# ============================================================================
# Program: CPU Scheduling
# ============================================================================
# CPU Scheduling - console version (FCFS, SJF, SRTF, Priority, Round Robin).

SAMPLE = [("P1", 0, 8, 3), ("P2", 1, 4, 1), ("P3", 2, 9, 4), ("P4", 3, 5, 2), ("P5", 4, 2, 5)]


def to_process(tok, n):
    if len(tok) not in (3, 4):
        raise InputError(f"Row {n}: expected 'ID arrival burst [priority]'.")
    return Process(tok[0], parse_int(tok[1], f"Row {n} arrival", 0),
                      parse_int(tok[2], f"Row {n} burst", 1),
                      parse_int(tok[3], f"Row {n} priority", 0) if len(tok) == 4 else 0)


def random_processes(n):
    return [Process(f"P{i + 1}", random.randint(0, max(5, n)), random.randint(1, 20),
                       random.randint(1, 10)) for i in range(n)]


def show(res, limit):
    banner(res.algorithm)
    print(f"Average waiting    = {res.avg_waiting:.2f}")
    print(f"Average turnaround = {res.avg_turnaround:.2f}")
    print(f"Average response   = {res.avg_response:.2f}")
    print(f"CPU utilization    = {res.cpu_utilization:.1f}%   Throughput = {res.throughput:.4f}"
          f"   Context switches = {res.context_switches}")
    print("\nGantt chart:")
    text_gantt(res.timeline)
    print()
    print_table(["Process", "Arrival", "Burst", "Priority", "Start", "Completion", "Turnaround",
                 "Waiting", "Response"],
                [[r["pid"], r["arrival"], r["burst"], r["priority"], r["start"], r["completion"],
                  r["turnaround"], r["waiting"], r["response"]] for r in res.rows], limit)


def main():
    banner("OPERATING SYSTEM SIMULATOR - CPU SCHEDULING")
    print("Turnaround = Completion - Arrival | Waiting = Turnaround - Burst | "
          "Response = First start - Arrival")
    while True:
        src = ask_source()
        if src == 3:
            print("Goodbye.")
            return
        if src == 0:
            procs = read_rows("Enter the processes", "ID arrival burst [priority]   e.g.  P1 0 8 3", to_process)
        elif src == 1:
            procs = [Process(*row) for row in SAMPLE]
        else:
            procs = random_processes(ask_int("How many processes", 1, 100000, 1000))
        algos = ask_multi("Algorithms to run", ALGORITHMS)
        quantum = ask_int("Time quantum (Round Robin)", 1, default=4) if "Round Robin" in algos else 4
        lower = ask_choice("Priority rule", ["Lower number = higher priority",
                                             "Higher number = higher priority"], 0) == 0
        try:
            results = [run_algorithm(a, procs, quantum, lower) for a in algos]
        except InputError as exc:
            print("  ! " + str(exc))
            continue
        limit = None if len(procs) <= 30 else 15
        for r in results:
            show(r, limit)
        banner(f"Comparison ({len(procs)} processes)")
        print_table(["Algorithm", "Avg Waiting", "Avg Turnaround", "Avg Response", "CPU Util %", "Ctx Switches"],
                    [[r.algorithm, f"{r.avg_waiting:.2f}", f"{r.avg_turnaround:.2f}", f"{r.avg_response:.2f}",
                      f"{r.cpu_utilization:.1f}", r.context_switches] for r in results])
        best = min(results, key=lambda r: r.avg_waiting)
        print(f"Lowest average waiting time: {best.algorithm} ({best.avg_waiting:.2f})")


if __name__ == "__main__":
    run(main)
