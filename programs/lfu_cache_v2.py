from collections import defaultdict
class Node:
    def __init__(self, key: int, value: int):
        self.key = key
        self.value = value
        self.frequency = 1
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = Node(-1,-1)
        self.tail = Node(-1,-1)
        self.head.next = self.tail
        self.tail.prev = self.head

class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.frequency_to_node = defaultdict(DoublyLinkedList)
        self.key_to_node = {}
        self.min_frequency:int = 0

        pass

    def remove_from_old(self, node:Node, frequency:int):
        node.prev.next = node.next
        node.next.prev = node.prev
        # update min freuqncy if asked element was only Least freuqnetly elemnt
        if self.min_frequency == frequency: 
            nodes:DoublyLinkedList = self.frequency_to_node[frequency]
            if(nodes.head.next == nodes.tail):
                self.min_frequency+=1
                del self.frequency_to_node[frequency]
    
    def add_to_new(self,node:Node,frequency:int):
        nodes = self.frequency_to_node[frequency+1]
        head = nodes.head
        node.next = head.next
        node.prev = head
        head.next = node
        node.next.prev = node


    def get(self, key):
        if key not in self.key_to_node:
            return -1
        node : Node = self.key_to_node[key]
        frequency : int = node.frequency
        # update node frequency
        node.frequency+=1
        # remove from old frequency list
        self.remove_from_old(node,frequency)

        # add to new list
        self.add_to_new(node,frequency)
        return node.value
        


    def put(self, key, value):
        if self.capacity == 0:
            return
        
        #  If key exists 
        #1:  Update the frequency of node 
        #2:  Remove from exisint frequency node 
        #    and add to new frequency node
        #3:  Validate that frequency is min tand only in min 
        #     update min frequency
        if key in self.key_to_node:
            node = self.key_to_node[key]
            node.value = value
            self.get(key)
            return

        else:
            node = Node(key,value)
            current_capacity = len(self.key_to_node)
            if(current_capacity == self.capacity):
                # remove least freuqeuntly least recently 
                nodes:DoublyLinkedList = self.frequency_to_node[self.min_frequency]
                head = nodes.head
                tail = nodes.tail
                temp_node = tail.prev     # LRU node
                # //dereference old lru
                temp_node.prev.next = tail
                tail.prev = temp_node.prev
                del self.key_to_node[temp_node.key]
                if head.next == tail:
                    del self.frequency_to_node[self.min_frequency]
            self.key_to_node[key] = node
            self.min_frequency = 1
            self.add_to_new(node,0)


