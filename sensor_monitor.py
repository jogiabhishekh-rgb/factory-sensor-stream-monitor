from collections import deque
from collections.abc import Iterable, Iterator


def rolling_extrema(
    readings: Iterable[float], window_size: int
) -> Iterator[tuple[float, float]]:
    """Yield the maximum and minimum for each complete rolling window."""
    if (
        not isinstance(window_size, int)
        or isinstance(window_size, bool)
        or window_size <= 0
    ):
        raise ValueError("window_size must be a positive integer")

    def results() -> Iterator[tuple[float, float]]:
        maxima: deque[tuple[int, float]] = deque()
        minima: deque[tuple[int, float]] = deque()

        for index, value in enumerate(readings):
            while maxima and maxima[-1][1] <= value:
                maxima.pop()
            maxima.append((index, value))

            while minima and minima[-1][1] >= value:
                minima.pop()
            minima.append((index, value))

            expired_index = index - window_size
            if maxima and maxima[0][0] <= expired_index:
                maxima.popleft()
            if minima and minima[0][0] <= expired_index:
                minima.popleft()

            if index >= window_size - 1:
                yield maxima[0][1], minima[0][1]

    return results()
