# Example of Game Live implemented with Python, Numpy, Cython, Numba, CFFI, SciPy, Rust+Ctypes

About the algorithm https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life

Run as:

```
in game_life_benchmark$ ipython

from life_scipy import Areal
areal = Areal(420, 10_000)
an = areal.animate(1500)
```

### Benchmark results

Average step execution time with areal size 128x128:

```
- Native Python: ~28 ms

- Numpy with cycles: ~33 ms

- SciPy (correlate2d): ~1.5 ms

- Cython with OMP (4 cpu): ~0.96 ms

- Cython: ~0.38 ms

- CFFI + Numpy: ~0.36 ms

- Rust + Ctypes + Numpy: ~0.36 ms

- Numba + Numpy: ~0.34 ms
```

Average step execution time with areal size 256x256:

```
- SciPy (correlate2d): ~5.0 ms

- Numba + Numpy: ~1.40 ms

- Cython with OMP (4 cpu): ~1.36 ms

- CFFI + Numpy: ~1.35 ms

- Cython: ~1.02 ms

- Rust + Ctypes + Numpy: ~1.01 ms
```

Average step execution time with areal size 420x420:

```
- CFFI + Numpy: ~3.19 ms

- Numba + Numpy: ~2.75 ms

- Rust + Ctypes + Numpy: ~2.64 ms

- Cython: ~2.24 ms

- Cython with OMP (4 cpu): ~1.75 ms
```
