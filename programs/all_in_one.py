from collections import defaultdict
class Node:

    def __init__(self, frequency=0):
        self.frequency = frequency
        self.keys = set()
        self.prev = None
        self.next = None

class DLL:
    
    def __init__(self):
        self.head = Node()
        self.tail = Node()

        self.head.next = self.tail
        self.tail.prev = self.head
        pass

class AllOne:

    def __init__(self):
        self.dll = DLL()
        self.count_to_node = {}
        self.key_to_frequency = defaultdict(int)
        pass
    
    def clean_node_with_no_keys(self,node:Node)-> Node:
        if len(node.keys) == 0:
                del self.count_to_node[node.frequency]
                prev_node = node.prev
                prev_node.next = node.next
                node.next.prev = prev_node
                node = prev_node
        return node

    def add_before(self,node:Node,new_node:Node):
            prev_node = node.prev
            new_node.prev = prev_node
            new_node.next = node
            node.prev = new_node
            prev_node.next=new_node             

    def add_after(self,node:Node,new_node:Node):
            next_node = node.next
            new_node.prev = node
            new_node.next = next_node
            node.next = new_node
            next_node.prev = new_node

    def inc(self, key: str) -> None:
        frequency = self.key_to_frequency[key]
        node:Node
        
        if frequency>0:
            node= self.count_to_node[frequency]
            node.keys.remove(key)
            node = self.clean_node_with_no_keys(node)
        else :
            node = self.dll.head

        if (frequency+1) not in self.count_to_node:
            new_node = Node(frequency+1)
            self.add_after(node,new_node)
            self.count_to_node[frequency+1] = new_node

        new_node = self.count_to_node[frequency+1]
        new_node.keys.add(key)
        self.key_to_frequency[key] = frequency+1
        

    def dec(self, key: str) -> None:
        frequency = self.key_to_frequency[key]
        node: Node = self.count_to_node[frequency]
        node.keys.remove(key)
        node = self.clean_node_with_no_keys(node)
        if frequency > 1 :
            if (frequency-1) not in self.count_to_node:
                new_node = Node(frequency-1)
                self.add_before(node,new_node)
                self.count_to_node[frequency-1] = new_node
            
            new_node:Node =  self.count_to_node[frequency-1]
            new_node.keys.add(key)
            self.key_to_frequency[key] = frequency-1
        else: 
            del self.key_to_frequency[key]
            pass


    def getMaxKey(self) -> str:
        if self.dll.head.next == self.dll.tail:
            return ""
        node:Node = self.dll.tail.prev
        return next(iter(node.keys))

    def getMinKey(self) -> str:
        if self.dll.head.next == self.dll.tail:
            return ""
        node:Node = self.dll.head.next
        return next(iter(node.keys))
        pass


# Your AllOne object will be instantiated and called as such:
# obj = AllOne()
# obj.inc(key)
# obj.dec(key)
# param_3 = obj.getMaxKey()
# param_4 = obj.getMinKey()