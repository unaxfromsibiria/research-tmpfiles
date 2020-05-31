import typing

import cffi
import os
import numpy as np

from .field_state import lib


make_step: typing.Callable = lib.make_step
make_step_th: typing.Callable = lib.make_step_th


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


class FieldStatePthreads:
    """State api class.
    """
    size: int
    threads_count: int
    shape: typing.Tuple[int, int]
    state: np.array
    _ffi: cffi.FFI
    _state_c_ptr = None

    def __init__(self, size: int):
        self.size = size
        self.threads_count = os.cpu_count() or 0
        assert self.threads_count > 1, "For multiprocessor systems only"
        if self.threads_count <= 4:
            self.threads_count = 2

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
        make_step_th(self.size, self.threads_count, self._state_c_ptr)
