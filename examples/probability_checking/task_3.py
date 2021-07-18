import numpy as np

# P(A) = SUM(P(Bi) * P(A|Bi))
# after 5 selects possible 3 results - B
# B1 - from 10 chosen 1 bad and 4 good objects
# B2 - from 10 chosen 2 bad and 3 good objects
# B3 - from 10 chosen 5 good objects
# combinations
# P(B1) - math.comb(2, 1) * math.comb(8, 4) / math.comb(10, 5)
# P(B2) - math.comb(2, 2) * math.comb(8, 3) / math.comb(10, 5)
# P(B3) - math.comb(8, 5) / math.comb(10, 5)
# and P(A|B1..3) = remains of bad 1..3 / total remains = x / 15
# full formula
# P(A) = SUM(P(B1..3) * P(A|B1..3))
# (
#   math.comb(2, 1) * math.comb(8, 4) / math.comb(10, 5) * 5 / 15
# ) + (
#   math.comb(2, 2) * math.comb(8, 3) / math.comb(10, 5) * 4 / 15
# ) + (
#   math.comb(8, 5) / math.comb(10, 5) * 6 / 15
# )
# result 0.3333333333333333 by formula

# checking by an experiment
box_count = 2
count = 10_000
state_variants = 2
# object in box is bad or good
bad_index = 0
good_index = 1
box_states = np.full((count, box_count, state_variants), 1)
# begin state
# in 1
box_states[:, 0, good_index] = 8  # 8 good
box_states[:, 0, bad_index] = 2  # 2 bad
# in 2
box_states[:, 1, good_index] = 6  # 6 good
box_states[:, 1, bad_index] = 4  # 4 bad

experiments = np.zeros((count,))

select = 5
for i in range(count):
    # first selection
    n = box_states[i, 0, good_index]
    m = box_states[i, 0, bad_index]
    state: np.array = np.full((n + m,), good_index)
    state[:m] = bad_index
    np.random.shuffle(state)
    part = state[:select]
    remain_n = (part == good_index).sum()
    remain_m = (part == bad_index).sum()
    assert remain_n + remain_m  == n + m - select
    # remains moves
    box_states[i, 1, good_index] += remain_n
    box_states[i, 1, bad_index] += remain_m
    # probability of one choice of the bad object
    experiments[i] = box_states[i, 1, bad_index] / (
        box_states[i, 1, bad_index] + box_states[i, 1, good_index]
    )

print(experiments.mean())

# results:
# 0.3336333333333333
# 0.33396
# 0.3330066666666667
# 0.3338933333333333
# done!
