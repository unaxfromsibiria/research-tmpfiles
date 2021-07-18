import numpy as np

# #
# P(Bi|A) = (P(Bi) * P(A|Bi)) / SUM(P(Bj) * P(A|Bj))
# accuracy 1 - 80%
# accuracy 2 - 70%
# accuracy 3 - 60%
# P(A|B) = 1 (2 events done). That was 3?
# that was 3 P(B1) = 0.8 * 0.7 * (1 - 0.6)
# that was 2 P(B2) = 0.8 * (1 - 0.7) * 0.6
# that was 1 P(B3) = (1 - 0.8) * 0.7 * 0.6
# (P(B1)) / SUM(P(B1..3))
# 0.22399999999999998 / sum((0.22399999999999998, 0.14400000000000002, 0.08399999999999998)) = 0.49557522123893805

# checking the Bayes' formula by an experiment

count = 1_000_000
p_events = [0.8, 0.7, 0.6]
wrong_index = 2
size = len(p_events)

limits = np.zeros((size, count))
for i, p_val in enumerate(p_events):
    limits[i, :] = p_val

experiments = (np.random.rand(size, count) <= limits) * 1
two_sum_filter = experiments.T @ np.full((size, 1), 1) == 2
experiments: np.array = experiments[:, two_sum_filter[:, 0]]

_, count = experiments.shape
result = (experiments[wrong_index] == 0).sum() / count
print(result)

# 0.4950009971415276
# 0.4963626548194824
# 0.49545640605812524
# 0.4953349808952146
# done!
