'''
    deferred.py
    Meta Bloqs that defer instantiation
'''
from typing import Dict, Iterator, Generator
from types import FunctionType
from numpy.typing import NDArray

import cirq
import qualtran
from qualtran._infra.gate_with_registers import GateWithRegisters
from qualtran._infra.registers import Signature

from pyLIQTR.utils.meta import MetaBloq

class Deferred(MetaBloq):
    '''
        This Bloq exists to defer instantiation
    '''

    def __init__(
                self,
                subbloq_gen: FunctionType,
                *args,
                caching: bool = False,
                **kwargs
            ):
        '''
            Constructor for the Deferred bloq
            :: subbloq_gen : FunctionType :: Constructor for the gate
            :: *args :: Args to the deferred bloq
            :: caching : bool :: Whether the repeated object should be cached
            :: quregs : dict :: Map back to cirq qubit labels for qualtran bloq
            :: **kwargs :: Kwargs to the deferred bloq
        '''
        self.subbloq_gen = subbloq_gen

        self.args = None
        self.kwargs = None

    @property
    def signature(self) -> Signature:
        '''
            Signature is instantiated after resolution
        '''
        pass

    def __str__(self) -> str:
        '''
            Due to strcmp operations elsewhere in pyLIQTR this may cause issues
        '''
        return f'DEFER'

    def compose(self) -> Generator[
            qualtran.Bloq | cirq.Gate | cirq.Circuit,
            None,
            None
            ]:
        '''
        Dispatch method for decomposer
        Dynamic dispatch is set in the constructor
        '''
        bloq = self.subbloq_gen(
            *self.args,
            **self.kwargs
        )
        yield bloq


class Cached(MetaBloq):
    '''
        This Bloq exists to cache sub-bloqs
        Defers instantiation 
        Generates singleton instances of sub-bloqs
    '''

    SINGLETON_CACHE = {}

    def __init__(
                self,
                tag,
                subbloq_gen: FunctionType,
                *args,
                **kwargs
            ):
        '''
            Constructor for the Parameterised tagged Bloq
            :: tag : Hashable ::   
            :: subbloq_gen : FunctionType :: Constructor for the gate
            :: caching : bool :: Whether the repeated object should be cached
            :: quregs : dict :: Map back to cirq qubit labels for qualtran bloq
        '''
        self.tag = tag
        self.subbloq_gen = subbloq_gen

        self.args = None
        self.kwargs = None

    @property
    def signature(self) -> Signature:
        '''
            Signature is instantiated after resolution
        '''
        pass

    def __str__(self) -> str:
        '''
            Due to strcmp operations elsewhere in pyLIQTR this may cause issues
        '''
        return f'CACHE'

    def compose(self) -> Generator[
            qualtran.Bloq | cirq.Gate | cirq.Circuit,
            None,
            None
            ]:
        '''
        Dispatch method for decomposer
        '''
        cache_entry = Cached.SINGLETON_CACHE.get(self.tag, None)
    
        if cache_entry is None:
            bloq = self.subbloq_gen(
                *self.args,
                **self.kwargs
            )
            Cached.SINGLETON_CACHE[self.tag] = bloq
            yield bloq
        else:
            yield cache_entry
