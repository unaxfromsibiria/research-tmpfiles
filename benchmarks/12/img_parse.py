import time
import argparse
import os.path

from PIL import Image

from img_filter import ContourExtractor

parser = argparse.ArgumentParser(
    description="Image filter example.")

parser.add_argument(
    "--img", dest="img", type=str, default="",
    help="Image file path."
)

com_params = parser.parse_args()


def run_parse(img_file_path: str):
    """Parse image and create filters.
    """
    _, file_name = os.path.split(img_file_path)
    file_name, _ = file_name.split(".", 2)
    layers = ContourExtractor(img_file_path)
    start_time = time.time()
    img = Image.fromarray(layers.get_layer_r(), 'RGB')
    img.save("{}_r.png".format(file_name))
    img = Image.fromarray(layers.get_layer_g(), 'RGB')
    img.save("{}_g.png".format(file_name))
    img = Image.fromarray(layers.get_layer_b(), 'RGB')
    img.save("{}_b.png".format(file_name))
    print(
        "Save time: {:0.2f} ms.".format(
            1000 * (time.time() - start_time))
    )


run_parse(com_params.img)
