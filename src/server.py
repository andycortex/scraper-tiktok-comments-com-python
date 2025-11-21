from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, DisconnectEvent
import uvicorn
import asyncio

app = FastAPI()

class UniqueIdRequest(BaseModel):
    uniqueId: str  # ← Esto valida exactamente lo que envías desde frontend

clients = {}
comments_store = {}

@app.post("/scrape/connect")
async def connect(request: UniqueIdRequest):
    username = request.uniqueId.lstrip("@")
    
    if not username:
        raise HTTPException(status_code=400, detail="TikTok uniqueId is required")
    
    if username in clients:
        return {"message": f"Ya conectado a @{username}"}
    
    try:
        client = TikTokLiveClient(unique_id=username)
        comments_store[username] = []

        @client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            print(f"✅ Conectado a @{username} – Espectadores: {event.viewer_count}")

        @client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            comment = {
                "user": event.user.unique_id,
                "name": event.user.nickname,
                "comment": event.comment
            }
            comments_store[username].append(comment)
            if len(comments_store[username]) > 100:
                comments_store[username].pop(0)
            print(f"💬 {event.user.nickname}: {event.comment}")

        @client.on(DisconnectEvent)
        async def on_disconnect(event: DisconnectEvent):
            print(f"🔌 Live de @{username} terminó")
            if username in clients:
                del clients[username]
            if username in comments_store:
                del comments_store[username]

        await client.connect()
        clients[username] = client
        return {"message": f"Conectado exitosamente a @{username}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape/disconnect")
async def disconnect(request: UniqueIdRequest):
    username = request.uniqueId.lstrip("@")
    
    if username in clients:
        await clients[username].disconnect()
        del clients[username]
        del comments_store[username]
        return {"message": f"Desconectado de @{username}"}
    
    raise HTTPException(status_code=404, detail="No hay conexión activa")

@app.get("/scrape/comments")
async def get_comments(username: str):
    username = username.lstrip("@")
    return {
        "username": username,
        "total": len(comments_store.get(username, [])),
        "comments": comments_store.get(username, [])[-50:]  # Últimos 50
    }

if __name__ == "__main__":
    print("🚀 Server Python corriendo en http://localhost:5000")
    print("Rutas: /scrape/connect, /scrape/disconnect, /scrape/comments?username=anita_avila65")
    uvicorn.run(app, host="0.0.0.0", port=5000)