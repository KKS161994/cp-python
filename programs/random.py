import random
class InsertGetRandom:
    def __init__(self):
        self.set = list()
        self.map = {}
        pass

    def insert(self, val:int):
        if val in self.map:
            return False
        self.map[val]=len(self.set)
        self.set.append(val)
        return True


    
    def remove(self, val:int):
        if val not in self.map:
            return False
       
        index = self.map[val]
        end = self.set[-1]

        self.set[index] = end
        self.map[end] = index

        self.set.pop()
        del self.map[val]
        
        return True

    def random(self):
        return random.choice(self.set)


            
