import argparse
import re
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider


def read_readings(path):
    text = Path(path).read_text(encoding="utf-8")
    readings = [int(value) for value in re.findall(r"-?\d+", text)]
    if not readings:
        raise ValueError(f"No integer readings found in {path}")
    return readings


def rolling_extrema(readings, window_size):
    max_values = []
    min_values = []
    max_queue = deque()
    min_queue = deque()

    for index, value in enumerate(readings):
        while max_queue and readings[max_queue[-1]] <= value:
            max_queue.pop()
        max_queue.append(index)

        while min_queue and readings[min_queue[-1]] >= value:
            min_queue.pop()
        min_queue.append(index)

        if max_queue[0] <= index - window_size:
            max_queue.popleft()
        if min_queue[0] <= index - window_size:
            min_queue.popleft()

        if index >= window_size - 1:
            max_values.append(readings[max_queue[0]])
            min_values.append(readings[min_queue[0]])

    return max_values, min_values


def main():
    parser = argparse.ArgumentParser(description="Factory sensor Matplotlib dashboard")
    parser.add_argument("file", nargs="?", default="stream.txt")
    parser.add_argument("--save", help="Save the dashboard to an image instead of opening the window")
    args = parser.parse_args()

    source = Path(args.file)
    if not source.is_absolute():
        source = Path(__file__).resolve().parent / source
    readings = read_readings(source)

    count = len(readings)
    default_window = min(4, count)
    data_min = min(readings)
    data_max = max(readings)
    padding = max(1, (data_max - data_min) // 10)
    axis_min = data_min - padding
    axis_max = data_max + padding
    default_low = max(axis_min, min(readings))
    default_high = min(axis_max, max(readings))

    plt.style.use("dark_background")
    plt.rcParams.update({
        "text.color": "#f9fafb",
        "axes.labelcolor": "#e5e7eb",
        "xtick.color": "#cbd5e1",
        "ytick.color": "#cbd5e1",
        "font.size": 10,
    })
    fig = plt.figure(figsize=(14, 9), facecolor="#0b1220")
    fig.canvas.manager.set_window_title("Factory Sensor Stream Monitor")
    fig.text(0.07, 0.955, "Factory Sensor Monitor", fontsize=20, fontweight="bold",
             color="#f9fafb", ha="left")
    fig.text(0.07, 0.925, "Live readings, rolling limits, and clear alert status",
             fontsize=10, color="#94a3b8", ha="left")

    raw_ax = fig.add_axes([0.07, 0.61, 0.63, 0.28])
    rolling_ax = fig.add_axes([0.07, 0.22, 0.63, 0.28])
    status_ax = fig.add_axes([0.74, 0.24, 0.21, 0.64])
    status_ax.set_facecolor("#172033")
    status_ax.axis("off")

    k_ax = fig.add_axes([0.14, 0.14, 0.54, 0.025])
    low_ax = fig.add_axes([0.14, 0.09, 0.54, 0.025])
    high_ax = fig.add_axes([0.14, 0.04, 0.54, 0.025])
    reset_ax = fig.add_axes([0.75, 0.05, 0.19, 0.05])

    control_color = "#253247"
    k_slider = Slider(k_ax, "Window size", 1, count, valinit=default_window,
                      valstep=1, color="#38bdf8", track_color=control_color)
    low_slider = Slider(low_ax, "Minimum allowed", axis_min, axis_max,
                        valinit=default_low, color="#34d399", track_color=control_color)
    high_slider = Slider(high_ax, "Maximum allowed", axis_min, axis_max,
                         valinit=default_high, color="#fb7185", track_color=control_color)
    reset_button = Button(reset_ax, "Reset settings", color="#253247", hovercolor="#334155")
    reset_button.label.set_color("#f9fafb")
    for slider in (k_slider, low_slider, high_slider):
        slider.label.set_color("#e2e8f0")
        slider.label.set_fontsize(9)
        slider.valtext.set_color("#f8fafc")
        slider.valtext.set_fontweight("bold")
        slider.ax.set_facecolor("#0b1220")

    def update(_=None):
        window = int(k_slider.val)
        low = low_slider.val
        high = high_slider.val
        max_values, min_values = rolling_extrema(readings, window)
        centers = list(range(window - 1, count))
        bad = [maximum > high or minimum < low for maximum, minimum in zip(max_values, min_values)]
        alert_count = sum(bad)

        raw_ax.clear()
        rolling_ax.clear()

        raw_ax.plot(range(count), readings, color="#38bdf8", linewidth=2.2, marker="o",
                    markersize=5, label="Sensor reading", zorder=3)
        raw_ax.axhline(high, color="#fb7185", linewidth=1.8, linestyle="--",
                       label="Maximum allowed", zorder=2)
        raw_ax.axhline(low, color="#34d399", linewidth=1.8, linestyle="--",
                       label="Minimum allowed", zorder=2)
        raw_ax.set_title("Sensor readings", color="#f8fafc", loc="left",
                         fontweight="bold", pad=10)
        raw_ax.set_xlabel("Reading number (oldest to newest)")
        raw_ax.set_ylabel("Sensor value")
        raw_ax.grid(color="#64748b", alpha=0.22, linewidth=0.8)
        raw_ax.legend(facecolor="#172033", edgecolor="#334155", labelcolor="#f8fafc",
                      loc="upper right", framealpha=0.95)

        rolling_ax.plot(centers, max_values, color="#f87171", linewidth=2,
                        marker="o", markersize=4, label="Window maximum")
        rolling_ax.plot(centers, min_values, color="#34d399", linewidth=2,
                        marker="o", markersize=4, label="Window minimum")
        rolling_ax.fill_between(centers, min_values, max_values, color="#60a5fa", alpha=0.12)
        rolling_ax.axhline(high, color="#fb7185", linewidth=1.8, linestyle="--",
                           label="Maximum allowed")
        rolling_ax.axhline(low, color="#34d399", linewidth=1.8, linestyle="--",
                           label="Minimum allowed")
        rolling_ax.set_title("Highest and lowest value in each window", color="#f8fafc",
                             loc="left", fontweight="bold", pad=10)
        rolling_ax.set_xlabel("Window end (reading number)")
        rolling_ax.set_ylabel("Sensor value")
        rolling_ax.grid(color="#64748b", alpha=0.22, linewidth=0.8)
        rolling_ax.legend(facecolor="#172033", edgecolor="#334155", labelcolor="#f8fafc",
                          loc="upper right", framealpha=0.95)

        latest_max = max_values[-1]
        latest_min = min_values[-1]
        latest_alert = bad[-1]
        status_ax.clear()
        status_ax.set_facecolor("#172033")
        status_ax.axis("off")
        status_ax.text(0.07, 0.94, "At a glance", fontsize=15, color="#f8fafc",
                       fontweight="bold", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.87, f"Data file: {source.name}", fontsize=9,
                       color="#cbd5e1", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.77, f"{count} readings", fontsize=13, color="#7dd3fc",
                       fontweight="bold", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.71, f"{len(max_values)} complete windows checked",
                       fontsize=10, color="#e2e8f0", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.61, f"{alert_count} windows outside limits",
                       fontsize=11, color="#fb7185" if alert_count else "#34d399",
                       fontweight="bold", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.51, "Most recent window", fontsize=11,
                       color="#f8fafc", fontweight="bold", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.44, f"Highest value: {latest_max}", fontsize=10,
                       color="#e2e8f0", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.38, f"Lowest value: {latest_min}", fontsize=10,
                       color="#e2e8f0", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.34, "What this means", fontsize=10,
                       color="#f8fafc", fontweight="bold", transform=status_ax.transAxes)
        status_ax.text(0.07, 0.23,
                       "A window is flagged if its highest\nvalue is above the maximum, or its\nlowest value is below the minimum.",
                       fontsize=8.5, color="#cbd5e1", linespacing=1.5, va="top",
                       transform=status_ax.transAxes)
        status_ax.text(0.07, 0.08, "CHECK NEEDED" if latest_alert else "ALL CLEAR",
                       fontsize=13, color="#fb7185" if latest_alert else "#34d399",
                       fontweight="bold", transform=status_ax.transAxes)

        for ax in (raw_ax, rolling_ax):
            ax.set_facecolor("#1f2937")
            ax.tick_params(colors="#cbd5e1", labelsize=9)
            for spine in ax.spines.values():
                spine.set_color("#334155")

        fig.canvas.draw_idle()

    def reset(_):
        k_slider.reset()
        low_slider.reset()
        high_slider.reset()

    k_slider.on_changed(update)
    low_slider.on_changed(update)
    high_slider.on_changed(update)
    reset_button.on_clicked(reset)
    update()

    if args.save:
        fig.savefig(args.save, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    else:
        plt.show()


if __name__ == "__main__":
    main()
