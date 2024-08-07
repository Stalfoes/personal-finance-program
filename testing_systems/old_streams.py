from __future__ import annotations
from collections import defaultdict
import uuid
from timewrapper import Time, TimeDelta
from environments import CopyableObject
import copy
import math
from typing import TypeVar


class Id:
    def __init__(self, objectType, time:Time, amount:float):
        self.objectType = objectType
        self.time = time
        self.amount = amount
    def __hash__(self):
        return hash((self.objectType, self.time, self.amount))
    def __int__(self):
        return hash(self)


class HashableObject:
    objects:dict[Id,HashableObject] = {}
    def __init__(self, id:Id=None):
        if id is None:
            selfType = type(self)
            if selfType == Stream:
                self._id = Id(selfType, self.identifying_time, self.)
            HashableObject.objects[self._uuid] = self
        else:
            self._uuid = uuid4
    def copy(self):
        raise NotImplementedError(f"Cannot create a copy of an instance of {type(self)}.")
    def __del__(self):
        del HashableObject.objects[self._uuid]
    def __equal__(self, other):
        assert isinstance(other, HashableObject), f"Other type must be HashableObject"
        return self._uuid == other._uuid
    def __hash__(self):
        return hash(self._uuid)


class classproperty(property):
    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


class Pool(HashableObject, CopyableObject):
    def __init__(self, name:str, initial_stream:OnceStream, interest_rate:float=0, first_compounding_time:Time=Time(seconds_since_epoch_utc=0), compounding_frequency:TimeDelta=TimeDelta(seconds=1)):
        self._name = name
        self._initial_stream = initial_stream
        self._streams:set[Stream] = set()
        self._interest_rate = interest_rate
        self._first_compounding_time = first_compounding_time
        self._compounding_frequency = compounding_frequency

    def interest_coefficient_at(self, time:Time) -> float:
        return 1.0
        # offset_time = (time - self._first_compounding_time)._delta_seconds
        # freq_secs = self._compounding_frequency._delta_seconds
        # return max((1 + self._interest_rate) ** math.floor(offset_time / freq_secs), 1.0)

    def value_at(self, time:Time) -> float:
        assert time >= self._initial_stream._time, "Time must be after the initial stream time"
        balances = [s.value_to_at(time, self) for s in self._streams]
        balance_sum = sum(balances) + self._initial_stream._amount
        return self.interest_coefficient_at(time) * balance_sum


class Stream(HashableObject,CopyableObject):
    labelled_streams:defaultdict[str,set[Stream]] = defaultdict(lambda: set())
    def __init__(self, identifying_time:Time, description:str, source:Pool, destination:Pool):
        super().__init__()
        self._description = description
        self._source = source
        self._destination = destination
    def _location_sign(self, location:Pool) -> int:
        if location == self._source:
            return -1.0
        elif location == self._destination:
            return 1.0
        else:
            return 0.0
    def value_to_at(self, time:Time, location:Pool) -> float:
        return 0.0
    def significant_times_between(self, start:Time, end:Time) -> set[Time]:
        return set()
    def copy(self) -> Stream:
        return Stream(self._description, self._source, self._destination)


class OnceStream(Stream):
    def __init__(self, description:str, source:Pool, destination:Pool, time:Time, amount:float):
        super().__init__(description, source, destination)
        self._time = time
        self._amount = amount
        assert self._amount >= 0, f"Amount must be >= 0. If it's a cost, then direct it away from a spot where it's an asset"
    def value_to_at(self, time:Time, location:Pool) -> float:
        if self._time >= time:
            return self._location_sign(location) * self._amount
        else:
            return 0.0
    def significant_times_between(self, start:Time, end:Time) -> set[Time]:
        if self._time >= end:
            return set()
        elif start <= self._time and self._time < end:
            return {self._time}
        elif self._time < start:
            return {start}
    def copy(self) -> OnceStream:
        return OnceStream(self._description, self._source, self._destination, self._time.copy(), self._amount)


class RepeatingStream(Stream):
    def __init__(self, description:str, source:Pool, destination:Pool, first_time:Time, amount:float, frequency:TimeDelta):
        super().__init__(description, source, destination)
        self._first_time = first_time
        self._amount = amount
        self._frequency = frequency
        assert self._amount >= 0, f"Amount must be >= 0. If it's a cost, then direct it away from a spot where it's an asset"
    def value_to_at(self, time:Time, location:Pool) -> float:
        subtracted_time:Time = time - self._first_time
        value = max(math.floor(subtracted_time.utc_seconds_since_epoch / self._frequency._delta_seconds) + 1.0, 0.0) * self._amount
        return self._location_sign(location) * value
    def significant_times_between(self, start:Time, end:Time) -> set[Time]:
        if self._first_time >= end:
            return set()
        else:
            times = set()
            current_time = self._first_time
            while current_time < end:
                if start <= current_time:
                    times.add(current_time)
                current_time += self._frequency
            return times
    def copy(self) -> RepeatingStream:
        return RepeatingStream(self._description, self._source, self._destination, self._first_time.copy(), self._amount, self._frequency.copy())


TransactionType = TypeVar('TransactionType')
class Encoder(CopyableObject):
    """Maps transactions (maybe dictionaries, strings, etc) to Pools and Streams (and groups?)
    """
    def __init__(self):
        self._stream_mapping:dict[TransactionType,Stream] = {}
        self._pool_mapping:dict[TransactionType,Pool] = {}
    def copy(self) -> Encoder:
        t = Encoder()
        t._stream_mapping = copy.deepcopy(self._stream_mapping)
        t._pool_mapping = copy.deepcopy(self._pool_mapping)
        return t
    def encode(self, transaction:TransactionType) -> Stream:
        raise NotImplementedError("TODO") # TODO
    def group_as_repeating(self, streams:set[OnceStream]):
        ordered_streams = sorted(streams, key=lambda stream: stream._time.utc_seconds_since_epoch, reverse=True)
        stream1 = ordered_streams[0] # the latest stream
        for stream in ordered_streams[1:]:
            assert stream._amount == stream1._amount, f"All streams must have the same amount to be grouped. {stream1._amount} ≠ {stream._amount}"
            assert stream._source == stream1._source, f"All streams must have the same sources. {stream1._source} ≠ {stream._source}"
            assert stream._destination == stream1._destination, f"All streams must have the same destinations. {stream1._destination} ≠ {stream._destination}"
        changes_in_time:list[TimeDelta] = [ordered_streams[i]._time - ordered_streams[i - 1]._time for i in range(1, len(ordered_streams))]
        changes_in_time_seconds = [change._delta_seconds for change in changes_in_time]
        average_frequency_seconds = sum(changes_in_time_seconds) / len(changes_in_time_seconds)
        frequency = TimeDelta(seconds=average_frequency_seconds)
        repeating_stream = RepeatingStream(stream1._description, stream1._source, stream1._destination, ordered_streams[-1]._time, stream._amount, frequency)
        # TODO -- figure out how to map the OnceStreams to the RepeatingStream
        return repeating_stream
        