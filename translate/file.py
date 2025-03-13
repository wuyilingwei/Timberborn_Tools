import os
import csv

def search_file(path: str) -> str:
    # Add your implementation here
    pass



class CSV_File:
    """
    
    """
    id: int
    raw: csv.reader
    target: list[str]
    old_data: dict[str, list]
    data: dict[str, list]

    def __init__(self, id: int, raw: csv.reader, target: list[str]):
        self.id = id
        self.raw = raw
        self.old_data = {}
        self.data = {}
        self.target = target

    def load_data(self) -> None:
        # Add your implementation here
        pass

    def save_data(self) -> None:
        # Add your implementation here
        pass

    def transfer_data(self) -> None:
        # Add your implementation here
        pass

    def get_data(self) -> dict[str, list]:
        # Add your implementation here
        pass