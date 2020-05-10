import random
from time import monotonic

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from scipy.signal import correlate2d


class Areal:
    """Steps driven by Python + Numpy + SciPy.
    """
    size: int
    exec_time: float
    step_count: int
    field: np.array
    kernel: np.array

    def __init__(self, size: int, start_points: int = 100):
        self.size = size
        self.step_count = 0
        self.exec_time = 0
        assert 32 <= size <= 1024
        self.field = np.zeros((size, size), dtype=int)
        for _ in range(start_points):
            self.field[
                random.randint(0, size - 1), random.randint(0, size - 1)
            ] = 1

        self.kernel = np.array([
            [1, 1, 1], [1, 10, 1], [1, 1, 1],
        ])

    def __repr__(self) -> str:
        avg = np.round(
            self.exec_time / (self.step_count or 1) * 1000, 2
        )
        return f"Steps: {self.step_count} avg {avg} ms"

    def step(self):
        state = correlate2d(self.field, self.kernel, mode="same")
        self.field = (
            (state == 3) | (state == 13) | (state == 12)
        ).astype(int)
        self.step_count += 1

    def show(self):
        plt.imshow(self.field == 0, interpolation="nearest", cmap="gray")
        plt.title(f"{self}")
        plt.show()

    def animate(self, steps: int) -> FuncAnimation:
        """Evolution with animation for N steps.
        """

        def animate(*args):
            start_time = monotonic()
            self.step()
            self.exec_time += monotonic() - start_time
            img = plt.imshow(
                self.field == 0,
                interpolation="nearest", cmap="gray", animated=True
            )
            ax = img.axes
            ttl = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="center")
            ttl.set_text(f"{self}")
            if self.step_count > steps:
                nonlocal anim
                anim.event_source.stop()

            return img, ttl

        fig = plt.figure()
        anim = FuncAnimation(fig, animate, interval=50, blit=True)

        return anim
