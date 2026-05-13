# set(key, value, timestamp)
# get(key, timestamp)

# Problem

# Design a data structure that supports:

# set(key, value, timestamp)
# get(key, timestamp)
# Behavior
# set: store value with timestamp
# get: return value with largest timestamp ≤ given timestamp
# Example
# set("foo", "bar", 1)
# get("foo", 1) → "bar"
# get("foo", 3) → "bar"

# set("foo", "bar2", 4)
# get("foo", 4) → "bar2"
# get("foo", 5) → "bar2"

# Start with your thoughts.
from collections import defaultdict

class OpenMap:
    def __init__(self):
        self.def_map = defaultdict(list)

    def set(self, key, value, timestamp):
        self.def_map[key].append([timestamp, value])

    def get(self, key, timestamp):
        values_list = self.def_map.get(key, [])
        if not values_list:
            return ""

        left = 0
        right = len(values_list) - 1
        while left <= right:
            mid = (left + right) // 2
            if timestamp < values_list[mid][0]:
                right = mid - 1
            else:
                left = mid + 1

        if right == -1:
            return ""
        return values_list[right][1]

        
