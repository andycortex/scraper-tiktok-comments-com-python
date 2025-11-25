# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL = "gemini-2.5-flash"

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3307"))
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB")
    MYSQL_CHARSET = "utf8mb4"

    BATCH_SIZE = 5
    INTERVAL_SECONDS = 60

    CANDIDATE_LABELS = [
    "intención de compra (ej: lo quiero, dónde compro, me interesa)",
    "pregunta sobre precio (ej: cuánto cuesta, tiene valor)",
    "pregunta general (ej: dudas, consultas, información)",
    "elogio (ej: me gusta, buen producto, recomendación)",
    "queja (ej: problema, mala experiencia, no funciona)",
    "comentario neutral o irrelevante (ej: ok, gracias, emojis, saludos)"
    ]
