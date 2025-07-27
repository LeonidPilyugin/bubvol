import numpy as np
from multiprocessing import Pool, cpu_count

def cut(gas_positions, lattice_positions, margin, box):
    gas_positions = np.fmod(gas_positions + box * 100, box)
    lattice_positions = np.fmod(lattice_positions + box * 100, box)

    gas_lo = np.min(gas_positions, axis=0)
    gas_hi = np.max(gas_positions, axis=0)

    del_lo = gas_lo - margin
    del_hi = gas_hi + margin

    np.delete(
        lattice_positions,
        np.all(lattice_positions < del_lo, axis=1),
        0
    )
    np.delete(
        lattice_positions,
        np.all(lattice_positions > del_hi, axis=1),
        0
    )

def compute_volume(gas_positions, lattice_positions, factor, n, seed=-1):
    np.random.seed(seed)

    def is_hit(point):
        r_g = np.min(np.linalg.norm(gas_positions - point))
        r_l = np.min(np.linalg.norm(lattice_positions - point))
        return r_g * factor < r_l

    workers = cpu_count()

    plo = np.min(lattice_positions, axis=0)
    phi = np.max(lattice_positions, axis=0)

    points = []
    k = n // (workers - 1)
    for _ in range(workers - 1):
        points.append(plo + (phi - plo) * np.random.rand(k, 3))
    else:
        points.append(plo + (phi - plo) * np.random.rand(n - k * (workers - 1), 3))


    hit = None
    total = len(points)
    volume = np.prod(phi - plo)
    with Pool(workers) as pool:
        hit = sum(pool.map(lambda arr: np.apply_along_axis(is_hit, 1, arr).sum(), points))

    return hit / total * volume

