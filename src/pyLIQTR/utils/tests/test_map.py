'''
    Tests for the Param Bloq
'''
import types
import unittest

from functools import partial

import cirq
from qualtran import CompositeBloq
from pyLIQTR.utils.repeat import Parameterised, ParamMap
from pyLIQTR.utils.repeat import circuit_to_quregs

from pyLIQTR.utils.circuit_decomposition import circuit_decompose_multi
from pyLIQTR.utils.circuit_decomposition import generator_decompose

from pyLIQTR.utils.tests.test_helpers import TestHelpers, extract_and_run_tests

class TestParamMapBloq(unittest.TestCase, TestHelpers):
    '''
        Tests for the ParamMap Bloq
    '''
    def test_cirq_unary_gate(self, n_qubits=10):

        qubits = [cirq.LineQubit(i) for i in range(n_qubits)]
        target_gate = cirq.H
        param_gate = Parameterised(target_gate) 

        # Map gate over all qubits
        bloq = ParamMap(
                qubits,
                *[param_gate] * n_qubits
                )

        circuit = cirq.Circuit()
        for idx in range(n_qubits): 
            circuit.append(target_gate(qubits[idx]))

        # Test composition
        for idx, gate in enumerate(bloq.compose()): 
            assert gate == target_gate(qubits[idx])

        # Test generator_decompose and circuit_decompose_multi
        assert self.generator_commutative_equality(
            circuit,
            bloq
        )
   
        assert self.circuit_equality(
            circuit,
            bloq
        )

    def test_mixed_param(self, n_qubits=10):
        from itertools import repeat

        qubits = [cirq.LineQubit(i) for i in range(n_qubits)]

        # Test using a generator to build the circuit
        def operations(registers):
            for reg in registers:
                yield cirq.H(reg) 
                if reg is not registers[0]:
                    yield Parameterised(cirq.CZ, reg) 

        # Map gate over all qubits
        bloq = ParamMap(
                repeat(qubits[0]),
                operations(qubits) 
                )

        circuit = cirq.Circuit()
        for reg in qubits[1:]: 
            circuit.append(cirq.H(reg))
            circuit.append(cirq.CZ(reg, qubits[0]))

        # Test generator_decompose and circuit_decompose_multi
        assert self.generator_commutative_equality(
            circuit,
            bloq
        )
  
        # Map gate over all qubits
        bloq = ParamMap(
                repeat(qubits[0]),
                operations(qubits) 
        )

        assert self.circuit_equality(
            circuit,
            bloq
        )

# Test runner without invoking subprocesses
# Used for interactive and pdb hooks
if __name__ == '__main__':
    extract_and_run_tests(TestParamMapBloq())
