
import uvloop
import asyncio
import functools
import os
import sys
import signal
# needed python setup_processing.py build_ext --inplace
from fastserver import cprocessing

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
server = None
loop = asyncio.get_event_loop()
cmd_args = set(sys.argv[1:])
statistic = {"input": 0, "output": 0}


def ask_exit(signal_name):
    """Terminate method.
    """
    print("got signal {}: exit".format(signal_name))
    print("Statistic: \n{}".format(
        "\n".join(
            ("{} = {}".format(*row) for row in statistic.items())
        )
    ))
    server.close()
    loop.stop()


class EchoServerCountTraf(asyncio.Protocol):
    """Count volume of input/output data.
    """
    connection = None
    stat = None
    rand_msg_mode = '-rand_msg' in cmd_args

    def connection_made(self, transport):
        """Prepare connection.
        """
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.connection = transport
        global statistic
        self.stat = statistic

    def data_received(self, data):
        """Read/write socket.
        """
        try:
            message = data.decode()
        except UnicodeDecodeError:
            print(data)
            message = "unknown"
        else:
            message = message.strip()

        if message == "exit":
            print("Close the client socket")
            self.connection.close()
        else:
            msg_size = len(data)
            answer_data = cprocessing.calc_answer(message).encode()
            self.stat["output"] += len(answer_data)
            self.stat["input"] += msg_size
            self.connection.write(answer_data)


for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(
        getattr(signal, signame),
        functools.partial(ask_exit, signame))


host, port = '0.0.0.0', 8888
for cmd_arg in cmd_args:
    try:
        host, port = cmd_arg.split(':')
        port = int(port)
    except (ValueError, TypeError):
        continue
    else:
        break

listen = loop.create_server(EchoServerCountTraf, host, port)
server = loop.run_until_complete(listen)

print('Serving on {}'.format(server.sockets[0].getsockname()))

try:
    loop.run_forever()
finally:
    loop.close()
