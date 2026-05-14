from collections import defaultdict

class MyHashSet:

    def __init__(self):
        self.present = defaultdict(bool)      
        pass

    def add(self, key: int) -> None:
        self.present[key] = True

    def remove(self, key: int) -> None:
        del self.present[key]

    def contains(self, key: int) -> bool:
        return self.present[key]