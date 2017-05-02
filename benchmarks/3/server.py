import asyncio
import json
import functools
import os
import sys
import signal
import string
import random
import msg_pb2 as protomsg

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
    show_all_mode = '-show' in cmd_args

    def connection_made(self, transport):
        """Prepare connection.
        """
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.connection = transport
        global statistic
        self.stat = statistic

    def create_message(self, client_data: bytes) -> tuple:
        """Convert data to protobuf message DataMsg
        message DataMsg {
            repeated float a = 1 [packed=true];
            repeated float b = 2 [packed=true];
        }
        Create answer as:
        message DataAnswer {
            required float a = 1;
            required float b = 2;
            required float c = 3;
        }
        """
        try:
            msg = protomsg.DataMsg()
            msg.ParseFromString(client_data)
            msgA = msg.a
            msgB = msg.b
            a, b = sum(msgA), sum(msgB) / len(msgB)
            answer = protomsg.DataAnswer(
                a=a, b=b, c=a / b)
        except ValueError as err:
            print("Error:", err)
            print(client_data)
            result = b"error"
        else:
            result = answer.SerializeToString()
            if self.show_all_mode:
                print((
                    "DataAnswer(a:{answer.a},b:{answer.b},c: {answer.c})"  # noqa
                ).format(answer=answer))

        return result, len(result)

    def data_received(self, data):
        """Read/write socket.
        """
        self.stat["input"] += len(data)
        try:
            answer_data, size = self.create_message(data)
        except Exception as err:
            try:
                message = data.decode()
                if message == "exit":
                    print("Close the client socket")
                    self.connection.close()
            except UnicodeDecodeError:
                print("Decode error", data)
        else:
            self.stat["output"] += size
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
