from __future__ import annotations

class Label:
    _retired:set[Label] = set()

    @classmethod
    def is_name_available(cls, name:str, parent:Label) -> bool:
        if name in parent.children:
            return False
        return True

    def __init__(self, name:str, parent:Label):
        self.parent = parent
        self.children:list[Label] = []
        self.name = name
        self._is_retired = False
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, parent={self.parent}, nChildren={len(self.children)}, retired?={self._is_retired})"

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name):
        if self.__class__.is_name_available(new_name, self.parent) == False:
            raise KeyError(f"Name {new_name} is already in use in the {self.parent.name} group.")
        self._name = new_name
    
    def retire(self):
        self._is_retired = True
        self.__class__._retired.add(self)
        for child in self.children:
            child.retire()
    
    def unretire(self):
        self._is_retired = False
        self.__class__._retired.remove(self)
        for child in self.children:
            child.unretire()
    
    def get_unretired_children(self) -> list[Label]:
        return [child for child in self.children if child._is_retired == False]
    
    def __hash__(self):
        if self.parent is None:
            return hash(self.name)
        return hash((self.parent, self.name))
    
    def __eq__(self, other):
        if isinstance(other, self.__class__) == False:
            return False
        return hash(self) == hash(other)
