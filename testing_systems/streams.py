from __future__ import annotations
from collections import defaultdict
import math

from trees import BasicObject
from timewrapper import *
from pools import Pool


class Stream(BasicObject):
    labelled_streams:defaultdict[str,set[Stream]] = defaultdict(lambda: set())
    def __init__(self, description:str, identifying_time:Time, source:Pool, destination:Pool):
        super().__init__()
        self._description = description
        self._identifying_time = identifying_time
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
        super().__init__(description, time, source, destination)
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
        super().__init__(description, first_time, source, destination)
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
