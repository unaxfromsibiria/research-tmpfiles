
import io

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

fig, ax = plt.subplots()

ax.fmt_xdata = mdates.DateFormatter("%Y-%m-%d")
ax.set_title("Rate at date")
ax.grid(True)


def create_image(data: pd.DataFrame) -> bytes:
    """Create image with rate table.
    """
    dia = data.plot()
    img_src = dia.get_figure()
    buffer = io.BytesIO()
    img_src.savefig(buffer)
    buffer.seek(0)
    return buffer.read()
