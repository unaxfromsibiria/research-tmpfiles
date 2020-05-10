# Example of Game Live implemented with Python, Numpy, Cython, Numba, SciPy

About the algorithm https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life

### Benchmark results

Average step execution time:

- Native Python: ~28 ms

- Numpy with cycles: ~33 ms

- SciPy (correlate2d): ~1.5 ms

- Cython: ~0.38 ms

- Numba + Numpy: ~0.34 ms
