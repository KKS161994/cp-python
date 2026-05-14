import heapq
class FindMedian:
    def __init__(self):
        self.lower = list()
        self.higher = list()
        pass


    def addNum(self,num: int)-> None:
        heapq.heappush(self.higher,-num)
        heapq.heappush(self.lower, - heapq.heappop(self.higher))
        if len(self.lower) > len(self.higher):
            heapq.heappush(self.higher, - heapq.heappop(self.lower))
    
    def median(self)->int:
        if (len(self.lower) + len(self.higher)) % 2 == 0:
            return (-self.higher[0] + self.lower[0])/2
        return - self.higher[0]
        