from __future__ import annotations
import time
from streams import CopyableObject


class Time(CopyableObject):
    def __init__(self, seconds_since_epoch_utc:float):
        self.utc_seconds_since_epoch = seconds_since_epoch_utc
    @property
    def local_seconds(self) -> time.struct_time:
        return time.localtime(self.utc_seconds_since_epoch)
    def copy(self) -> Time:
        return Time(self.utc_seconds_since_epoch)
    def __str__(self) -> str:
        return time.strftime("%I:%M:%S %p, %a, %b %d %Y", self.local_seconds)
    def __sub__(self, other) -> TimeDelta:
        assert isinstance(other, Time)
        return TimeDelta(self.utc_seconds_since_epoch - other.utc_seconds_since_epoch)
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.utc_seconds_since_epoch})"
    def __equal__(self, other) -> bool:
        assert isinstance(other, Time)
        return self.utc_seconds_since_epoch == other.utc_seconds_since_epoch
    def __lt__(self, other) -> bool:
        assert isinstance(other, Time)
        return self.utc_seconds_since_epoch < other.utc_seconds_since_epoch
    def __gt__(self, other) -> bool:
        assert isinstance(other, Time)
        return self.utc_seconds_since_epoch > other.utc_seconds_since_epoch
    def __le__(self, other) -> bool:
        assert isinstance(other, Time)
        return self.utc_seconds_since_epoch <= other.utc_seconds_since_epoch
    def __ge__(self, other) -> bool:
        assert isinstance(other, Time)
        return self.utc_seconds_since_epoch >= other.utc_seconds_since_epoch
    def __ne__(self, other) -> bool:
        assert isinstance(other, Time)
        return self.utc_seconds_since_epoch != other.utc_seconds_since_epoch
    def __hash__(self):
        return hash((self.__class__, self.utc_seconds_since_epoch))


class TimeDelta(CopyableObject):
    def __init__(self, seconds:float=0, minutes:float=0, hours:float=0, days:float=0, weeks:float=0):
        assert seconds >= 0 and minutes >= 0 and hours >= 0 and days >= 0 and weeks >= 0
        self._delta_seconds = seconds + minutes*60 + hours*60*60 + days*24*60*60 + weeks*7*24*60*60
    def copy(self) -> TimeDelta:
        return TimeDelta(seconds=self._delta_seconds)
    def __add__(self, other:Time|TimeDelta) -> Time|TimeDelta:
        if isinstance(other, Time):
            return Time(other.utc_seconds_since_epoch + self._delta_seconds)
        elif isinstance(other, TimeDelta):
            return TimeDelta(self._delta_seconds + other._delta_seconds)
        else:
            return NotImplementedError(f"Cannot add to {type(other)}")
    def __sub__(self, other:TimeDelta) -> TimeDelta:
        if isinstance(other, TimeDelta):
            return TimeDelta(self._delta_seconds - other._delta_seconds)
        else:
            raise NotImplementedError(f"Cannot subtract {type(other)} from {type(self)}")
    def __radd__(self, other:Time|TimeDelta) -> Time|TimeDelta:
        return self.__add__(other)
    def __rsub__(self, other:Time|TimeDelta) -> Time|TimeDelta:
        if isinstance(other, Time):
            return Time(other.utc_seconds_since_epoch - self._delta_seconds)
        else:
            return self.__sub__(other)
    def __hash__(self):
        return hash((self.__class__, self._delta_seconds))