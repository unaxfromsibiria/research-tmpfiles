from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        "cmdparser.pyx",
        compiler_directives={
            "initializedcheck": False,
            "nonecheck": False,
            "language_level": 3,
            "infer_types": True,
        }
    )
)
