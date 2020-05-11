import numpy as np

from base_areal import BaseAreal


class Areal(BaseAreal):
    """Steps driven by Python.
    """

    field: list
    indexes: tuple = (
        (-1, 0, 1, -1, 1, -1, 0, 1),
        (-1, -1, -1, 0, 0, 1, 1, 1),
    )
    x_indexes: tuple
    y_indexes: tuple

    def add_point(self, x: int, y: int):
        self.field[x][y] = 1

    def init_field(self, size: int):
        self.field = [[0 for _ in range(size + 2)] for _ in range(size + 2)]

        x_delta, y_delta = self.indexes
        self.x_indexes = tuple(
            tuple(i + dx for dx in x_delta) for i in range(1, size + 1)
        )
        self.y_indexes = tuple(
            tuple(i + dy for dy in y_delta) for i in range(1, size + 1)
        )

    def run_step(self):
        field = [
            [0 for _ in range(self.size + 2)] for _ in range(self.size + 2)
        ]
        for i, x_index in enumerate(self.x_indexes, 1):
            for j, y_index in enumerate(self.y_indexes, 1):
                m = sum(
                    1
                    for index in range(8)
                    if self.field[x_index[index]][y_index[index]]
                )
                field[i][j] = int(
                    m == 3 or (self.field[i][j] and m == 2)
                )

        self.field = field

    def as_state_img(self) -> np.array:
        return np.array(self.field) == 0
