from abc import ABC, abstractmethod


class porousMedium(ABC):
    @abstractmethod
    def create_boundary_walls():
        pass

    def create_obstacles():
        pass
