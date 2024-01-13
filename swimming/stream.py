from swimming.pool import Pool

class BasicStream:
    def __init__(self, source:Pool, outputs:list[Pool]):
        self.source = source
        self.outputs = outputs
    def take_and_distribute(self):
        amount_to_distribute = self.take_behaviour()
        if amount_to_distribute > self.source.balance:
            raise ValueError(f"Amount to distribute is too large (${amount_to_distribute}), while Pool {self.source} only has ${self.source.balance}")
        self.distribute_behaviour(amount_to_distribute)
        self.source.balance -= amount_to_distribute
    def __repr__(self):
        return f"Stream({self.__class__.__name__}, {self.source} -> [{','.join(str(o) for o in self.outputs)}])"
    def take_behaviour(self) -> float:
        return 0.0
    def distribute_behaviour(self, amount: float):
        pass


class DirectStream(BasicStream):
    def __init__(self, source:Pool, output:Pool, amount:float, label:str=""):
        super().__init__(source, [output])
        self.amount = amount
        self.label = label
    def take_behaviour(self) -> float:
        return self.amount
    def distribute_behaviour(self, amount: float):
        self.outputs[0].balance += amount
    def __str__(self):
        return self.label


class PercentageStream(BasicStream):
    def __init__(self, source:Pool, outputs:list[Pool], percentages:list[float]):
        super().__init__(source, outputs)
        self.percentages = percentages
        assert len(self.outputs) == len(self.percentages)
    def take_behaviour(self) -> float:
        return self.source.balance
    def distribute_behaviour(self, amount: float):
        for pool, percentage in zip(self.outputs, self.percentages):
            pool.balance += percentage * amount
