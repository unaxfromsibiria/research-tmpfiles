import typing

import cffi
import numpy as np

from .field_state import lib


make_step: typing.Callable = lib.make_step


class FieldState:
    """State api class.
    """
    size: int
    shape: typing.Tuple[int, int]
    state: np.array
    _ffi: cffi.FFI
    _state_c_ptr = None

    def __init__(self, size: int):
        self.size = size
        self.shape = (size + 2, size + 2)
        self.state = np.zeros(self.shape, dtype=np.intc)
        self._ffi = cffi.FFI()
        self._state_c_ptr = self._ffi.cast(
            "int *", self._ffi.from_buffer(self.state)
        )

    def add_point(self, x: int, y: int):
        """Set point to 1.
        """
        self.state[x, y] = 1

    def as_array(self) -> np.array:
        """Create bool np.array
        """
        return self.state == 0

    def evolut(self):
        """Make new state.
        """
        make_step(self.size, self._state_c_ptr)
