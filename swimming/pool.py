from __future__ import annotations
import time

class Pool:
    pools:dict[str,Pool] = {}
    def __init__(self, unique_name:str, starting_balance:float):
        self.name = unique_name
        Pool.pools[self.name] = self
        self.balance = starting_balance
        self.checkpoints:list[dict[str,float]] = [{'time':time.time(), 'balance':self.balance, 'change':0.0}]
    def __del__(self):
        del Pool.pools[self.name]
    @property
    def name(self):
        return self.__name
    @name.setter
    def name(self, new_name):
        if not isinstance(new_name, str):
            raise TypeError(f"New name must be of type str. {type(new_name)} was provided instead.")
        if new_name in Pool.pools:
            raise KeyError(f"New name, {new_name}, must not already be taken.")
        old_name = self.__name
        self.__name = new_name
        del Pool.pools[old_name]
        Pool.pools[self.__name] = self
    @property
    def balance(self):
        return self.__balance
    @balance.setter
    def balance(self, new_balance):
        if new_balance < 0:
            raise ValueError(f"Cannot reduce balance below $0.00")
        old_balance = self.__balance
        self.__balance = new_balance
        self.checkpoints.append(
            {'time':time.time(), 'balance':new_balance, 'change':new_balance - old_balance}
        )
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.__class__.__name__ + f"({self.name}, {self.balance})"
    def amount_at(self, timestamp:float) -> float:
        for checkpoint in self.checkpoints[::-1]:
            if timestamp >= checkpoint['time']:
                return checkpoint['balance']
        raise KeyError(f"Cannot get balance at {time.ctime(timestamp)} because that is earlier than the account was created - {time.ctime(self.checkpoints[0]['time'])}.")
    def total_in_out_over_time(self, start_time:float, end_time:float) -> tuple[float, float]:
        t_in, t_out = 0.0, 0.0
        for checkpoint in self.checkpoints:
            if start_time <= checkpoint['time'] and checkpoint['time'] <= end_time:
                if checkpoint['change'] >= 0:
                    t_in += checkpoint['change']
                else:
                    t_out += -checkpoint['change'] # abs(checkpoint['change'])
            elif checkpoint['time'] > end_time:
                break
        return t_in, t_out
    def __hash__(self):
        return hash((self.__class__, self.name))