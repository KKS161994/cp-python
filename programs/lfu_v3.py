from collections import defaultdict

class Node:
    def __init__(self, key: int, value: int):
        self.key = key
        self.value = value
        self.freq = 1
        self.prev = None
        self.next = None


class DoublyLinkedList:
    def __init__(self):
        self.head = Node(-1, -1)
        self.tail = Node(-1, -1)
        self.head.next = self.tail
        self.tail.prev = self.head

    def add_first(self, node: Node) -> None:
        first = self.head.next

        node.next = first
        node.prev = self.head

        self.head.next = node
        first.prev = node

    def remove(self, node: Node) -> None:
        prev_node = node.prev
        next_node = node.next

        prev_node.next = next_node
        next_node.prev = prev_node

        node.prev = None
        node.next = None

    def remove_last(self) -> Node:
        if self.is_empty():
            return None

        node = self.tail.prev
        self.remove(node)
        return node

    def is_empty(self) -> bool:
        return self.head.next == self.tail


class LFUCache:

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.key_to_node = {}
        self.freq_to_nodes = defaultdict(DoublyLinkedList)

    def _increase_freq(self, node: Node) -> None:
        old_freq = node.freq
        old_list = self.freq_to_nodes[old_freq]

        old_list.remove(node)

        if old_freq == self.min_freq and old_list.is_empty():
            self.min_freq += 1
            del self.freq_to_nodes[old_freq]

        node.freq += 1
        new_list = self.freq_to_nodes[node.freq]
        new_list.add_first(node)

    def get(self, key: int) -> int:
        if key not in self.key_to_node:
            return -1

        node = self.key_to_node[key]
        self._increase_freq(node)

        return node.value

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return

        if key in self.key_to_node:
            node = self.key_to_node[key]
            node.value = value
            self._increase_freq(node)
            return

        if len(self.key_to_node) == self.capacity:
            min_freq_list = self.freq_to_nodes[self.min_freq]
            node_to_remove = min_freq_list.remove_last()

            del self.key_to_node[node_to_remove.key]

            if min_freq_list.is_empty():
                del self.freq_to_nodes[self.min_freq]

        new_node = Node(key, value)
        self.key_to_node[key] = new_node
        self.freq_to_nodes[1].add_first(new_node)
        self.min_freq = 1