from collections import defaultdict
class Node:
    def __init__(self):
        self.content:str = ""
        self.nodes = defaultdict(Node)
        self.is_eof = False # eof describe its a file and end 

class FileSystem:

    def __init__(self):
        self.root = Node()

    def ls(self, filepath: str) -> list[str]:
        paths = filepath.split("/")[1:] if filepath != "/" else []
        node = self.root
        for path in paths:
            if path not in node.nodes:
                break
            node = node.nodes[path]
        if node.is_eof:
            return [paths[-1]]
        return sorted(node.nodes.keys())
        

    def mkdir(self, filePath: str) -> None:
        paths = filePath.split("/")[1:] if filePath != "/" else []
        node = self.root
        for path in paths:
            if path not in node.nodes:
                new_node = Node()
                node.nodes[path] = new_node
                node = new_node
            else: node = node.nodes[path]
        

    def addContentToFile(self, filePath: str, content: str) -> None:
        paths = filePath.split("/")[1:] if filePath != "/" else []
        node = self.root
        for path in paths:
            if path not in node.nodes:
                new_node = Node()
                node.nodes[path] = new_node
                node = new_node
            else: node = node.nodes[path]
        node.content+=content
        node.is_eof = True

    def readContentFromFile(self, filePath: str) -> str:
        paths = filePath.split("/")[1:] if filePath != "/" else []
        node = self.root
        for path in paths:
            # Assuming the path always exist else break
            if path not in node.nodes:
                break
            node = node.nodes[path]
        
        if node.is_eof:
            return node.content
        return ""
        



# Your FileSystem object will be instantiated and called as such:
# obj = FileSystem()
# param_1 = obj.ls(path)
# obj.mkdir(path)
# obj.addContentToFile(filePath,content)
# param_4 = obj.readContentFromFile(filePath)