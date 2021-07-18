import numpy as np
# #
# P(Bi|A) = (P(Bi) * P(A|Bi)) / SUM(P(Bj) * P(A|Bj))
# possible results:
# B1 - 1 bad
# B2 - 2 bad
# B3 - 3 bad
# B4 - 0 bad
# P(B1..4) = 1/4
# in fact (selection result) first 3 were good P(A|B4) = 1
# other hypotheses B1..3 after B4 got a fact
# P(A|B1) = (10 - 1)/10 * (10 - 2) / (10 - 1) * (10 - 3) / (10 - 2)
# P(A|B2) = (10 - 2)/10 * (10 - 3) / (10 - 1) * (10 - 4) / (10 - 2)
# P(A|B3) = (10 - 3)/10 * (10 - 4) / (10 - 1) * (10 - 5) / (10 - 2)
# P(B4|A) = P(B4) * P(A|B4) / SUM(P(B1..4) * P(A|B1..4))
# 1/4 * 1 / (1/4 * 1 + sum(1/4 * ((10 - i)/10 * (10 - i - 1) / (10 - 1) * (10 - i - 2) / (10 - 2)) for i in range(1, 4)))               
# 0.4067796610169491

count = 150_000
size = 10
good_state = 1
bad_state = 0
sample_size = 3

states = np.full((count, size), good_state)
# mix bad results
bad_count = (np.random.rand(count) * (sample_size + 1)).astype(np.int32)

total = good_count = 0
for i, b_count in enumerate(bad_count):
    states[i, :b_count] = bad_state
    np.random.shuffle(states[i])
    # get 3 random
    if (states[i, :sample_size] == good_state).sum() != sample_size:
        continue

    # check other
    total += 1
    if (states[i] == good_state).sum() == size:
        good_count += 1

print(good_count / total)

# results:
# 0.406694351437144
# 0.4065328653547329
# 0.4086211762662556
# 0.4086738677771994
# done!
