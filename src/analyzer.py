from database import get_pending_comments, update_analysis
from gemini_client import classify_comment
from config import Config
import aiohttp

async def analyze_batch():
    comments = await get_pending_comments(Config.BATCH_SIZE)
    if not comments:
        print("No hay comentarios pendientes")
        return

    print(f"Analizando {len(comments)} comentarios...")

    async with aiohttp.ClientSession() as session:
        for comment in comments:
            cid = comment["id"]
            text = str(comment["comment"] or "").strip()

            print(f"ID {cid} → \"{text[:70]}{'...' if len(text)>70 else ''}\"")

            if not text:
                await update_analysis(cid, "EMPTY", "SKIPPED")
                continue

            try:
                label = await classify_comment(session, text)
                await update_analysis(cid, label, "ANALYZED")
                print(f"ID {cid} → {label}")
            except Exception as e:
                print(f"ID {cid} → ERROR: {e}")
                await update_analysis(cid, "ERROR", "ANALYSIS_FAILED")