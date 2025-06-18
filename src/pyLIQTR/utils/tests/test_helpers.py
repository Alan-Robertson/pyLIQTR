'''
    Common helper methods for tests
'''

import types
import typing
import unittest

import numpy
import cirq
from qualtran import CompositeBloq, Register, QBit, BloqBuilder, Bloq, Signature
from qualtran._infra.gate_with_registers import GateWithRegisters
from qualtran.bloqs.basic_gates import CNOT, Hadamard
from qualtran import BloqBuilder


from pyLIQTR.utils.meta import MetaBloq
from pyLIQTR.utils.circuit_decomposition import circuit_decompose_multi
from pyLIQTR.utils.circuit_decomposition import generator_decompose


def extract_and_run_tests(tst: unittest.TestCase):
    '''
        Test runner without invoking subprocesses
    '''
    # Extract test functions from tst object
    for prop in dir(tst):
        if prop[:4] == 'test':
            obj = getattr(tst, prop)
            if issubclass(type(obj), types.MethodType):
                obj()

class TestHelpers():
    '''
        Class containing static methods for comparisons between decomposed  
        bloqs and circuits
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
        n_qubits: int = 2,
        CNOT = CNOT,
        Hadamard = Hadamard,
        ) -> None:
        '''
        Generates a simple circuit
        '''
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

    @staticmethod
    def consume(iterable: typing.Iterable):
        '''
            Forces evaluation of all elements in an iterable
            Useful for stateful map operations without allocating memory 
        '''
        for _ in iterable:
            pass

    @staticmethod
    def non_empty(iterable: typing.Iterable) -> bool:
        try:
            next(iterable)
            return True
        except StopIteration:
            return False

    @staticmethod
    def generator_equality(
            circuit: cirq.Circuit,
            bloq: CompositeBloq 
            ) -> bool:
        '''
            Tests equality for generator decompose
        '''
        # Test that the bloq is not empty
        assert TestHelpers.non_empty(generator_decompose(bloq))

        # Test that all decomposition objects match  
        return all(
            map(
                lambda x: x[0] == x[1],
                zip(
                    generator_decompose(bloq),
                    generator_decompose(circuit)
                )
            )
        )

    @staticmethod
    def circuit_equality(
            circuit: cirq.Circuit,
            bloq: CompositeBloq,
            decomp: int = 1
            ) -> bool:
        '''
            Tests circuits for equality, moment by moment
            :: circuit : cirq.Circuit :: Repeated Circuit Object
            :: bloq : Repeat :: Repeating Bloq Object
            :: decomp : int :: Number of decompositions for the decomp_multi
        '''
        # Test that the bloq is not empty
        assert TestHelpers.non_empty(iter(circuit_decompose_multi(bloq, decomp)))
    
        # Test that all decomposition objects match 
        return all(
            map(
                lambda x: x[0] == x[1],
                zip(
                    circuit,
                    circuit_decompose_multi(bloq, decomp)
                )
            )
        )

    @staticmethod
    def generator_commutative_equality(
            circuit: cirq.Circuit,
            bloq: CompositeBloq 
            ) -> bool:
        '''
            Tests equality for generator decompose
            This resolves issues where the gates are out of order but commute
            :: circuit : cirq.Circuit :: Repeated Circuit Object
            :: bloq : Repeat :: Repeating Bloq Object
        '''

        # Test that the bloq is not empty
        assert TestHelpers.non_empty(generator_decompose(bloq))

        backlog = []
        # Tracks the iterator for the decomposition of the circuit
        gen = generator_decompose(circuit)

        # Tracks the iterator for the decomposition of the repeating bloq
        # Not the happiest with the amount of GOTO-like structures here;
        # Python for loops lack grace
        for bloq_gate in generator_decompose(bloq):

            qubits = bloq_gate.qubits
            found = False

            # First check any backlogged gates
            for cmp in backlog:
                if any(i in cmp.qubits for i in qubits):
                    # Gate resolution is out of order, bail
                    if cmp != bloq_gate:
                        return False
                    found = cmp
                    break

            # Gate was in commutative order in the backlog, continue
            if found is not False:
                backlog.remove(found)
                continue

            # Gate was not in the backlog
            # Traverse the generator until we find the appropriate gate
            for cmp in gen:

                # Gate resolution is out of order, bail
                if any(i in cmp.qubits for i in qubits):
                    if cmp != bloq_gate:
                        return False
                    found = True
                    break

                # Append non-matching gates to the backlog
                backlog.append(cmp)

            if not found:
                return False

        # All gates were matched in order
        return True

    @staticmethod
    def naive_compose_bloqs(n_regs, *bloqs):
        '''
         Composes bloqs together
         This is a naive method that serves to test composite bloqs
        '''
        regs = [Register(f'q{i}', dtype=QBit()) for i in range(n_regs)] 
        soquets = [None for _ in range(n_regs)]

        bb = BloqBuilder()
        for i, reg in enumerate(regs):
            soquets[i] = bb.add_register(reg)

        for bloq in bloqs:
            n_args = len(list(bloq.signature.lefts()))
            bindings = {reg.name:arg for reg, arg in zip(bloq.signature.lefts(), soquets)}
            soquets[:n_args] = bb.add(bloq, **bindings) 

        cbloq = bb.finalize(**{reg.name:soquet for reg, soquet in zip(regs, soquets)})
        return cbloq


    @staticmethod
    def naive_decomposable_bloq(n_regs, *bloqs):
        '''
            Factory for decomposable bloqs
        '''
        class NaiveDecomposableBloq(GateWithRegisters):

            # Placeholders
            n_regs = None 
            bloqs = None 

            @property
            def signature(self):
                return Signature(
                        [Register(f'q{i}', dtype=QBit()) for i in range(self.n_regs)]
                       )

            def build_composite_bloq(
                self,
                bb: BloqBuilder,
                **kwargs):
                '''
                 Composes bloqs together
                 This is a naive method that serves to test composite bloqs
                '''
                regs = [Register(f'q{i}', dtype=QBit()) for i in range(self.n_regs)] 
                soquets = [kwargs[reg.name] for reg in regs]

                for bloq in self.bloqs:
                    n_args = len(list(bloq.signature.lefts()))
                    bindings = {reg.name:arg for reg, arg in zip(bloq.signature.lefts(), soquets)}
                    soquets[:n_args] = bb.add(bloq, **bindings) 

                return {reg.name:soquet for reg, soquet in zip(regs, soquets)}

            def _decompose_with_context_(self, *, context=None, **kwargs):
                yield from self.bloqs

        # Inject class objects
        NaiveDecomposableBloq.n_regs = n_regs
        NaiveDecomposableBloq.bloqs = list(bloqs)

        return NaiveDecomposableBloq
