import re
from libc.stdlib cimport malloc, free, realloc

cdef:
    # some constants
    char _end_line_ch = ord('\n')
    char _write_label_ch = ord('w')
    char _space_ch = ord(' ')

cdef class CmdParser:
    """Helper for data extracting.
    """
    cdef:
        char *_data
        int _size
        int data_size_start_index
        bint _write, _is_full

    def __init__(self):
        self._size = 0
        self.data_size_start_index = 0
        self._write = False
        self._is_full = False
        self._data = NULL

    cdef _clear(self):
        # clear
        if self._size > 0:
            self._size = 0
            free(self._data)

        self._is_full = False
        self._write = False
        self.data_size_start_index = 0

    cdef char _get_el(self, int index):
        """Access method to content.
        """
        if index < self._size and index >= 0 and self._size > 0:
            return self._data[index]
        else:
            return chr(0)

    cdef _fill(self, char *data, int data_size):
        # append data to content
        if self._size > 0:
            self._data = <char *>realloc(self._data, sizeof(char) * (self._size + data_size))
        else:
            self._data = <char *>malloc(sizeof(char) * data_size)
            self._size = 0

        for i in range(data_size):
            self._data[self._size + i] = data[i]

        self._size += data_size
        self._is_full = self._data[self._size - 1] == _end_line_ch
        if self._is_full:
            self._write = self._data[0] == _write_label_ch

    cdef list _extract_array(self):
        # extract array
        cdef int index = self.data_size_start_index
        cdef bint done = True
        cdef char el
        cdef int size = self._size - 1

        result = []
        num = []

        while index < size:
            num.clear()
            done = True
            while done:
                done = self._get_el(index) == _space_ch
                index += 1

            index -= 1
            done = True
            while done:
                el = self._get_el(index)
                done = el != _space_ch
                if done:
                    num.append(chr(el))
                index += 1
                if index >= size:
                    done = False

            result.append(float("".join(num)))

        return result

    cdef str _extract_code(self):
        # extract code
        cdef int index = 0
        cdef char el
        cdef bint done = True

        while done:
            done = self._get_el(index) != _space_ch and index < self.size
            index += 1

        done = True
        while done:
            done = self._get_el(index) == _space_ch
            index += 1

        index -= 1
        done = True
        result = []
        while done:
            # look for code
            el = self._get_el(index)
            done = el != _space_ch and index < self.size
            if done:
                result.append(chr(el))
            index += 1

        self.data_size_start_index = index
        return "".join(result)

    def clear(self):
        """Clean content.
        """
        self._clear()

    @property
    def is_full(self) -> bool:
        """Ready for reading the content.
        """
        return self._is_full

    def fill(self, data: bytes):
        """Append data to content.
        """
        if data:
            self._fill(data, len(data))

    @property
    def is_operation_write(self) -> bool:
        """Command is "write".
        """
        return self._write

    @property
    def is_operation_read(self) -> bool:
        """Command is "read".
        """
        return not self._write

    def get_bytes(self) -> bytes:
        """Get the bytes of current message.
        """
        if self._size > 0:
            return bytes((
                self._data[i] for i in range(self._size - 1)
            ))
        else:
            return b""

    def get_line(self) -> str:
        """Join the string.
        """
        if self._size > 0:
            return "".join((
                # by size, bytes(self._data) is unsafe
                chr(self._data[i]) for i in range(self._size - 1)
            ))
        else:
            return ""

    @property
    def size(self) -> int:
        """Get data size.
        """
        return self._size

    def get_data_fast(self) -> (str, list):
        """Getting the data without converting to string.
        6.49 µs ± 11.6 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
        with float elements:
        7.43 µs ± 19.6 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
        """
        code = self._extract_code()
        return code, self._extract_array()

    def get_data(self) -> (str, list):
        """Getting the data with converting to string
        10.2 µs ± 21.4 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
        with float elements:
        11.4 µs ± 41.3 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
        """
        data = re.split("\s+", self.get_line())
        return data[1], [float(item) for item in data[2:]]
