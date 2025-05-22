#!/usr/bin/env python3

import warnings
with warnings.catch_warnings(action="ignore"):
    from gi.repository import AmlCore, AmlParticles, AmlTypes, AmlMath, AmlLammpsIO, AmlBox, Bubvol, GLib

GLib.random_set_seed(1)

from pathlib import Path
import argparse
from delete import DeleteParams, DeleteAction

def get_options():
    parser = argparse.ArgumentParser("bubvol")
    parser.add_argument("-f", type=Path, help="Path to the LAMMPS dump")
    parser.add_argument("-b", action="store_true", help="If set, binary LAMMPS dump is expected")

    return parser.parse_args()

def load_file(root, is_binary, path):
    ps = AmlLammpsIO.ReaderParams()
    ps.set_properties(
        ["id", "type", "x", "y", "z"],
        [
            AmlTypes.Int64Type.instance(),
            AmlTypes.Int64Type.instance(),
            AmlTypes.Float64Type.instance(),
            AmlTypes.Float64Type.instance(),
            AmlTypes.Float64Type.instance(),
        ],
    )
    ps.set_particles_id("particles")
    ps.set_box_id("box")
    ps.set_timestep_id("timestep")
    ps.set_filepath(str(path))

    action = AmlLammpsIO.BinaryDumpReader() if is_binary else AmlLammpsIO.DumpReader()
    action.set_params(ps)

    action.perform(root)

def delete_p(root):
    ps = DeleteParams()
    ps.particles_id = "particles"

    action = DeleteAction()
    action.set_params(ps)

    action.perform(root)

def perform_mc(root, iter=1000, save=False):
    ps = Bubvol.VolumeParams()
    ps.particles_id = "particles"
    ps.iterations = iter
    ps.write_points = save

    action = Bubvol.VolumeAction()
    action.set_params(ps)
    action.perform(root)

def print_results(root):
    res = root.get_element("VolumeResult")

    print("Volume information")
    print(f"Total points:\t\t{res.get_total()}")
    print(f"Hit points:\t\t{res.get_hit()}")
    print(f"Hit percent:\t\t{100 * res.get_part()}")
    print(f"Box volume:\t\t{res.get_volume()}")
    print(f"Expected volume:\t{res.get_expected_volume()}")

def dump_lammps(root, file):
    ps = AmlLammpsIO.WriterParams()
    ps.set_particles_id("particles")
    ps.set_box_id("box")
    ps.set_filepath(file)
    ps.set_properties(["type", "x", "y", "z"])
    ps.set_timestep_id("timestep")

    action = AmlLammpsIO.DumpWriter()
    action.set_params(ps)

    action.perform(root)

if __name__ == "__main__":
    show_points = True
    opts = get_options()
    root = AmlCore.DataCollection()
    print("Loading file ...")
    load_file(root, opts.b, opts.f)
    dump_lammps(root, "init.lammpsdump")
    print("Deleting particles ...")
    delete_p(root)
    dump_lammps(root, "del.lammpsdump")
    print("Calculating volume ...")
    perform_mc(root, iter=10000, save=show_points)
    print()
    print_results(root)
    print()
    if show_points:
        print("Writing hit points")
        dump_lammps(root, "hit.lammpsdump")
