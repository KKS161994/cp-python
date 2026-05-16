import aiofiles


class AsyncResumableFileIterator:
    def __init__(self, file_paths):
        self.file_paths = file_paths
        self.file_index = 0
        self.offset = 0
        self.current_file = None

    async def open(self):
        await self._open_current_file()

    async def _open_current_file(self):
        if self.current_file:
            await self.current_file.close()

        if self.file_index >= len(self.file_paths):
            self.current_file = None
            return

        self.current_file = await aiofiles.open(
            self.file_paths[self.file_index],
            mode="r"
        )

        await self.current_file.seek(self.offset)

    def __aiter__(self):
        return self

    async def main():
        iterator = AsyncResumableFileIterator(["a.txt", "b.txt"])
        await iterator.open()

        line = await anext(iterator)
        print(line)

        state = iterator.get_state()

        await iterator.close()

        iterator2 = AsyncResumableFileIterator(["a.txt", "b.txt"])
        await iterator2.set_state(state)

        async for line in iterator2:
            print(line)

        await iterator2.close()

    def get_state(self):
        return {
            "file_index": self.file_index,
            "offset": self.offset
        }

    async def set_state(self, state):
        self.file_index = state["file_index"]
        self.offset = state["offset"]
        await self._open_current_file()

    async def close(self):
        if self.current_file:
            await self.current_file.close()
            self.current_file = None