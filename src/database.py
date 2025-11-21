import aiomysql
from config import Config

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
        maxsize=10,
    )
    print("Pool de conexiones MySQL creado")

async def close_pool():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()
        print("Pool de MySQL cerrado")

async def get_pending_comments(limit: int = 5):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT id, comment 
                FROM comments 
                WHERE analysis_status IS NULL OR analysis_status = 'PENDING'
                ORDER BY created_at ASC 
                LIMIT %s FOR UPDATE SKIP LOCKED
            """, (limit,))
            return await cur.fetchall()

async def update_analysis(comment_id: int, classification: str, status: str):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                UPDATE comments SET
                    classification = %s,
                    analysis_status = %s,
                    analyzed_at = NOW()
                WHERE id = %s
            """, (classification, status, comment_id))