"""The eight simulator pages.  Each page reads its inputs, calls the matching
algorithm module from the zip (see engine.py) and draws the results."""
from __future__ import annotations

import random
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFrame,
                               QHBoxLayout, QHeaderView, QLineEdit,
                               QMessageBox, QPlainTextEdit, QPushButton,
                               QScrollArea, QSpinBox, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

import bankersAlgorithm
import cpuScheduling
import diskScheduling
import fragmentation
import multiprogramming
import pageReplacement
import paging
import segmentation

INPUT_ERRORS = tuple(m.InputError for m in (cpuScheduling, bankersAlgorithm, paging, pageReplacement,
                     segmentation, fragmentation, diskScheduling, multiprogramming))

from widgets import (BAD_BG, OS_COLOR, ColorMap, BlockStrip, Card,
                     GanttChart, PathChart, RowTable, badge, button_row, form,
                     hint, hscroll, label, make_table, section, tiles)

BEST = "#DDF5E6"


def f2(x: float) -> str:
    return f"{x:.2f}"


def spin(lo: int, hi: int, value: int) -> QSpinBox:
    box = QSpinBox()
    box.setRange(lo, hi)
    box.setValue(value)
    return box


def line(text: str = "", placeholder: str = "") -> QLineEdit:
    box = QLineEdit(text)
    box.setPlaceholderText(placeholder)
    return box


def nums(values) -> str:
    return " ".join(str(v) for v in values)


# ==========================================================================
# Base page
# ==========================================================================
class ModulePage(QWidget):
    """Title + (Input card | Options card) + Results card, inside a scroll area."""

    status = Signal(str, bool)          # (message, is_error) -> footer bar

    title = ""
    subtitle = ""
    input_title = "Input"
    options_title = "Options"
    idle_text = "Run a simulation to see the results here."

    def __init__(self):
        super().__init__()
        self._slots = []                # keep guarded callbacks alive
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 16, 16, 12)
        root.setSpacing(2)
        root.addWidget(label(self.title, "moduleTitleLabel"))
        root.addWidget(label(self.subtitle, "moduleSubtitleLabel"))

        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        host.setObjectName("pageHost")
        col = QVBoxLayout(host)
        col.setContentsMargins(0, 10, 8, 6)
        col.setSpacing(14)

        upper = QHBoxLayout()
        upper.setSpacing(14)
        self.input_card = Card(self.input_title)
        self.option_card = Card(self.options_title)
        upper.addWidget(self.input_card, 3)
        upper.addWidget(self.option_card, 2)
        col.addLayout(upper)
        self.results_card = Card("Results")
        col.addWidget(self.results_card)
        col.addStretch(1)
        scroll.setWidget(host)
        scroll.viewport().setAutoFillBackground(False)
        root.addWidget(scroll, 1)

        self.build_inputs(self.input_card.body)
        self.build_options(self.option_card.body)
        self.option_card.body.addStretch(1)
        self.show_idle()

    # -- hooks ----------------------------------------------------------------
    def build_inputs(self, body):      # pragma: no cover - overridden
        raise NotImplementedError

    def build_options(self, body):     # pragma: no cover - overridden
        raise NotImplementedError

    def run(self):                     # pragma: no cover - overridden
        raise NotImplementedError

    # -- helpers --------------------------------------------------------------
    def action(self, text: str, fn, kind: str = "secondaryButton") -> QPushButton:
        """Create a button whose click runs ``fn`` with friendly error handling."""
        def slot(*_args):
            try:
                fn()
            except INPUT_ERRORS as exc:
                self.fail("Please check your input", str(exc), True)
            except Exception as exc:    # never let a bug close the window
                self.fail("Something went wrong", f"{type(exc).__name__}: {exc}", False)
        self._slots.append(slot)
        btn = QPushButton(text)
        btn.setObjectName(kind)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    def run_button(self, text: str = "Run Simulation") -> QPushButton:
        return self.action(text, self.run, "btnRunSimulation")

    def fail(self, title: str, message: str, is_input_error: bool) -> None:
        box = QMessageBox.warning if is_input_error else QMessageBox.critical
        box(self, title, message)
        self.status.emit((message.splitlines() or [title])[0], True)

    def ok(self, message: str) -> None:
        self.status.emit(message, False)

    def clear_results(self) -> None:
        lay = self.results_card.body
        while lay.count():
            item = lay.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def show_idle(self) -> None:
        self.clear_results()
        self.add(hint(self.idle_text))

    def add(self, widget: QWidget) -> None:
        self.results_card.body.addWidget(widget)


# ==========================================================================
# 1. CPU Scheduling
# ==========================================================================
class CpuPage(ModulePage):
    title = "CPU Scheduling"
    subtitle = "Choose an algorithm and simulate the scheduling process."
    input_title = "Process Input"
    options_title = "Algorithm"

    def build_inputs(self, body):
        self.table = RowTable(["Process ID", "Arrival Time", "Burst Time", "Priority (Optional)"],
                              ["", "0", "1", "1"], prefix="P", start=1, add_text="+  Add Process")
        self.table.set_rows([("P1", 0, 7, 1), ("P2", 1, 4, 2), ("P3", 2, 1, 3)])
        body.addWidget(self.table)

    def build_options(self, body):
        self.algo = QComboBox()
        self.algo.addItems(cpu.ALGORITHMS)
        self.algo.setCurrentText("Round Robin")
        self.quantum = spin(1, 1000, 2)
        self.low_first = QCheckBox("Lower number = higher priority")
        self.low_first.setChecked(True)
        form(body, [("Algorithm", self.algo), ("Time Quantum", self.quantum)])
        body.addWidget(self.low_first)
        self.algo.currentTextChanged.connect(self.sync)
        self.sync()
        body.addWidget(self.run_button())
        body.addWidget(button_row(self.action("Load Sample", self.load_sample),
                                  self.action("Random", self.randomize),
                                  self.action("Compare All", self.compare_all)))

    def sync(self, *_):
        name = self.algo.currentText()
        self.quantum.setEnabled(name == "Round Robin")
        self.low_first.setEnabled(name.startswith("Priority"))

    def load_sample(self):
        self.table.set_rows(cpu.SAMPLE)

    def randomize(self):
        self.table.set_rows([(p.pid, p.arrival, p.burst, p.priority)
                             for p in cpu.random_processes(5)])

    def read_processes(self):
        procs = []
        for n, row in enumerate(self.table.rows(), 1):
            pid = row[0].strip()
            if not pid:
                raise cpu.InputError(f"Row {n}: the process ID is blank.")
            procs.append(cpu.Process(
                pid,
                cpu.parse_int(row[1], f"{pid} arrival time", 0),
                cpu.parse_int(row[2], f"{pid} burst time", 1),
                cpu.parse_int(row[3], f"{pid} priority", 0) if row[3].strip() else 0))
        return procs

    def schedule(self, name):
        return cpu.run_algorithm(name, self.read_processes(), self.quantum.value(),
                                 self.low_first.isChecked())

    def run(self):
        res = self.schedule(self.algo.currentText())
        self.clear_results()
        colors = ColorMap({cpu.IDLE: "#E6E1F5"})
        chart = GanttChart()
        chart.set_segments(res.timeline, colors)
        self.add(section(f"Gantt Chart  -  {res.algorithm}"))
        self.add(hscroll(chart, 90))
        rows = [[r["pid"], r["arrival"], r["burst"], r["waiting"], r["turnaround"], r["response"]]
                for r in res.rows]
        rows.append(["Average", "", "", f2(res.avg_waiting), f2(res.avg_turnaround),
                     f2(res.avg_response)])
        cell = {(i, 0): colors.get(r["pid"]) for i, r in enumerate(res.rows)}
        self.add(section("Summary"))
        self.add(make_table(["Process", "Arrival", "Burst", "Waiting Time", "Turnaround Time",
                             "Response Time"], rows, cell_colors=cell, highlight_last=True))
        self.add(tiles([("CPU Utilization", f"{res.cpu_utilization:.1f}%"),
                        ("Throughput", f"{res.throughput:.3f} /unit"),
                        ("Context Switches", res.context_switches),
                        ("Finished at", f"t = {res.end_time}")]))
        self.ok(f"Simulation complete: {res.algorithm}")

    def compare_all(self):
        procs = self.read_processes()
        results = [cpu.run_algorithm(n, procs, self.quantum.value(), self.low_first.isChecked())
                   for n in cpu.ALGORITHMS]
        best = min(r.avg_waiting for r in results)
        rows = [[r.algorithm, f2(r.avg_waiting), f2(r.avg_turnaround), f2(r.avg_response),
                 f"{r.cpu_utilization:.1f}%", r.context_switches] for r in results]
        colors = [BEST if r.avg_waiting == best else None for r in results]
        self.clear_results()
        self.add(section("Comparison of all algorithms"))
        self.add(make_table(["Algorithm", "Avg Waiting", "Avg Turnaround", "Avg Response",
                             "CPU Util.", "Ctx Switches"], rows, colors=colors))
        self.add(hint("Green row = lowest average waiting time."))
        self.ok("Compared all CPU scheduling algorithms")


# ==========================================================================
# 2. Banker's Algorithm
# ==========================================================================
class BankersPage(ModulePage):
    title = "Banker's Algorithm"
    subtitle = "Check whether the system is in a safe state and test resource requests."
    input_title = "Allocation & Maximum Matrices"
    options_title = "System"

    def build_inputs(self, body):
        self.table = RowTable(["Process", "Allocation (A B C ...)", "Maximum (A B C ...)"],
                              ["", "0 0 0", "0 0 0"], prefix="P", start=0, add_text="+  Add Process")
        body.addWidget(self.table)
        body.addWidget(hint("One number per resource type, separated by spaces."))

    def build_options(self, body):
        self.available = line(placeholder="e.g. 3 3 2")
        form(body, [("Available resources", self.available)])
        body.addWidget(self.run_button("Check Safety"))
        body.addWidget(section("Resource request"))
        self.req_proc = line(placeholder="Process, e.g. P1")
        self.req_vec = line(placeholder="Request, e.g. 1 0 2")
        form(body, [("Process", self.req_proc), ("Request", self.req_vec)])
        body.addWidget(self.action("Check Request", self.check_request))
        body.addWidget(button_row(self.action("Load Sample", self.load_sample),
                                  self.action("Random Safe System", self.randomize)))
        self.load_sample()

    def load_sample(self):
        self.table.set_rows([(f"P{i}", nums(a), nums(m)) for i, (a, m) in
                             enumerate(zip(bankers.SAMPLE_ALLOC, bankers.SAMPLE_MAX))])
        self.available.setText(nums(bankers.SAMPLE_AVAIL))
        self.req_proc.setText("P1")
        self.req_vec.setText("1 0 2")

    def randomize(self):
        names, avail, alloc, mx = bankers.generate_safe_system(5, 3)
        self.table.set_rows([(n, nums(a), nums(m)) for n, a, m in zip(names, alloc, mx)])
        self.available.setText(nums(avail))

    def read_system(self):
        names, alloc, mx = [], [], []
        for n, row in enumerate(self.table.rows(), 1):
            name = row[0].strip()
            if not name:
                raise bankers.InputError(f"Row {n}: the process name is blank.")
            names.append(name)
            alloc.append(bankers.parse_int_list(row[1], f"{name} Allocation", 0))
            mx.append(bankers.parse_int_list(row[2], f"{name} Maximum", 0))
        avail = bankers.parse_int_list(self.available.text(), "Available", 0)
        return names, avail, alloc, mx

    def render_safety(self, res, alloc=None, mx=None):
        letters = bankers.resource_names(len(res.need[0])) if res.need else []
        if res.safe:
            self.add(badge("SAFE STATE  -  safe sequence:  " + "  \u2192  ".join(res.sequence), "ok"))
        else:
            self.add(badge("UNSAFE STATE  -  these processes can never finish: "
                           + ", ".join(res.stuck), "bad"))
        self.add(hint("Resource order: " + " ".join(letters)))
        if alloc is not None:
            rows = [[n, nums(a), nums(m), nums(nd)]
                    for n, a, m, nd in zip(res.names, alloc, mx, res.need)]
            self.add(make_table(["Process", "Allocation", "Maximum", "Need"], rows))
        else:
            self.add(make_table(["Process", "Need (after the request)"],
                                [[n, nums(nd)] for n, nd in zip(res.names, res.need)]))
        if res.steps:
            self.add(section("Safety algorithm steps"))
            rows = [[i, s.process, nums(s.work_before), nums(s.need), nums(s.work_after)]
                    for i, s in enumerate(res.steps, 1)]
            self.add(make_table(["Step", "Process", "Work (before)", "Need", "Work (after)"], rows))

    def run(self):
        names, avail, alloc, mx = self.read_system()
        res = bankers.analyse(names, avail, alloc, mx)
        self.clear_results()
        self.render_safety(res, alloc, mx)
        self.ok("System is SAFE" if res.safe else "System is UNSAFE")

    def check_request(self):
        names, avail, alloc, mx = self.read_system()
        who = self.req_proc.text().strip()
        if who not in names:
            raise bankers.InputError(f"Request: '{who}' is not one of the processes {names}.")
        vec = bankers.parse_int_list(self.req_vec.text(), "Request", 0)
        out = bankers.resource_request(names, names.index(who), vec, avail, alloc, mx)
        self.clear_results()
        self.add(badge(out["message"], "ok" if out["granted"] else "bad"))
        if out["result"] is not None:
            self.render_safety(out["result"])
        self.ok("Request granted" if out["granted"] else "Request denied")


# ==========================================================================
# 3. Paging
# ==========================================================================
class PagingPage(ModulePage):
    title = "Paging"
    subtitle = "Load processes into frames and translate logical addresses."
    input_title = "Processes & Addresses"
    options_title = "Memory"

    def build_inputs(self, body):
        body.addWidget(section("Processes"))
        self.procs = RowTable(["Process", "Size (bytes)"], ["", "1024"], prefix="P", start=1,
                              add_text="+  Add Process", min_height=150)
        body.addWidget(self.procs)
        body.addWidget(section("Logical addresses to translate"))
        self.addrs = RowTable(["Process", "Logical Address"], ["P1", "0"],
                              add_text="+  Add Address", min_height=150)
        body.addWidget(self.addrs)

    def build_options(self, body):
        self.page_size = spin(1, 1_048_576, 1024)
        self.frames = spin(1, 4096, 16)
        self.os_frames = spin(0, 4096, 2)
        self.mode = QComboBox()
        self.mode.addItems([paging.SEQUENTIAL, paging.SCATTERED])
        form(body, [("Page / frame size (bytes)", self.page_size),
                    ("Total frames", self.frames),
                    ("Frames reserved for the OS", self.os_frames),
                    ("Frame allocation", self.mode)])
        body.addWidget(self.run_button("Allocate & Translate"))
        body.addWidget(self.action("Load Sample", self.load_sample))
        self.load_sample()

    def load_sample(self):
        self.procs.set_rows(paging.SAMPLE_PROCS)
        self.addrs.set_rows(paging.SAMPLE_ADDR)

    def run(self):
        procs = [(r[0].strip(), paging.parse_int(r[1], f"{r[0].strip() or 'row'} size", 1))
                 for r in self.procs.rows()]
        addrs = [(r[0].strip(), paging.parse_int(r[1], "Logical address")) for r in self.addrs.rows()]
        state = paging.allocate_memory(self.page_size.value(), self.frames.value(),
                                       self.os_frames.value(), procs, self.mode.currentText())
        results = [paging.translate(state, name, a) for name, a in addrs]
        colors = ColorMap()
        self.clear_results()

        loaded = [r for r in state.rows if r["status"] == "LOADED"]
        free = sum(1 for e in state.frame_table if e is None)
        self.add(tiles([("Processes loaded", f"{len(loaded)} / {len(state.rows)}"),
                        ("Free frames", free),
                        ("Internal fragmentation", f"{sum(r['internal'] for r in loaded)} bytes")],
                       columns=3))
        self.add(section("Physical memory (frames)"))
        blocks = []
        for fr, entry in enumerate(state.frame_table):
            if entry is None:
                blocks.append(dict(label="free", caption=f"F{fr}", weight=1, color=None))
            elif entry[0] == "OS":
                blocks.append(dict(label="OS", caption=f"F{fr}", weight=1, color=OS_COLOR))
            else:
                blocks.append(dict(label=entry[0], caption=f"F{fr} \u00b7 pg {entry[1]}",
                                   weight=1, color=colors.get(entry[0])))
        strip = BlockStrip()
        strip.set_blocks(blocks)
        self.add(hscroll(strip, 74))

        self.add(section("Processes"))
        rows = [[r["name"], r["size"], r["pages"], r["internal"], r["status"]] for r in state.rows]
        shade = [None if r["status"] == "LOADED" else BAD_BG for r in state.rows]
        self.add(make_table(["Process", "Size", "Pages", "Internal Frag.", "Status"], rows, colors=shade))

        if state.page_tables:
            self.add(section("Page tables  (page \u2192 frame)"))
            rows = [[n, ",  ".join(f"{pg}\u2192{fr}" for pg, fr in enumerate(fl))]
                    for n, fl in state.page_tables.items()]
            self.add(make_table(["Process", "Page table"], rows))

        if results:
            self.add(section("Address translation"))
            rows, shade = [], []
            for t in results:
                dash = lambda v: "\u2014" if v is None else v
                rows.append([t["process"], t["logical"], dash(t["page"]), dash(t["offset"]),
                             dash(t["frame"]), dash(t["physical"]),
                             t["calc"] if t["ok"] else t["message"]])
                shade.append(None if t["ok"] else BAD_BG)
            self.add(make_table(["Process", "Logical", "Page", "Offset", "Frame", "Physical",
                                 "Calculation / Result"], rows, colors=shade))
        self.ok(f"Paging complete: {len(loaded)} process(es) loaded")


# ==========================================================================
# 4. Page Replacement
# ==========================================================================
class ReplacementPage(ModulePage):
    title = "Page Replacement"
    subtitle = "Compare FIFO, LRU, Optimal and Second Chance on a reference string."
    input_title = "Reference String"
    options_title = "Algorithm"

    def build_inputs(self, body):
        self.refs = line(nums(replacement.SAMPLE))
        self.frames = spin(1, 50, 3)
        form(body, [("Page reference string", self.refs), ("Number of frames", self.frames)])
        body.addWidget(hint("Separate page numbers with spaces or commas."))
        body.addStretch(1)

    def build_options(self, body):
        self.algo = QComboBox()
        self.algo.addItems(replacement.ALGORITHMS)
        form(body, [("Algorithm", self.algo)])
        body.addWidget(self.run_button())
        body.addWidget(button_row(self.action("Load Sample", self.load_sample),
                                  self.action("Random", self.randomize),
                                  self.action("Compare All", self.compare_all)))

    def load_sample(self):
        self.refs.setText(nums(replacement.SAMPLE))
        self.frames.setValue(3)

    def randomize(self):
        self.refs.setText(nums(random.randint(0, 9) for _ in range(20)))

    def read(self):
        return (replacement.parse_int_list(self.refs.text(), "Reference string", 0),
                self.frames.value())

    def run(self):
        refs, frames = self.read()
        res = replacement.run_algorithm(self.algo.currentText(), refs, frames)
        self.clear_results()
        self.add(section(f"{res.algorithm}  -  {frames} frame(s)"))
        self.add(self.step_table(res))
        self.add(tiles([("Page faults", res.faults), ("Page hits", res.hits),
                        ("Fault ratio", f"{res.fault_ratio * 100:.1f}%"),
                        ("Hit ratio", f"{res.hit_ratio * 100:.1f}%")]))
        self.add(hint("Pink = page fault (page loaded), green = hit."))
        self.ok(f"{res.algorithm}: {res.faults} page fault(s)")

    def step_table(self, res):
        n, rows = len(res.steps), res.frame_count + 2
        t = QTableWidget(rows, n)
        t.setHorizontalHeaderLabels([str(s.page) for s in res.steps])
        t.setVerticalHeaderLabels([f"Frame {i + 1}" for i in range(res.frame_count)]
                                  + ["Result", "Replaced"])
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        hdr.setDefaultSectionSize(42)
        hdr.setFixedHeight(34)
        t.verticalHeader().setDefaultSectionSize(30)

        def put(r, c, text, colour=None):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if colour:
                item.setBackground(QBrush(QColor(colour)))
            t.setItem(r, c, item)

        for c, step in enumerate(res.steps):
            for r, page in enumerate(step.frames):
                mark = None
                if page == step.page:
                    mark = BEST if step.hit else "#F7B8CB"
                put(r, c, "" if page is None else str(page), mark)
            put(res.frame_count, c, "H" if step.hit else "F", BEST if step.hit else "#F7B8CB")
            put(res.frame_count + 1, c, "" if step.victim is None else str(step.victim))
        t.setFixedHeight(34 + 30 * rows + 22)
        return t

    def compare_all(self):
        refs, frames = self.read()
        results = [replacement.run_algorithm(n, refs, frames) for n in replacement.ALGORITHMS]
        best = min(r.faults for r in results)
        rows = [[r.algorithm, r.faults, r.hits, f"{r.fault_ratio * 100:.1f}%",
                 f"{r.hit_ratio * 100:.1f}%"] for r in results]
        self.clear_results()
        self.add(section(f"All algorithms  -  {frames} frame(s), {len(refs)} references"))
        self.add(make_table(["Algorithm", "Page Faults", "Hits", "Fault Ratio", "Hit Ratio"], rows,
                            colors=[BEST if r.faults == best else None for r in results]))
        self.add(hint("Green row = fewest page faults."))
        self.ok("Compared all page replacement algorithms")


# ==========================================================================
# 5. Segmentation
# ==========================================================================
class SegmentationPage(ModulePage):
    title = "Segmentation"
    subtitle = "Build a segment table and translate (segment, offset) addresses."
    input_title = "Segment Table & Requests"
    options_title = "Translate"

    def build_inputs(self, body):
        body.addWidget(section("Segment table"))
        self.segs = RowTable(["Segment #", "Base", "Limit"], ["0", "0", "100"], prefix="", start=0,
                             add_text="+  Add Segment", min_height=150)
        body.addWidget(self.segs)
        body.addWidget(section("Logical addresses (segment, offset)"))
        self.reqs = RowTable(["Segment #", "Offset"], ["0", "0"], add_text="+  Add Address",
                             min_height=150)
        body.addWidget(self.reqs)

    def build_options(self, body):
        body.addWidget(hint("An address is valid when the segment exists and 0 \u2264 offset < limit. "
                            "Physical address = base + offset; otherwise the hardware traps."))
        body.addWidget(self.run_button("Translate Addresses"))
        body.addWidget(self.action("Load Sample", self.load_sample))
        self.load_sample()

    def load_sample(self):
        self.segs.set_rows(segmentation.SAMPLE_SEGS)
        self.reqs.set_rows(segmentation.SAMPLE_REQS)

    def run(self):
        P = segmentation.parse_int
        segs = [segmentation.Segment(P(r[0], "Segment number", 0), P(r[1], "Base", 0),
                                     P(r[2], "Limit", 1)) for r in self.segs.rows()]
        reqs = [(P(r[0], "Request segment"), P(r[1], "Request offset")) for r in self.reqs.rows()]
        warnings = segmentation.validate_segments(segs)
        results = segmentation.translate_all(segs, reqs)
        colors = ColorMap()
        self.clear_results()
        for w in warnings:
            self.add(badge("Warning: " + w, "bad"))

        self.add(section("Physical memory map"))
        blocks, cursor = [], 0
        for s in sorted(segs, key=lambda s: (s.base, s.seg_id)):
            if s.base > cursor:
                blocks.append(dict(label="free", caption=f"{cursor}\u2013{s.base - 1}",
                                   weight=s.base - cursor, color=None))
            blocks.append(dict(label=f"Seg {s.seg_id}", caption=f"{s.base}\u2013{s.end}",
                               weight=s.limit, color=colors.get(s.seg_id)))
            cursor = max(cursor, s.end + 1)
        strip = BlockStrip()
        strip.set_blocks(blocks)
        self.add(hscroll(strip, 74))

        self.add(section("Segment table"))
        self.add(make_table(["Segment", "Base", "Limit", "Last address"],
                            [[s.seg_id, s.base, s.limit, s.end] for s in segs]))
        if results:
            self.add(section("Address translation"))
            rows = [[t.seg, t.offset, "VALID" if t.valid else "TRAP",
                     "\u2014" if t.physical is None else t.physical, t.message] for t in results]
            self.add(make_table(["Segment", "Offset", "Result", "Physical", "Details"], rows,
                                colors=[None if t.valid else BAD_BG for t in results]))
        bad = sum(1 for t in results if not t.valid)
        self.ok(f"Translated {len(results)} address(es), {bad} trap(s)")


# ==========================================================================
# 6. Fragmentation
# ==========================================================================
class FragmentationPage(ModulePage):
    title = "Fragmentation"
    subtitle = "Place processes with First/Best/Worst/Next Fit and measure fragmentation."
    input_title = "Memory & Processes"
    options_title = "Strategy"

    def build_inputs(self, body):
        self.blocks = line(nums(fragmentation.SAMPLE_BLOCKS))
        form(body, [("Memory block sizes (in order)", self.blocks)])
        self.procs = RowTable(["Process", "Size"], ["", "100"], prefix="P", start=1,
                              add_text="+  Add Process", min_height=170)
        self.procs.set_rows(fragmentation.SAMPLE_PROCS)
        body.addWidget(self.procs)

    def build_options(self, body):
        self.strategy = QComboBox()
        self.strategy.addItems(fragmentation.STRATEGIES)
        self.mode = QComboBox()
        self.mode.addItems(fragmentation.MODES)
        form(body, [("Allocation strategy", self.strategy), ("Partitioning", self.mode)])
        body.addWidget(self.run_button())
        body.addWidget(button_row(self.action("Load Sample", self.load_sample),
                                  self.action("Compare All", self.compare_all)))

    def load_sample(self):
        self.blocks.setText(nums(fragmentation.SAMPLE_BLOCKS))
        self.procs.set_rows(fragmentation.SAMPLE_PROCS)

    def read(self):
        sizes = fragmentation.parse_int_list(self.blocks.text(), "Memory blocks", 1)
        procs = [(r[0].strip(), fragmentation.parse_int(r[1], f"{r[0].strip() or 'row'} size", 1))
                 for r in self.procs.rows()]
        return sizes, procs

    def run(self):
        sizes, procs = self.read()
        res = fragmentation.allocate(sizes, procs, self.strategy.currentText(), self.mode.currentText())
        colors = ColorMap()
        self.clear_results()
        self.add(section(f"{res.strategy}  -  {res.mode}"))
        blocks = []
        for b in res.blocks:
            if b.free:
                blocks.append(dict(label="Free", caption=str(b.size), weight=b.size, color=None))
            else:
                cap = f"{b.used}/{b.size}" if b.used < b.size else str(b.size)
                blocks.append(dict(label=b.owner, caption=cap, weight=b.size, color=colors.get(b.owner)))
        strip = BlockStrip()
        strip.set_blocks(blocks)
        self.add(hscroll(strip, 74))
        self.add(tiles([("Total memory", res.total_memory), ("Used by processes", res.used_total),
                        ("Internal fragmentation", res.internal_total), ("Free memory", res.free_total),
                        ("Largest free block", res.largest_free),
                        ("External fragmentation", res.external_total)], columns=3))
        rows, shade = [], []
        for r in res.rows:
            dash = lambda v: "\u2014" if v is None else v
            rows.append([r["name"], r["size"], r["status"], dash(r["bid"]), dash(r["start"]),
                         dash(r["block_size"]), r["internal"]])
            shade.append(BAD_BG if r["status"] == "WAITING" else None)
        self.add(section("Allocation table"))
        self.add(make_table(["Process", "Size", "Status", "Block", "Start", "Block size",
                             "Internal frag."], rows, colors=shade))
        for note in res.notes:
            self.add(badge(note, "bad"))
        self.ok(f"{res.strategy}: {sum(1 for r in res.rows if r['status'] == 'ALLOCATED')} of "
                f"{len(res.rows)} process(es) allocated")

    def compare_all(self):
        sizes, procs = self.read()
        results = [fragmentation.allocate(sizes, procs, s, self.mode.currentText())
                   for s in fragmentation.STRATEGIES]
        waits = [sum(1 for r in x.rows if r["status"] == "WAITING") for x in results]
        best = min(waits)
        rows = [[x.strategy, len(x.rows) - w, w, x.internal_total, x.external_total, x.free_total,
                 x.largest_free] for x, w in zip(results, waits)]
        self.clear_results()
        self.add(section(f"All strategies  -  {self.mode.currentText()}"))
        self.add(make_table(["Strategy", "Allocated", "Waiting", "Internal", "External", "Free",
                             "Largest free"], rows,
                            colors=[BEST if w == best else None for w in waits]))
        self.add(hint("Green row = fewest processes left waiting."))
        self.ok("Compared all allocation strategies")


# ==========================================================================
# 7. Disk Scheduling
# ==========================================================================
class DiskPage(ModulePage):
    title = "Disk Scheduling"
    subtitle = "Trace the disk head and compare total head movement."
    input_title = "Disk Requests"
    options_title = "Algorithm"

    def build_inputs(self, body):
        self.requests = line(nums(disk.SAMPLE))
        self.head = spin(0, 1_000_000, 53)
        self.size = spin(1, 1_000_001, 200)
        self.direction = QComboBox()
        self.direction.addItems(["Toward higher cylinders (up)", "Toward lower cylinders (down)"])
        self.jump = QCheckBox("Count the return jump (C-SCAN / C-LOOK)")
        self.jump.setChecked(True)
        form(body, [("Cylinder requests (queue order)", self.requests),
                    ("Initial head position", self.head),
                    ("Disk size (cylinders)", self.size),
                    ("Initial direction (SCAN / LOOK)", self.direction)])
        body.addWidget(self.jump)

    def build_options(self, body):
        self.algo = QComboBox()
        self.algo.addItems(disk.ALGORITHMS)
        form(body, [("Algorithm", self.algo)])
        body.addWidget(self.run_button())
        body.addWidget(button_row(self.action("Load Sample", self.load_sample),
                                  self.action("Compare All", self.compare_all)))

    def load_sample(self):
        self.requests.setText(nums(disk.SAMPLE))
        self.head.setValue(53)
        self.size.setValue(200)

    def solve(self, name):
        reqs = disk.parse_int_list(self.requests.text(), "Requests", 0)
        d = "up" if self.direction.currentIndex() == 0 else "down"
        return disk.run_algorithm(name, reqs, self.head.value(), self.size.value(), d,
                                  self.jump.isChecked())

    def run(self):
        res = self.solve(self.algo.currentText())
        self.clear_results()
        self.add(section(f"{res.algorithm}  -  head starts at {self.head.value()}"))
        self.add(tiles([("Total head movement", res.total_movement),
                        ("Average seek", f2(res.average_seek)),
                        ("Requests served", len(res.order))], columns=3))
        self.add(label("Service order:  " + "  \u2192  ".join(str(c) for c in res.order), wrap=True))
        chart = PathChart()
        chart.set_path(res.path, self.size.value())
        self.add(chart)
        self.add(section("Head movements"))
        rows = [[i, a, b, d, n] for i, (a, b, d, n) in enumerate(res.steps, 1)]
        self.add(make_table(["#", "From", "To", "Distance", "Note"], rows))
        self.ok(f"{res.algorithm}: total head movement = {res.total_movement}")

    def compare_all(self):
        results = [self.solve(n) for n in disk.ALGORITHMS]
        best = min(r.total_movement for r in results)
        rows = [[r.algorithm, r.total_movement, f2(r.average_seek)] for r in results]
        self.clear_results()
        self.add(section("All disk-scheduling algorithms"))
        self.add(make_table(["Algorithm", "Total head movement", "Average seek"], rows,
                            colors=[BEST if r.total_movement == best else None for r in results]))
        self.add(hint("Green row = least head movement."))
        self.ok("Compared all disk scheduling algorithms")


# ==========================================================================
# 8. Multiprogramming
# ==========================================================================
class MultiprogPage(ModulePage):
    title = "Multiprogramming"
    subtitle = "Overlap CPU and I/O work to raise utilisation."
    input_title = "Programs"
    options_title = "System"

    def build_inputs(self, body):
        self.table = RowTable(["Program", "Arrival", "Memory", "CPU Burst", "I/O Burst"],
                              ["", "0", "100", "5", "2"], prefix="J", start=1,
                              add_text="+  Add Program", min_height=230)
        self.table.set_rows(multiprog.SAMPLE)
        body.addWidget(self.table)

    def build_options(self, body):
        self.memory = spin(1, 10_000_000, 1024)
        self.quantum = spin(1, 1000, 2)
        self.degree = spin(0, 1000, 0)
        form(body, [("Total memory", self.memory), ("CPU time quantum", self.quantum),
                    ("Max degree of multiprogramming (0 = unlimited)", self.degree)])
        body.addWidget(self.run_button())
        body.addWidget(self.action("Load Sample", lambda: self.table.set_rows(multiprog.SAMPLE)))

    def run(self):
        P = multiprog.parse_int
        progs = []
        for n, r in enumerate(self.table.rows(), 1):
            name = r[0].strip()
            if not name:
                raise multiprog.InputError(f"Row {n}: the program name is blank.")
            progs.append(multiprog.Program(name, P(r[1], f"{name} arrival", 0),
                                           P(r[2], f"{name} memory", 1), P(r[3], f"{name} CPU burst", 1),
                                           P(r[4], f"{name} I/O burst", 0)))
        res = multiprog.simulate(progs, self.memory.value(), self.quantum.value(), self.degree.value())
        m = res.metrics
        colors = ColorMap({"IDLE": "#E6E1F5"})
        self.clear_results()
        self.add(tiles([("CPU utilization", f"{m['cpu_utilization']:.1f}%"),
                        ("I/O utilization", f"{m['io_utilization']:.1f}%"),
                        ("Memory utilization", f"{m['memory_utilization']:.1f}%"),
                        ("Throughput", f"{m['throughput']:.3f} /unit"),
                        ("Avg turnaround", f2(m["avg_turnaround"])),
                        ("Avg memory wait", f2(m["avg_mem_wait"])),
                        ("Avg / max degree", f"{m['avg_degree']:.2f} / {m['max_degree']}"),
                        ("Makespan", m["makespan"])]))
        for p in res.rejected:
            self.add(badge(f"{p.name} was rejected: it needs {p.memory} memory but the system "
                           f"only has {self.memory.value()}.", "bad"))
        lo = min([s for _, s, _ in res.cpu_segments + res.io_segments] or [0])
        hi = max([e for _, _, e in res.cpu_segments + res.io_segments] or [1])
        for title, segs in (("CPU timeline", res.cpu_segments), ("I/O timeline", res.io_segments)):
            self.add(section(title))
            chart = GanttChart()
            chart.set_segments(segs, colors, bounds=(lo, hi))
            self.add(hscroll(chart, 90))
        self.add(section("Programs"))
        rows = [[r["name"], r["arrival"], r["memory"], r["cpu"], r["io"], r["admitted"],
                 r["first_cpu"], r["finish"], r["turnaround"], r["waiting"], r["mem_wait"]]
                for r in res.rows]
        self.add(make_table(["Program", "Arrival", "Memory", "CPU", "I/O", "Admitted", "First CPU",
                             "Finished", "Turnaround", "Waiting", "Memory wait"], rows))
        self.add(section("Event log"))
        log = QPlainTextEdit()
        log.setReadOnly(True)
        log.setObjectName("logView")
        log.setPlainText("\n".join(res.log))
        log.setFixedHeight(190)
        self.add(log)
        self.ok(f"Multiprogramming complete: CPU utilization {m['cpu_utilization']:.1f}%")


ALL_PAGES = [CpuPage, BankersPage, PagingPage, ReplacementPage, SegmentationPage,
             FragmentationPage, DiskPage, MultiprogPage]
