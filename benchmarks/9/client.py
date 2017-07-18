import argparse
import asyncio
import random
import time
import json
import os.path
from uuid import uuid4

parser = argparse.ArgumentParser(
    description="Pool of clent reader/writer to data-map.")

parser.add_argument(
    "--size", dest="size", type=int, default=10,
    help="data file ~size in kb"
)
parser.add_argument(
    "--out", dest="out", type=str, default="",
    help="file for recording test data (json)"
)
parser.add_argument(
    "--data", dest="data", type=str, default="",
    help="file with test data (json)"
)
parser.add_argument(
    "--uvloop", dest="uvloop", type=bool, default=False,
    help="use uvloop"
)
parser.add_argument(
    "--connections", dest="connections", type=int, default=25,
    help="count of connections"
)
parser.add_argument(
    "--server", dest="server", type=str, default="127.0.0.1:8888",
    help="addres of server (host:port)"
)

cmd_args = parser.parse_args()


def create_data_file(
        filepath: str,
        full_size: int,
        cur: int=100000,
        limits: tuple=(-10, 10),
        code_size: int=2) -> tuple:
    """Crate file with test data.
    """

    data = []
    a, b = (val * cur for val in limits)
    size = .0
    cmd_keys = ["r", "w"]
    while size < full_size:
        code = uuid4().hex[:code_size]
        list_size = range(random.randint(1, 20))
        value = " ".join(
            map(str, (random.randint(a, b) / cur for _ in list_size))
        )
        line = "{} {} {}".format(random.choice(cmd_keys), code, value)
        size += (len(line) + 6) / 1024
        data.append(line)

    with open(filepath, mode='w') as file_json:
        file_json.write(json.dumps(data))

    return (
        os.path.getsize(filepath) / 1024,
        sum(map(len, data)),
    )


def read_data(filepath: str) -> list:
    """Read test data.
    """
    with open(filepath) as in_file:
        return [row.encode() + b"\n" for row in json.loads(in_file.read())]


async def tcp_client(
        index: int,
        commands: list,
        ev_loop: object,
        connect_to: tuple,
        stat: dict):
    """Connect TCP.
    """
    print("Start connection", index)
    host, port = connect_to
    results = {}
    try:
        start_time = time.time()
        reader, writer = await asyncio.open_connection(host, port, loop=ev_loop)
        start_time = time.time()
        for line in commands:
            writer.write(line)
            data = await reader.readline()
            if data:
                data = data.decode()
                try:
                    oper_code, value = data.split()
                    # return code and sum
                    value = float(value.strip())
                except Exception as err:
                    print("Error in answer: ", err, "data: ", data)
                    stat["error"] += 1
                else:
                    results[oper_code] = value
        end_time = time.time()

        writer.close()
    except IndexError as err:
        print("Critical error in {} worker:".format(index), err)
        stat["error"] += 1
    else:
        for res_code, value in results.items():
            stat[res_code] = value
    finally:
        stat["time"] += (end_time - start_time) / len(commands)

    print("Stop connection", index)


if cmd_args.out:
    file_data = create_data_file(cmd_args.out, cmd_args.size)
    print("File {} created with size: {} kb and {} commands.".format(
        cmd_args.out, *file_data))

elif cmd_args.data and cmd_args.server:
    data = read_data(cmd_args.data)
    if cmd_args.uvloop:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    workers = cmd_args.connections
    chunk_size = len(data) // workers
    server = cmd_args.server.split(":")
    server = server[0], int(server[1])
    loop = asyncio.get_event_loop()
    statistic = {"time": .0, "error": 0}
    try:
        loop.run_until_complete(
            asyncio.gather(*(
                tcp_client(
                    index + 1,
                    data[index * chunk_size:(index + 1) * chunk_size],
                    loop,
                    server,
                    statistic)
                for index in range(workers)
            ))
        )
        loop.close()
    finally:
        statistic["time"] = statistic["time"] / workers * 1000
        result_msg = (
            "Avg command: {time:0.6f} ms errors: {error}".format(**statistic))
        del statistic["time"]
        del statistic["error"]
        for code in sorted(statistic.keys()):
            print("{} = {:0.6f}".format(code, statistic[code]))
        print(result_msg)
