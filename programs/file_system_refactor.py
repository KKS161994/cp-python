class Node:
    def __init__(self):
        self.content = ""
        self.children = {}
        self.is_file = False


class FileSystem:

    def __init__(self):
        self.root = Node()

    def _get_parts(self, path: str) -> list[str]:
        if path == "/":
            return []
        return path.split("/")[1:]

    def _traverse(self, path: str, create_missing: bool = False) -> Node:
        node = self.root

        for part in self._get_parts(path):
            if part not in node.children:
                if not create_missing:
                    raise ValueError("Path does not exist")
                node.children[part] = Node()

            node = node.children[part]

        return node

    def ls(self, path: str) -> list[str]:
        node = self._traverse(path)

        if node.is_file:
            return [self._get_parts(path)[-1]]

        return sorted(node.children.keys())

    def mkdir(self, path: str) -> None:
        self._traverse(path, create_missing=True)

    def addContentToFile(self, filePath: str, content: str) -> None:
        node = self._traverse(filePath, create_missing=True)
        node.is_file = True
        node.content += content

    def readContentFromFile(self, filePath: str) -> str:
        node = self._traverse(filePath)
        return node.content