from __future__ import annotations
from typing import TypeVar

from class_properties import classproperty
from environments import CopyableObject


class BasicObject(CopyableObject):
    def __init__(self):
        self.label:GroupLabel = None
        GroupLabel.unlabeled.add(self)
    def copy(self) -> BasicObject:
        obj = BasicObject()
        self.label.add(obj)
        return obj


class GroupLabel:
    _unlabeled_obj = None
    @classproperty
    def unlabeled(cls) -> GroupLabel:
        if cls._unlabeled_obj is None:
            cls._unlabeled_obj = cls('*UNLABELLED*', parent=None, items=None)
        print("HERE", cls._unlabeled_obj)
        return cls._unlabeled_obj
    def __init__(self, label:str, parent:GroupLabel=None, items:set[BasicObject]=None):
        self._label = label
        self._children:set[GroupLabel] = set()
        self._parent = parent
        self.items:set[BasicObject] = set() if items is None else items
    def __repr__(self):
        return f"<{repr(self._label)}, length={len(self.items)}>"
    def __str__(self):
        return repr(self)
    def __len__(self) -> int:
        return len(self._children)
    def add_child(self, group:GroupLabel):
        self._children.add(group)
    def remove_child(self, group:GroupLabel):
        self._children.remove(group)
    def __hash__(self) -> int:
        return hash((self.__class__, self._parent, self._label))
    def __eq__(self, other) -> bool:
        return isinstance(other, GroupLabel) and hash(self) == hash(other)
    def add(self, obj:BasicObject):
        if obj.label is not None:
            obj.label.items.remove(obj)
        self.items.add(obj)
        obj.label = self
    def remove(self, obj:BasicObject):
        self.items.remove(obj)
        self.__class__.unlabeled.items.add(obj)
        obj.label = self.__class__.unlabeled


class GroupTree(GroupLabel):
    def __init__(self):
        super().__init__(label='PARENT', parent=None, items=None)