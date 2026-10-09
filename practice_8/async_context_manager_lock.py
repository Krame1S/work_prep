import asyncio

class HoldLock:
    def __init__(self, lock: asyncio.Lock):
        self.lock = lock

    async def __aenter__(self):
       await self.lock.acquire() 
       return self.lock

    async def __aexit__(self, exc_type, exc_val, exc_tb):
       self.lock.release() 
       return False
