import cupy
import random
import math

class IGate:
    def __init__(self):
        pass

    def apply(self, helper, qubits, targets):
        return qubits

    def to_qasm(self, helper, targets):
        return []

class XGate:
    _kernel = cupy.ElementwiseKernel(
        "uint64 target_mask, raw T q_inout",
        "",
        """
        if (i & target_mask) {
          T tmp = q_inout[i];
          q_inout[i] = q_inout[i - target_mask];
          q_inout[i - target_mask] = tmp;
        }
        """
    )

    def __init__(self):
        pass

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        for target in slicing(targets, n_qubits):
            target_mask = 1 << target
            self._kernel(target_mask, qubits, size=len(qubits))
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        for target in slicing(targets, n_qubits):
            qasm.append("x q[{}];".format(target))
        return qasm


class YGate:
    def __init__(self):
        pass

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        i = helper["indices"]
        for target in slicing(targets, n_qubits):
            newq = cupy.zeros_like(qubits)
            newq[(i & (1 << target)) == 0] = -1.0j * qubits[(i & (1 << target)) != 0]
            newq[(i & (1 << target)) != 0] = 1.0j * qubits[(i & (1 << target)) == 0]
            qubits = newq
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        for target in slicing(targets, n_qubits):
            qasm.append("y q[{}];".format(target))
        return qasm

class ZGate:
    _kernel = cupy.ElementwiseKernel(
        "uint64 target_mask, T q_inout",
        "",
        "q_inout = (1.0 - 2.0*(!!(i & target_mask)))*q_inout"
    )

    def __init__(self):
        pass

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        for target in slicing(targets, n_qubits):
            target_mask = 1 << target
            self._kernel(target_mask, qubits)
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        for target in slicing(targets, n_qubits):
            qasm.append("z q[{}];".format(target))
        return qasm

class HGate:
    _kernel = cupy.ElementwiseKernel(
        "uint64 target_mask, raw T q_inout",
        "",
        """
        if (i & target_mask) {
          double sqrt2_inv = 1.0 / sqrt(2.0);
          T tmp1 = q_inout[i];
          T tmp0 = q_inout[i - target_mask];
          q_inout[i] = (tmp0 - tmp1) * sqrt2_inv;
          q_inout[i - target_mask] = (tmp0 + tmp1) * sqrt2_inv;
        }
        """
    )

    def __init__(self):
        pass

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        for target in slicing(targets, n_qubits):
            target_mask = 1 << target
            self._kernel(target_mask, qubits, size=len(qubits))
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        for target in slicing(targets, n_qubits):
            qasm.append("h q[{}];".format(target))
        return qasm

class CZGate:
    def __init__(self):
        pass

    def apply(self, helper, qubits, args):
        n_qubits = helper["n_qubits"]
        for control, target in qubit_pairs(args, n_qubits):
            i = helper["indices"]
            qubits[((i & (1 << control)) != 0) & ((i & (1 << target)) != 0)] *= -1
        return qubits

    def to_qasm(self, helper, args):
        n_qubits = helper["n_qubits"]
        qasm = []
        for control, target in qubit_pairs(args, n_qubits):
            qasm.append("cz q[{}],q[{}];".format(control, target))
        return qasm

class CXGate:
    def __init__(self):
        pass

    def apply(self, helper, qubits, args):
        n_qubits = helper["n_qubits"]
        i = helper["indices"]
        for control, target in qubit_pairs(args, n_qubits):
            newq = qubits.copy()
            newq[((i & (1 << control)) != 0) & ((i & (1 << target)) != 0)] = qubits[((i & (1 << control)) != 0) & ((i & (1 << target)) == 0)]
            newq[((i & (1 << control)) != 0) & ((i & (1 << target)) == 0)] = qubits[((i & (1 << control)) != 0) & ((i & (1 << target)) != 0)]
            qubits = newq
        return qubits

    def to_qasm(self, helper, args):
        n_qubits = helper["n_qubits"]
        qasm = []
        for control, target in qubit_pairs(args, n_qubits):
            qasm.append("cx q[{}],q[{}];".format(control, target))
        return qasm

class RXGate:
    def __init__(self, theta):
        self.theta = theta

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        i = helper["indices"]
        theta = self.theta
        for target in slicing(targets, n_qubits):
            newq = cupy.zeros_like(qubits)
            newq[(i & (1 << target)) == 0] = (
                cupy.cos(theta / 2) * qubits[(i & (1 << target)) == 0] +
                -1.0j * cupy.sin(theta / 2) * qubits[(i & (1 << target)) != 0]
            )
            newq[(i & (1 << target)) != 0] = (
                -1.0j * cupy.sin(theta / 2) * qubits[(i & (1 << target)) == 0] +
                cupy.cos(theta / 2) * qubits[(i & (1 << target)) != 0]
            )
            qubits = newq
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        theta = self.theta
        for target in slicing(targets, n_qubits):
            qasm.append("rx({}) q[{}];".format(theta, target))
        return qasm

class RYGate:
    def __init__(self, theta):
        self.theta = theta

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        i = helper["indices"]
        theta = self.theta
        for target in slicing(targets, n_qubits):
            newq = cupy.zeros_like(qubits)
            newq[(i & (1 << target)) == 0] = (
                cupy.cos(theta / 2) * qubits[(i & (1 << target)) == 0] +
                -cupy.sin(theta / 2) * qubits[(i & (1 << target)) != 0]
            )
            newq[(i & (1 << target)) != 0] = (
                cupy.sin(theta / 2) * qubits[(i & (1 << target)) == 0] +
                cupy.cos(theta / 2) * qubits[(i & (1 << target)) != 0]
            )
            qubits = newq
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        theta = self.theta
        for target in slicing(targets, n_qubits):
            qasm.append("ry({}) q[{}];".format(theta, target))
        return qasm

class RZGate:
    def __init__(self, theta):
        self.theta = theta

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        i = helper["indices"]
        theta = self.theta
        for target in slicing(targets, n_qubits):
            qubits[(i & (1 << target)) != 0] *= complex(math.cos(theta), math.sin(theta))
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        theta = self.theta
        for target in slicing(targets, n_qubits):
            qasm.append("rz({}) q[{}];".format(theta, target))
        return qasm

class TGate:
    def __init__(self):
        pass

    def apply(self, helper, qubits, targets):
        sqrt2_inv = 1 / cupy.sqrt(2)
        factor = complex(sqrt2_inv, sqrt2_inv)
        n_qubits = helper["n_qubits"]
        i = helper["indices"]
        for target in slicing(targets, n_qubits):
            qubits[(i & (1 << target)) != 0] *= factor
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        for target in slicing(targets, n_qubits):
            qasm.append("t q[{}];".format(target))
        return qasm

class SGate:
    def __init__(self):
        pass

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        i = helper["indices"]
        for target in slicing(targets, n_qubits):
            qubits[(i & (1 << target)) != 0] *= 1.j
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        for target in slicing(targets, n_qubits):
            qasm.append("s q[{}];".format(target))
        return qasm

class Measurement:
    _kernel = cupy.ReductionKernel(
        "uint64 target_mask, float64 p, T q_inout",
        "float64 b",
        "(!(_j & target_mask)) * (q_inout * q_inout.conj()).real()",
        "a + b",
        """
        q_inout = (!(_i & target_mask) == (a <= p)) * q_inout / sqrt((a <= p) * a + (a > b) * (1.0 - a))
        """,
        "0.0"
    )

    no_cache = True
    def __init__(self):
        pass

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        i = helper["indices"]
        p = random.random()
        for target in slicing(targets, n_qubits):
            target_mask = 1 << target
            a = self._kernel(target_mask, p, qubits)
            helper["cregs"][target] = int(a > p)
        return qubits

    def to_qasm(self, helper, targets):
        n_qubits = helper["n_qubits"]
        qasm = []
        for target in slicing(targets, n_qubits):
            qasm.append("measure q[{}] -> c[{}];".format(target, target))
        return qasm

class DebugDisplay:
    def __init__(self, *args, **kwargs):
        self.ctor_args = (args, kwargs)

    def apply(self, helper, qubits, targets):
        n_qubits = helper["n_qubits"]
        for target in slicing(targets, n_qubits):
            print("ctor arguments:", self.ctor_args)
            print("helper:", helper)
            print("target:", target)
            print("qubits:", qubits)
            indices = cupy.arange(0, 2**n_qubits, dtype=int)
        return qubits

    def to_qasm(self, helper, targets):
        return []

def slicing_singlevalue(arg, length):
    if isinstance(arg, slice):
        start, stop, step = arg.indices(length)
        i = start
        if step > 0:
            while i < stop:
                yield i
                i += step
        else:
            while i > stop:
                yield i
                i += step
    else:
        try:
            i = arg.__index__()
        except AttributeError:
            raise TypeError("indices must be integers or slices, not " + arg.__class__.__name__)
        if i < 0:
            i += length
        yield i

def slicing(args, length):
    if isinstance(args, tuple):
        for arg in args:
            yield from slicing_singlevalue(arg, length)
    else:
        yield from slicing_singlevalue(args, length)

def qubit_pairs(args, length):
    if not isinstance(args, tuple):
        raise ValueError("Control and target qubits pair(s) are required.")
    if len(args) != 2:
        raise ValueError("Control and target qubits pair(s) are required.")
    controls = list(slicing(args[0], length))
    targets = list(slicing(args[1], length))
    if len(controls) != len(targets):
        raise ValueError("The number of control qubits and target qubits are must be same.")
    for c, z in zip(controls, targets):
        if c == z:
            raise ValueError("Control qubit and target qubit are must be different.")
    return zip(controls, targets)

def get_maximum_index(indices):
    def _maximum_idx_single(idx):
        if isinstance(idx, slice):
            start = -1
            stop = 0
            if idx.start is not None:
                start = idx.start.__index__()
            if idx.stop is not None:
                stop = idx.stop.__index__()
            return max(start, stop - 1)
        else:
            return idx.__index__()
    if isinstance(indices, tuple):
        return max(_maximum_idx_single(i) for i in indices)
    else:
        return _maximum_idx_single(indices)
