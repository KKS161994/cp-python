"""Streaming + backpressure, demonstrated three ways.

Backpressure is the mechanism by which a SLOW consumer makes a FAST producer
slow down. Without it, the producer outpaces the consumer, items pile up in
some buffer, and memory grows unboundedly — the classic "queue depth blows
up" failure mode.

This file shows the same producer/consumer scenario three times:

    1. demo_no_backpressure  — unbounded queue. BROKEN: producer dumps all
       items at once; peak queue depth equals the entire stream.

    2. demo_bounded_queue    — bounded queue. WORKS: producer's `put()`
       blocks once the queue fills, naturally pacing it to the consumer.

    3. demo_async_generator  — async generator. WORKS and is the most
       idiomatic Python streaming primitive: each `yield` waits for the
       consumer to ask for the next item, so the "buffer" is always 1 item.

Run with:
    python3 programs/streaming_backpressure.py

Look at the "peak buffer" number printed at the end of each demo. That's the
metric that decides whether your system stays up at 3 AM or runs out of RAM.
"""

import asyncio
import time
from typing import AsyncIterator

# ---------- Knobs ----------
# How many items the producer will generate. Keep small enough that the
# broken demo doesn't actually OOM your machine — but the *pattern* would
# OOM in production if N or item size grew.
N_ITEMS = 20

# How long the consumer takes to process each item. Real consumers might be
# writing to a database, calling an API, or running ML inference.
CONSUMER_DELAY_S = 0.20

# How long the producer takes between yielding items. 0 = "as fast as
# possible" — the worst case for backpressure.
PRODUCER_DELAY_S = 0.0


# ---------- Tiny helpers ----------
START = time.perf_counter()


def stamp() -> str:
    """Seconds since the demo started, for prefixing log lines."""
    return f"{time.perf_counter() - START:5.2f}s"


def banner(title: str) -> None:
    """Print a section header so demo output is easy to scan."""
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


# =============================================================================
# Demo 1 — Unbounded queue. BROKEN.
# =============================================================================
async def demo_no_backpressure() -> None:
    """Producer pushes into an unbounded queue. Peak depth == entire stream.

    The signature failure mode: the producer ``await``s ``queue.put()`` but
    that ``put`` *never blocks*, because the queue has no maxsize. So the
    producer dumps everything in immediately and exits, leaving the consumer
    to drain it.

    Symptoms in production:
        - Peak memory == total number of in-flight items.
        - If the producer is faster than the consumer for long enough, you
          OOM. Even if you don't OOM, the latency for the last item is
          terrible (everything had to be buffered first).
    """
    banner("Demo 1 — UNBOUNDED queue (BROKEN: no backpressure)")
    queue: asyncio.Queue = asyncio.Queue()  # No maxsize -> infinite buffer.
    peak_depth = 0

    async def producer() -> None:
        nonlocal peak_depth
        for i in range(N_ITEMS):
            await queue.put(i)
            peak_depth = max(peak_depth, queue.qsize())
            print(f"[{stamp()}] producer  -> put {i:2d}  (queue depth={queue.qsize()})")
            if PRODUCER_DELAY_S:
                await asyncio.sleep(PRODUCER_DELAY_S)
        # Sentinel value tells the consumer "no more items".
        await queue.put(None)

    async def consumer() -> None:
        while True:
            item = await queue.get()
            if item is None:
                return
            await asyncio.sleep(CONSUMER_DELAY_S)
            print(f"[{stamp()}] consumer <- got {item:2d}  (queue depth={queue.qsize()})")

    t0 = time.perf_counter()
    await asyncio.gather(producer(), consumer())
    elapsed = time.perf_counter() - t0

    print(f"\n  total time:   {elapsed:5.2f}s")
    print(f"  peak buffer:  {peak_depth} items   <-- THE DANGER NUMBER")
    print("  ^ Every one of those items lived in memory at the same instant.")


# =============================================================================
# Demo 2 — Bounded queue. WORKS.
# =============================================================================
async def demo_bounded_queue() -> None:
    """Same scenario, but queue has ``maxsize=3``.

    The instant ``queue.qsize() == 3``, the producer's next ``await queue.put(i)``
    BLOCKS until the consumer calls ``queue.get()``. The producer is now
    naturally paced to the consumer's speed — that's backpressure.
    """
    banner("Demo 2 — BOUNDED queue (WORKS: backpressure via maxsize)")
    queue: asyncio.Queue = asyncio.Queue(maxsize=3)
    peak_depth = 0

    async def producer() -> None:
        nonlocal peak_depth
        for i in range(N_ITEMS):
            await queue.put(i)  # <-- This is where backpressure happens.
            peak_depth = max(peak_depth, queue.qsize())
            print(f"[{stamp()}] producer  -> put {i:2d}  (queue depth={queue.qsize()})")
            if PRODUCER_DELAY_S:
                await asyncio.sleep(PRODUCER_DELAY_S)
        await queue.put(None)

    async def consumer() -> None:
        while True:
            item = await queue.get()
            if item is None:
                return
            await asyncio.sleep(CONSUMER_DELAY_S)
            print(f"[{stamp()}] consumer <- got {item:2d}  (queue depth={queue.qsize()})")

    t0 = time.perf_counter()
    await asyncio.gather(producer(), consumer())
    elapsed = time.perf_counter() - t0

    print(f"\n  total time:   {elapsed:5.2f}s")
    print(f"  peak buffer:  {peak_depth} items   <-- bounded by maxsize")
    print("  ^ Memory stays flat no matter how big the stream is.")


# =============================================================================
# Demo 3 — Async generator. WORKS, and is the most idiomatic.
# =============================================================================
async def demo_async_generator() -> None:
    """Producer is an ``async def`` with ``yield``; consumer uses ``async for``.

    Each ``yield`` pauses the producer until the consumer asks for the next
    item. There is no explicit buffer — at most ONE item is "in flight" (the
    one currently yielded). This is the smallest possible buffer and the
    cleanest API; no queue, no sentinels, no manual peak tracking.

    Use this pattern when the producer is naturally expressible as "a loop
    that yields values" — e.g. paging through an API, reading a file
    chunk-by-chunk, iterating DB rows.
    """
    banner("Demo 3 — ASYNC GENERATOR (WORKS: implicit single-item buffer)")
    peak_depth = 0  # Always 0 or 1 here — generators don't pre-buffer.

    async def producer() -> AsyncIterator[int]:
        nonlocal peak_depth
        for i in range(N_ITEMS):
            print(f"[{stamp()}] producer  -> yield {i:2d}")
            peak_depth = max(peak_depth, 1)
            yield i  # <-- pauses here until consumer asks for next.
            if PRODUCER_DELAY_S:
                await asyncio.sleep(PRODUCER_DELAY_S)

    t0 = time.perf_counter()
    async for item in producer():
        await asyncio.sleep(CONSUMER_DELAY_S)
        print(f"[{stamp()}] consumer <- got   {item:2d}")
    elapsed = time.perf_counter() - t0

    print(f"\n  total time:   {elapsed:5.2f}s")
    print(f"  peak buffer:  {peak_depth} item    <-- generators self-pace")


# =============================================================================
# Bonus mention — task fanout
# =============================================================================
# A related backpressure failure happens when you fan out concurrent work:
#
#     for item in stream:
#         asyncio.create_task(process(item))   # BROKEN: unbounded fanout
#
# The bounded equivalent uses an ``asyncio.Semaphore`` (or a worker pool /
# ``asyncio.TaskGroup`` with limits) so at most N tasks are in flight:
#
#     sem = asyncio.Semaphore(5)
#     async def bounded(item):
#         async with sem:
#             await process(item)
#     for item in stream:
#         asyncio.create_task(bounded(item))   # WORKS: capped at 5 concurrent
#
# Same lesson: every async producer needs an explicit upper bound on its
# in-flight work, otherwise the slowest downstream component dictates how
# much memory you'll burn waiting on it.


async def main() -> None:
    global START
    START = time.perf_counter()
    await demo_no_backpressure()
    START = time.perf_counter()
    await demo_bounded_queue()
    START = time.perf_counter()
    await demo_async_generator()


if __name__ == "__main__":
    asyncio.run(main())
