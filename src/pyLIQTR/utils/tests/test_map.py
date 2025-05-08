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

    @staticmethod
    def generate_circuit(
            *,
            n_repetitions: int = 1,
            n_qubits: int = 2
            ) -> cirq.Circuit:
        '''
        Generates a simple circuit to test on
        '''
        circ = cirq.Circuit()
        q = [cirq.LineQubit(i) for i in range(n_qubits)]

        for _ in range(n_repetitions):
            for i in range(n_qubits - 1):
                circ.append(cirq.H(q[i]))
                circ.append(cirq.CNOT(q[i], q[i + 1]))

        return circ

    @staticmethod
    def generate_bloqs(
        *,
        n_repetitions: int = 1,
        n_qubits: int = 2
        ) -> None:

        from qualtran.bloqs.basic_gates import CNOT, Hadamard
        from qualtran import BloqBuilder
        CX = CNOT()
        H = Hadamard()

        bb = BloqBuilder() 

        qubits = [
            bb.add_register(f'q{i}', 1)
            for i in range(n_qubits)
        ]
        
        for _ in range(n_repetitions):
            for i in range(n_qubits - 1):
                qubits[i] = bb.add(H, q=qubits[i])
                qubits[i], qubits[i + 1] = bb.add(CX, ctrl=qubits[i], target=qubits[i + 1])
        cbloq=bb.finalize(**{f'q{i}':qubits[i] for i in range(len(qubits))})
        return cbloq
                
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
            for reg in registers[1:]:
                yield cirq.H(reg) 
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
