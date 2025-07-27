#!/usr/bin/env python3

import numpy as np
from multiprocessing import Pool, cpu_count
import time

def cut(gas_positions, lattice_positions, margin, box):
    gas_positions = np.fmod(gas_positions + box * 100, box)
    lattice_positions = np.fmod(lattice_positions + box * 100, box)

    gas_lo = np.min(gas_positions, axis=0)
    gas_hi = np.max(gas_positions, axis=0)

    del_lo = gas_lo - margin
    del_hi = gas_hi + margin

    lattice_positions = np.delete(
        lattice_positions,
        np.all(lattice_positions < del_lo, axis=1),
        0
    )
    np.delete(
        lattice_positions,
        np.all(lattice_positions > del_hi, axis=1),
        0
    )

    return lattice_positions

class Mapper:
    def __init__(self, factor, gas, lattice):
        self.factor = factor
        self.gas = gas
        self.lattice = lattice

    def __call__(self, arr):
        return np.apply_along_axis(self.is_hit, 1, arr).sum()

    def is_hit(self, point):
        r_g = np.min(np.linalg.norm(self.gas - point, axis=1))
        r_l = np.min(np.linalg.norm(self.lattice - point, axis=1))
        return r_g * self.factor < r_l

def compute_volume(gas_positions, lattice_positions, factor, n, seed=None, workers=None):
    if seed is not None:
        np.random.seed(seed)

    plo = np.min(lattice_positions, axis=0)
    phi = np.max(lattice_positions, axis=0)

    if workers is None:
        workers = cpu_count() - 1

    points = []
    k = 0 if workers == 1 else n // (workers - 1)
    for _ in range(workers - 1):
        points.append(plo + (phi - plo) * np.random.rand(k, 3))
    else:
        points.append(plo + (phi - plo) * np.random.rand(n - k * (workers - 1), 3))


    hit = 0
    total = len(points)
    volume = np.prod(phi - plo)

    with Pool(workers) as pool:
        hit = sum(pool.map(Mapper(factor, gas_positions, lattice_positions), points))
    return hit / total * volume
