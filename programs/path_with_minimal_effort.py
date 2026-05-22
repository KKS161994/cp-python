import heapq
class Path:
    
    directions = ((-1, 0), (0, 1), (1, 0), (0, -1))

    def minPath(self,heights:list):
        # 0 effort for 0 , 0
        min_heap = [(0,0,0)] # (effort, i, j) -> effort in reaching i and j node
        m,n = len(heights),len(heights[0])
        distances = [[float("inf")] * n for _ in range(m)]
        distances[0][0] = 0
        while min_heap:
            effort,i,j = heapq.heappop(min_heap)
            if(distances[i][j]<effort):
                continue
            if i == m - 1 and j == n - 1:
                return effort
            for dx,dy in self.directions:
                new_x = dx+i
                new_y = dy+j
                if self.isValid(new_x,new_y,m,n):
                    new_effort = max(effort,abs(heights[new_x][new_y]-heights[i][j]))
                    if new_effort < distances[new_x][new_y]:
                        distances[new_x][new_y] = new_effort
                        heapq.heappush(min_heap,(new_effort,new_x,new_y))
        
        return distances[m-1][n-1]
        

    def isValid(self,new_i,new_j,m,n):
        return 0 <= new_i < m and 0 <= new_j < n