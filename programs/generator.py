
import asyncio

def my_gen():
    x = yield "First Item"
    print(f"Generator received: {x}")
    yield "Second Item"

# g = my_gen()
# print(next(g))
# print(g.send("hello"))



# g = my_gen()
# print(next(g))          # prime: runs until first yield, prints "First Item"
# g.send("Hi")     # resumes, x = "Hi", runs until next yield, prints "Second Item"
# print(next(g))


async def gen():
    for i in range(3):
        await asyncio.sleep(1)
        yield i


async def main():
    g = gen()
    print(await anext(g))
    print(await anext(g))
    print(await anext(g))
    # async for x in gen():
    #     print(x)


asyncio.run(main())