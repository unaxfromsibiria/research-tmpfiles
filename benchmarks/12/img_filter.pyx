import time
import numpy as np
from PIL import Image
from cython.parallel import parallel, prange
from libc.stdlib cimport malloc, free, realloc


cdef enum:
    _layers_count = 3
    _locality_size = 5
    _default_difference = 64


cdef char _max_difference(char *data, int w, int h, int x, int y) nogil:
    # max - min value in cube
    cdef int i, j, s
    cdef int ax = x - _locality_size, bx = x + _locality_size
    cdef int ay = y - _locality_size, by = y + _locality_size
    cdef char max_v = 255, min_v = 0

    if ax < 0:
        ax = 0
    if bx > w:
        bx = w
    if ay < 0:
        ay = 0
    if by > h:
        by = h

    for i in range(ay, by):
        for j in range(ax, bx):
            # get min/max
            s = i * w + j
            if min_v > data[s]:
                min_v = data[s]
            elif max_v < data[s]:
                max_v = data[s]

    return max_v - min_v

cdef void _extract_contour(char difference, char *data, char *layer, int w, int h) nogil:
    # create layer
    cdef int i, j

    for i in range(h):
        for j in range(w):
            if _max_difference(data, w, h, j, i) > difference:
                layer[i * w + j] = 1

cdef class ContourExtractor:
    # extract contours
    # method of img managment
    cdef:
        int w, h
        int _significant_difference
        char *content_r
        char *content_g
        char *content_b
        char *layer_r
        char *layer_g
        char *layer_b

    cdef _init(self, img: object):
        # create layers
        cdef int size = 0, i = 0, r, g, b
        self.w, self.h = img.size
        size = self.w * self.h
        self.content_r = <char *>malloc(sizeof(char) * size)
        self.content_g = <char *>malloc(sizeof(char) * size)
        self.content_b = <char *>malloc(sizeof(char) * size)
        self.layer_r = <char *>malloc(sizeof(char) * size)
        self.layer_g = <char *>malloc(sizeof(char) * size)
        self.layer_b = <char *>malloc(sizeof(char) * size)

        # fill 3 layers by color
        for r, g, b in img.getdata():
            self.content_r[i], self.content_g[i], self.content_b[i] = r, g, b
            self.layer_r[i] = self.layer_g[i] = self.layer_b[i] = 0
            i += 1

    def __init__(self, img_path: str, significant_difference: int=_default_difference):
        self._significant_difference = significant_difference
        start_time = time.time()
        img = Image.open(img_path).convert("RGB")
        self._init(img)
        end_time = time.time()
        print("Read content time: {:0.2f} ms.".format(1000 * (end_time - start_time)))
        start_time = time.time()
        self._calc()
        end_time = time.time()
        print("Apply filter time: {:0.2f} ms.".format(1000 * (end_time - start_time)))

    cdef _calc(self):
        # do parallel

        cdef int i = 0
        with nogil, parallel():
            for i in prange(_layers_count):
                if i == 0:
                    _extract_contour(self._significant_difference, self.content_r, self.layer_r, self.w, self.h)
                elif i == 1:
                    _extract_contour(self._significant_difference, self.content_g, self.layer_g, self.w, self.h)
                elif i == 2:
                    _extract_contour(self._significant_difference, self.content_b, self.layer_b, self.w, self.h)

    def clear(self):
        pass

    cdef _layer_to_array(self, char *layer):
        cdef int i, j, s, v
        data = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        for i in range(self.h):
            for j in range(self.w):
                v = 0
                if layer[i * self.w + j] > 0:
                    v = 255
                data[i, j, 0] = data[i, j, 1] = data[i, j, 2] = v

        return data

    def get_layer_r(self):
        return self._layer_to_array(self.layer_r)

    def get_layer_g(self):
        return self._layer_to_array(self.layer_g)

    def get_layer_b(self):
        return self._layer_to_array(self.layer_b)
