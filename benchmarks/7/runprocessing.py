
import asyncio
import functools
import random
import signal
import sys
import time

DEFAULT_INPUT_SIZE = 100
DEFAULT_MSG_COUNT = 10
DEFAULT_POOL_SIZE = 10
BUFFER_SIZE = 10000


async def client_input(
        index: int, msg_count: int, input_queue: asyncio.Queue):
    """Source data from clients.
    """
    start_time = time.time()
    total_data_size = 0
    total_msg_count = 0
    for msg_index in range(1, msg_count + 1):
        future = asyncio.Future()
        num = random.randint(0, 1000 ** 2)
        str_num = str(num)
        msg = {
            "id": msg_index,
            "future": future,
            "value": str_num,
        }
        total_data_size += sys.getsizeof(str_num)
        await input_queue.put(msg)
        while not future.done():
            await asyncio.sleep(0)

        res = future.result()
        if int(res["value"], 16) != num:
            print(
                "client {} result: {} source value: {}".format(
                    index, res, num))
        else:
            total_msg_count += 1

        await asyncio.sleep(0)

    return (
        total_msg_count,
        time.time() - start_time,
        total_data_size,
    )


async def worker(index: int, input_queue: asyncio.Queue):
    """Handler of worker.
    """
    print("worker {} started".format(index))
    active = True
    while active:
        msg = await input_queue.get()
        if msg.get("exit"):
            active = False
            print("worker {} stopped".format(index))
        else:
            future = msg["future"]
            del msg["future"]
            msg["worker"] = index
            msg["value"] = "{0:x}".format(int(msg["value"]))
            future.set_result(msg)

        await asyncio.sleep(0)


async def run_workers(
        input_queue: asyncio.Queue,
        pool: int,
        **kwargs):
    """Starting workers.
    """
    coroutines = [
        worker(i, input_queue)
        for i in range(1, pool + 1)
    ]
    completed, _ = await asyncio.wait(coroutines)
    return all(
        item.result()
        for item in completed)


async def run_clients(
        input_queue: asyncio.Queue,
        input: int,
        message: int,
        **kwargs):
    """Method for starting all clients.
    """
    coroutines = [
        client_input(i, message, input_queue)
        for i in range(input)
    ]
    start_time = time.time()
    completed, _ = await asyncio.wait(coroutines)
    total_data_size = 0
    total_exec_time = 0
    total_msg_count = 0
    for item in completed:
        msg_count, exec_time, data_size = item.result()
        total_data_size += data_size
        total_exec_time += exec_time
        total_msg_count += msg_count

    print(
        """
        input data size: {:d}
        msg count: {:d}
        avg client time (ms): {:.6f}
        avg msg exec time (ms): {:.6f}
        client wait (sec): {:.6f}""".format(
            total_data_size,
            total_msg_count,
            total_exec_time * 1000 / float(input),
            total_exec_time * 1000 / float(input * msg_count),
            time.time() - start_time))

#  #run#  #
run_data = {
    "input": DEFAULT_INPUT_SIZE,
    "message": DEFAULT_MSG_COUNT,
    "pool": DEFAULT_POOL_SIZE,
}

cmd_args = set(sys.argv[1:])
for key in run_data:
    for cmd_arg in cmd_args:
        try:
            arg, val = cmd_arg.split("=")
        except ValueError:
            continue
        else:
            if '-{}'.format(key) == arg:
                try:
                    run_data[key] = int(val)
                except (TypeError, ValueError):
                    continue


def ask_exit(sig_name: str, msg_queue: asyncio.Queue, workers: int):
    """Exit signal handler.
    """
    print("Exit signal:", sig_name)
    for _ in range(workers):
        msg_queue.put_nowait({"exit": True})


loop = asyncio.get_event_loop()
try:
    queue = asyncio.Queue(maxsize=BUFFER_SIZE)
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(
                ask_exit, signame, queue, run_data["pool"]))

    loop.run_until_complete(
        asyncio.gather(
            run_workers(input_queue=queue, **run_data),
            run_clients(input_queue=queue, **run_data)
        ))
finally:
    loop.close()
