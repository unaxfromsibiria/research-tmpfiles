
import numba
import numpy as np
import os

from base_areal import BaseAreal


@numba.jit(nopython=True)
def make_step(
    size: int,
    state: np.array,
    new_state: np.array,
    x_delta: tuple,
    y_delta: tuple,
    p_count: int,
):
    """Update state.
    """
    step: int = size // p_count
    a = b = 0
    for index in numba.prange(p_count):
        a = index * step
        b = (index + 1) * step if index < p_count - 1 else size
        for k in range(a, b):
            i = k + 1
            for j in range(1, size + 1):
                m = 0
                for index in range(8):
                    if state[i + x_delta[index], j + y_delta[index]]:
                        m += 1

                new_state[i, j] = int(
                    m == 3 or (state[i, j] and m == 2)
                )


class Areal(BaseAreal):
    """Steps driven by Numpy structures and Numba jit.
    """

    field: np.array
    x_delta: tuple = (-1, 0, 1, -1, 1, -1, 0, 1)
    y_delta: tuple = (-1, -1, -1, 0, 0, 1, 1, 1)
    p_count: int = 0
    skip_first: bool = True

    def init_field(self, size: int):
        self.p_count = os.cpu_count() or 0
        assert self.p_count > 1, "For multiprocessor systems only"
        self.field = np.zeros((size + 2, size + 2), dtype=int)

    def add_point(self, x: int, y: int):
        self.field[x, y] = 1

    def run_step(self):
        make_step(
            self.size,
            (self.field > 0),
            self.field,
            self.x_delta,
            self.y_delta,
            self.p_count
        )

    def as_state_img(self) -> np.array:
        return self.field == 0
