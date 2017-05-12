import random
import sys
import time
from geopy.distance import great_circle
from sanic import Sanic
from sanic.response import json

cmd_args = set(sys.argv[1:])

host, port = "0.0.0.0", 8888
api_url = "/min-distance/points/"

for param in cmd_args:
    if ":" in param:
        host, port = param.split(":")
        port = int(port)

fake_delay = '-fake_delay' in cmd_args

app = Sanic()


@app.route("/")
async def main_page(request):
    """
    """
    return json({"message": "Api url: {}".format(api_url)})


@app.route(api_url, methods=["POST"])
async def find_min_distance(request):
    """Search two of closely
    points by latitude and longitude, e.g.
    curl -H "Content-Type: application/json"
        -X POST -d '{"points":[
            ["43.48000","-71.412700"],
            ["41.49000","-71.412700"],
            ["41.49008","-71.312796"],
            ["41.499498", "-81.695391"]
        ]}' http://url/
    result (distance in kilometers):
        {
            "distance":"8.32",
            "points":[
                ["41.490000","-71.412700"],
                ["41.490080","-71.312796"]
            ]
        }
    """
    points = request.json.get("points")
    if not points:
        return json({"point": None})

    # [("latitude", "longitude")...]
    points = [
        tuple(map(float, p))
        for p in points
    ]
    res_points = None
    min_dis = 10 ** 30
    n = len(points)
    for i in range(n - 1):
        point_1 = points[i]
        for j in range(i + 1, n):
            point_2 = points[j]
            d = great_circle(point_1, point_2).meters
            if d < min_dis:
                min_dis = d
                res_points = [point_1, point_2]
    # fake delay
    if fake_delay:
        wait = float(random.randint(100, 2000)) / 1000.
        time.sleep(wait)
        print(
            " -> ",
            points,
            " after {:.2f} distance:".format(wait),
            min_dis)

    return json({
        "distance": "{0:.2f}".format(min_dis / 1000),
        "points": [
            tuple(map("{0:.6f}".format, p))
            for p in res_points
        ],
    })

app.run(
    host=host, port=port, debug=True, log_config=None)
