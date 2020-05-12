# python setup.py
from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef("void make_step(int size, int *state, int *new_state);")
ffibuilder.set_source(
    "field_state",
    """
    #include "field_state_step.h"
    """,
    sources=["field_state_step.c"],
    extra_compile_args=[
        "-O3",
        "-march=native",
        "-ffast-math",
        "-ftree-loop-distribution",
        "-floop-nest-optimize",
        "-floop-block",
    ]
)

ffibuilder.compile(verbose=True)
