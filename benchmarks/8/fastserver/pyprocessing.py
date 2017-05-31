# native python implementation
#import ujson as json

import json


def calc_answer(json_data: str) -> str:
    """Format:
        {
            "a": [23, 1 ... 3],
            "b": [4, 5, 6...5],
        }
        Answer:
        {
            "a": sum(a),
            "b": avg(b),
            "c": sum(a) / avg(b),
        }
    """
    client_data = json.loads(json_data)
    a = sum(map(float, client_data["a"]))
    b = sum(map(float, client_data["b"])) / len(client_data["b"])

    result = {
        "a": "{:0.6f}".format(a),
        "b": "{:0.6f}".format(b),
        "c": "{:0.6f}".format(a / b)
    }
    return json.dumps(result) + "\n"
