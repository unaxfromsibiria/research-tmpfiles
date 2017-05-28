import signal

try:
    from dotenv import load_dotenv, find_dotenv
except ImportError:
    pass
else:
    load_dotenv(find_dotenv())

from guardpi import MoveWatcher


watcher = MoveWatcher()


def finish_handler(signum, frame):
    """SIGINT handler.
    """
    watcher.stop()

signal.signal(signal.SIGINT, finish_handler)
watcher.start()
