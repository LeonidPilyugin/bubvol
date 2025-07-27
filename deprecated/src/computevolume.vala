using AmlCore;
using AmlParticles;
using AmlTypes;
using AmlMath;

namespace BubVol
{
    public class VolumeParams : ActionParams
    {
        public string particles_id = DataCollection.EMPTY_ID;
        public string x_id = "x";
        public string y_id = "y";
        public string z_id = "z";
        public string type_id = "type";
        public int lattice_id = 1;
        public int bubble_id = 2;
        public int hit_id = 3;
        public int out_id = 4;
        public uint64 iterations = 0;
        public bool write_points = false;
        public double factor = 1.0;

        public override ActionParams copy()
        {
            var res = new VolumeParams();

            res.particles_id = this.particles_id;
            res.lattice_id = this.lattice_id;
            res.bubble_id = this.bubble_id;
            res.hit_id = this.hit_id;
            res.out_id = this.out_id;

            res.x_id = this.x_id;
            res.y_id = this.y_id;
            res.z_id = this.z_id;
            res.type_id = this.type_id;

            res.iterations = this.iterations;
            res.write_points = this.write_points;

            res.factor = this.factor;

            return res;
        }
    }

    public class VolumeResult : DataObject
    {
        internal uint64 total_points;
        internal uint64 hit_points; 
        internal double xs;
        internal double ys;
        internal double zs;

        public uint64 get_total()
        {
            return this.total_points;
        }

        public uint64 get_hit()
        {
            return this.hit_points;
        }

        public double get_part()
        {
            return this.get_hit() / (double) this.get_total();
        }

        public double get_volume()
        {
            return this.xs * this.ys * this.zs;
        }

        public double get_expected_volume()
        {
            return this.get_volume() * this.get_part();
        }

        public override DataObject copy()
        {
            var res = new VolumeResult();
            res.total_points = this.total_points;
            res.hit_points = this.hit_points;
            res.xs = this.xs;
            res.ys = this.ys;
            res.zs = this.zs;
            return res;
        }
    }

    public class VolumeAction : AmlCore.Action
    {
        public override string get_params_error_message(ActionParams params)
        {
            if (!(params is VolumeParams))
                return "Params shoud be instance of BubVol.VolumeParams";

            return "";
        }

        private bool is_probe_successful(Vector3 probe, List<Vector3?> lp, List<Vector3?> bp, double factor)
        {
            Vector3 temp = Vector3.substract(probe, lp.nth_data(0));
            Vector3 nearest_lp = temp;
            double min_n = temp.norm();
            double n;
            foreach (unowned Vector3 v in lp)
            {
                temp = Vector3.substract(v, probe);
                n = temp.norm();
                if (n < min_n)
                {
                    min_n = n;
                    nearest_lp = temp;
                }
            }

            temp = Vector3.substract(probe, bp.nth_data(0));
            Vector3 nearest_bp = temp;
            min_n = temp.norm();
            foreach (unowned Vector3 v in bp)
            {
                temp = Vector3.substract(v, probe);
                n = temp.norm();
                if (n < min_n)
                {
                    min_n = n;
                    nearest_bp = temp;
                }
            }

            return nearest_bp.norm() < factor * nearest_lp.norm();
        }

        public override void perform(DataCollection data) throws ActionError
        {
            VolumeParams ps = (VolumeParams) this.get_params();
            Particles particles;
            try
            {
                particles = data.get_dataobject<Particles>(ps.particles_id);
            } catch (DataCollectionError.ELEMENT_ERROR e)
            {
                throw new ActionError.RUNTIME_ERROR(e.message);
            }

            int64[:size_t] types = ((Int64ArrayProperty) particles.get_prop(ps.type_id)).get_arr();
            double[:size_t] xs = ((Float64ArrayProperty) particles.get_prop(ps.x_id)).get_arr();
            double[:size_t] ys = ((Float64ArrayProperty) particles.get_prop(ps.y_id)).get_arr();
            double[:size_t] zs = ((Float64ArrayProperty) particles.get_prop(ps.z_id)).get_arr();

            Vector3[:size_t] positions = new Vector3[particles.get_size()];
            Vector3 temp = {};
            
            for (size_t i = 0; i < particles.get_size(); i++)
            {
                positions[i].set_element(0, xs[i]);
                positions[i].set_element(1, ys[i]);
                positions[i].set_element(2, zs[i]);
            }

            List<Vector3?> lattice_ps = new List<Vector3?>();
            List<Vector3?> bubble_ps = new List<Vector3?>();

            Vector3[] bonds = new Vector3[2];

            bonds[0] = positions[0];
            bonds[1] = positions[0];

            for (size_t i = 0; i < types.length; i++)
            {
                for (int j = 0; j < 3; j++)
                {
                    if (bonds[0].get_element(j) > positions[i].get_element(j))
                        bonds[0].set_element(j, positions[i].get_element(j));
                    if (bonds[1].get_element(j) < positions[i].get_element(j))
                        bonds[1].set_element(j, positions[i].get_element(j));
                }
            }

            for (size_t i = 0; i < particles.get_size(); i++)
            {
                int64 t = types[i];
                if (t == ps.lattice_id)
                    lattice_ps.append(positions[i]);
                if (t == ps.bubble_id)
                    bubble_ps.append(positions[i]);
            }

            VolumeResult result = new VolumeResult();

            temp = Vector3.substract(bonds[1], bonds[0]);

            result.xs = temp.get_element(0);
            result.ys = temp.get_element(1);
            result.zs = temp.get_element(2);

            result.total_points = ps.iterations;
            result.hit_points = 0;

            size_t out_points_n = 0;

            Vector3 probe = {};

            Vector3[:size_t] hit_points = {};
            Vector3[:size_t] out_points = {};

            if (ps.write_points)
            {
                hit_points = new Vector3[ps.iterations];
                out_points = new Vector3[ps.iterations];
            }

            for (size_t iter = 0; iter < result.total_points; iter++)
            {
                for (uint i = 0; i < 3; i++)
                    probe.set_element(i, GLib.Random.double_range(
                        bonds[0].get_element(i), bonds[1].get_element(i)));

                if (this.is_probe_successful(probe, lattice_ps, bubble_ps, ps.factor))
                {
                    if (ps.write_points)
                        hit_points[result.hit_points] = probe;
                    result.hit_points++;
                } else if (ps.write_points)
                {
                    out_points[out_points_n++] = probe;
                }
            }

            if (ps.write_points)
            {
                size_t old_l = types.length;
                size_t new_l = types.length + (size_t) ps.iterations;
                types.resize(new_l);
                xs.resize(new_l);
                ys.resize(new_l);
                zs.resize(new_l);

                size_t i;

                for (i = old_l; i < old_l + result.hit_points; i++)
                {
                    types[i] = ps.hit_id;
                    xs[i] = hit_points[i - old_l].get_element(0);
                    ys[i] = hit_points[i - old_l].get_element(1);
                    zs[i] = hit_points[i - old_l].get_element(2);
                }

                size_t i0 = i;

                for (; i < old_l + result.total_points; i++)
                {
                    types[i] = ps.out_id;
                    xs[i] = out_points[i - i0].get_element(0);
                    ys[i] = out_points[i - i0].get_element(1);
                    zs[i] = out_points[i - i0].get_element(2);
                }

                particles.clear();
                particles.set_size(new_l);
                
                var X = new Float64ArrayProperty.create(new_l);
                X.set_arr(xs);
                var Y = new Float64ArrayProperty.create(new_l);
                Y.set_arr(ys);
                var Z = new Float64ArrayProperty.create(new_l);
                Z.set_arr(zs);
                var T = new Int64ArrayProperty.create(new_l);
                T.set_arr(types);

                particles.set_prop("x", X);
                particles.set_prop("y", Y);
                particles.set_prop("z", Z);
                particles.set_prop("type", T);
            }

            data.set_element("VolumeResult", result);
        }
    }
}
