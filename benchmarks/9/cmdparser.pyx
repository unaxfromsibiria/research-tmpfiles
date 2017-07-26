from libc.stdlib cimport malloc, free, realloc

cdef:
    # some constants
    char _end_line_ch = ord('\n')
    char _write_label_ch = ord('w')

cdef class CmdParser:
    """Helper for data extracting.
    """
    cdef:
        char *_data
        int size
        bint _write, _is_full

    def __init__(self):
        self.size = 0
        self._write = False
        self._is_full = False
        self._data = NULL

    cdef _clear(self):
        # clear
        if self.size > 0:
            self.size = 0
            free(self._data)

        self._is_full = False
        self._write = None

    def _fill(self, char *data, int data_size):
        # append data to content
        if self.size > 0:
            self._data = <char *>realloc(self._data, sizeof(char) * (self.size + data_size))
        else:
            self._data = <char *>malloc(sizeof(char) * data_size)
            self.size = 0

        for i in range(data_size):
            self._data[self.size + i] = data[i]

        self.size += data_size
        self._is_full = self._data[self.size - 1] == _end_line_ch
        if self._is_full:
            self._write = self._data[0] == _write_label_ch

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

    def get_data(self) -> bytes:
        """Get the bytes of current message.
        """
        if self.size > 0:
            return bytes(self._data)


    def get_size(self) -> int:
        """Get data size.
        """
        return self.size
