import warnings
with warnings.catch_warnings(action="ignore"):
    from gi.repository import AmlCore, AmlParticles, AmlTypes, AmlMath, AmlBox
import numpy as np

class DeleteParams(AmlCore.ActionParams):
    def __init__(
        self,
        particles_id="particles",
        box_id="box",
        lattice_index=1,
        bubble_index=2,
        cut=7,
        x_id="x",
        y_id="y",
        z_id="z",
        type_id="type",
    ):
        super().__init__()
        self.particles_id = particles_id
        self.lattice_index = lattice_index
        self.bubble_index = bubble_index
        self.cut = cut
        self.x_id = x_id
        self.y_id = y_id
        self.z_id = z_id
        self.type_id = type_id
        self.box_id = box_id

    def do_copy(self):
        return DeleteParams(
            self.particles_id,
            self.box_id,
            self.lattice_index,
            self.bubble_index,
            self.cut,
            self.x_id,
            self.y_id,
            self.z_id,
            self.type_id,
        )

class DeleteAction(AmlCore.Action):
    def __init__(self):
        super().__init__()

    def do_get_params_error_message(self, params):
        return ""

    def do_perform(self, data):
        ps = self.get_params()
        particles = data.get_element(ps.particles_id)
        box = data.get_element(ps.box_id)
        assert isinstance(particles, AmlParticles.Particles)
        assert isinstance(box, AmlBox.ParallelepipedBox)

        types = np.asarray(particles.get_prop(ps.type_id).get_arr())
        xs = np.asarray(particles.get_prop(ps.x_id).get_arr())
        ys = np.asarray(particles.get_prop(ps.y_id).get_arr())
        zs = np.asarray(particles.get_prop(ps.z_id).get_arr())

        mat = box.get_edge()
        LX, LY, LZ = mat.get_element(0, 0), mat.get_element(1, 1), mat.get_element(2, 2)

        xs = np.fmod(xs + LX * 100, LX)
        ys = np.fmod(ys + LY * 100, LY)
        zs = np.fmod(zs + LZ * 100, LZ)

        b_xs = xs[types == ps.bubble_index]
        b_ys = ys[types == ps.bubble_index]
        b_zs = zs[types == ps.bubble_index]

        x_lo = np.min(b_xs)
        x_hi = np.max(b_xs)
        y_lo = np.min(b_ys)
        y_hi = np.max(b_ys)
        z_lo = np.min(b_zs)
        z_hi = np.max(b_zs)

        ids = []
        for i in range(len(types)):
            if types[i] == ps.bubble_index:
                ids.append(i)
                continue
            if types[i] != ps.lattice_index:
                continue
            x, y, z = xs[i], ys[i], zs[i]
            if all([
                x_lo - ps.cut < x < x_hi + ps.cut,
                y_lo - ps.cut < y < y_hi + ps.cut,
                z_lo - ps.cut < z < z_hi + ps.cut,
            ]):
                ids.append(i)
            # dx, dy, dz = b_xs - x, b_ys - y, b_zs - z
            # drs = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
            # if np.min(drs) < ps.cut:
            #     ids.append(i)

        _xs = []
        _ys = []
        _zs = []
        _types = []

        for i in ids:
            _types.append(types[i])
            _xs.append(xs[i])
            _ys.append(ys[i])
            _zs.append(zs[i])

        xs = AmlTypes.Float64ArrayProperty.create(len(_xs))
        xs.set_arr(_xs)
        ys = AmlTypes.Float64ArrayProperty.create(len(_ys))
        ys.set_arr(_ys)
        zs = AmlTypes.Float64ArrayProperty.create(len(_zs))
        zs.set_arr(_zs)
        types = AmlTypes.Int64ArrayProperty.create(len(_types))
        types.set_arr(_types)

        particles.clear()
        particles.set_size(xs.get_size())

        particles.set_prop("x", xs)
        particles.set_prop("y", ys)
        particles.set_prop("z", zs)
        particles.set_prop("type", types)
