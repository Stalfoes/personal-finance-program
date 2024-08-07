from __future__ import annotations
import math

from trees import BasicObject
from streams import Stream, OnceStream
from ordered_list import OrderedList
from timewrapper import *


class Pool(BasicObject):
    def __init__(self, name:str, initial_stream:OnceStream):
        super().__init__()
        self._name = name
        self._initial_stream = initial_stream
        self._streams:OrderedList[Stream] = OrderedList(lambda s: s._identifying_time)

    def value_at(self, time:Time) -> float:
        assert time >= self._initial_stream._time, "Time must be after the initial stream time"
        balances = [s.value_to_at(time, self) for s in self._streams]
        balance_sum = sum(balances) + self._initial_stream._amount
        return balance_sum
    
    def copy(self) -> Pool:
        p = Pool(self._name, self._initial_stream.copy())
        p._streams = self._streams.copy()
        return p


class InterestPool(Pool):
    def __init__(self, name:str, initial_stream:OnceStream, interest_rate:float=0, first_compounding_time:Time=Time(seconds_since_epoch_utc=0), compounding_frequency:TimeDelta=TimeDelta(seconds=1)):
        super().__init__(name, initial_stream)
        self._interest_rate = interest_rate
        self._first_compounding_time = first_compounding_time
        self._compounding_frequency = compounding_frequency

    def interest_coefficient_at(self, time:Time) -> float:
        offset_time = (time - self._first_compounding_time)._delta_seconds
        freq_secs = self._compounding_frequency._delta_seconds
        return max((1 + self._interest_rate) ** math.floor(offset_time / freq_secs), 1.0)

    def value_at(self, time:Time) -> float:
        return super().value_at(time) * self.interest_coefficient_at(time)
    
    def copy(self) -> InterestPool:
        p = InterestPool(self._name, self._initial_stream.copy(), self._interest_rate, self._first_compounding_time.copy(), self._compounding_frequency.copy())
        return p