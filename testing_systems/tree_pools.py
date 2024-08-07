import trees


class BasicObject:
    def __init__(self):
        self.label:trees.GroupLabel = None
        trees.GroupLabel.unlabeled.add(self)


def label_object(obj:BasicObject, label:trees.GroupLabel):
    obj.label = label
    label.items.add(obj)