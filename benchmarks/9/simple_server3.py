import argparse
import asyncio
import functools
import signal
from socket import socket

parser = argparse.ArgumentParser(
    description="Server for data processing.")

parser.add_argument(
    "--addr", dest="addr", type=str, default="127.0.0.1",
    help="This server host addres."
)

parser.add_argument(
    "--port", dest="port", type=int, default=8888,
    help="This server port."
)

parser.add_argument(
    "--uvloop", dest="uvloop", type=bool, default=False,
    help="Uses uvloop."
)


class CommandParser:
    """Helper for data extracting.
    """
    _write = _data = None
    _is_full = None
    target_code = None
    _end_line_ch = ord(b"\n")
    _write_label_ch = ord(b"w")

    def __init__(self):
        self._data = bytearray()
        self._write = False
        self._is_full = False

    def clear(self):
        """Clean content.
        """
        self._data.clear()
        self._is_full = False

    @property
    def is_full(self) -> bool:
        """Ready for reading the content.
        """
        return self._is_full

    def fill(self, data: bytes):
        """Append data to content.
        """
        self._data.extend(data)
        self._is_full = self._data and (self._data[-1] == self._end_line_ch)
        if self._is_full:
            self._write = self._data[0] == self._write_label_ch

    @property
    def is_operation_write(self) -> bool:
        """Command is "write".
        """
        return self._write

    @property
    def is_operation_read(self) -> bool:
        """Command is "read"
        """
        return not self._write

    def get_data(self) -> bytes:
        """Get the bytes of current message.
        """
        return self._data


class DataStorage:
    """Combines the methods of storage.
    """
    data = None

    def __init__(self):
        self.data = {}

    def write(self, data: bytes) -> str:
        """Main write method.
        """
        items = data.decode().split()
        code = None
        for index, val in enumerate(items):
            if index == 0 or not val:
                continue

            if index == 1:
                code = val
            elif code:
                val = float(val)
                if code not in self.data:
                    self.data[code] = []

                use_index = 0
                for i, el in enumerate(self.data[code]):
                    if val > el:
                        use_index = i + 1

                    if val < el:
                        break

                self.data[code].insert(use_index, val)

        return code

    def read(self, data: bytes) -> (str, float):
        """Main read method.
        """
        items = data.decode().split()
        code = None
        result = None
        min_dt = None
        for index, value in enumerate(items):
            if index == 0 or not value:
                continue
            if index == 1:
                code = value
            elif code:
                value = float(value)
                data = self.data.get(code)
                if not data:
                    break

                size = orig_size = len(data)
                val = 0
                dt_value = None

                # binary search
                m_index = size // 2
                while size > 1:
                    val = data[m_index]
                    size = size // 2
                    h_size = (size // 2) or 1
                    if val > value and size > 0 and m_index > 0:
                        m_index = m_index - h_size
                    elif m_index < orig_size - 1:
                        m_index = m_index + h_size

                iter_result = data[m_index]
                dt_value = abs(iter_result - value)

                if m_index > 0:
                    val = data[m_index - 1]
                    new_dt_value = abs(val - value)
                    if dt_value > new_dt_value:
                        iter_result = val
                        dt_value = new_dt_value

                if m_index < orig_size - 1:
                    val = data[m_index + 1]
                    new_dt_value = abs(val - value)
                    if dt_value > new_dt_value:
                        iter_result = val
                        dt_value = new_dt_value

                new_min_dt = dt_value
                if result:
                    if min_dt > new_min_dt:
                        min_dt = new_min_dt
                        result = iter_result
                else:
                    min_dt = new_min_dt
                    result = iter_result

        return code, result

    def sum(self, code: str) -> float:
        """Get sum of values by code.
        """
        data = self.data.get(code)
        return sum(data) if data else 0


def ask_exit(signal_name, server, loop):
    """Terminate method.
    """
    print("got signal {}: exit".format(signal_name))
    server.close()
    loop.stop()


def run_server(
        in_socket: object,
        storage: DataStorage,
        use_uvloop: bool=False):
    """Create asyncio net server worker.
    """

    class ValuesMapProcessor(asyncio.Protocol):
        """Count volume of input/output data.
        """
        parser = connection = None

        def connection_made(self, transport):
            """Prepare connection.
            """
            peername = transport.get_extra_info('peername')
            print('Connection from {}'.format(peername))
            self.connection = transport
            self.parser = CommandParser()

        def data_received(self, data):
            """Read/write socket.
            """
            if data[:4] == b"exit":
                print("Close the client socket")
                self.connection.close()
            else:
                self.parser.fill(data)
                if self.parser.is_full:
                    answer = "error\n"
                    value = None
                    if self.parser.is_operation_write:
                        code = storage.write(self.parser.get_data())
                        if code:
                            value = "w", code, storage.sum(code)
                    else:
                        code, value = storage.read(self.parser.get_data())
                        if code:
                            value = "r", code, value or 0

                    if value:
                        answer = "{}.{} {:.6f}\n".format(*value)

                    try:
                        self.connection.write(answer.encode())
                    finally:
                        self.parser.clear()

        def connection_lost(self, exc):
            pass

    if use_uvloop:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    loop = asyncio.get_event_loop()
    listen = loop.create_server(
        ValuesMapProcessor,
        host=None,
        port=None,
        reuse_port=True,
        sock=in_socket)

    server = loop.run_until_complete(listen)

    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(ask_exit, signame, server, loop))

    print('Worker {} started'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    finally:
        loop.close()


def run_workers():
    """Open socket and run workers.
    """
    cmd_data = parser.parse_args()
    server_socket = (cmd_data.addr, cmd_data.port)
    sock = socket()
    sock.bind(server_socket)
    sock.set_inheritable(True)

    print("Server started at {}:{}.".format(*server_socket))
    if cmd_data.uvloop:
        print("Uses uvloop.")

    try:
        run_server(sock, DataStorage(), cmd_data.uvloop)
    finally:
        sock.close()


# run all
run_workers()
