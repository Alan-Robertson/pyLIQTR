'''
    Tests for the Param Bloq
'''
from functools import partial
import unittest

import cirq

from pyLIQTR.utils.repeat import Parameterised, Repeat
from pyLIQTR.utils.tests.test_helpers import TestHelpers, extract_and_run_tests


class TestParamBloq(unittest.TestCase, TestHelpers):
    '''
        Tests for the Param Bloq
    '''

    def test_cirq_unary_gate(self, n_qubits=10):
        '''
            Test param single cirq gate
        '''
        q = [cirq.LineQubit(i) for i in range(n_qubits)]
        target_gate = cirq.H
        bloq = Parameterised(target_gate)

        for i in range(n_qubits):
            # This function is invoked internally in the ParamMapBloq
            bloq.bind_params(q[i])

            # Test the bloq compose
            assert next(bloq.compose()) == target_gate(q[i])

            # Test the pyLIQTR decomposers
            circuit = cirq.Circuit()
            circuit.append(target_gate(q[i]))

            # Test generator_decompose and circuit_decompose_multi
            assert self.generator_commutative_equality(
                circuit,
                bloq
            )
            assert self.circuit_equality(
                circuit,
                bloq
            )

    def test_cirq_binary_gate(self, n_qubits=10):
        '''
            Tests multiple arguments
        '''
        q = [cirq.LineQubit(i) for i in range(n_qubits)]
        target_gate = cirq.CNOT
        bloq = Parameterised(target_gate)

        for i in range(n_qubits - 1):

            # Test the block internal composition
            args = (q[i], q[i + 1])
            bloq.bind_params(*args)
            assert next(bloq.compose()) == target_gate(*args)

            # Test the pyLIQTR decomposers
            circuit = cirq.Circuit()
            circuit.append(target_gate(*args))

            # Test generator_decompose and circuit_decompose_multi
            assert self.generator_commutative_equality(
                circuit,
                bloq
            )
            assert self.circuit_equality(
                circuit,
                bloq
            )

    def test_cirq_partial_binary_gate(self, n_qubits=10):
        '''
            Tests multiple arguments
            This test pre-binds some gate arguments
        '''
        q = [cirq.LineQubit(i) for i in range(n_qubits)]
        target_gate = cirq.ZPowGate

        targ = q[n_qubits - 1]

        # Wrapper function to redirect args appropriately
        def param_gate(gate, *args, **gate_kwargs):
            return gate(**gate_kwargs)(*args)

        # Paramterise a partial function
        bloq = Parameterised(
            partial(param_gate, cirq.ZPowGate),
            targ
        )

        for i in range(n_qubits - 1):
            bloq.bind_params(exponent=i)
            assert next(bloq.compose()) == target_gate(exponent=i)(targ)

            # Test the pyLIQTR decomposers
            circuit = cirq.Circuit()
            circuit.append(target_gate(exponent=i)(targ))

            # Test generator_decompose and circuit_decompose_multi
            assert self.generator_commutative_equality(
                circuit,
                bloq
            )
            assert self.circuit_equality(
                circuit,
                bloq
            )

    def test_bloq(self, n_qubits=4, n_repetitions=2):
        '''
            Test parameterising a bloq generating function
        '''

        circ = self.generate_bloqs(
            n_qubits=n_qubits,
            n_repetitions=n_repetitions
        )
        param = Parameterised(
                    self.generate_bloqs
                )
        param.bind_params(n_repetitions=2, n_qubits=n_qubits)

        assert self.generator_commutative_equality(
            circ.to_cirq_circuit(),
            next(param.compose()).to_cirq_circuit()
        )

    def test_repeat_bloq(self,  n_qubits: int = 4, n_repetitions: int = 3):
        '''
            Test parameterising a repeat
        '''
        circ = self.generate_circuit(n_qubits=n_qubits)
        bloq = Parameterised(Repeat, circ)

        for i in range(1, n_repetitions):
            repeat_circuit = self.generate_circuit(
                n_qubits=n_qubits,
                n_repetitions=i
            )
            repeat_bloq = Repeat(circ, n_repetitions=i)

            bloq.bind_params(n_repetitions=i)

            # Test generator_decompose and circuit_decompose_multi
            assert self.generator_commutative_equality(
                repeat_circuit,
                repeat_bloq
            )

            # Test generator_decompose and circuit_decompose_multi
            assert self.generator_commutative_equality(
                repeat_circuit,
                bloq,
            )

            assert self.circuit_equality(
                repeat_circuit,
                repeat_bloq,
                decomp=2
            )

            assert self.circuit_equality(
                repeat_circuit,
                bloq,
                decomp=2  # Needs two rounds of decomposition
            )


# Test runner without invoking subprocesses
# Used for interactive and pdb hooks
if __name__ == '__main__':
    extract_and_run_tests(TestParamBloq())
