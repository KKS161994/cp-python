# left to right decreasing
from collections import deque
from typing import List
def max_within_k_window_v2(nums, k):
    dq = deque()
    res = List()
    for i in range(len(nums)):
        if dq and dq[-1]<= i-k :
            dq.pop()
        
        while dq and nums[dq[0]]<nums[i]:
            dq.popleft()
        
        dq.appendleft(i)

        if i >= k-1:
            res.append(dq[-1])
    return res


    