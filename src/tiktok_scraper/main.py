from contextlib import asynccontextmanager
import aiomysql
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, DisconnectEvent

from database import create_pool, close_pool, save_tiktok_comment, get_pool

# ==================== CONFIGURACIÓN ====================
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tiktok_scraper")

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Iniciando conexión a MySQL...")
    await create_pool()
    log.info("Backend TikTok Scraper + DB iniciado correctamente")
    yield
    log.info("Cerrando conexión a MySQL...")
    await close_pool()

app = FastAPI(
    title="TikTok Live Scraper + DB",
    description="Captura comentarios en vivo y los guarda en MySQL",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://taptap-live.vercel.app",  # ← tu frontend en producción
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELOS Y ESTADO ====================
class ConnectRequest(BaseModel):
    uniqueId: str

# Diccionarios globales para manejar múltiples lives
clients: dict[str, TikTokLiveClient] = {}
in_memory_comments: dict[str, list] = {}

# ==================== ENDPOINTS ====================
@app.get("/")
async def root():
    return {"message": "TikTok Live Scraper API corriendo correctamente"}

@app.post("/scrape/connect")
async def connect(req: ConnectRequest):
    username = req.uniqueId.lstrip("@").lower()

    if username in clients:
        return {"message": f"Ya conectado a @{username}"}

    try:
        log.info(f"Intentando conectar a @{username}...")
        client: TikTokLiveClient = TikTokLiveClient(unique_id=username)
        in_memory_comments[username] = []

        @client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            try:
                user = event.user

                # Compatibilidad total con TikTokLive v5 y v6+
                user_id = getattr(user, "unique_id", "desconocido")
                nickname = getattr(user, "nickname", "Anónimo")

                # Fallback seguro si hay user_info
                if hasattr(user, "user_info") and user.user_info:
                    user_id = user.user_info.unique_id or user_id
                    nickname = user.user_info.nickname or nickname

                comment_text = event.comment or ""

                # Guardar en memoria (últimos 200)
                comment_data = {
                    "user": user_id,
                    "name": nickname,
                    "comment": comment_text,
                    "timestamp": datetime.now().isoformat()
                }
                in_memory_comments[username].append(comment_data)
                if len(in_memory_comments[username]) > 200:
                    in_memory_comments[username].pop(0)

                # Guardar en base de datos
                await save_tiktok_comment(
                    tiktok_username=username,
                    user_id=user_id,
                    nickname=nickname,
                    comment=comment_text
                )

                print(f"@{nickname}: {comment_text}")

            except Exception as e:
                log.error(f"Error procesando comentario: {e}", exc_info=True)

        @client.on(ConnectEvent)
        async def on_connect(_: ConnectEvent):
            log.info(f"Conectado a @{username} – Live en vivo")

        @client.on(DisconnectEvent)
        async def on_disconnect(_: DisconnectEvent):
            log.info(f"Live terminado o desconectado: @{username}")
            clients.pop(username, None)
            in_memory_comments.pop(username, None)

        # Iniciar conexión en background
        asyncio.create_task(client.connect())
        clients[username] = client

        log.info(f"Conexión iniciada correctamente para @{username}")
        return {"message": f"Conectado a @{username}"}

    except Exception as e:
        log.error(f"Error conectando a @{username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/disconnect")
async def disconnect(req: ConnectRequest):
    username = req.uniqueId.lstrip("@").lower()
    if username not in clients:
        raise HTTPException(status_code=404, detail="No hay conexión activa")

    await clients[username].disconnect()
    clients.pop(username, None)
    in_memory_comments.pop(username, None)
    return {"message": f"Desconectado @{username}"}


@app.get("/scrape/comments")
async def get_live_comments(username: str):
    username = username.lstrip("@").lower()
    comments = in_memory_comments.get(username, [])
    return {
        "username": username,
        "total": len(comments),
        "comments": comments[-50:]
    }


@app.get("/scrape/user/{username}/comments")
async def get_all_comments(username: str, limit: int = 200):
    username = username.lstrip("@").lower()
    pool = get_pool()

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT 
                        userId as user,
                        nickname as name,
                        comment,
                        timestamp as timestamp
                    FROM comments 
                    WHERE scrapedUsername = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (username, limit))
                rows = await cur.fetchall()
                return {"username": username, "total": len(rows), "comments": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== EJECUCIÓN DIRECTA ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.tiktok_scraper.main:app", host="0.0.0.0", port=5000, reload=True)