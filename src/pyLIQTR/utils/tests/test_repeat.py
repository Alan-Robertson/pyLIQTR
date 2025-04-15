import unittest 
import types
from itertools import count

import cirq
from qualtran import CompositeBloq
from pyLIQTR.utils.repeat import Repeat
from pyLIQTR.utils.circuit_decomposition import circuit_decompose_multi, generator_decompose    

class TestRepeatBloq(unittest.TestCase): 

    @staticmethod
    def generate_circuit(*, n_repetitions=1, n_qubits=2):
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
    def generator_equality(repeated_circuit, repeated_bloq):
        '''
            Tests equality for generator decompose
        ''' 
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
    def generator_commutative_equality(repeated_circuit, repeated_bloq):
        '''
            Tests equality for generator decompose
            This resolves issues where the gates are out of order but still commute  
        ''' 
        backlog = [] 
        gen = generator_decompose(repeated_circuit)

        for bloq_gate in generator_decompose(repeated_bloq): 
            qubits = bloq_gate.qubits 

            found = False

            # First check any backlogged gates
            for cmp in backlog:
                if any([i in cmp.qubits for i in qubits]): 
                    if cmp != bloq_gate:  
                        return False
                    else:
                        backlog.remove(cmp)
                        found = True
                        break

            # Gate was in commutative order in the backlog, continue
            if found:
                continue

            # Gate was not in the backlog 
            for cmp in gen:      
                if any([i in cmp.qubits for i in qubits]): 
                    if cmp != bloq_gate:  
                        return False
                    else:
                        found = True
                        break
                backlog.append(cmp)
            
            if not found:
                return False

        return True
                

    def test_bloq(self):
        '''
            Tests wrapping a CompositeBloq in a Repeat  
        '''
        n_repetitions = 6
        n_qubits = 5
        circ = self.generate_circuit(n_qubits=n_qubits)
        repeated_circuit = self.generate_circuit(n_repetitions=n_repetitions, n_qubits=n_qubits)

        quregs = {'qubits': 
                   [[q] for q in sorted(circ.all_qubits())]
                 }

        bloq = CompositeBloq.from_cirq_circuit(circ)
        repeat_bloq = Repeat(
            bloq,
            n_repetitions=n_repetitions,
            cirq_quregs=quregs
        )

        assert self.generator_commutative_equality(repeated_circuit, repeat_bloq)


    def test_gate(self):
        '''
            Tests wrapping a gate in a Repeat
        '''
        n_repetitions = 9

        gate = cirq.X  
        qubits = cirq.GridQubit.square(2)

        op = gate(qubits[0]) 

        repeat_bloq = Repeat(
            gate,
            qubits[0],
            n_repetitions=n_repetitions
        )
        
        for generated_op in generator_decompose(repeat_bloq): 
            assert op == generated_op 


    def test_circuit(self):
        '''
            Test wrapping a cirq.Circuit in a Repeat
        '''
        n_repetitions = 11 

        circ = self.generate_circuit()

        # Baseline repeated circuit
        repeated_circuit = self.generate_circuit(n_repetitions=n_repetitions)
       
        # Repeated circuit representation 
        repeat_bloq = Repeat(circ, n_repetitions=n_repetitions) 

        assert self.generator_equality(repeated_circuit, repeat_bloq)
    

# Test runner without invoking subprocesses 
# Used for interactive and pdb hooks
if __name__ == '__main__':
    tst = TestRepeatBloq()
    for prop in dir(tst):
        if prop[:4] == 'test':
            obj = getattr(tst, prop) 
            if issubclass(type(obj), types.MethodType):
                obj()
