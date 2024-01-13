import datetime

class TimeStamp:
    def __init__(self):
        pass
    def now(self):
        t = datetime.datetime.now()
        return f"{t.year}{t.month:02d}{t.day:02d}-{t.hour:02d}{t.minute:02d}{t.second:02d}"

class SaveManager:
    def __init__(self):
        self._timestamp = TimeStamp()
    def save(self, save_dir:str='saves', **kwargs):
        filename = save_dir + self._timestamp.now()
        raise NotImplementedError('TODO -- implement saving')
    def load(self, latest:bool=True, save_dir:str='saves', save:str=None, **kwargs):
        raise NotImplementedError('TODO -- implement loading')