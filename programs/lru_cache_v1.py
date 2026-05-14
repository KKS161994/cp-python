from collections import deque

class Node:
    key: int 
    value: int

    def __init__(self):
        pass

class LRUCache:
    def __init__(self, capacity: int):
        self.deque = deque()
        self.map = dict()
        self.capacity = capacity

    def get(self, key: int):
        if key not in self.map:
            return -1
        node = self.map[key]
        self.deque.remove(node)
        self.deque.append(node)
        return node.value

    def put(self,key: int,value):
        node = Node()
        if key not in self.map:
            node.key  = key
            node.value = value
            self.map.put(key,node)
        self.deque.remove(node)
        self.deque.append(node)
        node.value = value
        if len(self.deque) > self.capacity:
            self.deque.popleft()

