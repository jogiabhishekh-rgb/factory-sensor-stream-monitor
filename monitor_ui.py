import argparse
import re
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider


_DIGIT_VALUES = {
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
    "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
}


def item_count(items):
    count = 0
    for _ in items:
        count += 1
    return count


def parse_integer(text):
    negative = text.startswith("-")
    number = 0
    for character in text:
        if character != "-":
            number = number * 10 + _DIGIT_VALUES[character]
    return -number if negative else number


def greater_of(left, right):
    return left if left > right else right


def lesser_of(left, right):
    return left if left < right else right


def read_readings(path):
    text = Path(path).read_text(encoding="utf-8")
    readings = []
    for value in re.findall(r"-?\d+", text):
        readings.append(parse_integer(value))
    if not readings:
        raise ValueError(f"No integer readings found in {path}")
    return readings


def rolling_extrema(readings, window_size):
    max_values = []
    min_values = []
    max_queue = deque()
    min_queue = deque()

    index = 0
    for value in readings:
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

        index += 1

    return max_values, min_values


def find_out_of_limit_readings(readings, low_limit, high_limit):
    flagged = []
    reading_number = 1
    for value in readings:
        if value < low_limit or value > high_limit:
            flagged.append((reading_number, value))
        reading_number += 1
    return flagged


def main():
    parser = argparse.ArgumentParser(description="Factory sensor Matplotlib dashboard")
    parser.add_argument("file", nargs="?", default="stream.txt")
    parser.add_argument("--save", help="Save the dashboard to an image instead of opening the window")
    args = parser.parse_args()

    source = Path(args.file)
    if not source.is_absolute():
        source = Path(__file__).resolve().parent / source
    readings = read_readings(source)

    count = item_count(readings)
    default_window = lesser_of(4, count)
    data_min = readings[0]
    data_max = readings[0]
    for value in readings:
        if value < data_min:
            data_min = value
        if value > data_max:
            data_max = value
    padding = greater_of(1, (data_max - data_min) // 10)
    axis_min = data_min - padding
    axis_max = data_max + padding
    default_low = greater_of(axis_min, data_min)
    default_high = lesser_of(axis_max, data_max)

    plt.style.use("dark_background")
    plt.rcParams.update({
        "text.color": "#f9fafb",
        "axes.labelcolor": "#e5e7eb",
        "xtick.color": "#cbd5e1",
        "ytick.color": "#cbd5e1",
        "font.size": 10,
    })
    fig = plt.figure(figsize=(14, 9), facecolor="#0b1220")
    if fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title("Factory Sensor Stream Monitor")
    fig.text(0.07, 0.955, "Factory Sensor Monitor", fontsize=20, fontweight="bold",
             color="#f9fafb", ha="left")
    fig.text(0.07, 0.925, "Live readings, rolling limits, and clear alert status",
             fontsize=10, color="#94a3b8", ha="left")

    raw_ax = fig.add_axes((0.07, 0.61, 0.63, 0.28))
    rolling_ax = fig.add_axes((0.07, 0.22, 0.63, 0.28))
    status_ax = fig.add_axes((0.74, 0.72, 0.21, 0.16))
    sensors_ax = fig.add_axes((0.74, 0.36, 0.21, 0.33))
    faults_ax = fig.add_axes((0.74, 0.15, 0.21, 0.19))
    status_ax.set_facecolor("#172033")
    status_ax.axis("off")
    sensors_ax.set_facecolor("#172033")
    sensors_ax.axis("off")
    faults_ax.set_facecolor("#172033")
    faults_ax.axis("off")

    k_ax = fig.add_axes((0.14, 0.14, 0.54, 0.025))
    low_ax = fig.add_axes((0.14, 0.09, 0.54, 0.025))
    high_ax = fig.add_axes((0.14, 0.04, 0.54, 0.025))
    reset_ax = fig.add_axes((0.75, 0.05, 0.19, 0.05))

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

    raw_ax.set_facecolor("#1f2937")
    rolling_ax.set_facecolor("#1f2937")
    for ax in (raw_ax, rolling_ax):
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        ax.grid(color="#64748b", alpha=0.22, linewidth=0.8)
        for spine in ax.spines.values():
            spine.set_color("#334155")

    reading_indices = []
    index = 0
    while index < count:
        reading_indices.append(index)
        index += 1

    raw_ax.plot(
        reading_indices, readings, color="#38bdf8", linewidth=2.2,
        marker="o", markevery=greater_of(1, count // 40), markersize=4,
        label="Sensor reading", zorder=3,
    )
    raw_high_line = raw_ax.axhline(
        default_high, color="#fb7185", linewidth=1.8, linestyle="--",
        label="Maximum allowed", zorder=2,
    )
    raw_low_line = raw_ax.axhline(
        default_low, color="#34d399", linewidth=1.8, linestyle="--",
        label="Minimum allowed", zorder=2,
    )
    raw_ax.set_title("Sensor readings", color="#f8fafc", loc="left",
                     fontweight="bold", pad=10)
    raw_ax.set_xlabel("Reading number (oldest to newest)")
    raw_ax.set_ylabel("Sensor value")
    raw_ax.set_xlim(-0.5, greater_of(0.5, count - 0.5))
    raw_ax.set_ylim(axis_min, axis_max)
    raw_ax.legend(facecolor="#172033", edgecolor="#334155", labelcolor="#f8fafc",
                  loc="upper right", framealpha=0.95)

    rolling_max_line, = rolling_ax.plot(
        [], [], color="#f87171", linewidth=2, marker="o",
        markevery=greater_of(1, count // 40), markersize=3,
        label="Window maximum",
    )
    rolling_min_line, = rolling_ax.plot(
        [], [], color="#34d399", linewidth=2, marker="o",
        markevery=greater_of(1, count // 40), markersize=3,
        label="Window minimum",
    )
    rolling_high_line = rolling_ax.axhline(
        default_high, color="#fb7185", linewidth=1.8, linestyle="--",
        label="Maximum allowed",
    )
    rolling_low_line = rolling_ax.axhline(
        default_low, color="#34d399", linewidth=1.8, linestyle="--",
        label="Minimum allowed",
    )
    rolling_ax.set_title("Highest and lowest value in each window", color="#f8fafc",
                         loc="left", fontweight="bold", pad=10)
    rolling_ax.set_xlabel("Window end (reading number)")
    rolling_ax.set_ylabel("Sensor value")
    rolling_ax.set_xlim(-0.5, greater_of(0.5, count - 0.5))
    rolling_ax.set_ylim(axis_min, axis_max)
    rolling_ax.legend(facecolor="#172033", edgecolor="#334155", labelcolor="#f8fafc",
                      loc="upper right", framealpha=0.95)

    status_text = {
        "title": status_ax.text(0.07, 0.92, "Monitor summary", fontsize=10,
                                color="#f8fafc", fontweight="bold",
                                transform=status_ax.transAxes),
        "source": status_ax.text(0.07, 0.68, f"Data: {source.name}",
                                 fontsize=7.5, color="#cbd5e1",
                                 transform=status_ax.transAxes),
        "readings": status_ax.text(0.07, 0.47, f"Readings: {count}",
                                   fontsize=8.5, color="#7dd3fc",
                                   fontweight="bold", transform=status_ax.transAxes),
        "windows": status_ax.text(0.07, 0.28, "", fontsize=7.5,
                                  color="#e2e8f0", transform=status_ax.transAxes),
        "alerts": status_ax.text(0.07, 0.09, "", fontsize=7.5,
                                 fontweight="bold", transform=status_ax.transAxes),
    }

    sensor_ids = []
    sensor_number = 1
    while sensor_number <= 8:
        sensor_ids.append(f"S{sensor_number}r")
        sensor_number += 1
    sensor_rows = ""
    for sensor_id in sensor_ids:
        sensor_rows += f"{sensor_id:<10} UNKNOWN\n"

    sensors_ax.text(0.07, 0.92, "Sensor roster", fontsize=10,
                    color="#f8fafc", fontweight="bold",
                    transform=sensors_ax.transAxes)
    sensors_ax.text(0.08, 0.80, f"{'Sensor ID':<10} Status",
                    fontsize=8, color="#94a3b8", fontweight="bold",
                    family="monospace", transform=sensors_ax.transAxes)
    sensors_ax.text(0.08, 0.72, sensor_rows, fontsize=8.5,
                    color="#e2e8f0", family="monospace", linespacing=1.5,
                    va="top", transform=sensors_ax.transAxes)
    sensors_ax.text(0.07, 0.05, "No readings mapped to sensor IDs.",
                    fontsize=7, color="#94a3b8",
                    transform=sensors_ax.transAxes)

    faults_ax.text(0.07, 0.92, "Out-of-limit readings", fontsize=10,
                   color="#f8fafc", fontweight="bold", transform=faults_ax.transAxes)
    faults_ax.text(0.07, 0.77, "Sensor ID not linked", fontsize=7,
                   color="#cbd5e1", transform=faults_ax.transAxes)
    faults_ax.text(0.08, 0.60, f"{'Reading #':>10} {'Value':>10}",
                   fontsize=8, color="#94a3b8", fontweight="bold",
                   family="monospace", transform=faults_ax.transAxes)
    fault_rows_text = faults_ax.text(
        0.08, 0.52, "", fontsize=8, color="#f8fafc",
        family="monospace", linespacing=1.35, va="top",
        transform=faults_ax.transAxes,
    )
    fault_scroll_text = faults_ax.text(
        0.07, 0.04, "", fontsize=6.5, color="#94a3b8",
        transform=faults_ax.transAxes,
    )
    fault_records = []
    fault_scroll_offset = 0
    visible_fault_rows = 3

    def refresh_fault_column():
        nonlocal fault_scroll_offset
        fault_count = item_count(fault_records)
        last_offset = greater_of(0, fault_count - visible_fault_rows)
        if fault_scroll_offset > last_offset:
            fault_scroll_offset = last_offset
        if fault_scroll_offset < 0:
            fault_scroll_offset = 0

        if fault_count == 0:
            fault_rows_text.set_text("No readings outside limits.")
            fault_scroll_text.set_text("Adjust limits to check for outliers.")
            return

        rows = ""
        row_index = fault_scroll_offset
        last_row = lesser_of(fault_count, fault_scroll_offset + visible_fault_rows)
        while row_index < last_row:
            reading_number, value = fault_records[row_index]
            rows += f"{reading_number:>10} {value:>10}\n"
            row_index += 1
        fault_rows_text.set_text(rows)
        fault_scroll_text.set_text(f"{fault_scroll_offset + 1}-{last_row} of {fault_count}; scroll")

    def scroll_fault_column(event):
        nonlocal fault_scroll_offset
        if event.inaxes is not faults_ax:
            return
        if event.step > 0:
            fault_scroll_offset -= 1
        elif event.step < 0:
            fault_scroll_offset += 1
        else:
            return
        refresh_fault_column()
        fig.canvas.draw_idle()

    def update(_=None):
        window = parse_integer(f"{k_slider.val:.0f}")
        low = low_slider.val
        high = high_slider.val
        max_values, min_values = rolling_extrema(readings, window)
        centers = []
        index = window - 1
        while index < count:
            centers.append(index)
            index += 1

        alert_count = 0
        window_count = item_count(max_values)
        index = 0
        while index < window_count:
            if max_values[index] > high or min_values[index] < low:
                alert_count += 1
            index += 1

        fault_records.clear()
        fault_records.extend(find_out_of_limit_readings(readings, low, high))
        refresh_fault_column()

        raw_high_line.set_ydata([high, high])
        raw_low_line.set_ydata([low, low])
        rolling_max_line.set_data(centers, max_values)
        rolling_min_line.set_data(centers, min_values)
        rolling_high_line.set_ydata([high, high])
        rolling_low_line.set_ydata([low, low])

        latest_max = max_values[-1]
        latest_min = min_values[-1]
        latest_alert = latest_max > high or latest_min < low
        status_text["windows"].set_text(
            f"{window_count} complete windows checked"
        )
        status_text["alerts"].set_text(f"Out-of-limit windows: {alert_count}")
        status_text["alerts"].set_color("#fb7185" if alert_count else "#34d399")
        fig.canvas.draw_idle()

    def reset(_):
        k_slider.reset()
        low_slider.reset()
        high_slider.reset()

    k_slider.on_changed(update)
    low_slider.on_changed(update)
    high_slider.on_changed(update)
    reset_button.on_clicked(reset)
    fig.canvas.mpl_connect("scroll_event", scroll_fault_column)
    update()

    if args.save:
        fig.savefig(args.save, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    else:
        plt.show()


if __name__ == "__main__":
    main()
