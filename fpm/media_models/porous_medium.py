from abc import ABC, abstractmethod


class PorousMedium(ABC):
    @abstractmethod
    def create_boundary_walls():
        pass

    @abstractmethod
    def create_obstacles():
        pass

    @abstractmethod
    def save_spec_to_file():
        pass
