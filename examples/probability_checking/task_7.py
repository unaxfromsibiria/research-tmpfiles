import numpy as np

# one side of the coin P(A) = 0.5
# 10 attempt, 5 results should be in one side and 5 with another
# by Bernoulli formula
# n = 10, k = 5
# Pn(k) = comb(n, k) * P(A) ** k * (1 - P(A)) ** (n - k)
# math.comb(n, k) * 0.5 ** k * (1 - 0.5) ** (n - k)                                                                                                                                         
# 0.24609375

count = 1_000_000
p_a = 0.5
attempt = 10

event_count = 0
for _ in range(count):
    experiments = (np.random.rand(attempt) < p_a) * 1
    if experiments.sum() == attempt // 2:
        event_count += 1

print(event_count / count)

# 0.245791
# 0.246219
# 0.245601
# 0.245751
# done!
