import random
from time import monotonic

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


class BaseAreal:
    """Base areal.
    """
    size: int
    exec_time: float
    step_count: int

    def __init__(self, size: int = 128, start_points: int = 3000):
        self.size = size
        self.step_count = 0
        self.exec_time = 0
        assert 32 <= size <= 1024
        self.init_field(size)
        for _ in range(start_points):
            self.add_point(
                random.randint(1, size - 1), random.randint(1, size - 1)
            )

    def __repr__(self) -> str:
        avg = np.round(
            self.exec_time / (self.step_count or 1) * 1000, 2
        )
        return (
            f"Steps in {self.__class__.__name__}: "
            f"{self.step_count} avg {avg} ms"
        )

    def step(self):
        self.run_step()
        self.step_count += 1

    def show(self):
        plt.imshow(
            self.as_state_img(),
            interpolation="nearest", cmap="gray"
        )
        plt.title(f"{self}")
        plt.show()

    def animate(self, steps: int = 1000) -> FuncAnimation:
        """Evolution with animation for N steps.
        """

        def animate(*args):
            start_time = monotonic()
            self.step()
            self.exec_time += monotonic() - start_time
            img = plt.imshow(
                self.as_state_img(),
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

    def init_field(self, size: int):
        pass

    def add_point(self, x: int, y: int):
        pass

    def as_state_img(self) -> np.array:
        pass

    def run_step(self):
        pass
