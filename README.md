# Factory Sensor Stream Monitor

A real-time factory sensor monitoring system that tracks rolling window extrema (maximum and minimum temperature readings) and triggers safety threshold alerts without rescanning historical data.

Built using a **Monotonic Queue (Double-Ended Queue / Deque ADT)** to achieve $O(1)$ amortized per-reading updates, alongside a naive rescanning baseline for performance benchmarking and a Python UI for live visualization.

---

## Problem Overview

Industrial factory sensors emit continuous streams of temperature readings (up to $100,000$ readings per replay). Naive monitoring systems repeatedly scan the last $K$ readings on every new arrival, degrading performance as window size $K$ grows.

This system solves the problem by:
- Processing sensor readings sequentially via manual input or a replay file (`stream.txt`).
- Computing exact **rolling maximum** and **rolling minimum** values for every complete window of $K$ consecutive readings.
- Suppressing alerts until the first complete window of $K$ readings has arrived.
- Flagging safety breaches whenever a window's maximum exceeds a configured **High Limit** or its minimum drops below a **Low Limit**.
- Handling negative values, duplicate/repeated peaks, and changing trends across multiple replays with configurable window sizes ($1 \le K \le n$).

---

## Repository Structure

```text
factory-sensor-stream-monitor/
├── monitor.c       # Core C implementation (Monotonic Deque ADT + O(nK) baseline comparison)
├── monitor_ui.py   # Live monitoring dashboard / visualization interface
├── ui.py           # Interactive UI components and stream controls
├── stream.txt      # Sample sensor temperature stream for replay testing
├── LICENSE         # Repository license
└── README.md       # Project documentation
