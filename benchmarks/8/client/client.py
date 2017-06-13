import argparse
import asyncio
import random
import time

try:
    import ujson as json
except Exception:
    import json

parser = argparse.ArgumentParser(
    description="Pool of tcp clients with test data.")

parser.add_argument(
    "--count", dest="count", type=int, default=10,
    help="connection count"
)

parser.add_argument(
    "--msg", dest="msg", type=int, default=10,
    help="messages count"
)

parser.add_argument(
    "--host", dest="host", type=str, default="127.0.0.1",
    help="connection to host"
)

parser.add_argument(
    "--port", dest="port", type=int, default=8888,
    help="connection with port"
)

parser.add_argument(
    "--uvloop", dest="uvloop", type=bool, default=False,
    help="use uvloop"
)

parser.add_argument(
    "--norandom", dest="norandom", type=bool, default=False,
    help="without random (faster case)"
)

cmd_args = parser.parse_args()

if cmd_args.uvloop:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


cmd_data_set = [
    json.dumps({
        "a": [
            "{:0.6f}".format(random.randint(10, 10000) / 1000)
            for _ in range(random.randint(5, 20))
        ],
        "b": [
            "{:0.6f}".format(random.randint(10, 10000) / 1000)
            for _ in range(random.randint(5, 20))
        ],
    }).encode() + b"\n"
    for _ in range(1000)
]

# once variant of test data
once_msg = json.dumps({
    "a": [
        "6.810000", "2.494000", "4.617000", "3.518033",
        "1.26035", "5.802000", "6.854045", "0.084022",
        "4.678", "4.67875", "6.7788", "29.46754", "2/345345"
    ],
    "b": [
        "6.14505", "5.762000", "9.167000", "9.255000", "2.678000",
        "5.84934", "4.031000", "6.785000", "2.015000", "1.013000", "6.132000",
        "3.184000", "2.613012", "9.938000", "4.146000",
    ]
}).encode() + b"\n"


def create_msg(no_random: bool=False) -> bytes:
    """Return message data.
    """
    if no_random:
        return once_msg
    else:
        return random.choice(cmd_data_set)


async def tcp_client(index: int, conf, ev_loop, statistic: dict):
    """Connect and send messages.
    """
    print("Start connection", index)
    reader, writer = await asyncio.open_connection(
        conf.host, conf.port, loop=ev_loop)

    input_volume = output_volume = answers = 0
    start_time = time.time()
    no_random = conf.norandom
    try:
        for _ in range(conf.msg):
            data = create_msg(no_random=no_random)
            output_volume += len(data)
            writer.write(data)
            data = await reader.readline()
            if data:
                input_volume += len(data)
                answers += 1

        writer.close()
    finally:
        statistic["time"] += time.time() - start_time
        statistic["in"] += input_volume
        statistic["out"] += output_volume
        statistic["msg"] += answers

    print("Stop connection", index)


stat = {"in": 0, "out": 0, "time": 0, "msg": 0}

try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(*(
            tcp_client(client_index, cmd_args, loop, stat)
            for client_index in range(1, cmd_args.count + 1)
        ))
    )
    loop.close()
finally:
    stat["avg"] = stat["time"] / stat["msg"] * 1000
    print("""
    input: {in}
    output: {out}
    messages: {msg}
    avg exec time (ms): {avg:0.6f}
    """.format(**stat))
