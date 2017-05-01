import asyncio
import functools
import os
import sys
import signal
import string
import random

loop = server = None
#str_base = tuple((ord(ch) for ch in string.ascii_letters + string.digits))
str_base = tuple(string.ascii_letters + string.digits)
str_base_size = len(str_base)
once_msg = None
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

    def create_message(self, size=64):
        """Random data.
        """
        if self.rand_msg_mode:
            choice = random.choice
            data = ("".join((choice(str_base) for _ in range(size)))).encode()
            return data + b"\n", len(data)
        else:
            global once_msg
            if not once_msg:
                once_msg = ("-" * size).encode() + b"\n"
            return once_msg, size + 1

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
        msg_size = len(data)
        answer_data, size = self.create_message(msg_size - 1)
        self.stat["output"] += size
        self.stat["input"] += msg_size
        self.connection.write(answer_data)

if '-uvloop' in cmd_args:
    import uvloop
    loop = uvloop.new_event_loop()
else:
    loop = asyncio.get_event_loop()

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
