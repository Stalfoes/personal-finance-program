import pygame
import UIBasics
from copy import deepcopy


class Cell(UIBasics.Content):
    def __init__(self, content:UIBasics.Content, bounding_box:UIBasics.BoundingBox):
        self.content = content
        self.bounding_box = bounding_box
    def draw(self, surface:pygame.Surface, bounding_box:UIBasics.BoundingBox):
        # TODO
        raise NotImplementedError("TODO")


class BasicGrid(UIBasics.Content):
    def __init__(self, bounding_box:UIBasics.BoundingBox, cells:list[list[Cell]]=None, shape:list[int]=None, name:str=None):
        if cells is not None:
            self.cells = deepcopy(cells)
        self.bounding_box = bounding_box
        self.name = name
        self.is_on = False
    def draw(self, surface:pygame.Surface, bounding_box:UIBasics.BoundingBox):
        # TODO
        raise NotImplementedError("TODO")