#!/usr/bin/env python3
from rc import RC4
import numpy as np
import random
from math import ceil, sqrt
from PIL import Image
from typing import Tuple


def binstrip(num: int):
    return bin(num)[2:]  # equivalent to .lstrip("0x")


def calc_square_edge(encoded_len: int):
    pixel_amount = encoded_len / 3 + 1
    return ceil(sqrt(pixel_amount))


def create_pixel_array(encoded, edge: int, appendix: int):
    arr = np.asarray(encoded, dtype=np.uint8)
    arr = np.append(arr, np.random.randint(0, 256, appendix))
    arr.resize(edge, edge, 3)
    return arr


def calc_encoded_ex_appendix(ex_appendix, xored):
    return ex_appendix ^ xored & 0x3fffff


def insert_bits(original: int, bits: dict):
    out = ""
    shift = 0
    for bl in binstrip(original).zfill(22):
        while shift in bits:
            out += bits[shift]
            shift += 1
        out += bl
        shift += 1
    while shift in bits:
        out += bits[shift]
        shift += 1
    return out


def assemble_mod_square(bitseq: str):
    mod_square = np.zeros(3, dtype=np.uint8)
    for i in range(0, len(bitseq), 8):
        mod_square[i // 8] = int(bitseq[i:i + 8], 2)
    return mod_square


class Rothko():
    """creates colorful squares off given secret msg and key
    unless the user provided a dull msg :f """
    def __init__(self, key):
        self.rc = RC4(key)
        self.xor_gen = self.xorshitf(sum(ord(c) for c in key) * len(key))
        self.gen()
        self.arr = None

    def encode(self, secret):
        encoded = np.asarray(self.rc.encode(secret), dtype=np.uint8)
        leftovers = len(encoded) % 3
        edge = calc_square_edge(len(encoded))
        appendix = edge**2 * 3 - len(encoded)
        ex_appendix = appendix - 1
        self.arr = create_pixel_array(encoded, edge, appendix)
        mod_square = assemble_mod_square(
            self.encode_mod_square(ex_appendix, leftovers))
        mod_square_position = self.gen() % edge**2

    def encode_mod_square(self, ex_appendix, leftovers):
        """Prepares and encodes information in the mod square
        about the amount of non-significant random squares
        called here ex_appendix and the amount of leftovers"""

        lin = binstrip(leftovers) if leftovers else random.choice(("00", "11"))
        first, second = self.calc_mod_bits_positions()
        encoded_ex_appendix = (ex_appendix ^ self.gen()) & 0x3fffff
        print(encoded_ex_appendix)
        print(binstrip(encoded_ex_appendix))
        bitseq = insert_bits(encoded_ex_appendix, {
            first: lin[0],
            second: lin[1]
        })
        print(bitseq)
        return bitseq

    def decode_mod_square(self, square, first_bit_pos,
                          second_bit_pos) -> Tuple[int, int]:
        # TODO change it to masks and shifts
        # this just a fast solution
        bits = list("".join(binstrip(byte).zfill(8) for byte in square))

        second_bit = bits[second_bit_pos]
        first_bit = bits.pop(first_bit_pos)
        bits.pop(second_bit_pos)
        leftovers = int((first_bit + second_bit), 2) % 3  # 11 and 00 both 0
        encoded = int("".join(bits), 2)
        print(binstrip(encoded))
        print(encoded)

        decoded_ex_appendix = (encoded ^ self.gen()) & 0x3fffff
        print(decoded_ex_appendix)

        return leftovers, decoded_ex_appendix

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