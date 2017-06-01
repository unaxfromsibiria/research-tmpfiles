import ujson


cdef class MsgHandler:
    """Msg reader and handler.
    """

    cdef public:
        bytearray msg

    cdef char end_bt

    def __cinit__(self):
        self.msg = bytearray()
        self.end_bt = 10

    cdef bytes _processing(self):
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
        client_data = ujson.loads(self.msg.decode())
        cdef double sum_a = 0
        cdef double sum_b = 0
        data_a = client_data["a"]
        data_b = client_data["b"]
        cdef int len_a = len(data_a)
        cdef int len_b = len(data_b)

        for i in range(len_a):
            sum_a += float(data_a[i])

        for i in range(len_b):
            sum_b += float(data_b[i])

        cdef double avg_b = (sum_b / len_b)

        return ujson.dumps({
            "a": "{:0.6f}".format(sum_a),
            "b": "{:0.6f}".format(avg_b),
            "c": "{:0.6f}".format(sum_a /avg_b)
        }).encode() + b"\n"

    def parse(self, bytes data) -> bytes:
        """Method for new data.
        """
        self.msg.extend(data)
        result = None
        cdef int len_d = len(self.msg)
        cdef bint done = (len_d > 0 and self.msg[len_d - 1] == self.end_bt)

        if done:
            result = self._processing()
            self.msg.clear()

        return result
