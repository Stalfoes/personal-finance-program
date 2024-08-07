from __future__ import annotations

from pools import Pool
from streams import Stream
from encoder import Encoder, TransactionType


class CopyableObject:
    def __init__(self):
        pass
    def copy(self):
        raise NotImplementedError(f"CopyableObject must be able to be copied.")
    @classmethod
    def is_instance(cls, obj):
        return isinstance(obj, cls) or hasattr(obj, 'copy')
    def __copy__(self):
        return self.copy()
    def __deepcopy__(self):
        return self.copy()


class Environment(CopyableObject):
    def __init__(self):
        self._pools:set[Pool] = set()
    def copy(self) -> Environment:
        raise NotImplementedError("TODO")
    def encode_and_add(self, transaction:TransactionType):
        # Encode transaction:
        #   - Check if stream can be mapped into existing reoccuring streams
        #     - If yes, we're finished
        #   - Otherwise, create a OnceStream
        #   - Check if pools exist for stream to connect to
        #     - If yes, connect the stream to pools
        #   - Otherwise, create the pools and connect the stream
        raise NotImplementedError("TODO")