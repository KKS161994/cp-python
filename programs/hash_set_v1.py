from collections import defaultdict
class MyHashSet:

    def __init__(self):
        self.size = 1009
        self.buckets = defaultdict(list)

    def _hash(self,key:int)-> int:
        return key % self.size

    def _get_bucket(self,key):
        index = self._hash(key)
        return self.buckets[index]
    

    def add(self, key: int) -> None:
        bucket = self._get_bucket(key)
        if key not in bucket:
            bucket.append(key)

    def remove(self, key: int) -> None:
        bucket = self._get_bucket(key)
        if key in bucket:
            bucket.remove(key)


    def contains(self, key: int) -> bool:
        bucket = self._get_bucket(key)
        if key in bucket:
            return True
        