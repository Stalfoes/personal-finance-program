from __future__ import annotations
from typing import TypeVar, Generic
import copy

from environments import CopyableObject
from streams import Stream, OnceStream, RepeatingStream
from pools import Pool
from timewrapper import Time, TimeDelta


class ValueRange:
    def __init__(self, low=None, high=None, low_inclusive=True, high_inclusive=True):
        if (low is None) and (high is None):
            raise ValueError("One of `low` and `high` have to be not None.")
        self.low = low
        self.high = high
        self.low_inclusive = low_inclusive
        self.high_inclusive = high_inclusive
    def within(self, obj) -> bool:
        if self.low is not None:
            if self.low_inclusive:
                low_bool = obj >= self.low
            else:
                low_bool = obj > self.low
        else:
            low_bool = True
        if self.high is not None:
            if self.high_inclusive:
                high_bool = obj <= self.high
            else:
                high_bool = obj < self.high
        else:
            high_bool = True
        return low_bool and high_bool
    def hash(self):
        return hash((self.low, self.high))


ObjectType = TypeVar('ObjectType')
class KWargsToObject(Generic[ObjectType]):
    def __init__(self):
        self.splits:list
        self.mapping:dict[tuple,ObjectType] = {}
        self.granularity = None
        self.key_tuple = tuple()
    def get(self, **keys) -> ObjectType:
        pass
    def map(self, **region):
        pass
    def _kwargs_to_tuple(self, **kwargs):
        kwargs_keys = set(kwargs)
        for key in self.key_tuple:
            if key in kwargs_keys:
                kwargs_keys.remove(key)
        new_keys = tuple(kwargs_keys)
        self.key_tuple = (*self.key_tuple, *new_keys)
        new_mappings = {}
        for key,value in self.mapping.items():
            new_key = (*key, *(ValueRange(None,None) for new_key in new_keys))
            new_mappings[new_key] = value
        self.mapping = new_mappings


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