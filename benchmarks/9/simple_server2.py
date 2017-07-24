import argparse
import asyncio
import functools
import os
import signal
from multiprocessing import Process, cpu_count
from multiprocessing.managers import BaseManager
from socket import SO_REUSEADDR, SOL_SOCKET, socket

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
    "--worker", dest="worker", type=int, default=cpu_count(),
    help="Workers by multiprocessing."
)

parser.add_argument(
    "--uvloop", dest="uvloop", type=bool, default=False,
    help="Uses uvloop."
)


class LocalManager(BaseManager):
    """MP Manager class for registration custom shared classes.
    """
    pass


class StorageDict:
    """Concurency dict proxy.
    """
    _data = None
    cell_cls = list

    def __init__(self):
        self._data = {}

    def get(self, key: str):
        """Get by key.
        """
        return self._data.get(key)

    def exists(self, key: str):
        """Check the key in content.
        """
        return key in self._data

    def insert(self, key: str, index: int, value: float):
        """Insert by key and index.
        """
        self._data[key].insert(index, value)

    def search(self, key: str, value: float) -> int:
        """Get index of cell for new value.
        """
        if key not in self._data:
            self._data[key] = self.cell_cls()

        result = 0
        for i, el in enumerate(self._data[key]):
            if value > el:
                result = i + 1

            if value < el:
                return result

        return result

    def near_value(self, key: str, value: float) -> float:
        """Look for value in array (by key) near the value.
        """
        data = self._data.get(key)
        if not data:
            return 0

        # binary search
        value = 0
        dt_value = None
        m_index = len(data) // 2
        to_low = True
        while to_low:
            cur_value = data[m_index]
            if dt_value is None:
                dt_value = abs(cur_value - value) + 1

            new_dt_value = abs(cur_value - value)
            to_low = new_dt_value < dt_value
            if to_low:
                value = cur_value
                if cur_value > value:
                    data = data[:m_index]
                else:
                    data = data[m_index:]
                m_index = len(data) // 2
                to_low = len(data) > 1

        return value


LocalManager.register("StorageDict", StorageDict)


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

    def __init__(self, storage_dict: StorageDict):
        self.data = storage_dict

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
                use_index = self.data.search(code, val)
                self.data.insert(code, use_index, val)

        return code

    def read(self, data: bytes) -> (str, float):
        """Main read method.
        """
        items = data.decode().split()
        code = None
        result = None
        min_dt = None
        for index, val in enumerate(items):
            if index == 0 or not val:
                continue

            if index == 1:
                code = val
            elif code:
                val = float(val)
                value = self.data.near_value(code, val)
                new_min_dt = abs(value - val)
                if result:
                    if min_dt > new_min_dt:
                        min_dt = new_min_dt
                        result = value
                else:
                    min_dt = new_min_dt
                    result = value

        return code, result

    def sum(self, code: str) -> float:
        """Get sum of values by code.
        """
        data = self.data.get(code)
        return sum(data) if data else 0


def ask_exit(signal_name, index, server, loop):
    """Terminate method.
    """
    print("got signal {}: exit in worker {}".format(signal_name, index))
    server.close()
    loop.stop()


def run_server(
        worker_index: int,
        in_socket: object,
        storage_dict: dict,
        use_uvloop: bool=False):
    """Create asyncio net server worker.
    """

    class ValuesMapProcessor(asyncio.Protocol):
        """Count volume of input/output data.
        """
        parser = connection = None
        storage = DataStorage(storage_dict)

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
                        code = self.storage.write(self.parser.get_data())
                        if code:
                            value = "w", code, self.storage.sum(code)
                    else:
                        code, value = self.storage.read(self.parser.get_data())
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
            functools.partial(ask_exit, signame, worker_index, server, loop))

    print('Worker {} started on {}'.format(
        worker_index, server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    finally:
        loop.close()


def run_workers():
    """Open socket and run workers.
    """
    cmd_data = parser.parse_args()
    workers_count = cmd_data.worker
    server_socket = (cmd_data.addr, cmd_data.port)
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(server_socket)
    sock.set_inheritable(True)
    pid_list = []
    print("Server started at {}:{}.".format(*server_socket))
    if cmd_data.uvloop:
        print("Uses uvloop.")

    def main_sig_handler(*args):
        """Main stop signal handler.
        """
        for pid in pid_list:
            os.kill(pid, signal.SIGINT)

    for signame in ('SIGINT', 'SIGTERM'):
        signal.signal(getattr(signal, signame), main_sig_handler)

    processes = []
    manager = LocalManager()
    manager.start()

    storage_dict = manager.StorageDict()
    for index in range(workers_count):
        process = Process(
            target=run_server,
            args=(index + 1, sock, storage_dict, cmd_data.uvloop))

        process.daemon = True
        process.start()
        processes.append(process)
        pid_list.append(process.pid)

    for process in processes:
        process.join()

    for process in processes:
        process.terminate()

    sock.close()


# run all
run_workers()
