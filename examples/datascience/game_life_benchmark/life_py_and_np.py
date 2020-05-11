
import numpy as np

from base_areal import BaseAreal


class Areal(BaseAreal):
    """Steps driven by Python + Numpy.
    """

    field: np.array
    indexes: tuple = (
        (-1, 0, 1, -1, 1, -1, 0, 1),
        (-1, -1, -1, 0, 0, 1, 1, 1),
    )
    x_indexes: tuple
    y_indexes: tuple

    def init_field(self, size: int):
        self.field = np.zeros((size + 2, size + 2), dtype=int)

        x_delta, y_delta = self.indexes
        self.x_indexes = tuple(
            tuple(i + dx for dx in x_delta) for i in range(1, size + 1)
        )
        self.y_indexes = tuple(
            tuple(i + dy for dy in y_delta) for i in range(1, size + 1)
        )

    def add_point(self, x: int, y: int):
        self.field[x, y] = 1

    def run_step(self):
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

    def as_state_img(self) -> np.array:
        return self.field == 0
