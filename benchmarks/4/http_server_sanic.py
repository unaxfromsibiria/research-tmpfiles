import sys

from sanic import Sanic
from sanic.response import json
from multiprocessing import cpu_count

cmd_args = set(sys.argv[1:])
# -workers=4
workers = cpu_count()
host, port = "0.0.0.0", 8888
for param in cmd_args:
    if ":" in param:
        host, port = param.split(":")
        port = int(port)
    elif "workers" in param:
        try:
            workers = int(param.replace("-workers=", ""))
        except ValueError:
            pass
        else:
            print("With workers: ", workers)

app = Sanic(log_config=None)


@app.route("/")
async def main_page(request):
    return json({"message": "Use url /calc/ and method POST."})


@app.route("/calc/", methods=["POST"])
async def calc_data(request):
    data = request.json
    a = map(float, data["a"])
    b = map(float, data["b"])
    sum_a = sum(a)
    avg_b = sum(b) / len(data["b"])
    c = sum_a / avg_b
    return json({
        "a": "{0:.6f}".format(sum_a),
        "b": "{0:.6f}".format(avg_b),
        "c": "{0:.6f}".format(c),
    })

app.run(host=host, port=port, workers=workers)
