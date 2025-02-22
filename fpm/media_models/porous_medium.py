from abc import ABC, abstractmethod


class porousMedium(ABC):
    @abstractmethod
    def create_boundary_walls():
        pass

    @abstractmethods
    def create_obstacles():
        pass

    @abstractmethods
    def save_spec_to_file():
        pass
