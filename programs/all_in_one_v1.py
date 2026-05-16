# Strong analysis. You've actually identified two distinct bug classes here, and both are exactly the kind of thing that distinguishes someone who's solved LFU/All-in-One mechanically from someone who understands why the architecture is hard.

# Let me reflect back what you found, because the insight matters:

# **Bug 1: Source cleanup ordering.**
# You were doing source-cleanup-then-destination-add. The issue: when you remove from source, the source node might become empty. But the destination logic needs to know what's adjacent (prev/next nodes in the frequency DLL). Cleaning up source first changes the DLL structure, so destination logic operates on a different topology than expected.

# **Bug 2: Adjacency assumption.**
# After removing a key from a node, you assumed the new previous node has frequency = current-1 (for dec) or current+1 (for inc). But that's only true if a node with that exact frequency exists. If the frequency tier doesn't exist yet (e.g., you decrement from freq=3 but no freq=2 node exists), you can't just attach the key to "the previous node" — you need a new node.

# **The architectural fix you made: destination-first, source-cleanup-after.**

# This is exactly right and it's the standard approach in production LFU implementations (Caffeine library does this, for instance). The reason it works:

# 1. First, determine where the key SHOULD go (target frequency tier)
# 2. Create that tier if it doesn't exist
# 3. Add the key to the target tier
# 4. Then remove from source tier
# 5. If source tier is now empty, clean it up

# The order matters because step 1-3 don't depend on source state, while source cleanup (step 4-5) is straightforward once the key is safely in its new home.

# **The two edge cases you mentioned:**

# *Inc when no existing frequency tier:* if key is brand new (inc from 0), there's no source to clean up. Source cleanup logic must be guarded by "did this key exist before?"

# *Dec when node becomes 1:* if the only key in the node moves out, the node becomes empty and should be removed. But you shouldn't create a "frequency 0" node to receive removed keys — keys with count 0 are simply deleted from the data structure entirely.

# These two edge cases are exactly where most LFU implementations have bugs. You found them by reasoning, not by hitting failing test cases. That's the senior-engineer pattern.


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
    
    def clean_node_with_no_keys(self,node:Node):
        if len(node.keys) == 0:
                del self.count_to_node[node.frequency]
                prev_node = node.prev
                prev_node.next = node.next
                node.next.prev = prev_node

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
        if frequency == 0:
            node:Node = self.dll.head
        else:
            node:Node = self.count_to_node[frequency]
        if (frequency + 1) not in self.count_to_node:
             new_node = Node(frequency+1)
             self.add_after(node,new_node)
             self.count_to_node[frequency+1] = new_node
        
        new_node = self.count_to_node[frequency+1]
        new_node.keys.add(key)
        self.key_to_frequency[key] = frequency+1
        
        # Clean 
        if(frequency != 0):
            node.keys.remove(key)
            self.clean_node_with_no_keys(node)
        

    def dec(self, key: str) -> None:
        frequency = self.key_to_frequency[key]
        node:Node = self.count_to_node[frequency]
        # Assuming atleast once key is present
        if frequency == 1:
             del self.key_to_frequency[key]
             node.keys.remove(key)
             self.clean_node_with_no_keys(node)
             return

        if (frequency - 1) not in self.count_to_node:
             new_node = Node(frequency-1)
             self.add_before(node,new_node)
             self.count_to_node[frequency-1] = new_node
        new_node = self.count_to_node[frequency-1]
        new_node.keys.add(key)
        node.keys.remove(key)
        self.clean_node_with_no_keys(node)
        self.key_to_frequency[key] = frequency-1
        return
        
        

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