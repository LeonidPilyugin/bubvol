from pathlib import Path
import subprocess as su
import pandas as pd
from itertools import product
from tqdm import tqdm
import numpy as np

r_vac = {
    16: 1.0,
    19: 1.2,
    13: 0.8,
    43: 1.3,
    55: 1.5,
    79: 1.6,
}

n_vac = r_vac.keys()
he_vac = [ 0.3, 0.5, 0.7, 1.0, 1.5, 2.0 ]

vac_a3 = 4.124 ** 3 / 4

def start_lammps(**kwargs):
    command = "/home/leonid/opt/lammps/build/eam/lmp -sf gpu -pk gpu 1 -nonbuf -in script.lmp"

    for key, value in kwargs.items():
        command += f" -v {key} {value}"

    p = su.Popen(
        command,
        shell=True,
        stdout=su.DEVNULL,
        stderr=su.DEVNULL,
    )
    p.wait()
    return p.returncode

def get_true_vac(path):
    import ov
    return ov.get_true_nvac(str(path), str(path.parent.joinpath("reference.atom")))

def get_vac(path, r):
    command = f"zsh bv.sh 100000 {str(path)} 1 {r}"
    out = su.run(
        command,
        shell=True,
        encoding="ascii",
        capture_output=True,
    ).stdout

    for line in out.split("\n"):
        if line.startswith("Expected volume:"):
            res = float(line.strip().split()[-1]) / vac_a3
            return res

def get_r(filename, v_true, treshold=0.1):
    r1 = 1
    r2 = 2
    v1 = get_vac(filename, r1)
    v2 = get_vac(filename, r2)
    e1 = v1 / v_true - 1
    e2 = v2 / v_true - 1

    if abs(e1) < treshold:
        return v1, e1, r1
    if abs(e2) < treshold:
        return v2, e2, r2

    while e1 > 0:
        r1 = r1 * 0.9
        v1 = get_vac(filename, r1)
        e1 = v1 / v_true - 1

    while e2 < 0:
        r2 = r2 * 1.1
        v2 = get_vac(filename, r2)
        e2 = v2 / v_true - 1


    while min(abs(e1), abs(e2)) > treshold and abs(r2 - r1) > 1e-3:
        if r1 > r2:
            r1, r2 = r2, r1
            e1, e2 = e2, e1
            v1, v2 = v2, v1

        assert v1 < v2 and e1 < e2

        assert e1 <= 0 and e2 >= 0
        r = (r1 + r2) / 2
        v = get_vac(filename, r2)
        e = v / v_true - 1
        if e > 0:
            r2 = r
            v2 = v
            e2 = e
        else:
            r1 = r
            v1 = v
            e1 = e

    if abs(e1) < abs(e2):
        return (v1, e1, r1)
    else:
        return (v2, e2, r2)


def do_iteration(n_vac, he_vac):
    directory = Path(__file__).parent.joinpath("trjs").joinpath(f"{n_vac}-{he_vac}")
    directory.mkdir(exist_ok=True)
    assert start_lammps(
        r=r_vac[n_vac],
        n=int(he_vac * n_vac),
        path=directory,
        rr=100000,
        d=10000
    ) == 0

    steps = []
    true_nvac = []
    r_best = []
    vac = []
    err = []
    vac_with_best = []

    for file in directory.glob("*.atom"):
        if file.name != "reference.atom":
            vc = get_true_vac(file)
            steps.append(int(file.stem))
            true_nvac.append(vc)
            del vc
    
    for i, step in enumerate(steps):
        filename = directory.joinpath(f"{step}.atom")
        res = get_r(filename, true_nvac[i], treshold=0.05)
        print(res)
        vc, er, r = res
        vac.append(vc)
        err.append(er)
        r_best.append(r)

    r = np.mean(r_best)
    for i, step in enumerate(steps):
        filename = directory.joinpath(f"{step}.atom")
        v = get_vac(filename, r)
        vac_with_best.append(v)
        print(v)


    df = pd.DataFrame({
        "steps": steps,
        "true_nvac": true_nvac,
        "r_best": r_best,
        "vac": vac,
        "err": err,
        "vac_with_best": vac_with_best,
    })

    df.to_csv(directory.joinpath("result.csv"))


if __name__ == "__main__":
    for v, h in tqdm(list(product(n_vac, he_vac))):
        do_iteration(v, h)
