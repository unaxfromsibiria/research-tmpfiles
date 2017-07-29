from libc.stdlib cimport malloc, free, realloc


cdef double _simple_abs(double value):
    # local abs method
    if value < 0:
        return value * -1
    else:
        return value


cdef class CellStorage:
    """Sorted array with methods of searching
    """
    cdef:
        double *content
        int size

    def __init__(self):
        self.size = 0

    def clear(self):
        # clear content
        if self.size > 0:
            free(self.content)
            self.size = 0

    cdef _search_near(self, double value):
        # search near element from array by value
        cdef int size = self.size
        cdef int half_size = 0
        cdef double dt_value = 0, val = 0, new_dt_value = 0, result = 0
        cdef int m_index = int(size / 2)

        while size > 1:
            val = self.content[m_index]
            size = int(size / 2)
            half_size = int(size / 2)
            if half_size < 0:
                half_size = 0
            if val > value and size > 0 and m_index > 0:
                m_index = m_index - half_size
            elif m_index < self.size - 1:
                m_index = m_index - half_size

        result = self.content[m_index]
        dt_value = _simple_abs(result - value)

        if m_index > 0:
            val = self.content[m_index - 1]
            new_dt_value = _simple_abs(val - value)
            if dt_value > new_dt_value:
                result = val
                dt_value = new_dt_value

        if m_index < self.size - 1:
            val = self.content[m_index + 1]
            new_dt_value = _simple_abs(val - value)
            if dt_value > new_dt_value:
                result = val
                dt_value = new_dt_value

        return result

    cdef int _search_insert_index(self, double value):
        # search insert index
        cdef int result = 0
        for i in range(self.size):
            if value > self.content[i]:
                result = i + 1

            if value < self.content[i]:
                return result

        return result

    cdef double _sum(self):
        # calc sum
        cdef double result = 0
        if self.size > 0:
            for i in range(self.size):
                result += self.content[i]
        return result

    cdef _insert(self, double value):
        # insert value to needed cell
        cdef int new_index = 0, index = 0
        if self.size > 0:
            self.size += 1
            self.content = <double *>realloc(self.content, sizeof(double) * self.size)
            # search position
            new_index = self._search_insert_index(value)
            if new_index >= self.size:
                # to end
                self.content[self.size - 1] = value
            else:
                # move to right
                index = self.size
                while index > new_index:
                    self.content[index - 1] = self.content[index - 2]
                    index -= 1

                self.content[new_index] = value

        else:
            # first value
            self.size = 1
            self.content = <double *>malloc(sizeof(double) * self.size)
            self.content[0] = value

    cdef double _search_variant(self, list data):
        # search value with min dt value
        cdef double dt_value = -1, new_dt_value = 0, val = 0
        cdef double result = 0, x = 0
        for el in data:
            x = el
            val = self._search_near(x)
            new_dt_value = _simple_abs(val - x)

            if dt_value >= 0:
                if new_dt_value < dt_value:
                    dt_value = new_dt_value
                    result = val
            else:
                dt_value = new_dt_value
                result = val

        return result

    def insert(self, float value):
        """Insert the value with safety of the sorting.
        """
        self._insert(value)

    def get_data(self) -> list:
        """Content as list.
        """
        return [self.content[i] for i in range(self.size)]

    def sum(self) -> float:
        """Calc sum.
        """
        return self._sum()

    def search(self, float value) -> float:
        """Search an element of array is most closely to the value.
        """
        return self._search_near(value)

    def search_variant(self, list data) -> float:
        """Search in many values.
        """
        return self._search_variant(data)

    def extend(self, list values):
        """Insert new values.
        """
        for value in values:
            self._insert(value)
