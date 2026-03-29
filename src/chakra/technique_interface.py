from abc import ABC, abstractmethod

class TechniqueInterface(ABC):
    @abstractmethod
    def apply(self, frame, *args) -> tuple:
        """Applies the technique effect to the given frame if the conditions are met."""
        pass