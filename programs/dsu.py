class DSU:
    def __init__(self,n):
        self.parent = list(range(n))
        self.size = [1]*n
        self.components = n

    def find(self,x : int):
        while x != self.parent[x]:
            self.parent[x] = self.parent[self.parent[x]]
            x=self.parent[x]
        return x
    
    def union(self,x,y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.size[rx] < self.size[ry]:
            rx,ry = ry,rx
        self.parent[ry]= rx
        self.size[rx] += self.size[ry]
        self.components -= 1
        return True

    def connected(self, x, y):
        return self.find(x) == self.find(y)

    def component_size(self, x):
        return self.size[self.find(x)]