from libc.stdlib cimport malloc, free, realloc


cdef class SqCcMxObj:
    # Simple matrix like PySqMxObj (the interface is the same)
    cdef:
        double *content
        int m_size
        int content_size

    @property
    def size(self):
        return int(self.m_size)

    def __init__(self, list data=[]):
        self.m_size = len(data)
        self.content_size = 0
        if self.m_size < 1:
            return

        cdef int size = self.m_size * self.m_size
        self.content_size = size
        self.content = <double *>malloc(sizeof(double) * size)
        cdef int i = 0
        for line in data:
            for x in line:
                if i < size:
                    self.content[i] = float(x)
                i += 1

    def fill(self, list line):
        cdef int n = len(line)
        cdef int index = 0
        cdef int size = 0
        if self.m_size == 0:
            self.content_size = n
            self.m_size = n
            self.content = <double *>malloc(sizeof(double) * n)
            for x in line:
                self.content[index] = float(x)
                index += 1
        elif self.m_size == n:
            size = self.content_size + n
            self.content = <double *>realloc(self.content, sizeof(double) * size)
            for x in line:
                self.content[self.content_size + index] = float(x)
                index += 1
            self.content_size = size

    def clear(self):
        if self.m_size > 0:
            free(self.content)
            self.m_size = 0
            self.content_size = 0

    def load(self, str path) -> bool:
        with open(path) as mx_data:
            line = True
            while line:
                line = mx_data.readline()
                if line:
                    self.fill(line.split())

        if self.is_valid:
            return True
        else:
            self.clear()
            return False

    def save(self, path: str):
        # save to file
        cdef str line = ""
        cdef int line_count = 0
        cdef bint is_last = False
        with open(path, mode='w') as res:
            for index in range(self.content_size):
                line_count += 1
                is_last = line_count == self.m_size
                line ="{0:s}{1:.6f}{2}".format(
                    line,
                    self.content[index],
                    "\n" if is_last else " ")

                if is_last:
                    res.write(line)
                    line = ""
                    line_count = 0

    @property
    def is_valid(self) -> bool:
        if self.m_size < 1:
            return True
        else:
            return self.m_size * self.m_size == self.content_size

    def show(self, int size=0):
        cdef int n = size
        cdef str line
        if n < 1:
            n = self.m_size

        if self.m_size > 0:
            for i in range(n):
                line = "|"
                for j in range(n):
                    line = "{}{:.6f}{}".format(
                        line,
                        self.content[i * n + j],
                        "|" if j == n - 1 else " ")
                print(line)
        else:
            print("||")

    cdef double * _compact(self, int size):
        # Calculation of average values in each cell
        cdef int m_size = self.m_size
        cdef int new_content_size = size * size
        cdef double step, el_sum
        cdef double *data = NULL
        cdef int a_x, a_y, b_x, b_y, volume

        if m_size > 0 and size > 0 and m_size > size:
            # step size
            step = float(m_size) / float(size)
            # new matrix
            data = <double *>malloc(sizeof(double) * new_content_size)

            for x in range(size):
                a_x = int((x - 1) * step)
                if a_x < 0:
                    a_x = 0
                b_x = int((x + 1) * step)
                if b_x > m_size:
                    b_x = m_size

                for y in range(size):
                    a_y = int((y - 1) * step)
                    if a_y < 0:
                        a_y = 0
                    b_y = int((y + 1) * step)
                    if b_y > m_size:
                        b_y = m_size

                    # submatrix cells count
                    volume = (b_x - a_x) * (b_y - a_y)
                    el_sum = 0.0
                    for x_i in range(a_x, b_x):
                        for y_i in range(a_y, b_y):
                            el_sum += self.content[x_i * m_size + y_i]

                    data[x * size + y] = el_sum / float(volume)

        return data

    def compact(self, int size):
        cdef double *data = self._compact(size)
        self.clear()
        self.content = data
        self.m_size = size
        self.content_size = size * size
