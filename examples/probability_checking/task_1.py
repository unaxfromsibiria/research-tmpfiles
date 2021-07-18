import sys
import numpy as np
import math


def binomial_coefficient(n: int, r: int) -> int:
    """Binomial coefficient from n for r (like math.comb)"""
    return (
        math.factorial(n) // (math.factorial(r) * math.factorial(n - r))
        if n >= r else
        0
    )


def triangle(size: int) -> str:
    """Pascal's triangle"""
    m = np.full((2, size, size), 1)
    for i in range(size):
        m[0, :, i] = m[1, i, :] = i

    applay_calc = lambda row: binomial_coefficient(row[0], row[1])
    res = np.apply_along_axis(applay_calc, 0, m).T
    max_len = len(str(res.max())) + 1
    cell_tpl = f"{{: <{max_len}}}"

    return "\n".join(
        "{}{}".format(
            (" " * (max_len // 2)) * (size - (res[i] > 0).sum()),
            "".join(
                map(cell_tpl.format, (val for val in res[i] if val > 0))
            )
        )
        for i in range(size)
    )

_, size, *_ = sys.argv
size = int(size)

print(triangle(size))
