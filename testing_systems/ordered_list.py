from __future__ import annotations
import copy
from typing import TypeVar, Generic
from collections.abc import Callable

from timewrapper import *


class Event:
    def __init__(self, time, value):
        self.time = time
        self.value = value
    def __str__(self):
        return f"<${self.value:.2f} @ {self.time.utc_seconds_since_epoch}>"
    def __repr__(self):
        return str(self)

class OrderedEventsList:
    def __init__(self):
        self.events = []
    def __len__(self):
        return len(self.events)
    def __getitem__(self, index):
        assert isinstance(index, int)
        return self.events[index]
    def __delitem__(self, index):
        assert isinstance(index, int)
        del self.events[index]
    def remove(self, event):
        pass
    def remove_with_and(self, amount=None, time=None):
        pass
    def add(self, event):
        if len(self.events) == 0:
            self.events = [event]
            return
        self.events.insert(self._binary_search(event), event)
    def _binary_search(self, target_event):
        if target_event.time <= self.events[0].time:
            return 0
        elif target_event.time >= self.events[-1].time:
            return len(self.events)
        L = 0
        R = len(self.events) - 1
        while L <= R:
            m = (L + R) // 2
            if self.events[m].time == target_event.time:
                return m
            elif self.events[m].time < target_event.time:
                L = m + 1
            else:
                R = m - 1
        return L
    def __str__(self):
        return str(self.events)


ItemType = TypeVar('ItemType')
class OrderedList(CopyableObject, Generic[ItemType]):
    def __init__(self, key_access_method:Callable):
        self.events:list[ItemType] = []
        self.key_of = key_access_method
    def __len__(self):
        return len(self.events)
    def __getitem__(self, index:int):
        assert isinstance(index, int)
        return self.events[index]
    def __delitem__(self, index:int):
        assert isinstance(index, int)
        del self.events[index]
    def add(self, item:ItemType):
        if len(self.events) == 0:
            self.events = [item]
            return
        self.events.insert(self._binary_search(item), item)
    def _binary_search(self, target_event:ItemType) -> int:
        if self.key_of(target_event) <= self.key_of(self.events[0]):
            return 0
        elif self.key_of(target_event) >= self.key_of(self.events[-1]):
            return len(self.events)
        L = 0
        R = len(self.events) - 1
        while L <= R:
            m = (L + R) // 2
            if self.key_of(self.events[m]) == self.key_of(target_event):
                return m
            elif self.key_of(self.events[m]) < self.key_of(target_event):
                L = m + 1
            else:
                R = m - 1
        return L
    def __iter__(self):
        return iter(self.events)
    def copy(self) -> OrderedList:
        l = OrderedList(self.key_of)
        l.events = copy.deepcopy(self.events)
        return l


if __name__ == '__main__':
    events = OrderedEventsList()
    events.add(Event(Time(5), 10))
    events.add(Event(Time(15), 20))
    events.add(Event(Time(10), 30))
    events.add(Event(Time(10), 35))
    events.add(Event(Time(0), 0))
    print(events)