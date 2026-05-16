import heapq
class MaxStack:

    def __init__(self):
        self.max_heap = []
        self.stack = []
        self.counter = 0
        self.deleted_items_from_heap = set()
        self.deleted_items_from_stack = set()
        pass

    def _clean_stack(self) -> None:
        while self.stack and self.stack[-1][1] in self.deleted_items_from_stack:
            _, item_id = self.stack.pop()
            self.deleted_items_from_stack.remove(item_id)

    def _clean_heap(self) -> None:
        while self.max_heap and -self.max_heap[0][1] in self.deleted_items_from_heap:
            _, neg_id = heapq.heappop(self.max_heap)
            self.deleted_items_from_heap.remove(-neg_id)
            
    def push(self, x: int) -> None:
        self.counter+=1
        self.stack.append((x,self.counter))
        heapq.heappush(self.max_heap, (-x, -self.counter))
        
    def pop(self) -> int:
        self._clean_stack()
        item = self.stack.pop()
        self.deleted_items_from_heap.add(item[1])
        return item[0]

    def top(self) -> int:
        self._clean_stack()
        return self.stack[-1][0]

    def peekMax(self) -> int:
        self._clean_heap()
        return -self.max_heap[0][0]

    def popMax(self) -> int:
        self._clean_heap()
        item = heapq.heappop(self.max_heap)
        self.deleted_items_from_stack.add(-item[1])
        return -item[0]