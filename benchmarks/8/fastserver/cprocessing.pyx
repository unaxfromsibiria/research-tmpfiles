import ujson

from libc.stdlib cimport malloc, free
from libc.string cimport memcpy


cdef class MsgHandler:
    """Msg reader and handler.
    """

    cdef public:
        char *buffer

    cdef:
        char end_bt
        bint wait_part
        char *tmp
        int new_size, buffer_size, data_size

    def __cinit__(self):
        self.end_bt = 10
        self.wait_part = False

    cdef char* _processing(self):
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
        cdef dict client_data = ujson.loads(self.buffer.decode())
        cdef double sum_a = 0
        cdef double sum_b = 0
        cdef list data_a = client_data["a"]
        cdef list data_b = client_data["b"]
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
        return self.cparse(data)

    cdef char *cparse(self, char *data):
        """Method for new data.
        """

        if self.wait_part:
            self.buffer_size = len(self.buffer)
            self.data_size = len(data)
            self.new_size = sizeof(char) * (self.buffer_size + self.data_size)
            self.tmp = <char *>malloc(self.new_size)
            memcpy(self.tmp, self.buffer, self.buffer_size * sizeof(char))
            memcpy(self.tmp + self.buffer_size, data, self.data_size * sizeof(char))
            self.buffer = self.tmp
        else:
            self.buffer = data

        cdef char *result = NULL
        cdef int len_d = len(self.buffer)
        self.wait_part = not(len_d > 0 and self.buffer[len_d - 1] == self.end_bt)

        if not self.wait_part:
            result = self._processing()
            self.wait_part = False

        return result
