'''
    Common helper methods for tests
'''

import types
import unittest

import cirq
from qualtran import CompositeBloq

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

    @staticmethod
    def generator_equality(
            repeated_circuit: cirq.Circuit,
            repeated_bloq: CompositeBloq 
            ) -> bool:
        '''
            Tests equality for generator decompose
        '''
        try:
            # Raises StopIteration if either are empty 
            next(
                zip(
                    generator_decompose(repeated_bloq),
                    generator_decompose(repeated_circuit)
                )
            )
        except:
            assert False 

        # Test for equality
        return all(
            map(
                lambda x: x[0] == x[1],
                zip(
                    generator_decompose(repeated_bloq),
                    generator_decompose(repeated_circuit)
                )
            )
        )

    @staticmethod
    def circuit_equality(
            repeated_circuit: cirq.Circuit,
            repeated_bloq: CompositeBloq,
            decomp: int = 1
            ) -> bool:
        '''
            Tests circuits for equality, moment by moment
            :: repeated_circuit : cirq.Circuit :: Repeated Circuit Object
            :: repeated_bloq : Repeat :: Repeating Bloq Object
            :: decomp : int :: Number of decompositions for the decomp_multi
        '''
        return all(
            map(
                lambda x: x[0] == x[1],
                zip(
                    repeated_circuit,
                    circuit_decompose_multi(repeated_bloq, decomp)
                )
            )
        )

    @staticmethod
    def generator_commutative_equality(
            repeated_circuit: cirq.Circuit,
            repeated_bloq: CompositeBloq 
            ) -> bool:
        '''
            Tests equality for generator decompose
            This resolves issues where the gates are out of order but commute
            :: repeated_circuit : cirq.Circuit :: Repeated Circuit Object
            :: repeated_bloq : Repeat :: Repeating Bloq Object
        '''
        backlog = []
        # Tracks the iterator for the decomposition of the circuit
        gen = generator_decompose(repeated_circuit)

        # Tracks the iterator for the decomposition of the repeating bloq
        # Not the happiest with the amount of GOTO-like structures here, but
        # Python for loops lack grace
        for bloq_gate in generator_decompose(repeated_bloq):

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
