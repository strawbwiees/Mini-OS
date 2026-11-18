# Mini-OS: Operating System Simulator

A desktop app that lets you **see** how core operating-system algorithms work. Type in your own data (or load a sample), press **Run Simulation**, and get step-by-step results with Gantt charts, memory maps and disk-head path charts.

Built with Python and PySide6 (Qt), with a lavender/purple theme designed in Qt Designer.

---

## Modules

| # | Module | What it simulates |
|---|--------|-------------------|
| 1 | **CPU Scheduling** | FCFS, SJF (non-preemptive), SRTF, Priority (non-preemptive and preemptive), Round Robin. Shows a Gantt chart plus waiting and turnaround times, and a **Compare All** mode. |
| 2 | **Banker's Algorithm** | Deadlock avoidance: checks whether a system state is safe and finds a safe sequence of processes. |
| 3 | **Paging** | Splits processes into pages and frames, then translates logical addresses to physical ones. |
| 4 | **Page Replacement** | FIFO, LRU, Optimal and Second Chance (Clock), with page-fault counts. |
| 5 | **Segmentation** | Segment tables, with logical-address translation and limit checks. |
| 6 | **Fragmentation** | First Fit, Best Fit, Worst Fit and Next Fit, in fixed or dynamic partition mode, with a memory map. |
| 7 | **Disk Scheduling** | FCFS, SSTF, SCAN, C-SCAN, LOOK and C-LOOK, with a head-movement path chart and total seek distance. |
| 8 | **Multiprogramming** | Memory-limited job scheduling with a time quantum. |

Every page has **Load Sample** (and, where it makes sense, **Random**) so you can try it right away. Bad input (blank fields, negative numbers, out-of-range values) is reported in the status bar instead of crashing.

---

## Requirements

- Python 3.9 or newer (`pyproject.toml` currently asks for 3.14, so lower `requires-python` if your version is older)
- PySide6 6.5 or newer

## Install and run

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. install the dependency
pip install -r requirements.txt   # or: pip install PySide6

# 3. launch
python main.py
```

Using [uv](https://docs.astral.sh/uv/)? Run `uv sync`, then `uv run main.py`.

> **Font:** the theme uses *Century Gothic*. If it isn't installed, the app falls back to Poppins, Segoe UI, Helvetica Neue or Arial.

---

## How to use

1. Pick a module from the sidebar.
2. Enter your data in the input tables, or click **Load Sample**.
3. Choose an algorithm or strategy and set any options (time quantum, frame count, and so on).
4. Click **Run Simulation** and read the results below.
5. Watch the status bar at the bottom for confirmations and error messages.

---

## Project structure

```
MiniOS/
├── main.py              App start-up: font, stylesheet, opens the window
├── main_window.ui       Qt Designer file: window, header, sidebar, workspace, status bar
├── main_window.py       Loads the .ui, adds its layouts, plugs the 8 pages into the workspace
├── pages.py             The 8 module screens (input forms, run buttons, result views)
├── widgets.py           Reusable pieces: cards, editable tables, Gantt chart,
│                        memory map, disk path chart, monitor icon
├── styles.qss           Lavender/purple theme
│
├── cpuScheduling.py     ┐
├── bankersAlgorithm.py  │
├── paging.py            │  Algorithm modules: pure Python logic, no GUI code.
├── pageReplacement.py   │  The GUI imports them and displays their results.
├── segmentation.py      │
├── fragmentation.py     │
├── diskScheduling.py    │
├── multiprogramming.py  ┘
│
├── pyproject.toml       Project metadata and dependencies
├── requirements.txt     pip dependencies
└── uv.lock              uv lock file
```

### How the pieces fit together

```
main.py ──► main_window.py ──► main_window.ui   (layout designed in Qt Designer)
                 │
                 └──► pages.py ──► widgets.py    (drawing and tables)
                          │
                          └──► algorithm modules (the actual OS logic)
```

- **Algorithms are separate from the GUI.** Each algorithm file contains only the logic (plus input validation), so you can test or reuse it without Qt.
- **`pages.py` aliases the modules** to short names (`cpu`, `bankers`, `replacement`, `disk`, `multiprog`) at the top of the file.
- **Input errors** use one shared pattern: every module raises its own `InputError(ValueError)`, and the GUI catches them all and shows the message in the status bar.

---

## Run a module without the GUI

Each algorithm file also works as a standalone console program, with no PySide6 needed:

```bash
python cpuScheduling.py
python diskScheduling.py
```

---

## Customising

- **Colors and look:** edit `styles.qss`. Chart colors are in the palette at the top of `widgets.py`.
- **Layout, sidebar, header text:** open `main_window.ui` in Qt Designer. Button object names (`btnCpuScheduling`, `btnBankers`, …) must stay the same, because `main_window.py` looks them up by name.
- **Adding a module:** write the algorithm file, add a page class to `pages.py` and list it in `ALL_PAGES`. Then add a matching sidebar button in the `.ui` and its name to `BUTTON_NAMES` in `main_window.py`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'PySide6'` | Run `pip install PySide6` in the same environment you launch from. |
| `main_window.ui has no widget named '...'` | A widget was renamed or deleted in Qt Designer. Restore the object name. |
| Window opens but looks unstyled | `styles.qss` must sit next to `main.py`. Check the console for a "stylesheet not found" warning. |
| `uv sync` fails on Python version | Lower `requires-python` in `pyproject.toml` to match your installed Python. |
