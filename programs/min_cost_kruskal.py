from typing import List
class DSU:
    def __init__(self,n):
        self.parent = list(range(n))
        self.size = [1]*n
    
    def find(self,x):
        while x != self.parent[x]:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    
    def union(self, x, y):
        rx,ry = self.find(x), self.find(y)
        
        if rx == ry:
            return False
        
        if self.size[rx] < self.size[ry]:
            rx,ry = ry, rx
        
        self.parent[ry] = rx
        self.size[ry] += self.size[rx]
        return True
    

class MST_Kruska:
    def __init__(self):
        pass

    def minCostConnectPoints(self, points: List[List[int]]) -> int:
        edges = []
        n = len(points)

        for i in range(n):
            x1,y1 = points[i]
            for j in range(i+1,n):
                x2,y2 = points[j]
                edges.append(abs(x1-x2)+abs(y1-y2),i,j)
        
        edges.sort()
        dsu = DSU()
        total_cost = 0
        edges_used = 0

        for cost,u,v in edges:
            if dsu.union(u,v):
                total_cost+=cost
                edges_used+=1

                if edges_used == n - 1:
                    break
        return total_cost
    
