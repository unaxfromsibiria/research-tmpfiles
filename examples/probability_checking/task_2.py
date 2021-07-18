import numpy as np

# P(A1) = 0.3 P(A2) = 0.6 P(A3) = 0.8
# P(B) = P(A1) + P(A2) + P(A3) - P(A1 * A2) - P(A1 * A3) - P(A2 * A3) + P(A1 * A2 * A3)
# 0.3 + 0.6 + 0.8 - 0.3 * 0.6 - 0.3 * 0.8 - 0.6 * 0.8 + 0.3 * 0.6 * 0.8 = 0.9440000000000001
# checking by an experiment

count = 100_000

p_events = np.array([[0.6], [0.8], [0.3]])
result = p_events @ np.full((1, count), 1)
w, _ = p_events.shape
experiments = np.random.rand(w, count)
experiments_result = ((result > experiments) * 1).T @ np.full((w, 1), 1)

print("Test result", (experiments_result > 0).sum() / count)
# Test result 0.94467
# Test result 0.94383
# Test result 0.9446
# done!
