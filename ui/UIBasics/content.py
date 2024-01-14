import pygame
from boundingBox import BoundingBox

class Content:
    def __init__(self):
        pass
    def draw(self, surface:pygame.Surface, bounding_box:BoundingBox):
        raise NotImplementedError("Must be implemented in super class.")
