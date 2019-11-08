from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

# python setup_*.py build_ext --inplace

modules = [
    Extension(
        "num_path_dataset",
        ["num_path_dataset.pyx"],
        extra_compile_args=[
            "-O3",
            "-ffast-math",
            "-march=native",
            # "-fopenmp",
            "-ftree-loop-distribution",
            "-floop-nest-optimize",
            "-floop-block",
        ],
        # extra_link_args=["-fopenmp"],
    )
]

setup(
    ext_modules=cythonize(
        modules,
        compiler_directives={
            "initializedcheck": False,
            "nonecheck": False,
            "language_level": 3,
            "infer_types": True,
            "boundscheck": False,
            "cdivision": True,
        }
    )
)
