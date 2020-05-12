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

    def __init__(self, size: int):
        self.size = size
        self.shape = (size + 2, size + 2)
        self.state = np.zeros(self.shape, dtype=np.intc)
        self._ffi = cffi.FFI()

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
        state_c_ptr = self._ffi.cast(
            "int *", self._ffi.from_buffer(self.state)
        )
        new_state = self.state.copy()
        new_state_c_ptr = self._ffi.cast(
            "int *", self._ffi.from_buffer(new_state)
        )
        make_step(self.size, state_c_ptr, new_state_c_ptr)
        del self.state
        self.state = new_state
