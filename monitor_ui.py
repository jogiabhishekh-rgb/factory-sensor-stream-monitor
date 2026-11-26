import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider


_DIGIT_VALUES = {
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
    "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
}


def item_count(items):
    count = 0
    for _item in items:
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


class IndexDeque:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._items = [0] * capacity
        self._capacity = capacity
        self._head = 0
        self._size = 0

    def is_empty(self):
        return self._size == 0

    def front(self):
        if self.is_empty():
            raise IndexError("front from empty deque")
        return self._items[self._head]

    def back(self):
        if self.is_empty():
            raise IndexError("back from empty deque")
        return self._items[(self._head + self._size - 1) % self._capacity]

    def push_back(self, value):
        if self._size == self._capacity:
            raise OverflowError("deque is full")
        index = (self._head + self._size) % self._capacity
        self._items[index] = value
        self._size += 1

    def pop_back(self):
        if self.is_empty():
            raise IndexError("pop from empty deque")
        self._size -= 1

    def pop_front(self):
        if self.is_empty():
            raise IndexError("pop from empty deque")
        self._head = (self._head + 1) % self._capacity
        self._size -= 1


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
    max_queue = IndexDeque(window_size + 1)
    min_queue = IndexDeque(window_size + 1)

    index = 0
    for value in readings:
        while not max_queue.is_empty() and readings[max_queue.back()] <= value:
            max_queue.pop_back()
        max_queue.push_back(index)

        while not min_queue.is_empty() and readings[min_queue.back()] >= value:
            min_queue.pop_back()
        min_queue.push_back(index)

        if max_queue.front() <= index - window_size:
            max_queue.pop_front()
        if min_queue.front() <= index - window_size:
            min_queue.pop_front()

        if index >= window_size - 1:
            max_values.append(readings[max_queue.front()])
            min_values.append(readings[min_queue.front()])

        index += 1

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
        "title": status_ax.text(0.07, 0.94, "At a glance", fontsize=15,
                                color="#f8fafc", fontweight="bold",
                                transform=status_ax.transAxes),
        "source": status_ax.text(0.07, 0.87, f"Data file: {source.name}",
                                 fontsize=9, color="#cbd5e1",
                                 transform=status_ax.transAxes),
        "readings": status_ax.text(0.07, 0.77, f"{count} readings",
                                   fontsize=13, color="#7dd3fc",
                                   fontweight="bold", transform=status_ax.transAxes),
        "windows": status_ax.text(0.07, 0.71, "", fontsize=10,
                                  color="#e2e8f0", transform=status_ax.transAxes),
        "alerts": status_ax.text(0.07, 0.61, "", fontsize=11,
                                 fontweight="bold", transform=status_ax.transAxes),
        "latest_title": status_ax.text(0.07, 0.51, "Most recent window",
                                       fontsize=11, color="#f8fafc",
                                       fontweight="bold", transform=status_ax.transAxes),
        "maximum": status_ax.text(0.07, 0.44, "", fontsize=10,
                                  color="#e2e8f0", transform=status_ax.transAxes),
        "minimum": status_ax.text(0.07, 0.38, "", fontsize=10,
                                  color="#e2e8f0", transform=status_ax.transAxes),
        "explanation_title": status_ax.text(0.07, 0.34, "What this means",
                                            fontsize=10, color="#f8fafc",
                                            fontweight="bold", transform=status_ax.transAxes),
        "explanation": status_ax.text(
            0.07, 0.23,
            "A window is flagged if its highest\nvalue is above the maximum, or its\nlowest value is below the minimum.",
            fontsize=8.5, color="#cbd5e1", linespacing=1.5, va="top",
            transform=status_ax.transAxes,
        ),
        "state": status_ax.text(0.07, 0.08, "", fontsize=13,
                                fontweight="bold", transform=status_ax.transAxes),
    }

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
        status_text["alerts"].set_text(f"{alert_count} windows outside limits")
        status_text["alerts"].set_color("#fb7185" if alert_count else "#34d399")
        status_text["maximum"].set_text(f"Highest value: {latest_max}")
        status_text["minimum"].set_text(f"Lowest value: {latest_min}")
        status_text["state"].set_text("CHECK NEEDED" if latest_alert else "ALL CLEAR")
        status_text["state"].set_color("#fb7185" if latest_alert else "#34d399")

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
