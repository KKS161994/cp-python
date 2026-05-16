from collections import defaultdict
import heapq
class Solution:
    def minCostConnectPoints(self, points: List[List[int]]) -> int:
        graph = defaultdict(list)
        n = len(points) 
        for i in range(n):
            x1,y1 = points[i]
            for j in range(i+1,n):
                x2,y2 = points[j]
                cost = abs(x1-x2) + abs(y1-y2)
                graph[i].append((cost,j))
                graph[j].append((cost,i))
        
        start = 0
        minheap = [(0,start)]
        visited = set()
        total_cost = 0
        while minheap:
            cost,node = heapq.heappop(minheap)
            if node in visited:
                continue

            visited.add(node)
            total_cost+=cost

            for cost,neighour in graph[node]:
                if neighour not in visited:
                    heapq.heappush(minheap,(cost,neighour))
        return total_cost

            




                