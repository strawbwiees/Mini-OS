import sys
from pathlib import Path
from collections import deque

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QComboBox, QSpinBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QPlainTextEdit, QScrollArea, QGroupBox, QSizePolicy
)


MODULES = [
    ("CPU Scheduling", "Explore how processes share the CPU."),
    ("Banker's Algorithm", "Find a safe sequence and prevent deadlock."),
    ("Paging", "Translate logical addresses into physical addresses."),
    ("Page Replacement", "See what stays in memory and what gets replaced."),
    ("Segmentation", "Explore memory divided into logical segments."),
    ("Fragmentation", "Understand internal and external memory waste."),
    ("Disk Scheduling", "Compare how disk requests are serviced."),
    ("Multiprogramming", "See how processes are placed into memory.")
]


def card(title=None):
    frame = QFrame()
    frame.setObjectName("panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    if title:
        label = QLabel(title)
        label.setObjectName("panelTitle")
        layout.addWidget(label)
    return frame, layout


def make_table(headers, rows=0):
    table = QTableWidget(rows, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    return table


def put(table, row, col, value):
    table.setItem(row, col, QTableWidgetItem(str(value)))


def action_button(text, primary=False):
    b = QPushButton(text)
    b.setProperty("primary", primary)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def spin(value=0, maximum=9999):
    s = QSpinBox()
    s.setRange(0, maximum)
    s.setValue(value)
    return s


class MiniOS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Operating System")
        self.resize(1250, 850)
        self.setMinimumSize(980, 700)
        self.current_index = 0
        self.pages = QStackedWidget()
        self.nav_buttons = []

        root = QWidget()
        root.setObjectName("root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(26, 14, 26, 14)
        title = QLabel("Mini Operating System")
        title.setObjectName("appTitle")
        tagline = QLabel("LEARN BY SIMULATING")
        tagline.setObjectName("tagline")
        hl.addWidget(title)
        hl.addStretch()
        hl.addWidget(tagline)
        outer.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(225)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(16, 20, 16, 18)
        sl.setSpacing(9)
        explore = QLabel("EXPLORE MODULES")
        explore.setObjectName("eyebrow")
        sl.addWidget(explore)
        for i, (name, _) in enumerate(MODULES):
            b = QPushButton(name)
            b.setObjectName("navButton")
            b.setCheckable(True)
            b.clicked.connect(lambda checked=False, idx=i: self.show_module(idx))
            self.nav_buttons.append(b)
            sl.addWidget(b)
        sl.addStretch()
        foot = QLabel("8 concepts. One workspace.\n\nMini OS  /  Learning lab")
        foot.setObjectName("sideFoot")
        sl.addWidget(foot)
        body.addWidget(sidebar)

        content = QWidget()
        content.setObjectName("content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 20, 24, 16)
        cl.setSpacing(14)
        heading = QHBoxLayout()
        heading_text = QVBoxLayout()
        self.module_title = QLabel()
        self.module_title.setObjectName("moduleTitle")
        self.module_subtitle = QLabel()
        self.module_subtitle.setObjectName("moduleSubtitle")
        heading_text.addWidget(self.module_title)
        heading_text.addWidget(self.module_subtitle)
        heading.addLayout(heading_text)
        heading.addStretch()
        lab = QLabel("●  Learning lab")
        lab.setObjectName("labBadge")
        heading.addWidget(lab, 0, Qt.AlignmentFlag.AlignTop)
        cl.addLayout(heading)
        cl.addWidget(self.pages, 1)
        body.addWidget(content, 1)
        outer.addLayout(body, 1)

        footer = QFrame()
        footer.setObjectName("footer")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 7, 24, 7)
        self.footer_note = QLabel("Sample data • Times in milliseconds unless noted")
        self.page_count = QLabel("01 / 08")
        fl.addWidget(self.footer_note)
        fl.addStretch()
        fl.addWidget(self.page_count)
        outer.addWidget(footer)
        self.setCentralWidget(root)

        builders = [
            self.cpu_page, self.bankers_page, self.paging_page, self.replacement_page,
            self.segmentation_page, self.fragmentation_page, self.disk_page,
            self.multiprogramming_page
        ]
        for builder in builders:
            self.pages.addWidget(builder())
        self.show_module(0)

    def show_module(self, index):
        self.current_index = index
        self.pages.setCurrentIndex(index)
        self.module_title.setText(MODULES[index][0])
        self.module_subtitle.setText(MODULES[index][1])
        self.page_count.setText(f"{index + 1:02d} / 08")
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

    # ---------- CPU SCHEDULING ----------
    def cpu_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        top = QHBoxLayout()
        input_card, il = card("Process input")
        self.cpu_table = make_table(["Process ID", "Arrival time", "Burst time", "Priority"], 3)
        self.cpu_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed | QTableWidget.EditTrigger.SelectedClicked)
        for r, vals in enumerate([("P1", 0, 7, 1), ("P2", 1, 4, 2), ("P3", 2, 1, 3)]):
            for c, v in enumerate(vals):
                put(self.cpu_table, r, c, v)
        il.addWidget(self.cpu_table)
        row = QHBoxLayout()
        add = action_button("+ Add process")
        remove = action_button("Remove selected")
        add.clicked.connect(self.add_cpu_process)
        remove.clicked.connect(lambda: self.cpu_table.removeRow(self.cpu_table.currentRow()) if self.cpu_table.currentRow() >= 0 else None)
        row.addWidget(add); row.addWidget(remove); row.addStretch()
        il.addLayout(row)
        top.addWidget(input_card, 2)

        algo_card, al = card("Algorithm")
        self.cpu_algo = QComboBox()
        self.cpu_algo.addItems(["First Come First Serve (FCFS)", "Shortest Job First (SJF)", "Priority (Non-preemptive)", "Round Robin (RR)"])
        self.quantum = spin(2, 100)
        self.quantum.setPrefix("Time quantum: ")
        al.addWidget(QLabel("Scheduling policy"))
        al.addWidget(self.cpu_algo)
        al.addWidget(self.quantum)
        al.addWidget(QLabel("Non-preemptive policies run each selected process until it finishes."))
        run = action_button("▶  Run simulation", True)
        reset = action_button("Reset")
        run.clicked.connect(self.run_cpu)
        reset.clicked.connect(self.reset_cpu)
        buttons = QHBoxLayout(); buttons.addWidget(run); buttons.addWidget(reset)
        al.addLayout(buttons)
        top.addWidget(algo_card, 1)
        root.addLayout(top)

        result, rl = card("Simulation results")
        self.cpu_summary = QLabel("Run the simulation to see the execution order and metrics.")
        self.cpu_summary.setObjectName("muted")
        rl.addWidget(self.cpu_summary)
        self.gantt = QTableWidget(2, 0)
        self.gantt.verticalHeader().setVisible(False)
        self.gantt.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.gantt.setFixedHeight(105)
        rl.addWidget(self.gantt)
        self.cpu_results = make_table(["Process", "Waiting time", "Turnaround time", "Completion time"])
        rl.addWidget(self.cpu_results)
        self.cpu_metrics = QLabel("Average waiting time: —       Average turnaround time: —")
        self.cpu_metrics.setObjectName("metric")
        rl.addWidget(self.cpu_metrics)
        root.addWidget(result, 1)
        return page

    def add_cpu_process(self):
        r = self.cpu_table.rowCount()
        self.cpu_table.insertRow(r)
        for c, value in enumerate([f"P{r+1}", 0, 1, 1]):
            put(self.cpu_table, r, c, value)

    def reset_cpu(self):
        self.cpu_table.setRowCount(0)
        for vals in [("P1", 0, 7, 1), ("P2", 1, 4, 2), ("P3", 2, 1, 3)]:
            r = self.cpu_table.rowCount(); self.cpu_table.insertRow(r)
            for c, v in enumerate(vals): put(self.cpu_table, r, c, v)
        self.cpu_results.setRowCount(0); self.gantt.setColumnCount(0)
        self.cpu_summary.setText("Inputs reset. Run the simulation.")

    def run_cpu(self):
        try:
            jobs = []
            for r in range(self.cpu_table.rowCount()):
                jobs.append({"id": self.cpu_table.item(r,0).text().strip(),
                             "arrival": int(self.cpu_table.item(r,1).text()),
                             "burst": int(self.cpu_table.item(r,2).text()),
                             "priority": int(self.cpu_table.item(r,3).text())})
            if not jobs or any(j["burst"] <= 0 for j in jobs): raise ValueError()
            mode = self.cpu_algo.currentIndex()
            timeline, completion = [], {}
            if mode != 3:
                pending = jobs[:]; t = 0
                while pending:
                    ready = [j for j in pending if j["arrival"] <= t]
                    if not ready:
                        t = min(j["arrival"] for j in pending); ready = [j for j in pending if j["arrival"] <= t]
                    if mode == 0: chosen = min(ready, key=lambda j:j["arrival"])
                    elif mode == 1: chosen = min(ready, key=lambda j:j["burst"])
                    else: chosen = min(ready, key=lambda j:j["priority"])
                    start=t; t += chosen["burst"]; completion[chosen["id"]]=t
                    timeline.append((chosen["id"], start, t)); pending.remove(chosen)
            else:
                q=self.quantum.value(); remaining={j["id"]:j["burst"] for j in jobs}
                by_arrival=sorted(jobs,key=lambda j:j["arrival"]); ready=deque()
                t=0; k=0
                while k<len(by_arrival) or ready:
                    if not ready and k<len(by_arrival) and t<by_arrival[k]["arrival"]: t=by_arrival[k]["arrival"]
                    while k<len(by_arrival) and by_arrival[k]["arrival"]<=t:
                        ready.append(by_arrival[k]); k+=1
                    j=ready.popleft(); start=t; run=min(q,remaining[j["id"]]); t+=run; remaining[j["id"]]-=run
                    timeline.append((j["id"],start,t))
                    while k<len(by_arrival) and by_arrival[k]["arrival"]<=t:
                        ready.append(by_arrival[k]); k+=1
                    if remaining[j["id"]]>0: ready.append(j)
                    else: completion[j["id"]]=t
            self.gantt.setColumnCount(len(timeline)); self.gantt.setRowCount(2)
            self.gantt.setVerticalHeaderLabels(["Process","Time"])
            for c,(pid,start,end) in enumerate(timeline):
                put(self.gantt,0,c,pid); put(self.gantt,1,c,f"{start} – {end}")
            self.cpu_results.setRowCount(len(jobs)); waits=[]; turns=[]
            for r,j in enumerate(jobs):
                tat=completion[j["id"]]-j["arrival"]; wt=tat-j["burst"]
                waits.append(wt); turns.append(tat)
                for c,v in enumerate([j["id"],wt,tat,completion[j["id"]]]): put(self.cpu_results,r,c,v)
            self.cpu_summary.setText("Execution order:  " + "  →  ".join(x[0] for x in timeline))
            self.cpu_metrics.setText(f"Average waiting time: {sum(waits)/len(waits):.2f} ms       Average turnaround time: {sum(turns)/len(turns):.2f} ms")
        except Exception:
            QMessageBox.warning(self,"Invalid input","Enter valid process IDs, arrival times, burst times, and priorities. Burst time must be greater than zero.")

    # ---------- BANKER'S ALGORITHM ----------
    def bankers_page(self):
        page=QWidget(); root=QVBoxLayout(page)
        top=QHBoxLayout()
        self.alloc_table=make_table(["Process","A","B","C"],5)
        self.max_table=make_table(["Process","A","B","C"],5)
        alloc=[[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]]
        maximum=[[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]]
        for table,data in [(self.alloc_table,alloc),(self.max_table,maximum)]:
            table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed | QTableWidget.EditTrigger.SelectedClicked)
            for r,row in enumerate(data):
                for c,v in enumerate([f"P{r}"]+row): put(table,r,c,v)
        a,al=card("Allocation"); al.addWidget(self.alloc_table)
        m,ml=card("Maximum demand"); ml.addWidget(self.max_table)
        res,rl=card("Available resources")
        self.avail=[spin(3),spin(3),spin(2)]
        grid=QGridLayout()
        for i,name in enumerate("ABC"): grid.addWidget(QLabel(name),0,i); grid.addWidget(self.avail[i],1,i)
        rl.addLayout(grid)
        rl.addWidget(QLabel("Enter the currently available instances of each resource type."))
        run=action_button("▶  Run algorithm",True); run.clicked.connect(self.run_bankers)
        rl.addWidget(run)
        top.addWidget(a); top.addWidget(m); top.addWidget(res)
        root.addLayout(top)
        result,rl=card("Safety analysis")
        self.bank_status=QLabel("Run the algorithm to check whether the system is in a safe state.")
        self.bank_status.setObjectName("metric")
        rl.addWidget(self.bank_status)
        self.bank_output=QPlainTextEdit(); self.bank_output.setReadOnly(True); self.bank_output.setMinimumHeight(180)
        rl.addWidget(self.bank_output)
        root.addWidget(result,1)
        return page

    def run_bankers(self):
        try:
            alloc=[[int(self.alloc_table.item(r,c).text()) for c in range(1,4)] for r in range(5)]
            maximum=[[int(self.max_table.item(r,c).text()) for c in range(1,4)] for r in range(5)]
            avail=[x.value() for x in self.avail]
            need=[[maximum[i][j]-alloc[i][j] for j in range(3)] for i in range(5)]
            work=avail[:]; finish=[False]*5; seq=[]
            while len(seq)<5:
                found=False
                for i in range(5):
                    if not finish[i] and all(need[i][j]<=work[j] for j in range(3)):
                        work=[work[j]+alloc[i][j] for j in range(3)]
                        finish[i]=True; seq.append(f"P{i}"); found=True
                if not found: break
            lines=["Need = Maximum − Allocation",""]
            for i,row in enumerate(need): lines.append(f"P{i}:  A={row[0]}   B={row[1]}   C={row[2]}")
            lines.append("")
            if len(seq)==5:
                self.bank_status.setText("✓  SAFE STATE   •   " + "  →  ".join(seq))
                lines.append("Safe sequence: "+" → ".join(seq))
                lines.append("Every process can finish with the available resources.")
            else:
                self.bank_status.setText("⚠  UNSAFE STATE")
                lines.append("No complete safe sequence exists for the supplied values.")
            self.bank_output.setPlainText("\n".join(lines))
        except Exception:
            QMessageBox.warning(self,"Invalid input","Check that all allocation and maximum-demand cells contain valid numbers.")

    # ---------- PAGING ----------
    def paging_page(self):
        page=QWidget(); root=QVBoxLayout(page)
        form,fl=card("Paging configuration")
        row=QHBoxLayout()
        self.logical=spin(350,999999); self.page_size=spin(100,100000); self.frame_count=spin(8,1000)
        for label,w in [("Logical address",self.logical),("Page size",self.page_size),("Number of frames",self.frame_count)]:
            box=QVBoxLayout(); box.addWidget(QLabel(label)); box.addWidget(w); row.addLayout(box)
        fl.addLayout(row)
        run=action_button("Translate address",True); run.clicked.connect(self.run_paging); fl.addWidget(run,0,Qt.AlignmentFlag.AlignLeft)
        root.addWidget(form)
        out,ol=card("Address translation")
        self.paging_output=QLabel("Enter a logical address and page size, then translate it.")
        self.paging_output.setObjectName("metric"); ol.addWidget(self.paging_output)
        self.paging_details=QPlainTextEdit(); self.paging_details.setReadOnly(True); ol.addWidget(self.paging_details)
        root.addWidget(out,1)
        return page

    def run_paging(self):
        size=self.page_size.value(); address=self.logical.value()
        page=address//size; offset=address%size
        # Demonstration page table: map each logical page to a frame in round-robin order.
        frame=page % self.frame_count.value()
        physical=frame*size+offset
        self.paging_output.setText(f"Page: {page}     Frame: {frame}     Offset: {offset}     Physical address: {physical}")
        self.paging_details.setPlainText(
            f"Logical address = {address}\nPage size = {size}\nNumber of frames = {self.frame_count.value()}\n\n"
            f"Page number = {address} // {size} = {page}\n"
            f"Offset = {address} % {size} = {offset}\n"
            f"Demonstration page-table mapping: frame = page % frame count = {page} % {self.frame_count.value()} = {frame}\n"
            f"Physical address = (frame × page size) + offset = ({frame} × {size}) + {offset} = {physical}\n\n"
            "This uses a simple sample mapping to demonstrate translation; real operating systems maintain an actual page table."
        )

    # ---------- PAGE REPLACEMENT ----------
    def replacement_page(self):
        page=QWidget(); root=QVBoxLayout(page)
        config,cl=card("Reference configuration")
        row=QHBoxLayout()
        self.ref_string=QLineEdit("7, 0, 1, 2, 0, 3, 0, 4")
        self.ref_string.setPlaceholderText("Example: 7, 0, 1, 2, 0, 3")
        self.rep_frames=spin(3,20)
        self.rep_algo=QComboBox(); self.rep_algo.addItems(["FIFO","LRU","Optimal"])
        for label,w in [("Reference string",self.ref_string),("Frames",self.rep_frames),("Algorithm",self.rep_algo)]:
            box=QVBoxLayout(); box.addWidget(QLabel(label)); box.addWidget(w); row.addLayout(box)
        cl.addLayout(row)
        run=action_button("▶  Run simulation",True); run.clicked.connect(self.run_replacement); cl.addWidget(run,0,Qt.AlignmentFlag.AlignLeft)
        root.addWidget(config)
        result,rl=card("Frame-by-frame simulation")
        self.rep_output=QPlainTextEdit(); self.rep_output.setReadOnly(True); self.rep_output.setMinimumHeight(260)
        rl.addWidget(self.rep_output)
        self.rep_metrics=QLabel("Page faults: —       Page hits: —       Hit ratio: —")
        self.rep_metrics.setObjectName("metric"); rl.addWidget(self.rep_metrics)
        root.addWidget(result,1)
        return page

    def run_replacement(self):
        try:
            refs: list[int] = [int(x.strip()) for x in self.ref_string.text().split(",") if x.strip()]
            frame_limit: int = self.rep_frames.value()
            if not refs:
                raise ValueError("The reference string is empty.")

            frames: list[int] = []
            last_used: list[int] = []
            faults: int = 0
            hits: int = 0
            rows: list[tuple[int, list[int], str]] = []
            algorithm: str = self.rep_algo.currentText()

            for step, page_number in enumerate(refs):
                hit: bool = page_number in frames
                if hit:
                    hits += 1
                    frame_index = frames.index(page_number)
                    last_used[frame_index] = step
                else:
                    faults += 1
                    if len(frames) < frame_limit:
                        frames.append(page_number)
                        last_used.append(step)
                    else:
                        if algorithm == "FIFO":
                            victim_index = 0
                        elif algorithm == "LRU":
                            victim_index = last_used.index(min(last_used))
                        else:  # Optimal page replacement
                            future: list[int] = refs[step + 1:]
                            distances: list[float] = []
                            for resident_page in frames:
                                if resident_page in future:
                                    distances.append(float(future.index(resident_page)))
                                else:
                                    distances.append(float("inf"))
                            victim_index = distances.index(max(distances))

                        frames[victim_index] = page_number
                        last_used[victim_index] = step

                rows.append((page_number, frames.copy(), "HIT" if hit else "FAULT"))

            lines: list[str] = ["Ref   | Frames in memory                  | Result", "-" * 62]
            for page_number, frame_snapshot, status in rows:
                padded_frames = frame_snapshot + ["—"] * (frame_limit - len(frame_snapshot))
                lines.append(f"{page_number:<5} | {str(padded_frames):<34} | {status}")

            self.rep_output.setPlainText("\n".join(lines))
            hit_ratio = hits / len(refs) * 100
            self.rep_metrics.setText(
                f"Page faults: {faults}       Page hits: {hits}       Hit ratio: {hit_ratio:.1f}%"
            )
        except Exception:
            QMessageBox.warning(self,"Invalid input","Use a comma-separated reference string containing integers.")

    # ---------- SEGMENTATION ----------
    def segmentation_page(self):
        page=QWidget(); root=QVBoxLayout(page)
        cfg,cl=card("Segment table")
        self.seg_table=make_table(["Segment","Base address","Limit"],4)
        defaults=[("Code",1000,400),("Data",2000,300),("Stack",3000,200),("Heap",4000,500)]
        for r,row in enumerate(defaults):
            for c,v in enumerate(row): put(self.seg_table,r,c,v)
        cl.addWidget(self.seg_table)
        row=QHBoxLayout()
        self.seg_no=spin(0,3); self.seg_offset=spin(100,999999)
        row.addWidget(QLabel("Segment number")); row.addWidget(self.seg_no)
        row.addWidget(QLabel("Offset")); row.addWidget(self.seg_offset)
        run=action_button("Translate address",True); run.clicked.connect(self.run_segmentation); row.addWidget(run)
        cl.addLayout(row); root.addWidget(cfg)
        out,ol=card("Segmentation result")
        self.seg_output=QLabel("A logical address is valid when its offset is below the segment limit.")
        self.seg_output.setObjectName("metric"); ol.addWidget(self.seg_output)
        root.addWidget(out,1)
        return page

    def run_segmentation(self):
        try:
            i=self.seg_no.value(); base=int(self.seg_table.item(i,1).text()); limit=int(self.seg_table.item(i,2).text()); off=self.seg_offset.value()
            if off>=limit: self.seg_output.setText(f"⚠  SEGMENTATION FAULT — offset {off} exceeds segment limit {limit}.")
            else: self.seg_output.setText(f"✓  VALID ADDRESS — {base} + {off} = physical address {base+off}.")
        except Exception: QMessageBox.warning(self,"Invalid input","Check the segment table values.")

    # ---------- FRAGMENTATION ----------
    def fragmentation_page(self):
        page=QWidget(); root=QVBoxLayout(page)
        cfg,cl=card("Memory allocation example")
        row=QHBoxLayout()
        self.block_size=spin(100,100000); self.process_size=spin(65,100000)
        for label,w in [("Allocated block size",self.block_size),("Process size",self.process_size)]:
            box=QVBoxLayout(); box.addWidget(QLabel(label)); box.addWidget(w); row.addLayout(box)
        cl.addLayout(row)
        run=action_button("Calculate fragmentation",True); run.clicked.connect(self.run_fragmentation); cl.addWidget(run,0,Qt.AlignmentFlag.AlignLeft)
        root.addWidget(cfg)
        out,ol=card("Analysis")
        self.frag_output=QLabel("Enter the allocated block size and process size.")
        self.frag_output.setObjectName("metric"); ol.addWidget(self.frag_output)
        self.frag_details=QPlainTextEdit(); self.frag_details.setReadOnly(True); ol.addWidget(self.frag_details)
        root.addWidget(out,1)
        return page

    def run_fragmentation(self):
        block=self.block_size.value(); proc=self.process_size.value()
        if proc>block:
            self.frag_output.setText("Process does not fit in the selected memory block.")
            self.frag_details.setPlainText(f"Process size: {proc}\nBlock size: {block}\nAdditional memory required: {proc-block}")
        else:
            waste=block-proc
            self.frag_output.setText(f"Internal fragmentation: {waste} memory units ({waste/block*100:.1f}%).")
            self.frag_details.setPlainText(f"Allocated block: {block}\nProcess uses: {proc}\nUnused space inside allocated block: {waste}\n\nThis example demonstrates internal fragmentation. External fragmentation occurs when free memory is split into separated holes.")

    # ---------- DISK SCHEDULING ----------
    def disk_page(self):
        page=QWidget(); root=QVBoxLayout(page)
        cfg,cl=card("Disk request queue")
        row=QHBoxLayout()
        self.disk_requests=QLineEdit("98, 183, 37, 122, 14, 124, 65, 67")
        self.disk_head=spin(53,999999); self.disk_algo=QComboBox(); self.disk_algo.addItems(["FCFS","SSTF","SCAN (toward 0)","C-SCAN (toward 0)"])
        for label,w in [("Requests",self.disk_requests),("Initial head position",self.disk_head),("Algorithm",self.disk_algo)]:
            box=QVBoxLayout(); box.addWidget(QLabel(label)); box.addWidget(w); row.addLayout(box)
        cl.addLayout(row)
        run=action_button("▶  Run disk simulation",True); run.clicked.connect(self.run_disk); cl.addWidget(run,0,Qt.AlignmentFlag.AlignLeft)
        root.addWidget(cfg)
        out,ol=card("Head movement")
        self.disk_output=QPlainTextEdit(); self.disk_output.setReadOnly(True); ol.addWidget(self.disk_output)
        self.disk_metrics=QLabel("Total head movement: —")
        self.disk_metrics.setObjectName("metric"); ol.addWidget(self.disk_metrics)
        root.addWidget(out,1)
        return page

    def run_disk(self):
        try:
            req=[int(x.strip()) for x in self.disk_requests.text().split(",") if x.strip()]
            head=self.disk_head.value(); original=head
            if not req: raise ValueError()
            mode=self.disk_algo.currentIndex(); order=[]
            if mode==0: order=req[:]
            elif mode==1:
                pending=req[:]
                while pending:
                    nxt=min(pending,key=lambda x:abs(x-head)); order.append(nxt); pending.remove(nxt); head=nxt
            else:
                lower=sorted([x for x in req if x<=head],reverse=True)
                upper=sorted([x for x in req if x>head])
                if mode == 2:  # SCAN: continue toward track 0, then reverse
                    order=lower + upper
                else:  # C-SCAN: move toward 0, wrap to track 199, continue downward
                    order=lower + ([199] if upper else []) + sorted(upper, reverse=True)
            head=original; total=0; lines=[f"Starting head position: {head}"]
            for x in order:
                total+=abs(x-head); lines.append(f"{head} → {x}   ({abs(x-head)} tracks)"); head=x
            self.disk_output.setPlainText("\n".join(lines)+"\n\nService order: "+" → ".join(map(str,order)))
            self.disk_metrics.setText(f"Total head movement: {total} tracks  •  SCAN examples use track 0 and C-SCAN wraps at track 199")
        except Exception: QMessageBox.warning(self,"Invalid input","Enter a comma-separated list of integer track numbers.")

    # ---------- MULTIPROGRAMMING ----------
    def multiprogramming_page(self):
        page=QWidget(); root=QVBoxLayout(page)
        cfg,cl=card("Memory and process configuration")
        row=QHBoxLayout()
        self.memory_total=spin(1024,1000000); self.memory_os=spin(128,1000000)
        self.process_memory=QLineEdit("120, 250, 180, 300, 90")
        for label,w in [("Total memory",self.memory_total),("Operating system memory",self.memory_os),("Process sizes (comma-separated)",self.process_memory)]:
            box=QVBoxLayout(); box.addWidget(QLabel(label)); box.addWidget(w); row.addLayout(box)
        cl.addLayout(row)
        run=action_button("Allocate processes",True); run.clicked.connect(self.run_multiprogramming); cl.addWidget(run,0,Qt.AlignmentFlag.AlignLeft)
        root.addWidget(cfg)
        out,ol=card("Allocation results")
        self.multi_table=make_table(["Process","Memory required","Status","Remaining memory"])
        ol.addWidget(self.multi_table)
        self.multi_summary=QLabel("Run allocation to see how many processes fit in memory.")
        self.multi_summary.setObjectName("metric"); ol.addWidget(self.multi_summary)
        root.addWidget(out,1)
        return page

    def run_multiprogramming(self):
        try:
            total=self.memory_total.value(); osmem=self.memory_os.value()
            sizes=[int(x.strip()) for x in self.process_memory.text().split(",") if x.strip()]
            if osmem>total or not sizes: raise ValueError()
            free=total-osmem; self.multi_table.setRowCount(len(sizes))
            for r,size in enumerate(sizes):
                ok=size<=free
                if ok: free-=size
                vals=[f"P{r+1}",size,"Loaded" if ok else "Not enough memory",free]
                for c,v in enumerate(vals): put(self.multi_table,r,c,v)
            self.multi_summary.setText(f"Memory available after OS: {total-osmem} units       Memory remaining: {free} units       Loaded: {sum(1 for r in range(len(sizes)) if self.multi_table.item(r,2).text()=='Loaded')}/{len(sizes)}")
        except Exception: QMessageBox.warning(self,"Invalid input","Check memory values and process sizes.")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    project_dir = Path(__file__).resolve().parent
    qss_path = project_dir / "styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    # The complete interface is created in Python. Do not load main_window.ui
    # here: its existing fixed geometries/layouts can squeeze the new interface.
    window = MiniOS()
    window.resize(1440, 900)
    window.setMinimumSize(1050, 720)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
