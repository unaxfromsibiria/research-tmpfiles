import asyncio
import functools
import os
import signal
import sys
from multiprocessing import Manager, Process, cpu_count
from socket import SO_REUSEADDR, SOL_SOCKET, socket

import uvloop

# needed python setup_processing.py build_ext --inplace
from fastserver import cprocessing

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
cmd_args = set(sys.argv[1:])
worker_count = cpu_count()
host, port = '0.0.0.0', 8888
for cmd_arg in cmd_args:
    if '--workers' in cmd_arg:
        try:
            worker_count = int(cmd_arg.split('=')[-1].strip())
        except (ValueError, TypeError):
            pass

    try:
        host, port = cmd_arg.split(':')
        port = int(port)
    except (ValueError, TypeError):
        continue
    else:
        break


def ask_exit(signal_name, index, server, loop):
    """Terminate method.
    """
    print("got signal {}: exit in worker {}".format(signal_name, index))
    server.close()
    loop.stop()


def run_server(worker_index: int, in_socket, result_stat: dict):
    """Create asyncio net server worker.
    """
    stat = {"input": 0, "output": 0}

    class EchoServerCountTraf(asyncio.Protocol):
        """Count volume of input/output data.
        """
        connection = None
        handler = None
        in_size = out_size = 0

        def connection_made(self, transport):
            """Prepare connection.
            """
            peername = transport.get_extra_info('peername')
            print('Connection from {}'.format(peername))
            self.connection = transport
            self.handler = cprocessing.MsgHandler()
            self.in_size = 0
            self.out_size = 0

        def data_received(self, data):
            """Read/write socket.
            """
            if data[:4] == b"exit":
                print("Close the client socket")
                self.connection.close()
            else:
                self.in_size += len(data)
                answer_data = self.handler.parse(data)
                if answer_data:
                    self.out_size += len(data)
                    self.connection.write(answer_data)

        def connection_lost(self, exc):
            stat["input"] += self.in_size
            stat["output"] += self.out_size
            result_stat["input"] += self.in_size
            result_stat["output"] += self.out_size

    loop = asyncio.get_event_loop()
    listen = loop.create_server(
        EchoServerCountTraf,
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
        print(
            "in worker {index} input: {input} "
            "output: {output}".format(
                index=worker_index, **stat))


def run_workers(workers_count: int):
    """Open socket and run workers.
    """
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.set_inheritable(True)
    pid_list = []

    def main_sig_handler(*args):
        """Main stop signal handler.
        """
        for pid in pid_list:
            os.kill(pid, signal.SIGINT)

    for signame in ('SIGINT', 'SIGTERM'):
        signal.signal(getattr(signal, signame), main_sig_handler)

    processes = []
    manager = Manager()
    results = manager.dict()
    results["input"] = 0
    results["output"] = 0
    for index in range(workers_count):
        process = Process(
            target=run_server,
            args=(index + 1, sock, results))
        process.daemon = True
        process.start()
        processes.append(process)
        pid_list.append(process.pid)

    for process in processes:
        process.join()

    # the above processes will block this until they're stopped
    for process in processes:
        process.terminate()

    sock.close()
    print("""Total:
        input: {input}
        output: {output}
        """.format(**results))


# run workers
run_workers(worker_count)
