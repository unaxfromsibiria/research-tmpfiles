import numpy as np

from libc.stdlib cimport malloc, free, realloc


cdef class FieldState:
    """Based on C types.
    """
    cdef int size
    cdef bint *state
    cdef int *x_delta
    cdef int *y_delta

    def __init__(self, size: int):
        cdef int n = (size + 2) ** 2
        cdef int i = 0
        self.size = size
        self.state = <bint *>malloc(sizeof(bint) * n)
        for i in range(n):
            self.state[i] = 0

        self.x_delta = <int *>malloc(sizeof(int) * 8)
        self.y_delta = <int *>malloc(sizeof(int) * 8)
        x_delta = [-1, 0, 1, -1, 1, -1, 0, 1]
        y_delta = [-1, -1, -1, 0, 0, 1, 1, 1]
        for i in range(8):
            self.x_delta[i] = x_delta[i]
            self.y_delta[i] = y_delta[i]

    def add_point(self, x: int, y: int):
        """Set point to 1.
        """
        cdef int size = self.size + 2
        cdef int i = (1 + x) + (1 + y) * size
        self.state[i] = 1

    def evolut(self):
        """Make step.
        """
        cdef int n = self.size + 2
        cdef int index_size = n - 1
        cdef int i, j, m, k, index
        cdef bint *new_state = <bint *>malloc(sizeof(bint) * n * n)
        for i in range(n):
            for j in range(n):
                if 0 < i < index_size and 0 < j < index_size:
                    # create state
                    m = 0
                    for index in range(8):
                        k = (i + self.x_delta[index]) + (j + self.y_delta[index]) * n
                        if self.state[k]:
                            m += 1

                    k = i + j * n
                    new_state[k] = (
                        m == 3 or (self.state[k] == 1 and m == 2)
                    )
                else:
                    # init borders in new state
                    k = i + j * n
                    new_state[k] = 0

        free(self.state)
        self.state = new_state

    def as_array(self) -> np.array:
        """Create np.array with shape: size X size
        """
        cdef int size = self.size
        cdef int k, i, j
        field = np.zeros((size, size), dtype=bool)
        for i in range(1, size + 1):
            for j in range(1, size + 1):
                k = i + j * (size + 2)
                field[i - 1, j - 1] = bool(self.state[k])

        return field
