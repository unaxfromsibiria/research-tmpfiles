import os
import random
import tempfile
import time
import uuid


class PySqMxObj:
    """Simple square matrix.
    """
    content = None

    @property
    def size(self):
        """Get size.
        """
        return len(self.content or '')

    def __init__(self, data: list=[]):
        self.content = []
        for line in data:
            assert len(line) == len(data)
            self.fill(line)

    def load(self, path: str) -> bool:
        """Load from text file.
        """
        with open(path) as mx_data:
            line = True
            while line:
                line = mx_data.readline()
                if line:
                    self.fill(line.split())

        res = self.is_valid
        if not res:
            self.clear()
        return res

    @property
    def is_valid(self):
        """Matrix is square checking.
        """
        n = len(self.content)
        for line in self.content:
            if n != len(line):
                return False
        return True

    def clear(self):
        """Clear content.
        """
        self.content.clear()

    def show(self, size=0):
        """Print content.
        """
        size = size or self.size
        for x in range(size):
            line = " ".join(map("{:.6f}".format, self.content[x][:size]))
            print("|{}|".format(line))

    def save(self, path: str):
        """Save to file.
        """
        with open(path, mode='w') as res:
            for line in self.content:
                line = " ".join(map("{:.6f}".format, line))
                res.write(line + '\n')

    def fill(self, line: list):
        """Append row.
        """
        self.content.append(list(map(float, line)))

    def compact(self, size: int):
        """Squeeze to <size>.
        The calculation of average values in each cell of new matrix.
        """
        m_size = self.size
        step = m_size / size
        res = []
        for x in range(size):
            a_x = int((x - 1) * step)
            if a_x < 0:
                a_x = 0
            b_x = int((x + 1) * step)
            if b_x > m_size:
                b_x = m_size
            new_line = []
            for y in range(size):
                a_y = int((y - 1) * step)
                if a_y < 0:
                    a_y = 0
                b_y = int((y + 1) * step)
                if b_y > m_size:
                    b_y = m_size
                volume = (b_x - a_x) * (b_y - a_y)
                new_line.append(
                    sum((
                        self.content[x_i][y_i]
                        for x_i in range(a_x, b_x)
                        for y_i in range(a_y, b_y)
                    )) / volume)

            res.append(new_line)
        self.content = res


def create_mx(
        path: str = None,
        limits: tuple = (0, 1000),
        size: int = 1024,
        mx_cls: type=PySqMxObj) -> str:
    """Create matrix.
    """
    if not path:
        path = os.path.join(
            tempfile.gettempdir(), "{}_{}.mx".format(uuid.uuid4().hex[:8], size))

    m_res = []
    for _ in range(size):
        line = []
        for _ in range(size):
            line.append(random.random() + float(random.randint(*limits)))
        m_res.append(line)

    mx = mx_cls(m_res)
    mx.save(path)
    return path


def open_mx(path: str, mx_cls: type=PySqMxObj) -> object:
    """Open matrix.
    """
    mx = mx_cls()
    if not mx.load(path):
        mx.clear()
    return mx


def compact_mx(in_path: str, size: int, mx_cls: type=PySqMxObj) -> (str, float):
    """Squeeze matrix to <size> and save.
    """
    st_time = time.time()
    mx = open_mx(in_path, mx_cls=mx_cls)
    second_time = time.time()
    print("open: {:.6f} ms".format((second_time - st_time) * 1000))
    if size >= mx.size:
        return ""
    new_path = in_path.replace(
        "_{}".format(mx.size),
        "_{}".format(size))
    st_time = time.time()
    mx.compact(size)
    second_time = time.time()
    print("squeeze: {:.6f} ms".format((second_time - st_time) * 1000))
    st_time = time.time()
    mx.save(new_path)
    second_time = time.time()
    print("save: {:.6f} ms".format((second_time - st_time) * 1000))
    return new_path, time.time() - st_time
