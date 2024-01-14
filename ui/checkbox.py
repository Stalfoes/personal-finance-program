import pygame
import UIBasics

class BasicCheckbox(UIBasics.Content):
    def __init__(self, content:UIBasics.Content, bounding_box:UIBasics.BoundingBox, name:str=None):
        self.content = content
        self.bounding_box = bounding_box
        self.name = name
        self.on_toggle = UIBasics.Event()
        self.on_toggle_off = UIBasics.Event()
        self.on_toggle_on = UIBasics.Event()
        self.is_on = False
    def draw(self, surface:pygame.Surface, bounding_box:UIBasics.BoundingBox):
        # TODO
        raise NotImplementedError("TODO")
    def clicked(self):
        if self.is_on:
            self.is_on = False
            self.on_toggle_off.notify(self.name)
        else:
            self.is_on = True
            self.on_toggle_on.notify(self.name)
        self.on_toggle.notify(self.name)


class BasicToggleSlider(BasicCheckbox):
    pass
