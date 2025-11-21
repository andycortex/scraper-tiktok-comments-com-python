import asyncio
import signal
from database import create_pool, close_pool
from analyzer import analyze_batch
from config import Config

async def worker_loop():
    await create_pool()
    print(f"Worker iniciado → {Config.MODEL} | cada {Config.INTERVAL_SECONDS}s")

    # Primera ejecución inmediata
    await analyze_batch()

    while True:
        await asyncio.sleep(Config.INTERVAL_SECONDS)
        await analyze_batch()

def signal_handler():
    print("\nDeteniendo worker...")
    asyncio.create_task(shutdown())

async def shutdown():
    await close_pool()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for t in tasks:
        t.cancel()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        loop.run_until_complete(worker_loop())
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        print("Worker detenido correctamente.")