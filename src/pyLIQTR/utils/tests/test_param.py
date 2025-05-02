'''
    Tests for the Param Bloq
'''
import types
import unittest

from functools import partial

import cirq
from qualtran import CompositeBloq
from pyLIQTR.utils.repeat import Parameterised, Repeat 
from pyLIQTR.utils.repeat import circuit_to_quregs

from pyLIQTR.utils.circuit_decomposition import circuit_decompose_multi
from pyLIQTR.utils.circuit_decomposition import generator_decompose

from pyLIQTR.utils.tests.test_helpers import TestHelpers, extract_and_run_tests


class TestParamBloq(unittest.TestCase, TestHelpers):
    '''
        Tests for the Repeat Bloq
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
        
        circ = self.generate_bloqs(n_qubits=n_qubits, n_repetitions=n_repetitions)
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
            Test wrapping a cirq.Circuit in a Param
            The whole circuit is generated by the wrapping function
        '''
        circ = self.generate_circuit(n_qubits=n_qubits) 
        bloq = Parameterised(Repeat, circ)

        for i in range(1, n_repetitions):
            repeat_circuit = self.generate_circuit(n_qubits=n_qubits, n_repetitions=i)
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
                decomp = 2
            )

            assert self.circuit_equality(
                repeat_circuit,
                bloq,
                decomp = 2 # Needs two rounds of decomposition
            )

# Test runner without invoking subprocesses
# Used for interactive and pdb hooks
if __name__ == '__main__':
    extract_and_run_tests(TestParamBloq())
