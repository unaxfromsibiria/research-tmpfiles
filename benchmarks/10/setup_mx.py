from distutils.core import setup
from Cython.Build import cythonize

# python setup_mx.py build_ext --inplace
setup(
    ext_modules=cythonize(
        "simple_mx.pyx",
        compiler_directives={
            "initializedcheck": False,
            "nonecheck": False,
            "language_level": 3,
            "infer_types": True,
        })
)
