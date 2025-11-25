import aiomysql
from config import Config
from datetime import datetime

pool = None

async def create_pool():
    global pool
    print(f"Conectando a MySQL → {Config.MYSQL_USER}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}")
    pool = await aiomysql.create_pool(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        db=Config.MYSQL_DB,
        charset=Config.MYSQL_CHARSET,
        autocommit=True,
        minsize=1,
        maxsize=15,
    )
    print("Pool MySQL creado correctamente")

async def close_pool():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()
        print("Pool MySQL cerrado")

def get_pool():
    if pool is None:
        raise RuntimeError("Pool no inicializado")
    return pool

async def save_tiktok_comment(tiktok_username: str, user_id: str, nickname: str, comment: str):
    global pool
    if pool is None:
        print("Pool no está listo aún, comentario ignorado")
        return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO comments 
                (scrapedUsername, userId, nickname, comment, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    nickname = VALUES(nickname),
                    timestamp = VALUES(timestamp)
            """, (
                tiktok_username.lower(),
                user_id,
                nickname or "Anónimo",
                comment,
                datetime.now()
            ))

async def get_comments_by_username(
    username: str, 
    limit: int = 200, 
    offset: int = 0
) -> dict:
    """Devuelve comentarios + total para un usuario"""
    username = username.lower()
    global pool
    if not pool:
        return {"username": username, "total": 0, "comments": []}

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Comentarios
                await cur.execute("""
                    SELECT 
                        userId AS user,
                        scrapedUsername AS name,
                        comment,
                        timestamp AS timestamp
                    FROM comments
                    WHERE tiktok_username = %s
                    ORDER BY timestamp DESC
                    LIMIT %s OFFSET %s
                """, (username, limit, offset))
                comments = await cur.fetchall()

                # Total
                await cur.execute("""
                    SELECT COUNT(*) as total 
                    FROM comments 
                    WHERE tiktok_username = %s
                """, (username,))
                total = (await cur.fetchone())["total"]

        return {
            "username": username,
            "total": total,
            "comments": comments
        }
    except Exception as e:
        print(f"Error leyendo comentarios: {e}")
        return {"username": username, "total": 0, "comments": []}

# === OBTENER COMENTARIOS CON state = 'ANALYSIS' ===
async def get_pending_comments(limit: int = 50) -> list:
    """
    Obtiene comentarios que están en estado 'ANALYSIS' (tu estado actual)
    """
    global pool
    if not pool:
        print("Pool no inicializado (get_pending_comments)")
        return []

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT id, comment, scrapedUsername, userId
                    FROM comments 
                    WHERE state = 'ANALYSIS'
                    ORDER BY timestamp ASC
                   
                """)
                results = await cur.fetchall()
                print(f"Encontrados {len(results)} comentarios con state='ANALYSIS'")
                return results
    except Exception as e:
        print(f"Error obteniendo comentarios ANALYSIS: {e}")
        return []


# === ACTUALIZAR EL ESTADO DESPUÉS DEL ANÁLISIS ===
async def update_analysis(comment_id: int, purchase_intent: str, state: str = "ANALYZED"):
    """
    Cambia state de 'ANALYSIS' → 'ANALYZED' (o ERROR, etc.)
    """
    global pool
    if not pool:
        print("Pool no inicializado (update_analysis)")
        return

    valid_intents = ["HIGH", "MEDIUM", "LOW", "NONE", "EMPTY"]
    if purchase_intent not in valid_intents:
        purchase_intent = "NONE"

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE comments 
                    SET 
                        purchase_intent = %s,
                        state = %s
                    WHERE id = %s
                """, (purchase_intent, state, comment_id))
                print(f"Comentario {comment_id} → {purchase_intent} [{state}]")
    except Exception as e:
        print(f"Error actualizando comentario {comment_id}: {e}")

async def mark_all_as_pending():
    """
    (Opcional) Marca todos los comentarios como pendientes (útil para reprocesar)
    """
    global pool
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE comments 
                    SET state = 'PENDING', purchase_intent = NULL, analyzed_at = NULL
                    WHERE state != 'PENDING'
                """)
                print(f"Marcados {cur.rowcount} comentarios como PENDING")
    except Exception as e:
        print(f"Error marcando como pending: {e}")
