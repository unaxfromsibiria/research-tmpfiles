import numpy as np
import random

# in 1 km event P(A) = 0.1%, how many kilometers to get it in 99%
#
# Pn(k) = n! / (k! * (n - k)!) * P(A) ** k * (1 - P(A)) ** (n - k) Bernoulli formula
# n! / (k! * (n - k)!) = comb(n, k)
# k = 0, n = ?
# Pn(0) = 1 - (1 - P(A)) ** n
# (1 - P(A)) ** n = 1 - Pn(0)
# n = log(1 - Pn(0), 1 - P(A))
# Pn(0) >= 1 - (1 - P(A)) ** int(n)
# n = int(n + 1)
# n = int(1 + math.log(1 - 0.99, 1 - 0.001))
# 4603 km

# checking by an experiment
count = 200_000
p_a = 0.001
limit_perc = 99
result = np.zeros((count,)).astype(int)


for i in range(count):
    n = 0
    event = p_a * 2
    index = 0
    while event >= p_a:
        event = random.random()
        index += 1

    result[i] = index

print(np.percentile(result, limit_perc))

# 4606.010000000009
# 4639.010000000009
# 4593.010000000009
# 4611.0
# done!
