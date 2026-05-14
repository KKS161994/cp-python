from collections import defaultdict
class AllOne:

    def __init__(self):
        self.string_to_frequency = defaultdict(int)
        self.frequency_to_string = defaultdict(set)
        self.min = 0
        self.max = 0    

    def inc(self, key: str) -> None:
        initial_frequency = self.string_to_frequency[key]
        self.string_to_frequency[key]+=1
        if initial_frequency>0 : self.frequency_to_string[initial_frequency].remove(key)
        if not self.frequency_to_string[initial_frequency]: self.frequency_to_string.pop(initial_frequency)
        self.frequency_to_string[initial_frequency+1].add(key)
        if self.max < (initial_frequency+1) : self.max = initial_frequency+1
        

    def dec(self, key: str) -> None:
        initial_frequency = self.string_to_frequency[key]
        self.string_to_frequency[key]-=1
        self.frequency_to_string[initial_frequency].remove(key)
        if not self.frequency_to_string[initial_frequency]: self.frequency_to_string.pop(initial_frequency)
        if initial_frequency > 1: self.frequency_to_string[initial_frequency-1].add(key)

    def getMaxKey(self) -> str:
        return next(iter(self.frequency_to_string[self.max]))
        

    def getMinKey(self) -> str:
        return next(iter(self.frequency_to_string[self.min]))


# Your AllOne object will be instantiated and called as such:
# obj = AllOne()
# obj.inc(key)
# obj.dec(key)
# param_3 = obj.getMaxKey()
# param_4 = obj.getMinKey()