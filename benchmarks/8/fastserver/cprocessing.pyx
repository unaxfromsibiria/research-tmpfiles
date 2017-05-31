import ujson

cdef (double, double, double) _calc_answer(list data_a, list data_b):
    """With optimization general calc function.
    """
    cdef double sum_a = 0
    cdef double sum_b = 0
    cdef int len_a = len(data_a)
    cdef int len_b = len(data_b)

    for i in range(len_a):
        sum_a += float(data_a[i])

    for i in range(len_b):
        sum_b += float(data_b[i])

    cdef double avg_b = (sum_b / len_b)
    return sum_a, avg_b, sum_a / avg_b


def calc_answer(json_data: str) -> str:
    """API method. Data format (input/output):
        {
            "a": [23, 1 ... 3],
            "b": [4, 5, 6...5],
        }
        Answer:
        {
            "a": sum(a),
            "b": avg(b),
            "c": sum(a) / avg(b),
        }
    """
    client_data = ujson.loads(json_data)
    a, b, c = _calc_answer(client_data["a"], client_data["b"])
    result = {
        "a": "{:0.6f}".format(a),
        "b": "{:0.6f}".format(b),
        "c": "{:0.6f}".format(c)
    }
    return ujson.dumps(result) + "\n"
