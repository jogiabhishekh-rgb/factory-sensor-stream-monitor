# Factory Sensor Stream Monitor

A live sensor monitoring system that reports the **maximum and minimum of every window of K consecutive temperature readings** and flags windows that cross a safety limit, **without rescanning the history**.

It is built on a **monotonic deque** (double-ended queue ADT), which updates the window summary in O(1) amortized time per reading. A straightforward rescanning baseline runs alongside it for comparison.

## Features

- Reads measurements in arrival order from **manual input** or a **replay file**.
- Reports the maximum and minimum for each **complete** window of K readings. Nothing is reported until K readings have arrived.
- Updates the result as the window advances by one reading.
- Flags a completed window when its maximum is above the **high limit** or its minimum is below the **low limit**. Alerts never fire for incomplete windows.
- Displays the window table and the latest window's summary.
- Handles repeated peaks and negative values. K can be changed for each replay (1 ≤ K ≤ n, up to 100,000 readings).
- Compares the deque against a rescanning baseline (operation counts, run time, and a mismatch check).
- Includes a Python/Matplotlib dashboard with sliders for K and both limits.

## How it works

Two deques of reading indices are kept, one for the maximum and one for the minimum.

- **Max deque:** values are kept in decreasing order. A new reading removes every smaller or equal value from the back before it is added, so the front is always the window maximum.
- **Min deque:** the same idea with increasing order, so the front is the window minimum.
- **Expiry:** if the front index is no longer inside the window (`index <= i - K`), it is removed from the front.
- **Output:** a result is produced only when `i >= K - 1`, which is the first complete window.

Example: readings `4 1 7 3 6` with K = 3.

| Reading index | Max deque (values) | Min deque (values) | Window max / min |
|---|---|---|---|
| 0 | 4 | 4 | not yet complete |
| 1 | 4 1 | 1 | not yet complete |
| 2 | 7 | 1 7 | 7 / 1 |
| 3 | 7 3 | 1 3 | 7 / 1 |
| 4 | 7 6 | 3 6 | 7 / 3 |

Rolling maxima are `7 7 7` and rolling minima are `1 1 3`, as in the problem statement.

## Complexity

| Method | Time | Extra memory |
|---|---|---|
| Monotonic deque (this project) | **O(n)** total, O(1) amortized per reading, independent of K | O(K) |
| Rescanning baseline | O(n · K) | O(1) |

Each reading enters each deque once and leaves at most once, which is why the cost does not grow with K.

## Build and run

### C program

```bash
gcc -O2 monitor.c -o monitor
./monitor stream.txt          # Windows PowerShell: .\monitor stream.txt
```

The program then asks for the window size K, the high limit and the low limit. To type the readings by hand instead, run `./monitor` with no file; it asks for the number of readings first.

Example session with `stream.txt`, K = 4, high limit 11, low limit -2:

```
Window   Reading range        Maximum      Minimum Status
1        [0..3]                     9            2 OK
2        [1..4]                     9            2 OK
3        [2..5]                     9            1 OK
4        [3..6]                     9           -3 ALERT
5        [4..7]                     9           -3 ALERT
6        [5..8]                     4           -3 ALERT
7        [6..9]                     8           -3 ALERT
8        [7..10]                   12           -3 ALERT
9        [8..11]                   12            4 ALERT

Windows: 9 | Alerts: 6 | Mismatches vs baseline: 0
```

### Input file format

A plain text file of integers separated by spaces, commas or new lines. Negative values and repeated values are allowed. Do not include a header or units.

```
5 9 9 2 9 1 -3 -3 4 8 12 6
```

### Python dashboard

```bash
pip install matplotlib
python monitor_ui.py stream.txt
```

Use the sliders to change the window size, the minimum allowed value and the maximum allowed value. The status panel shows the latest window and the number of windows outside the limits.

## Benchmark: deque vs rescanning

100,000 random readings, K = 50,000 (generate the file with `python tests/gen_large.py tests/large.txt`):

| Method | Operations | Time |
|---|---|---|
| Monotonic deque | about 400,000 | about 0.002 s |
| Rescanning baseline | about 5,000,000,000 | about 1.5 s |

Both give identical results (0 mismatches). Times depend on the machine; the operation counts do not.

## Tests

```bash
gcc -O2 monitor.c -o monitor
python tests/run_tests.py
```

`tests/run_tests.py` runs the program on every file in `tests/` and compares the window count and alert count with an independent brute-force check. Cases:

| File | What it checks |
|---|---|
| `example.txt` | The example from the problem statement |
| `repeated_peaks.txt` | Repeated maxima and minima, changing trend |
| `all_equal.txt` | Every reading equal |
| `negative.txt` | Negative values only |
| `increasing.txt` / `decreasing.txt` | Monotonic streams (smallest and largest deque sizes) |
| `k_equals_n.txt` | A single window (K = n) |
| `k_equals_1.txt` | Every reading is its own window (K = 1) |
| `trend.txt` | Rising then falling trend with plateaus |

## Repository structure

```text
factory-sensor-stream-monitor/
├── monitor.c        # C implementation: deque ADT, rolling max/min, alerts, baseline comparison
├── monitor_ui.py    # Matplotlib dashboard with sliders
├── stream.txt       # Sample replay file
├── tests/           # Test streams, large-file generator and test runner
├── LICENSE
└── README.md
```

## Limits

Up to 100,000 integer readings per replay. K is fixed during a replay and 1 ≤ K ≤ n. Live hardware input is not included; replay files and manual input are used instead.

