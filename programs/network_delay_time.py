from typing import List
from collections import defaultdict
import heapq
class NetworkDelayTime:
    def __init__(self):
        pass

    def networkDelayTime(self, times: List[List[int]], n: int, k: int) -> int:
        graph = defaultdict(list)
        for source, destination, time in times:
            graph[source].append((destination, time))
        distances = {node: float('inf') for node in range(1, n + 1)}
        distances[k] = 0
        priority_queue = [(0,k)]

        while priority_queue:
            distance,node = heapq.heappop(priority_queue)
            if distance>distances[node]:
                continue

            for neighour_node,time in graph[node]:
                new_distance = distances[node]+time
                if new_distance  < distances[neighour_node]:
                    distances[neighour_node] = new_distance
                    heapq.heappush(priority_queue,(new_distance,neighour_node))
        answer = max(distances.values())

        return answer if answer != float("inf") else -1
