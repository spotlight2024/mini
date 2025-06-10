from abc import ABC, abstractmethod

class BaseWebDriver(ABC):
    @abstractmethod
    def connect(self, serial_id: str):
        pass

    @abstractmethod
    def find_element(self, by, selector):
        pass

    @abstractmethod
    def quit(self):
        pass 