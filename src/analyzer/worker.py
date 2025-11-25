import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import aiohttp

# IMPORTANTE: create_pool ANTES que database
from database import create_pool, close_pool, get_pending_comments, update_analysis
from gemini_client import classify_comment
from config import Config

async def analyze_batch():
    comments = await get_pending_comments(Config.BATCH_SIZE)
    
    if not comments:
        print("No hay comentarios pendientes de analizar.")
        return False

    print(f"Analizando {len(comments)} comentarios pendientes...")

    async with aiohttp.ClientSession() as session:
        for comment in comments:
            cid = comment["id"]
            text = str(comment.get("comment", "") or "").strip()

            print(f"ID {cid} → \"{text[:70]}{'...' if len(text)>70 else ''}\"", end=" → ")

            if not text or len(text) < 2:
                await update_analysis(cid, "EMPTY", "SKIPPED")
                print("SKIPPED (vacío)")
                continue

            try:
                label = await classify_comment(session, text)
                await update_analysis(cid, label, "ANALYZED")
                print(f"{label}")
            except Exception as e:
                print(f"ERROR → {e}")
                await update_analysis(cid, "ERROR", "ANALYSIS_FAILED")
    
    return True

# BUCLE INFINITO + CREAR POOL (¡ESTO ES LO QUE FALTABA!)
async def main():
    print("Worker de análisis Gemini INICIADO")
    print(f"Batch size: {Config.BATCH_SIZE}")
    
    # CREAR EL POOL (¡LA LÍNEA MÁGICA!)
    await create_pool()
    print("MySQL conectado correctamente")
    print("-" * 60)

    try:
        while True:
            had_work = await analyze_batch()
            if not had_work:
                print("Esperando nuevos comentarios... (5 seg)")
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\nWorker detenido por el usuario.")
    finally:
        await close_pool()
        print("Worker terminado.")

if __name__ == "__main__":
    asyncio.run(main())