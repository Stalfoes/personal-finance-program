import pygame

class BoundingBox:
    def __init__(self, top_left:tuple[float,float]=None, bottom_right:tuple[float,float]=None, width:float=None, height:float=None):
        self.top_left = top_left
        if bottom_right is None:
            if width is None or height is None:
                raise ValueError("One of bottom_right, width and height must be not None.")
            self.bottom_right = (top_left[0] + width, top_left[1] + height)
    @property
    def width(self) -> float:
        return self.bottom_right[0] - self.top_left[0]
    @property
    def height(self) -> float:
        return self.bottom_right[1] - self.top_left[1]
    @property
    def center(self) -> tuple[float,float]:
        return (self.top_left[0] + self.width / 2, self.top_left[1] + self.height / 2)
    def as_rect(self) -> pygame.Rect:
        return pygame.Rect(*self.top_left, self.width, self.height)
    def copy(self):
        return BoundingBox(top_left=self.top_left, bottom_right=self.bottom_right)
    def __contains__(self, point:tuple[float,float]):
        if self.top_left[0] <= point[0] and point[0] <= self.bottom_right[0]:
            if self.top_left[1] <= point[1] and point[1] <= self.bottom_right[1]:
                return True
        return False
    