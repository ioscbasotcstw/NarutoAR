import cv2
from abc import ABC, abstractmethod

class StyleInterface(ABC):
    @abstractmethod
    def apply(self, frame, *args) -> cv2.Mat:
        """Applies the style effect to the given frame if the conditions are met."""
        pass