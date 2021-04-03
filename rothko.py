#!/usr/bin/env python3
from rc import RC4
import numpy as np
from math import ceil, sqrt
from PIL import Image
from collections import deque
from itertools import cycle


def binstrip(num: int):
    return bin(num)[2:]  # equivalent to .lstrip("0x")


def calc_square_edge(encoded_len: int):
    pixel_amount = encoded_len / 3 + 1
    return ceil(sqrt(pixel_amount))


def create_pixel_array(encoded, edge: int, appendix: int):
    arr = np.asarray(encoded, dtype=np.uint8)
    arr = np.append(arr, np.random.randint(0, 256, appendix, dtype=np.uint8))
    arr.resize(edge * edge, 3)
    return arr


def assemble_mod_square(bitseq: str):
    bitseq = bitseq.zfill(24)
    mod_square = np.zeros(3, dtype=np.uint8)
    for i in range(0, len(bitseq), 8):
        mod_square[i // 8] = int(bitseq[i:i + 8], 2)
    return mod_square


class Rothko():
    """creates colorful squares off given secret msg and key
    unless the user provided a dull msg :f"""

    max_shuffles = 250

    def __init__(self, key):
        self.rc = RC4(key)
        self.xor_gen = self.xorshitf(sum(ord(c) for c in key) * len(key))
        self.gen()
        self.arr = None

    def encode(self, secret):
        self.init_array(secret)
        self.shuffle_squares()
        dimension = int(sqrt(self.arr.shape[0]))
        self.arr.resize(dimension, dimension, 3)
        self.xor_gen.close()  # closing inf generator for peace of mind
        return self.arr

    def to_img(self):
        img = Image.fromarray(self.arr)
        img.save("picture.png")

    def decode(self, arr):
        appendix_key = self.gen()
        self.arr = arr
        dim = int(self.arr.shape[0]**2)
        self.arr.resize(dim, 3)
        self.deshuffe_squares()
        mod_square = self.arr[-1].copy()
        appendix = self.decode_mod_square(mod_square, appendix_key)
        self.arr.resize(dim * 3)
        self.xor_gen.close()
        return self.rc.decode(self.arr[:-appendix])

    def init_array(self, secret):
        encoded = np.asarray(self.rc.encode(secret), dtype=np.uint8)
        edge = calc_square_edge(len(encoded))
        appendix = edge**2 * 3 - len(encoded)
        self.arr = create_pixel_array(encoded, edge, appendix)
        mod_square = assemble_mod_square(self.encode_mod_square(appendix))
        self.arr[-1] = mod_square
        print(mod_square)
        print("preshuffle\n", self.arr)

    def encode_mod_square(self, appendix):
        encoded_appendix = (appendix ^ self.gen()) & 0xffffff
        print(binstrip(encoded_appendix))
        return binstrip(encoded_appendix)

    @staticmethod
    def decode_mod_square(square, appendix_key) -> int:
        encoded = "".join(binstrip(byte).zfill(8) for byte in square)
        encoded = int(encoded, 2)
        return (encoded ^ appendix_key) & 0xffffff

    def calc_shuffling_amount(self, dim) -> int:
        amount = dim // 3 + 15
        return min(amount, self.max_shuffles)

    def __shuffle_core(self, dim, rng, shift, *args):
        """
        dim = amount of rows
        rng = function generating random numbers
        args = passed to range()
        shift = int 0 to 2
        """
        tmp = [True, True, True]
        tmp[shift] = False
        for i, row_time in zip(range(*args), cycle(tmp)):
            if row_time:  # swaps rows
                ix = i % dim
                rand = rng() % dim
                self.swap_arr_row(ix, rand)
            else:  # swaps columns
                ix = i % 3
                rand = rng() % 3
                self.swap_arr_column(ix, rand)

    def shuffle_squares(self):
        dim, *_ = self.arr.shape
        self.__shuffle_core(dim, self.gen, 2,
                            self.calc_shuffling_amount(dim) - 1, -1, -1)

    def deshuffe_squares(self):
        dim, *_ = self.arr.shape
        iterations = self.calc_shuffling_amount(dim)
        shift = iterations % 3
        swap_stack = deque(self.gen() for _ in range(iterations))
        self.__shuffle_core(dim, swap_stack.pop, shift, iterations)

    def swap_arr_row(self, i, j):
        self.arr[[i, j]] = self.arr[[j, i]]

    def swap_arr_column(self, i, j):
        self.arr[:, [i, j]] = self.arr[:, [j, i]]

    def calc_mod_bits_positions(self):
        """return position of bits in the mod_square that hold
        information about leftovers. the mod square is 3bytes
        so there are 24 positions for bits"""
        first_bit = self.gen() % 24
        second_bit = self.gen() % 24
        if second_bit == first_bit:
            second_bit = (first_bit + 1 % 24)
        return first_bit, second_bit

    def gen(self):
        """just a conviencince methods that return next xorshift gen yield"""
        return next(self.xor_gen)

    @staticmethod
    def xorshitf(seed: int):
        seed &= 0xFFFFFFFF
        while True:
            seed ^= np.left_shift(seed, 13)
            seed ^= np.right_shift(seed, 17)
            seed ^= np.left_shift(seed, 5)
            yield seed


if __name__ == "__main__":
    pass
