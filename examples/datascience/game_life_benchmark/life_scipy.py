import numpy as np
from scipy.signal import correlate2d

from base_areal import BaseAreal


class Areal(BaseAreal):
    """Steps driven by Python + Numpy + SciPy.
    """

    field: np.array
    kernel: np.array

    def init_field(self, size: int):
        self.field = np.zeros((size, size), dtype=int)
        self.kernel = np.array([
            [1, 1, 1], [1, 10, 1], [1, 1, 1],
        ])

    def add_point(self, x: int, y: int):
        self.field[x, y] = 1

    def run_step(self):
        state = correlate2d(self.field, self.kernel, mode="same")
        self.field = (
            (state == 3) | (state == 13) | (state == 12)
        ).astype(int)

    def as_state_img(self) -> np.array:
        return self.field == 0
