import random
from time import monotonic

import matplotlib.pyplot as plt
import numba
import numpy as np
from matplotlib.animation import FuncAnimation


@numba.jit(nopython=True)
def make_step(
    size: int,
    state: np.array,
    new_state: np.array,
    x_delta: tuple,
    y_delta: tuple
):
    """Update state.
    """
    for i in range(1, size + 1):
        for j in range(1, size + 1):
            m = 0
            for index in range(8):
                if state[i + x_delta[index], j + y_delta[index]]:
                    m += 1

            new_state[i, j] = int(
                m == 3 or (state[i, j] and m == 2)
            )


class Areal:
    """Steps driven by Numpy structures and Numba jit.
    """
    size: int
    exec_time: float
    step_count: int
    field: np.array
    x_delta: tuple = (-1, 0, 1, -1, 1, -1, 0, 1)
    y_delta: tuple = (-1, -1, -1, 0, 0, 1, 1, 1)

    def __init__(self, size: int, start_points: int = 100):
        self.size = size
        self.step_count = 0
        self.exec_time = 0
        assert 32 <= size <= 1024
        self.field = np.zeros((size + 2, size + 2), dtype=int)
        for _ in range(start_points):
            self.field[random.randint(1, size), random.randint(1, size)] = 1

    def __repr__(self) -> str:
        avg = np.round(
            self.exec_time / (self.step_count or 1) * 1000, 2
        )
        return f"Steps: {self.step_count} avg {avg} ms"

    def step(self):
        make_step(
            self.size,
            (self.field > 0),
            self.field,
            self.x_delta,
            self.y_delta
        )
        self.step_count += 1

    def show(self):
        plt.imshow(
            self.field == 0, interpolation="nearest", cmap="gray"
        )
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
