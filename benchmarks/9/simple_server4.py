import argparse
import asyncio
import functools
import os
import signal
from multiprocessing import Process, cpu_count
from multiprocessing.managers import BaseManager
from socket import SO_REUSEADDR, SOL_SOCKET, socket

from cmdparser import CmdParser
from storage import CellStorage

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


class DataStorage:
    """Combines the methods of storage.
    """
    data = None

    def __init__(self):
        self.data = {}
        self.parser = CmdParser()

    def write(self, data: bytes) -> str:
        """Main write method.
        """
        self.parser.clear()
        self.parser.fill(data)
        code, data = self.parser.get_data_fast()
        if code not in self.data:
            self.data[code] = CellStorage()
        self.data[code].extend(data)
        return code

    def read(self, data: bytes) -> (str, float):
        """Main read method.
        """
        self.parser.clear()
        self.parser.fill(data)
        result = 0.0
        code, data = self.parser.get_data_fast()
        stor = self.data.get(code)
        if stor:
            result = stor.search_variant(data)
        return code, result

    def sum(self, code: str) -> float:
        """Get sum of values by code.
        """
        stor = self.data.get(code)
        return stor.sum() if stor else 0.0


class LocalManager(BaseManager):
    """MP Manager class for registration custom shared classes.
    """
    pass

LocalManager.register("Storage", DataStorage)


def ask_exit(signal_name, index, server, loop):
    """Terminate method.
    """
    print("got signal {}: exit in worker {}".format(signal_name, index))
    server.close()
    loop.stop()


def run_server(
        worker_index: int,
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
            self.parser = CmdParser()

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
                        code = storage.write(self.parser.get_bytes())
                        if code:
                            value = "w", code, storage.sum(code)
                    else:
                        code, value = storage.read(self.parser.get_bytes())
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

    storage = manager.Storage()
    for index in range(workers_count):
        process = Process(
            target=run_server,
            args=(index + 1, sock, storage, cmd_data.uvloop))

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
