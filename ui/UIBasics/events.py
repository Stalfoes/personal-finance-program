class Event:
    def __init__(self):
        self.subscribers = set()
    def publisher(self, func):
        # decorator
        def inner(*args, **kwargs):
            ret = func(*args, **kwargs)
            self.notify()
            return ret
        return inner
    def subscribe(self, func):
        self.subscribers.add(func)
    def unsubcribe(self, func):
        self.subscribers.remove(func)
    def notify(self, *args, **kwargs):
        for func in self.subscribers:
            func(*args, **kwargs)
    def subscriber(self, func):
        # doesn't work for class methods but works for non-class methods
        # decorator
        self.subscribers.add(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        return inner