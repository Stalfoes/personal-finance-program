import pygame
import UIBasics
from copy import deepcopy

class Cell(UIBasics.Content):
    def __init__(self, content:UIBasics.Content, bounding_box:UIBasics.BoundingBox):
        self.content = content
        self.bounding_box = bounding_box
    

class BasicGrid(UIBasics.Content):
    def __init__(self, cells:list[list[Cell]], bounding_box:UIBasics.BoundingBox, name:str=None):
        self.cells = deepcopy(cells)
        self.bounding_box = bounding_box
        self.name = name
        self.on_toggle = UIBasics.Event()
        self.on_toggle_off = UIBasics.Event()
        self.on_toggle_on = UIBasics.Event()
        self.is_on = False
    def draw(self, surface:pygame.Surface, bounding_box:UIBasics.BoundingBox):
        # TODO
        raise NotImplementedError("TODO")