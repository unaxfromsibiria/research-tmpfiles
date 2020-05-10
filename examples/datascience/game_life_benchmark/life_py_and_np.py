import random
from time import monotonic

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


class Areal:
    """Steps driven by Python + Numpy.
    """
    size: int
    exec_time: float
    step_count: int
    field: np.array
    indexes: tuple = (
        (-1, 0, 1, -1, 1, -1, 0, 1),
        (-1, -1, -1, 0, 0, 1, 1, 1),
    )
    x_indexes: tuple
    y_indexes: tuple

    def __init__(self, size: int, start_points: int = 100):
        self.size = size
        self.step_count = 0
        self.exec_time = 0
        assert 32 <= size <= 1024
        self.field = np.zeros((size + 2, size + 2), dtype=int)
        for _ in range(start_points):
            self.field[random.randint(1, size), random.randint(1, size)] = 1

        x_delta, y_delta = self.indexes
        self.x_indexes = tuple(
            tuple(i + dx for dx in x_delta) for i in range(1, size + 1)
        )
        self.y_indexes = tuple(
            tuple(i + dy for dy in y_delta) for i in range(1, size + 1)
        )

    def __repr__(self) -> str:
        avg = np.round(
            self.exec_time / (self.step_count or 1) * 1000, 2
        )
        return f"Steps: {self.step_count} avg {avg} ms"

    def step(self):
        state = self.field > 0
        for i, x_index in enumerate(self.x_indexes, 1):
            for j, y_index in enumerate(self.y_indexes, 1):
                # m = state[x_index, y_index].sum() worse performance
                m = sum(
                    1
                    for index in range(8)
                    if state[x_index[index], y_index[index]]
                )
                self.field[i, j] = int(m == 3 or (self.field[i, j] and m == 2))

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
