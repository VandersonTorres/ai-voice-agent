import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor

# Creating a lot of threads can lead to resource exhaustion.
# Instead, we create a single global executor that can be reused
EXECUTOR = ThreadPoolExecutor(max_workers=10)


async def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(EXECUTOR, partial(func, *args, **kwargs))


# TODO: Consider implementing a Decorator if it is going to be used widely.
