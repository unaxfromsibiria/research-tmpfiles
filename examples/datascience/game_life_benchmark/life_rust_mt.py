# cd rust_impl
# cargo --version
#    cargo 1.45.0-nightly (cb06cb269 2020-05-08)
# cargo build --release
#   Compiling rust_impl v0.1.0 (/**/rust_impl)
#   Finished release [optimized] target(s) in 0.61s
# cd ../
# $ du -h ./rust_impl/target/release/librust_impl.so
# 4,0M    ./rust_impl/target/release/librust_impl.so

import typing
import ctypes
import os
import numpy as np

from base_areal import BaseAreal

INT_PTR = ctypes.POINTER(ctypes.c_int32)


class FieldStateMt:
    """State api class.
    """
    size: int
    shape: typing.Tuple[int, int]
    state: np.array
    lib = None
    cpu: int = 1

    def __init__(self, size: int):
        self.size = size
        self.shape = (size + 2, size + 2)
        self.state = np.zeros(self.shape, dtype=np.intc)
        lib = ctypes.cdll.LoadLibrary(
            "./rust_impl/target/release/librust_impl.so"
        )
        n = (size + 2) ** 2
        lib.make_step_mt.restype = ctypes.POINTER(ctypes.c_int32 * n)
        self.lib = lib
        self.cpu = int(os.cpu_count() or 0)
        assert self.cpu >= 2, "Only for multiprocessor systems."

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
        data_pointer = self.lib.make_step_mt(
            np.ctypeslib.as_ctypes(self.state), self.size, self.cpu
        )
        self.state = np.ctypeslib.as_array(
            ctypes.cast(data_pointer, INT_PTR), shape=self.shape
        )


class Areal(BaseAreal):
    """Steps driven by Rust with multithreading.
    """

    field_state: FieldStateMt

    def init_field(self, size: int):
        self.field_state = FieldStateMt(size)

    def add_point(self, x: int, y: int):
        self.field_state.add_point(x, y)

    def run_step(self):
        self.field_state.evolut()

    def as_state_img(self) -> np.array:
        return self.field_state.as_array()
