'''
    repeat.py
    Contains the Repeat meta-bloq
    Also contains a helper function circuit_to_quregs
'''
from typing import Dict, Iterator, Generator
from numpy.typing import NDArray

import cirq
import qualtran
from qualtran._infra.gate_with_registers import GateWithRegisters
from qualtran._infra.registers import Signature


def circuit_to_quregs(circuit: cirq.Circuit) -> dict:
    '''
        Extracts quregs from a circuit
        Uses the same ordering as the
         CompositeBloq methods, allowing for
        preservation of argument order
        :: circuit : cirq.Circuit :: Circuit
    '''
    all_qubits = sorted(circuit.all_qubits())
    return {'qubits': [[i] for i in all_qubits]}


class Repeat(GateWithRegisters):
    '''
        Composite bloq with options for how to handle generators
        May cache and re-emit, or may continuously instantiate and generate
    '''

    #pylint: disable=too-many-instance-attributes
    def __init__(
                self,
                subbloq: qualtran.Bloq | cirq.Gate | cirq.Circuit,
                *args,
                n_repetitions: int = 1,
                caching: bool = False,
                cirq_quregs: dict = None,
                **kwargs
            ):
        '''
            Constructor for the repeat bloq
            :: subbloq : GateWithRegisters | cirq.Gate :: Object to repeat
            :: *args :: Positional arguments
            :: n_repetitions : int :: Number of times to repeat the object
            :: caching : bool :: Whether the repeated object should be cached
            :: quregs : dict :: Map back to cirq qubit labels for qualtran bloq
        '''

        self.subbloq = subbloq
        self.args = args
        self.kwargs = kwargs
        self.n_repetitions = n_repetitions

        # Used to set quregs for bloq to cirq decomps if appropriate
        self.cirq_quregs = cirq_quregs

        # Caches the circuit between iterations
        # Should only be used if the repeated object is small or constant
        self.caching = caching
        self._cached = None

        # Dynamic dispatch
        # Sets different decomposers depending on the input
        self._decompose = None

        if issubclass(type(subbloq), qualtran.Bloq):
            self._decompose = self._qualtran_bloq_decomp

        elif issubclass(type(subbloq), cirq.Gate):
            self._decompose = self._cirq_gate_decomp

        elif issubclass(type(subbloq), cirq.Circuit):
            self._decompose = self._cirq_circuit_decomp

        else:
            raise TypeError(
                f"{subbloq} is not a qualtran.Bloq, cirq.Gate or cirq.Circuit"
            )

    @property
    def signature(self) -> Signature:
        '''
            Signature is directly inherited from the subbloq
            May throw errors if the subbloq lacks a signature
        '''
        return self.subbloq.signature

    def __str__(self) -> str:
        '''
            Due to strcmp operations elsewhere in pyLIQTR this may cause issues
        '''
        return f'REPEAT({str(self.subbloq)}, {self.n_repetitions})'

    def _cirq_gate_decomp(self) -> Generator[
            qualtran.Bloq | cirq.Gate | cirq.Circuit,
            None,
            None
            ]:
        '''
            _cirq_decomp
            Cirq gate decomposer
            Expected input is a single cirq gate object
        '''
        yield self.subbloq(*self.args, **self.kwargs)

    def _cirq_circuit_decomp(self) -> Generator[
            cirq.Circuit,
            None,
            None
            ]:
        '''
            _cirq_gate_decomp
            Cirq circuit decomposer
        '''
        for moment in self.subbloq:
            yield from moment

    def _qualtran_bloq_decomp(self) -> Generator[
            qualtran.Bloq,
            None,
            None
            ]:
        '''
            _qualtran_decomp
            Qualtran decomposer
        '''
        yield self.subbloq.to_cirq_circuit(
            *self.args,
            cirq_quregs=self.cirq_quregs,
            **self.kwargs
        )

    def build_composite_bloq(
            self,
            bb: qualtran.BloqBuilder,
            **soqs: qualtran.SoquetT
            ) -> Dict[str, qualtran.SoquetT]:
        '''
            Naive composite bloq builder
        '''
        for _ in range(self.n_repetitions):
            bb.add(self.subbloq, **soqs)
        return soqs

    def decompose_from_registers(
        self,
        *args,
        context: cirq.DecompositionContext,
        **quregs: NDArray[cirq.Qid]
    ) -> Iterator[cirq.OP_TREE]:
        '''
            decompose_from_registers
            Uses the subbloq's decomposition function and repeats the output
        '''
        if self.caching:
            cached_obj = list(
                self.subbloq.decompose_from_registers(
                    *args,
                    context,
                    quregs
                )
            )
            ops = iter(cached_obj)
        else:
            ops = self.subbloq.decompose_from_registers(*args, context, quregs)

        for _ in range(self.n_repetitions):
            yield from ops

    #pylint: disable=arguments-differ, unused-argument
    def _decompose_with_context_(self, *, context=None, **kwargs) -> Generator[
            qualtran.Bloq | cirq.Gate | cirq.Circuit,
            None,
            None
            ]:
        # Actually passing this into the decomposition depends on the decomp
        if context is None:
            context = cirq.DecompositionContext(
                cirq.ops.SimpleQubitManager()
            )
        yield from self.decompose()

    def decompose(self) -> Generator[
            qualtran.Bloq | cirq.Gate | cirq.Circuit,
            None,
            None
            ]:
        '''
        Dispatch method for decomposer
        Dynamic dispatch is set in the constructor
        '''
        for _ in range(self.n_repetitions):
            yield from self.decompose_once()

    def decompose_once(self) -> Generator[
            qualtran.Bloq | cirq.Gate | cirq.Circuit,
            None,
            None
            ]:
        '''
            Returns a single decomposition
        '''
        if self.caching:
            if self._cached is None:
                self._cached = tuple(self._decompose())
            decomp = self._cached
        else:
            decomp = self._decompose()

        yield from decomp

    def get_n_repetitions(self):
        '''
           Getter method
        '''
        return self.n_repetitions

    def _qid_shape_(self):
        '''
        Override for superclass abstract method
        '''

    def num_qubits(self):
        '''
        Instantiates against an abstract method
        These qubit counts only account for non-ancillae qubits
        '''
        return self.signature.n_qubits()
