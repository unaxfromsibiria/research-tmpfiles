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
        cdef double dt_value, cur_value, new_dt_value, result = 0
        cdef int m_index = int(size / 2)
        cdef bint to_low = size > 0
        cdef bint first_time = True

        while to_low:
            cur_value = self.content[m_index]
            if first_time:
                result = cur_value
                dt_value = _simple_abs(cur_value - value) + 1
                first_time = False
            else:
                dt_value = new_dt_value

            new_dt_value = _simple_abs(cur_value - value)
            to_low = new_dt_value < dt_value
            if to_low:
                result = cur_value
                size = int(size / 2)
                to_low = size > 1
                if to_low:
                    if cur_value > value:
                        m_index = m_index - int(size / 2)
                    else:
                        m_index = m_index + int(size / 2)
        
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

    cdef _insert(self, double value):
        # insert value to needed cell
        cdef int new_index, index = 0
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

    def insert(self, float value):
        """Insert the value with safety of the sorting.
        """
        self._insert(value)

    def get_data(self) -> list:
        """Content as list.
        """
        return [self.content[i] for i in range(self.size)]

    def search(self, float value) -> float:
        """Search an element of array is most closely to the value.
        """
        return self._search_near(value)

    def extend(self, list values):
        """Insert new values.
        """
        for value in values:
            self._insert(value)
