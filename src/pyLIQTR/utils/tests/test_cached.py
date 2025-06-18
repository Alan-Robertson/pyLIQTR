'''
    Tests for the Deferred Bloq
'''
import types
import unittest

from functools import partial

import cirq
from qualtran import CompositeBloq
from pyLIQTR.utils.deferred import Cached 
from pyLIQTR.utils.repeat import circuit_to_quregs

from pyLIQTR.utils.circuit_decomposition import circuit_decompose_multi
from pyLIQTR.utils.circuit_decomposition import generator_decompose

from pyLIQTR.utils.tests.test_helpers import TestHelpers, extract_and_run_tests

from qualtran.bloqs.basic_gates import CNOT, Hadamard
from qualtran import BloqBuilder


class TestDeferredBloq(unittest.TestCase, TestHelpers):
    '''
        Tests for the Deferred Bloq
    '''
    def test_cirq_unary_gate(self, n_qubits=10):

        q = [cirq.LineQubit(i) for i in range(n_qubits)]
        target_gate = cirq.H

        gate = Cached('tag', target_gate, q[0])
        assert next(gate.compose()) == target_gate(q[0])

        # Tag is already set, the cache should return a non-0 qubit object here
        for i in range(1, n_qubits): 
            assert not (next(gate.compose()) == target_gate(q[i]))

        # Tag is already set, the cache should return a non-0 qubit object here
        for i in range(1, n_qubits): 
            gate = Cached(f'tag_{i}', target_gate, q[0])

            assert not (next(gate.compose()) == target_gate(q[i]))

# Test runner without invoking subprocesses
# Used for interactive and pdb hooks
if __name__ == '__main__':
    extract_and_run_tests(TestDeferredBloq())
