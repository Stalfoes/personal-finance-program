import pygame
import UIBasics

class BasicButton(UIBasics.Content):
    def __init__(self, content:UIBasics.Content, bounding_box:UIBasics.BoundingBox, name:str=None):
        self.content = content
        self.bounding_box = bounding_box
        self.name = name
        self.on_click = UIBasics.Event()
    def draw(self, surface:pygame.Surface, bounding_box:UIBasics.BoundingBox):
        # TODO
        raise NotImplementedError("TODO")
    def clicked(self):
        self.on_click.notify(self.name)
    