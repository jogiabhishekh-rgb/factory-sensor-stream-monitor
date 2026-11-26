# factory-sensor-stream-monitor
Real-time factory sensor monitoring system using a monotonic queue (Deque ADT) to compute rolling window maxima/minima in $O(1)$ amortized time and trigger threshold alerts.

`sensor_monitor.rolling_extrema(readings, window_size)` streams `(maximum, minimum)`
pairs for complete windows only. It maintains decreasing and increasing monotonic
deques respectively, removing entries once their indices leave the current window.
For example:

```python
from sensor_monitor import rolling_extrema

for maximum, minimum in rolling_extrema([4, 1, 3, 2], 3):
    print(maximum, minimum)
```
