import time
import numpy as np
from PIL import Image
from cython.parallel import parallel, prange
from libc.stdlib cimport malloc, free, realloc


cdef enum:
    _layers_count = 3
    _locality_size = 5
    _default_difference = 48


cdef bint _max_difference(int *data, int w, int h, int x, int y) nogil:
    # max - min value in cube
    cdef int i, j, val, max_v = 0, min_v = 255
    cdef int ax = x - _locality_size, bx = x + _locality_size
    cdef int ay = y - _locality_size, by = y + _locality_size

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
            val = data[i * w + j]
            # get min/max
            if min_v > val:
                min_v = val
            # goto here in C if use "elif"
            if max_v < val:
                max_v = val

    return max_v - min_v

cdef void _extract_contour(int difference, int *data, bint *layer, int w, int h) nogil:
    # create layer
    cdef int i, j
    for i in range(h):
        for j in range(w):
            if _max_difference(data, w, h, j, i) > difference:
                layer[i * w + j] = True

cdef class ContourExtractor:
    # extract contours
    # method of img managment
    cdef:
        int w, h
        int _significant_difference
        int *content_r
        int *content_g
        int *content_b
        bint *layer_r
        bint *layer_g
        bint *layer_b

    cdef _init(self, img: object):
        # create layers
        cdef int size = 0, i = 0, r, g, b
        self.w, self.h = img.size
        size = self.w * self.h
        self.content_r = <int *>malloc(sizeof(int) * size)
        self.content_g = <int *>malloc(sizeof(int) * size)
        self.content_b = <int *>malloc(sizeof(int) * size)
        self.layer_r = <bint *>malloc(sizeof(bint) * size)
        self.layer_g = <bint *>malloc(sizeof(bint) * size)
        self.layer_b = <bint *>malloc(sizeof(bint) * size)
        # fill 3 layers by color
        for r, g, b in img.getdata():
            self.content_r[i] = r
            self.content_g[i] = g
            self.content_b[i] = b
            self.layer_r[i] = self.layer_g[i] = self.layer_b[i] = False
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

    cdef _layer_to_array(self, bint *layer):
        cdef int i, j

        data = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        for i in range(self.h):
            for j in range(self.w):
                if layer[i * self.w + j]:
                    data[i, j, 0] = data[i, j, 1] = data[i, j, 2] = 255

        return data

    def get_layer_r(self):
        return self._layer_to_array(self.layer_r)

    def get_layer_g(self):
        return self._layer_to_array(self.layer_g)

    def get_layer_b(self):
        return self._layer_to_array(self.layer_b)
