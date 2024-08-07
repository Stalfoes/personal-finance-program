import re
import json

class Labeller:
    def __init__(self, data_source:str='labels.json'):
        self._labels:dict[str,list[str]]
        self.load(data_source)
    def __getitem__(self, key:dict) -> list[str]:
        for pat in self._labels:
            if re.search(pat, key) is not None:
                return self._labels[pat]
        return []
    def load(self, data_source:str):
        with open(data_source, 'r') as file:
            self._labels:dict[str,list[str]] = json.loads(file.read())['labels']
    def save(self, filepath:str):
        data = json.dumps({'labels':self._labels})
        with open(filepath, 'w') as file:
            print(data, end='', file=file)
    