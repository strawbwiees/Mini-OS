"""Operating System Simulator (Python 3 + Tkinter, no extra dependencies).
Run:  python os_simulator.py
Modules: CPU Scheduling, Banker's, Paging, Page Replacement, Segmentation,
Fragmentation, Disk Scheduling, Multiprogramming.
Input is free-form text (one item per line / comma-separated), so there is
no fixed item limit. Invalid input shows an error message instead of crashing.
"""
import tkinter as tk
from tkinter import ttk, messagebox

SLATE, BLUSH, PINK, SOFT = "#6B717E", "#EFAAC4", "#FFC4D1", "#FFE8E1"


# ---------- helpers ----------
def lines(s):
    return [l.strip() for l in s.splitlines() if l.strip()]


def num(tok, name="value", lo=0, strict=False):
    try:
        v = int(tok)
    except (ValueError, TypeError):
        raise ValueError(f"'{tok}' is not a valid integer for {name}.")
    if v < lo or (strict and v == lo):
        raise ValueError(f"{name} must be {'>' if strict else '>='} {lo} (got {v}).")
    return v


def ints(s, name="values", lo=0):
    toks = s.replace(",", " ").split()
    if not toks:
        raise ValueError(f"Please enter {name}.")
    return [num(t, name, lo) for t in toks]


def matrix(s, name):
    rows = [ints(l, name) for l in lines(s)]
    if not rows:
        raise ValueError(f"Please enter the {name} matrix.")
    if len({len(r) for r in rows}) != 1:
        raise ValueError(f"Every row of {name} must have the same number of columns.")
    return rows


def table(headers, rows):
    rows = [[str(c) for c in r] for r in rows]
    w = [max(len(str(h)), *(len(r[i]) for r in rows)) if rows else len(str(h))
         for i, h in enumerate(headers)]
    f = lambda r: " | ".join(str(c).ljust(w[i]) for i, c in enumerate(r))
    return "\n".join([f(headers), "-+-".join("-" * x for x in w)] + [f(r) for r in rows])


# ---------- 1. CPU scheduling ----------
def cpu(f):
    procs = []
    for l in lines(f["procs"]):
        p = l.replace(",", " ").split()
        if len(p) not in (3, 4):
            raise ValueError(f"Line '{l}': use  PID arrival burst [priority]")
        procs.append((p[0], num(p[1], "arrival"), num(p[2], "burst", 0, True),
                      num(p[3], "priority") if len(p) == 4 else 0))
    if not procs:
        raise ValueError("Add at least one process.")
    if len({p[0] for p in procs}) != len(procs):
        raise ValueError("Process IDs must be unique.")
    algo, g, comp, t = f["algo"], [], {}, 0

    def add(pid, s, e):
        if g and g[-1][0] == pid and g[-1][2] == s:
            g[-1] = (pid, g[-1][1], e)
        else:
            g.append((pid, s, e))

    if algo in ("FCFS", "SJF (non-preemptive)", "Priority (lower = higher)"):
        left = sorted(procs, key=lambda p: p[1])
        key = {"FCFS": lambda p: 0, "SJF (non-preemptive)": lambda p: p[2]}.get(algo, lambda p: p[3])
        while left:
            ready = [p for p in left if p[1] <= t]
            if not ready:
                t = min(p[1] for p in left)
                continue
            p = min(ready, key=key)
            add(p[0], t, t + p[2]); t += p[2]; comp[p[0]] = t; left.remove(p)
    elif algo == "SRTF (preemptive SJF)":
        rem = {p[0]: p[2] for p in procs}; at = {p[0]: p[1] for p in procs}
        while rem:
            ready = [k for k in rem if at[k] <= t]
            if not ready:
                t = min(at[k] for k in rem); continue
            k = min(ready, key=lambda x: rem[x])
            nxt = [at[x] for x in rem if at[x] > t]
            d = min(rem[k], min(nxt) - t) if nxt else rem[k]
            add(k, t, t + d); t += d; rem[k] -= d
            if rem[k] == 0:
                del rem[k]; comp[k] = t
    else:  # Round Robin
        Q = num(f["q"], "time quantum", 0, True)
        ps = sorted(procs, key=lambda p: p[1]); n = len(ps); i = 0; qq = []
        rem = {p[0]: p[2] for p in ps}
        while i < n or qq:
            if not qq:
                t = max(t, ps[i][1])
            while i < n and ps[i][1] <= t:
                qq.append(ps[i]); i += 1
            p = qq.pop(0); d = min(Q, rem[p[0]])
            add(p[0], t, t + d); t += d; rem[p[0]] -= d
            while i < n and ps[i][1] <= t:
                qq.append(ps[i]); i += 1
            if rem[p[0]]:
                qq.append(p)
            else:
                comp[p[0]] = t
    rows, tw, tt = [], 0, 0
    for pid, a, b, pr in procs:
        ta = comp[pid] - a; wt = ta - b; tw += wt; tt += ta
        rows.append([pid, a, b, pr, comp[pid], ta, wt])
    n = len(procs)
    return ("Gantt: " + " ".join(f"[{p} {s}-{e}]" for p, s, e in g) + "\n\n" +
            table(["PID", "Arrival", "Burst", "Prio", "Completion", "Turnaround", "Waiting"], rows) +
            f"\n\nAverage waiting time    = {tw / n:.2f}\nAverage turnaround time = {tt / n:.2f}")


# ---------- 2. Banker's ----------
def banker(f):
    A, M, av = matrix(f["alloc"], "Allocation"), matrix(f["max"], "Max"), ints(f["avail"], "Available")
    if len(A) != len(M) or len(A[0]) != len(M[0]) or len(av) != len(A[0]):
        raise ValueError("Allocation, Max and Available must agree in processes/resources.")
    n, m = len(A), len(av)
    need = [[M[i][j] - A[i][j] for j in range(m)] for i in range(n)]
    if any(x < 0 for r in need for x in r):
        raise ValueError("Allocation cannot exceed Max for any process/resource.")
    work, done, seq, log = av[:], [False] * n, [], []
    while len(seq) < n:
        for i in range(n):
            if not done[i] and all(need[i][j] <= work[j] for j in range(m)):
                log.append(f"P{i}: Need {need[i]} <= Work {work} -> runs, releases {A[i]}")
                work = [work[j] + A[i][j] for j in range(m)]; done[i] = True; seq.append(i); break
        else:
            break
    out = table(["Process"] + [f"Need R{j}" for j in range(m)], [[f"P{i}"] + need[i] for i in range(n)])
    out += "\n\n" + "\n".join(log) + "\n\n"
    out += ("SAFE. Safe sequence: " + " -> ".join(f"P{i}" for i in seq)) if len(seq) == n else \
        "UNSAFE: no safe sequence exists (deadlock possible)."
    return out


# ---------- 3. Paging ----------
def paging(f):
    ps = num(f["ps"], "page size", 0, True)
    pt = [None if t == "-" else num(t, "frame number") for t in f["pt"].replace(",", " ").split()]
    if not pt:
        raise ValueError("Enter the page table (frame per page, '-' = not in memory).")
    rows = []
    for a in ints(f["addr"], "logical addresses"):
        p, o = divmod(a, ps)
        if p >= len(pt) or pt[p] is None:
            rows.append([a, p, o, "-", "PAGE FAULT / invalid page"])
        else:
            rows.append([a, p, o, pt[p], pt[p] * ps + o])
    return (table(["Page", "Frame"], [[i, "-" if x is None else x] for i, x in enumerate(pt)]) + "\n\n" +
            table(["Logical", "Page", "Offset", "Frame", "Physical"], rows))


# ---------- 4. Page replacement ----------
def replace(f):
    ref, nf = ints(f["ref"], "reference string"), num(f["frames"], "frames", 0, True)
    out = []
    for algo in (("FIFO", "LRU", "Optimal") if f["algo"] == "All" else (f["algo"],)):
        fr, rows, faults, last = [], [], 0, {}
        for i, p in enumerate(ref):
            hit = p in fr
            if not hit:
                faults += 1
                if len(fr) < nf:
                    fr.append(p)
                else:
                    if algo == "FIFO":
                        fr.pop(0); fr.append(p)
                    else:
                        if algo == "LRU":
                            v = min(fr, key=lambda x: last[x])
                        else:
                            v = max(fr, key=lambda x: ref.index(x, i + 1) if x in ref[i + 1:] else 10 ** 12)
                        fr[fr.index(v)] = p
            last[p] = i
            rows.append([i + 1, p, " ".join(map(str, fr)), "HIT" if hit else "FAULT"])
        out.append(f"=== {algo} ===\n" + table(["Step", "Page", "Frames", "Result"], rows) +
                   f"\nHits: {len(ref) - faults}  Faults: {faults}  Hit ratio: {(len(ref) - faults) / len(ref):.2%}")
    return "\n\n".join(out)


# ---------- 5. Segmentation ----------
def seg(f):
    segs = {}
    for l in lines(f["segs"]):
        p = l.replace(",", " ").split()
        if len(p) != 3:
            raise ValueError(f"Line '{l}': use  segment base limit")
        segs[num(p[0], "segment")] = (num(p[1], "base"), num(p[2], "limit", 0, True))
    if not segs:
        raise ValueError("Define at least one segment.")
    rows = []
    for l in lines(f["addr"]):
        p = l.replace(",", " ").split()
        if len(p) != 2:
            raise ValueError(f"Address '{l}': use  segment offset")
        s, o = num(p[0], "segment"), num(p[1], "offset")
        if s not in segs:
            rows.append([s, o, "-", "ERROR: segment does not exist"])
        elif o >= segs[s][1]:
            rows.append([s, o, "-", f"ERROR: offset out of range (limit {segs[s][1]})"])
        else:
            rows.append([s, o, segs[s][0] + o, "valid"])
    return (table(["Segment", "Base", "Limit"], [[k, *v] for k, v in sorted(segs.items())]) + "\n\n" +
            table(["Seg", "Offset", "Physical", "Status"], rows))


# ---------- 6. Fragmentation ----------
def frag(f):
    blocks, procs = ints(f["blocks"], "block sizes", 1), ints(f["procs"], "process sizes", 1)
    free, used, rows = blocks[:], [None] * len(blocks), []
    for i, p in enumerate(procs):
        c = [j for j in range(len(free)) if used[j] is None and free[j] >= p]
        if f["strat"] == "First Fit": j = c[0] if c else None
        elif f["strat"] == "Best Fit": j = min(c, key=lambda x: free[x]) if c else None
        else: j = max(c, key=lambda x: free[x]) if c else None
        if j is None:
            tot = sum(b for k, b in enumerate(blocks) if used[k] is None)
            rows.append([f"P{i + 1}", p, "-", "-", "External fragmentation (enough total free, not contiguous)" if tot >= p else "Not enough memory"])
        else:
            used[j] = i; rows.append([f"P{i + 1}", p, f"B{j + 1}", blocks[j] - p, "Allocated (internal frag.)"])
    internal = sum(r[3] for r in rows if r[2] != "-")
    ext = sum(b for k, b in enumerate(blocks) if used[k] is None)
    return (table(["Process", "Size", "Block", "Internal waste", "Status"], rows) +
            f"\n\nTotal internal fragmentation = {internal}\nTotal free (unused) blocks   = {ext}")


# ---------- 7. Disk scheduling ----------
def disk(f):
    size, head = num(f["size"], "disk size", 0, True), num(f["head"], "head position")
    r = ints(f["reqs"], "disk requests")
    if head >= size or any(x >= size for x in r):
        raise ValueError(f"Head and requests must be between 0 and {size - 1}.")
    right = f["dir"] == "Right"
    up = sorted(x for x in r if x >= head); dn = sorted((x for x in r if x < head), reverse=True)
    first, second = (up, dn) if right else (dn, up)
    e1, e2 = (size - 1, 0) if right else (0, size - 1)
    wrap = sorted(dn) if right else sorted(up, reverse=True)
    left, o, pos = r[:], [], head
    while left:
        x = min(left, key=lambda v: abs(v - pos)); left.remove(x); o.append(x); pos = x
    algos = {"FCFS": (r, [head] + r), "SSTF": (o, [head] + o),
             "SCAN": (first + second, [head] + first + [e1] + second),
             "C-SCAN": (first + wrap, [head] + first + [e1, e2] + wrap),
             "LOOK": (first + second, [head] + first + second),
             "C-LOOK": (first + wrap, [head] + first + wrap)}
    out, summ = [], []
    for k, (order, path) in algos.items():
        if f["algo"] not in ("All", k):
            continue
        mv = sum(abs(a - b) for a, b in zip(path, path[1:]))
        out.append(f"{k}: order = {order}\n   head path = {path}\n   total head movement = {mv}")
        summ.append([k, mv])
    return "\n\n".join(out) + "\n\n" + table(["Algorithm", "Total movement"], summ)


# ---------- 8. Multiprogramming ----------
def multi(f):
    total, osm, io = num(f["mem"], "total memory", 0, True), num(f["os"], "OS memory"), num(f["io"], "I/O wait %")
    if io > 100 or osm >= total:
        raise ValueError("I/O wait must be 0-100 and OS memory must be less than total memory.")
    free, rows, n = total - osm, [], 0
    for l in lines(f["progs"]):
        p = l.replace(",", " ").split()
        if len(p) != 2:
            raise ValueError(f"Line '{l}': use  name memory")
        m = num(p[1], "memory", 0, True)
        if m <= free:
            free -= m; n += 1; rows.append([p[0], m, "RUNNING (in memory)"])
        else:
            rows.append([p[0], m, "WAITING (job queue)"])
    cpu_u = 1 - (io / 100) ** n if n else 0
    bar = lambda v: "#" * int(v * 30) + "." * (30 - int(v * 30))
    used = (total - free) / total
    return (table(["Program", "Memory", "State"], rows) +
            f"\n\nDegree of multiprogramming : {n}\nMemory used : {total - free}/{total}  [{bar(used)}] {used:.1%}"
            f"\nCPU utilization = 1 - p^n = {cpu_u:.1%}  [{bar(cpu_u)}]")


# ---------- GUI (layout: sidebar | INPUT + ALGORITHM | RESULTS) ----------
E, T, C = "entry", "text", "combo"
DISKS = ["All", "FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK", "C-LOOK"]
# (name, function, input fields, algorithm-panel fields, description)
MODULES = [
    ("CPU Scheduling", cpu,
     [("procs", "Processes (PID arrival burst [priority]) - one per line", T, "P1 0 5 2\nP2 1 3 1\nP3 2 8 4\nP4 3 6 3", None)],
     [("algo", "Algorithm", C, "FCFS", ["FCFS", "SJF (non-preemptive)", "SRTF (preemptive SJF)", "Priority (lower = higher)", "Round Robin"]),
      ("q", "Time quantum (Round Robin)", E, "2", None)],
     "Shows the Gantt chart, completion, turnaround and waiting times, plus averages."),
    ("Banker's Algorithm", banker,
     [("alloc", "Allocation matrix (row per process)", T, "0 1 0\n2 0 0\n3 0 2\n2 1 1\n0 0 2", None),
      ("max", "Max matrix", T, "7 5 3\n3 2 2\n9 0 2\n2 2 2\n4 3 3", None),
      ("avail", "Available resources", E, "3 3 2", None)], [],
     "Computes Need = Max - Allocation, runs the safety check and prints a safe sequence if one exists."),
    ("Paging", paging,
     [("ps", "Page size", E, "1024", None), ("pt", "Page table (frame per page, '-' = absent)", E, "5 2 - 7 0", None),
      ("addr", "Logical addresses", E, "100 1500 2100 3500 4200 9000", None)], [],
     "Maps each logical address to page + offset, then to a physical address through the page table."),
    ("Page Replacement", replace,
     [("ref", "Reference string", E, "7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1", None), ("frames", "Number of frames", E, "3", None)],
     [("algo", "Algorithm", C, "All", ["All", "FIFO", "LRU", "Optimal"])],
     "Shows frame contents per step, hits, faults and hit ratio."),
    ("Segmentation", seg,
     [("segs", "Segments (id base limit)", T, "0 1400 1000\n1 6300 400\n2 4300 400\n3 3200 1100", None),
      ("addr", "Addresses (segment offset)", T, "0 999\n1 500\n2 100\n3 1200\n5 10", None)], [],
     "Validates offset < limit, then physical = base + offset; otherwise reports an out-of-range error."),
    ("Fragmentation", frag,
     [("blocks", "Memory blocks", E, "100 500 200 300 600", None), ("procs", "Process sizes", E, "212 417 112 426", None)],
     [("strat", "Strategy", C, "First Fit", ["First Fit", "Best Fit", "Worst Fit"])],
     "Allocates processes to blocks and reports internal and external fragmentation."),
    ("Disk Scheduling", disk,
     [("size", "Disk size (cylinders)", E, "200", None), ("head", "Initial head position", E, "53", None),
      ("reqs", "Requests", E, "98 183 37 122 14 124 65 67", None)],
     [("algo", "Algorithm", C, "All", DISKS), ("dir", "Direction", C, "Right", ["Right", "Left"])],
     "Shows service order, head path and total head movement."),
    ("Multiprogramming", multi,
     [("mem", "Total memory", E, "1024", None), ("os", "OS reserved memory", E, "128", None),
      ("io", "I/O wait % per process", E, "60", None), ("progs", "Programs (name memory)", T, "A 200\nB 300\nC 250\nD 400\nE 100", None)], [],
     "Admits programs while memory lasts; shows degree of multiprogramming, memory and CPU utilization."),
]


def panel(parent, title):
    outer = tk.Frame(parent, bg="white", highlightthickness=2, highlightbackground=SLATE)
    tk.Label(outer, text=title, bg=BLUSH, fg=SLATE, anchor="w", padx=10, pady=4,
             font=("Segoe UI", 11, "bold")).pack(fill="x")
    body = tk.Frame(outer, bg="white"); body.pack(fill="both", expand=True)
    return outer, body


class Module(tk.Frame):
    def __init__(self, parent, name, fn, inputs, algos, desc):
        super().__init__(parent, bg="white")
        self.fn, self.w = fn, {}
        tk.Label(self, text=name.upper(), bg="white", fg=SLATE, font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 6))
        io, ib = panel(self, "INPUT"); io.grid(row=1, column=0, sticky="nsew", padx=(14, 6))
        ao, ab = panel(self, "ALGORITHM"); ao.grid(row=1, column=1, sticky="nsew", padx=(6, 14))
        ro, rb = panel(self, "RESULTS"); ro.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=14, pady=10)
        self.columnconfigure(0, weight=3); self.columnconfigure(1, weight=1, minsize=270)
        self.rowconfigure(1, weight=2); self.rowconfigure(2, weight=3)
        for spec, host, horiz in ((inputs, ib, True), (algos, ab, False)):
            for key, label, kind, default, opts in spec:
                col = tk.Frame(host, bg="white")
                col.pack(side="left" if horiz else "top", fill="both" if horiz else "x", expand=horiz, padx=8, pady=6)
                tk.Label(col, text=label, bg="white", fg=SLATE, anchor="w", font=("Segoe UI", 9, "bold")).pack(fill="x")
                if kind == T:
                    w = tk.Text(col, width=24, height=6, relief="flat", highlightthickness=1, highlightbackground=BLUSH)
                    w.insert("1.0", default); w.pack(fill="both", expand=True)
                elif kind == C:
                    w = ttk.Combobox(col, values=opts, state="readonly"); w.set(default); w.pack(fill="x")
                else:
                    w = tk.Entry(col, relief="flat", highlightthickness=1, highlightbackground=BLUSH)
                    w.insert(0, default); w.pack(fill="x")
                self.w[key] = (w, kind)
        tk.Label(ab, text=desc, bg="white", fg=SLATE, wraplength=240, justify="left", font=("Segoe UI", 9)).pack(
            side="top", fill="x", padx=8, pady=6)
        bf = tk.Frame(ab, bg="white"); bf.pack(side="bottom", fill="x", padx=8, pady=8)
        tk.Button(bf, text="RUN", command=self.run, bg=SLATE, fg="white", relief="flat", padx=18, pady=4,
                  font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        tk.Button(bf, text="CLEAR", command=lambda: self.out.delete("1.0", "end"), bg=BLUSH, fg=SLATE,
                  relief="flat", padx=14, pady=4, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.out = tk.Text(rb, font=("Consolas", 10), bg="white", fg=SLATE, relief="flat", wrap="none", height=8)
        sy, sx = ttk.Scrollbar(rb, command=self.out.yview), ttk.Scrollbar(rb, orient="horizontal", command=self.out.xview)
        self.out.config(yscrollcommand=sy.set, xscrollcommand=sx.set)
        rb.rowconfigure(0, weight=1); rb.columnconfigure(0, weight=1)
        self.out.grid(row=0, column=0, sticky="nsew"); sy.grid(row=0, column=1, sticky="ns"); sx.grid(row=1, column=0, sticky="ew")

    def get(self):
        return {k: (w.get("1.0", "end") if t == T else w.get()) for k, (w, t) in self.w.items()}

    def run(self):
        try:
            res = self.fn(self.get())
        except ValueError as e:
            return messagebox.showerror("Invalid input", str(e))
        except Exception as e:
            return messagebox.showerror("Error", f"Could not process input: {e}")
        self.out.delete("1.0", "end"); self.out.insert("1.0", res)


def main():
    root = tk.Tk(); root.title("Mini Operating System"); root.geometry("1180x720"); root.configure(bg=PINK)
    ttk.Style().theme_use("clam")
    tk.Label(root, text="Mini Operating System", bg=SLATE, fg="white", anchor="w", padx=24, pady=14,
             font=("Segoe UI", 20, "bold")).pack(fill="x", padx=14, pady=(14, 0))
    body = tk.Frame(root, bg=SOFT); body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
    side = tk.Frame(body, bg=SOFT, width=220); side.pack(side="left", fill="y"); side.pack_propagate(False)
    card = tk.Frame(body, bg=SOFT); card.pack(side="left", fill="both", expand=True, padx=8, pady=8)
    card.rowconfigure(0, weight=1); card.columnconfigure(0, weight=1)
    mods, btns = {}, {}

    def show(name):
        mods[name].tkraise()
        for n, b in btns.items():
            b.config(bg=SLATE if n == name else PINK, fg="white" if n == name else SLATE)

    for name, fn, inputs, algos, desc in MODULES:
        m = Module(card, name, fn, inputs, algos, desc); m.grid(row=0, column=0, sticky="nsew"); mods[name] = m
        b = tk.Button(side, text=name.upper(), command=lambda n=name: show(n), relief="flat", bg=PINK, fg=SLATE,
                      font=("Segoe UI", 9, "bold"), pady=9, bd=0)
        b.pack(fill="x", padx=12, pady=(12 if not btns else 4, 4)); btns[name] = b
    show(MODULES[0][0]); root.mainloop()


if __name__ == "__main__":
    main()